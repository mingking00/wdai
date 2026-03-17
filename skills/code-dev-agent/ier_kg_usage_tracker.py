"""
经验使用频率追踪系统
基于Mem0自适应记忆机制实现

功能：
1. 追踪经验访问次数和时间
2. 计算经验活跃度评分
3. 自动识别高频/低频经验
4. 支持TTL (Time To Live) 管理
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import threading


@dataclass
class AccessRecord:
    """访问记录"""
    timestamp: float
    context: str  # 访问上下文（任务描述）
    source: str   # 访问来源（检索/推荐/直接）


@dataclass
class ExperienceMetrics:
    """经验指标"""
    experience_id: str
    experience_name: str
    
    # 访问统计
    total_accesses: int = 0
    daily_accesses: Dict[str, int] = None  # 按天统计
    last_accessed: float = 0.0
    first_accessed: float = 0.0
    
    # 访问记录（最近100条）
    access_history: List[AccessRecord] = None
    
    # 活跃度评分 (0-100)
    activity_score: float = 0.0
    
    # 频率分类
    frequency_class: str = "unknown"  # high/medium/low/archived
    
    # TTL管理
    ttl_days: int = 90  # 默认90天
    expires_at: float = 0.0
    
    def __post_init__(self):
        if self.daily_accesses is None:
            self.daily_accesses = {}
        if self.access_history is None:
            self.access_history = []


class ExperienceUsageTracker:
    """
    经验使用追踪器
    
    实现自适应记忆机制：
    - 高频经验: 快速检索，长期保留
    - 中频经验: 标准检索，定期评估
    - 低频经验: 降级检索，准备归档
    """
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.metrics_file = self.data_dir / "ier_kg_usage_metrics.json"
        self.metrics: Dict[str, ExperienceMetrics] = {}
        self.lock = threading.Lock()
        
        # 频率分类阈值
        self.thresholds = {
            "high": 10,      # 10次以上为高频
            "medium": 3,     # 3-9次为中频
            "low": 1,        # 1-2次为低频
            "archived": 0    # 0次为归档候选
        }
        
        self._load_metrics()
    
    def _load_metrics(self):
        """加载指标数据"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    for exp_id, metric_data in data.items():
                        # 转换access_history
                        if 'access_history' in metric_data:
                            metric_data['access_history'] = [
                                AccessRecord(**r) for r in metric_data['access_history']
                            ]
                        self.metrics[exp_id] = ExperienceMetrics(**metric_data)
            except Exception as e:
                print(f"[UsageTracker] 加载指标失败: {e}")
    
    def _save_metrics(self):
        """保存指标数据"""
        try:
            with self.lock:
                data = {}
                for exp_id, metric in self.metrics.items():
                    metric_dict = asdict(metric)
                    # 转换access_history为可序列化格式
                    metric_dict['access_history'] = [
                        asdict(r) for r in metric.access_history
                    ]
                    data[exp_id] = metric_dict
                
                with open(self.metrics_file, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[UsageTracker] 保存指标失败: {e}")
    
    def record_access(self, experience_id: str, experience_name: str,
                     context: str = "", source: str = "retrieval"):
        """
        记录经验访问
        
        Args:
            experience_id: 经验ID
            experience_name: 经验名称
            context: 访问上下文
            source: 访问来源 (retrieval/recommendation/direct)
        """
        with self.lock:
            now = time.time()
            today = datetime.now().strftime("%Y-%m-%d")
            
            # 获取或创建指标
            if experience_id not in self.metrics:
                self.metrics[experience_id] = ExperienceMetrics(
                    experience_id=experience_id,
                    experience_name=experience_name,
                    first_accessed=now
                )
            
            metric = self.metrics[experience_id]
            
            # 更新统计
            metric.total_accesses += 1
            metric.last_accessed = now
            metric.daily_accesses[today] = metric.daily_accesses.get(today, 0) + 1
            
            # 添加访问记录
            record = AccessRecord(
                timestamp=now,
                context=context[:100],  # 限制长度
                source=source
            )
            metric.access_history.append(record)
            
            # 只保留最近100条记录
            if len(metric.access_history) > 100:
                metric.access_history = metric.access_history[-100:]
            
            # 重新计算活跃度
            self._calculate_activity_score(metric)
            
            # 更新频率分类
            self._update_frequency_class(metric)
        
        # 异步保存
        self._save_metrics()
    
    def _calculate_activity_score(self, metric: ExperienceMetrics):
        """
        计算活跃度评分
        
        算法：
        - 基础分: 访问次数 * 5 (最高50分)
        - 时效分: 最近访问时间衰减 (最高30分)
        - 趋势分: 近期访问频率 (最高20分)
        """
        now = time.time()
        
        # 基础分
        base_score = min(metric.total_accesses * 5, 50)
        
        # 时效分 (最近访问越近分越高)
        days_since_last = (now - metric.last_accessed) / 86400
        recency_score = max(0, 30 - days_since_last) if metric.last_accessed > 0 else 0
        
        # 趋势分 (最近7天访问次数)
        recent_accesses = 0
        for i in range(7):
            day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            recent_accesses += metric.daily_accesses.get(day, 0)
        trend_score = min(recent_accesses * 2, 20)
        
        metric.activity_score = base_score + recency_score + trend_score
    
    def _update_frequency_class(self, metric: ExperienceMetrics):
        """更新频率分类"""
        accesses = metric.total_accesses
        
        if accesses >= self.thresholds["high"]:
            metric.frequency_class = "high"
            metric.ttl_days = 365  # 高频保留1年
        elif accesses >= self.thresholds["medium"]:
            metric.frequency_class = "medium"
            metric.ttl_days = 180  # 中频保留6个月
        elif accesses >= self.thresholds["low"]:
            metric.frequency_class = "low"
            metric.ttl_days = 90   # 低频保留3个月
        else:
            metric.frequency_class = "archived"
            metric.ttl_days = 30   # 归档候选保留1个月
        
        # 更新过期时间
        metric.expires_at = metric.last_accessed + (metric.ttl_days * 86400)
    
    def get_metrics(self, experience_id: str) -> Optional[ExperienceMetrics]:
        """获取经验指标"""
        return self.metrics.get(experience_id)
    
    def get_all_metrics(self) -> Dict[str, ExperienceMetrics]:
        """获取所有指标"""
        return self.metrics.copy()
    
    def get_frequency_distribution(self) -> Dict[str, int]:
        """获取频率分布统计"""
        distribution = {"high": 0, "medium": 0, "low": 0, "archived": 0, "unknown": 0}
        
        for metric in self.metrics.values():
            distribution[metric.frequency_class] = distribution.get(metric.frequency_class, 0) + 1
        
        return distribution
    
    def get_top_experiences(self, n: int = 10) -> List[ExperienceMetrics]:
        """获取Top N活跃经验"""
        sorted_metrics = sorted(
            self.metrics.values(),
            key=lambda m: m.activity_score,
            reverse=True
        )
        return sorted_metrics[:n]
    
    def get_expired_experiences(self) -> List[ExperienceMetrics]:
        """获取已过期的经验"""
        now = time.time()
        expired = []
        
        for metric in self.metrics.values():
            if metric.expires_at > 0 and metric.expires_at < now:
                expired.append(metric)
        
        return expired
    
    def generate_report(self) -> Dict:
        """生成使用统计报告"""
        total_experiences = len(self.metrics)
        
        if total_experiences == 0:
            return {"message": "暂无使用数据"}
        
        # 频率分布
        freq_dist = self.get_frequency_distribution()
        
        # Top经验
        top_exp = self.get_top_experiences(5)
        
        # 过期经验
        expired = self.get_expired_experiences()
        
        report = {
            "total_experiences": total_experiences,
            "total_accesses": sum(m.total_accesses for m in self.metrics.values()),
            "frequency_distribution": freq_dist,
            "top_experiences": [
                {
                    "name": m.experience_name,
                    "accesses": m.total_accesses,
                    "score": round(m.activity_score, 2),
                    "class": m.frequency_class
                }
                for m in top_exp
            ],
            "expired_count": len(expired),
            "avg_activity_score": sum(m.activity_score for m in self.metrics.values()) / total_experiences
        }
        
        return report


# 全局追踪器实例
_tracker_instance = None

def get_usage_tracker(data_dir: str = ".") -> ExperienceUsageTracker:
    """获取全局使用追踪器实例"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = ExperienceUsageTracker(data_dir)
    return _tracker_instance


if __name__ == "__main__":
    # 测试
    tracker = ExperienceUsageTracker(".")
    
    # 模拟访问
    tracker.record_access("exp_001", "使用@lru_cache", "缓存优化任务", "retrieval")
    tracker.record_access("exp_001", "使用@lru_cache", "另一个任务", "retrieval")
    
    # 生成报告
    report = tracker.generate_report()
    print(json.dumps(report, indent=2))
