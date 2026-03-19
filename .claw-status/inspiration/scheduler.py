#!/usr/bin/env python3
"""
灵感摄取系统 - 智能调度器 v2.0
防超载: 时间+资源+反馈导向（非API次数）

Author: wdai
Version: 2.0
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import sys

CLAW_STATUS = Path(__file__).parent
sys.path.insert(0, str(CLAW_STATUS))


@dataclass
class SourceMetrics:
    """信息源性能指标"""
    source_id: str
    total_crawls: int = 0
    new_items_found: int = 0
    avg_quality_score: float = 0.0
    last_crawl: Optional[str] = None
    avg_crawl_time_ms: float = 0.0
    success_rate: float = 1.0
    consecutive_empty: int = 0  # 连续空转次数
    
    # 动态调整参数
    current_interval_hours: float = 6.0
    priority_score: float = 0.5


class SmartScheduler:
    """
    智能调度器 v2.0
    
    超载防护策略（包月API友好）:
    1. 时间限制 - 最小间隔、最大运行次数/天
    2. 资源限制 - 单次处理数上限、执行时长上限
    3. 反馈驱动 - 无用户反馈时自动降频
    """
    
    CONFIG = {
        # 空转防护（核心）- 不限制运行次数，限制空转浪费
        'min_interval_minutes': 15,     # 最小间隔15分钟（有产出时可频繁）
        'max_interval_hours': 48,       # 最大间隔（空转惩罚上限）
        'empty_backoff_multiplier': 2,  # 空转后间隔倍增
        'max_consecutive_empty': 5,     # 连续空转5次后停止该源
        
        # 资源限制（防过载）
        'max_items_per_run': 50,        # 单次处理上限（防内存压力）
        'max_crawl_time_seconds': 600,  # 单次执行上限（10分钟）
        
        # 效率优化
        'batch_sources': True,          # 批量处理多个源
        'parallel_crawl': False,        # 是否并行抓取
        
        # 用户反馈驱动
        'user_silence_threshold': 3,    # 3次无反馈触发降频
        'feedback_boost_hours': 1,      # 有反馈时减少1小时间隔
    }
    
    def __init__(self, data_dir: str = "data/scheduler"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics_file = self.data_dir / "source_metrics.json"
        self.daily_stats_file = self.data_dir / "daily_stats_v2.json"
        self.overload_state_file = self.data_dir / "overload_state.json"
        self.feedback_file = self.data_dir / "user_feedback.json"
        
        self.metrics: Dict[str, SourceMetrics] = {}
        
        # 基于时间的统计（非API次数）
        self.daily_run_count = 0
        self.daily_items_processed = 0
        self.daily_crawl_time_seconds = 0
        self.last_run_time = None
        
        # 用户反馈
        self.user_feedback_count = 0
        self.last_user_feedback_time = None
        self.consecutive_no_feedback = 0
        
        self.overload_mode = False
        self.overload_reason = None
        
        self._load_state()
    
    def _load_state(self):
        """加载状态"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    self.metrics = {k: SourceMetrics(**v) for k, v in data.items()}
            except:
                self.metrics = {}
        
        if self.daily_stats_file.exists():
            try:
                with open(self.daily_stats_file, 'r') as f:
                    stats = json.load(f)
                    saved_date = stats.get('date', '')
                    today = datetime.now().strftime('%Y-%m-%d')
                    
                    if saved_date == today:
                        self.daily_run_count = stats.get('run_count', 0)
                        self.daily_items_processed = stats.get('items_processed', 0)
                        self.daily_crawl_time_seconds = stats.get('crawl_time_seconds', 0)
                    else:
                        self._reset_daily_stats()
            except:
                self._reset_daily_stats()
        
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r') as f:
                    fb = json.load(f)
                    self.user_feedback_count = fb.get('count', 0)
                    self.last_user_feedback_time = fb.get('last_time')
                    self.consecutive_no_feedback = fb.get('consecutive_no_feedback', 0)
            except:
                pass
        
        if self.overload_state_file.exists():
            try:
                with open(self.overload_state_file, 'r') as f:
                    state = json.load(f)
                    self.overload_mode = state.get('overload', False)
                    self.overload_reason = state.get('reason')
                    triggered_at = state.get('triggered_at', '')
                    if triggered_at:
                        triggered = datetime.fromisoformat(triggered_at)
                        if datetime.now() - triggered > timedelta(hours=24):
                            self.overload_mode = False
                            self.overload_reason = None
            except:
                self.overload_mode = False
    
    def _save_state(self):
        """保存状态"""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump({k: asdict(v) for k, v in self.metrics.items()}, f, indent=2)
            
            with open(self.daily_stats_file, 'w') as f:
                json.dump({
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'run_count': self.daily_run_count,
                    'items_processed': self.daily_items_processed,
                    'crawl_time_seconds': self.daily_crawl_time_seconds
                }, f)
            
            with open(self.feedback_file, 'w') as f:
                json.dump({
                    'count': self.user_feedback_count,
                    'last_time': self.last_user_feedback_time,
                    'consecutive_no_feedback': self.consecutive_no_feedback
                }, f)
        except:
            pass
    
    def _save_overload_state(self):
        """保存过载状态"""
        try:
            with open(self.overload_state_file, 'w') as f:
                json.dump({
                    'overload': self.overload_mode,
                    'reason': self.overload_reason,
                    'triggered_at': datetime.now().isoformat()
                }, f)
        except:
            pass
    
    def _reset_daily_stats(self):
        """重置每日统计"""
        self.daily_run_count = 0
        self.daily_items_processed = 0
        self.daily_crawl_time_seconds = 0
    
    def record_run_statistics(self, run_data: Dict):
        """
        🆕 记录运行统计历史（新增于2026-03-19）
        
        持久化每次运行的详细统计，用于长期趋势分析
        """
        stats_file = self.data_dir / 'run_history.jsonl'
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'run_count': self.daily_run_count,
            'items_processed': run_data.get('items_processed', 0),
            'items_new': run_data.get('items_new', 0),
            'crawl_time_seconds': run_data.get('crawl_time_seconds', 0),
            'sources_checked': run_data.get('sources_checked', []),
            'overload_mode': self.overload_mode,
            'user_feedback_count': self.user_feedback_count
        }
        
        try:
            with open(stats_file, 'a') as f:
                f.write(json.dumps(record) + '\n')
            print(f"[SmartScheduler] 📝 运行统计已记录 (#{record['run_count']})")
        except Exception as e:
            print(f"[SmartScheduler] ⚠️ 记录统计失败: {e}")
    
    def get_run_history_summary(self, days: int = 7) -> Dict:
        """
        🆕 获取运行历史摘要（新增于2026-03-19）
        
        分析最近N天的运行趋势
        """
        stats_file = self.data_dir / 'run_history.jsonl'
        
        if not stats_file.exists():
            return {'error': '无历史数据'}
        
        records = []
        cutoff = datetime.now() - timedelta(days=days)
        
        try:
            with open(stats_file) as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                        record_time = datetime.fromisoformat(record['timestamp'])
                        if record_time >= cutoff:
                            records.append(record)
                    except:
                        continue
        except:
            return {'error': '读取历史数据失败'}
        
        if not records:
            return {'error': f'过去{days}天无数据'}
        
        # 计算统计
        total_runs = len(records)
        total_items = sum(r.get('items_new', 0) for r in records)
        avg_time = sum(r.get('crawl_time_seconds', 0) for r in records) / total_runs if total_runs > 0 else 0
        items_per_run = total_items / total_runs if total_runs > 0 else 0
        
        return {
            'period_days': days,
            'total_runs': total_runs,
            'total_new_items': total_items,
            'avg_items_per_run': round(items_per_run, 2),
            'avg_run_time_seconds': round(avg_time, 2),
            'latest_records': records[-5:]  # 最近5条
        }
        self._save_state()
    
    def check_system_health(self) -> Tuple[bool, str]:
        """
        检查系统健康状态（资源导向）
        
        Note: 移除全局 last_run_time 检查，改为按源检查 (should_crawl)
        这样允许不同源独立调度，避免单次运行失败影响其他源
        
        Returns:
            (healthy, reason)
        """
        # 1. 检查全局过载
        if self.overload_mode:
            return False, f"系统处于过载保护模式: {self.overload_reason}"
        
        # 2. [已移除] 全局最小间隔检查 -> 移到 should_crawl 按源检查
        # 避免脚本启动时 record_run_start() 更新 last_run_time 导致后续检查失败
        
        # 3. 检查执行时长（如果上次运行太久，延迟下次）
        if self.daily_crawl_time_seconds > self.CONFIG['max_crawl_time_seconds'] * 3:
            return False, f"今日累计执行时间{self.daily_crawl_time_seconds:.0f}秒，建议休息"
        
        # 4. 检查用户反馈沉默
        if self.consecutive_no_feedback >= self.CONFIG['user_silence_threshold']:
            # 不阻止运行，但会降频
            pass
        
        return True, "系统健康"
    
    def should_crawl(self, source_id: str) -> Tuple[bool, str]:
        """判断是否应该抓取该源"""
        # 先检查系统健康
        healthy, reason = self.check_system_health()
        if not healthy:
            return False, reason
        
        # 获取或创建指标
        if source_id not in self.metrics:
            self.metrics[source_id] = SourceMetrics(source_id=source_id)
        
        metric = self.metrics[source_id]
        
        # 检查连续空转过多（停止监控）
        if metric.consecutive_empty >= self.CONFIG['max_consecutive_empty']:
            return False, f"连续空转{metric.consecutive_empty}次，已暂停监控该源"
        
        # 基础间隔检查（支持分钟级）
        if metric.last_crawl:
            last = datetime.fromisoformat(metric.last_crawl)
            minutes_since = (datetime.now() - last).total_seconds() / 60
            
            # 基础间隔（默认6小时 = 360分钟）
            effective_interval_minutes = metric.current_interval_hours * 60
            
            # 用户反馈奖励
            if self.last_user_feedback_time:
                hours_since_fb = (datetime.now() - datetime.fromisoformat(self.last_user_feedback_time)).total_seconds() / 3600
                if hours_since_fb < 24:
                    effective_interval_minutes = max(
                        effective_interval_minutes - self.CONFIG['feedback_boost_hours'] * 60,
                        self.CONFIG['min_interval_minutes']
                    )
            
            # 用户沉默惩罚
            if self.consecutive_no_feedback >= self.CONFIG['user_silence_threshold']:
                effective_interval_minutes = min(
                    effective_interval_minutes * 1.5,
                    self.CONFIG['max_interval_hours'] * 60
                )
            
            if minutes_since < effective_interval_minutes:
                return False, f"距离上次抓取{minutes_since:.0f}分钟，当前间隔{effective_interval_minutes:.0f}分钟"
        
        return True, "允许抓取"
    
    def record_run_start(self):
        """记录运行开始"""
        self.last_run_time = datetime.now()
        self.daily_run_count += 1
    
    def record_crawl(self, source_id: str, new_items: int, quality_scores: List[float], 
                     crawl_time_ms: float, success: bool = True):
        """记录抓取结果"""
        if source_id not in self.metrics:
            self.metrics[source_id] = SourceMetrics(source_id=source_id)
        
        metric = self.metrics[source_id]
        metric.total_crawls += 1
        metric.last_crawl = datetime.now().isoformat()
        metric.success_rate = (metric.success_rate * (metric.total_crawls - 1) + (1.0 if success else 0.0)) / metric.total_crawls
        metric.avg_crawl_time_ms = (metric.avg_crawl_time_ms * (metric.total_crawls - 1) + crawl_time_ms) / metric.total_crawls
        
        # 空转计数
        if new_items == 0:
            metric.consecutive_empty += 1
        else:
            metric.consecutive_empty = 0
            metric.new_items_found += new_items
        
        # 质量分
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            if metric.avg_quality_score == 0:
                metric.avg_quality_score = avg_quality
            else:
                metric.avg_quality_score = metric.avg_quality_score * 0.7 + avg_quality * 0.3
        
        # 更新统计
        self.daily_items_processed += new_items
        self.daily_crawl_time_seconds += crawl_time_ms / 1000
        
        # 动态调整间隔
        self._adjust_interval(source_id, new_items)
        
        self._save_state()
    
    def _adjust_interval(self, source_id: str, new_items: int):
        """动态调整抓取间隔 - 效率优先版"""
        metric = self.metrics[source_id]
        
        # 空转降频（指数退避）
        if metric.consecutive_empty > 0:
            multiplier = self.CONFIG['empty_backoff_multiplier'] ** (metric.consecutive_empty - 1)
            metric.current_interval_hours = min(
                metric.current_interval_hours * multiplier,
                self.CONFIG['max_interval_hours']
            )
        elif new_items > 0:
            # 有产出，快速恢复高频（可以15分钟一次）
            metric.current_interval_hours = max(
                metric.current_interval_hours * 0.5,  # 快速降间隔
                self.CONFIG['min_interval_minutes'] / 60  # 最低15分钟
            )
        
        # 质量调整
        if metric.avg_quality_score > 0:
            if metric.avg_quality_score < 0.4:
                metric.current_interval_hours = min(
                    metric.current_interval_hours * 1.3,
                    self.CONFIG['max_interval_hours']
                )
            elif metric.avg_quality_score > 0.8:
                # 高质量源，允许更频繁
                metric.current_interval_hours = max(
                    metric.current_interval_hours * 0.9,
                    self.CONFIG['min_interval_minutes'] / 60
                )
    
    def record_user_feedback(self, feedback_type: str = "general"):
        """记录用户反馈（驱动调度）"""
        self.user_feedback_count += 1
        self.last_user_feedback_time = datetime.now().isoformat()
        self.consecutive_no_feedback = 0
        self._save_state()
        
        print(f"[SmartScheduler] 👤 记录用户反馈，下次运行将提前")
    
    def record_no_feedback(self):
        """记录无反馈"""
        self.consecutive_no_feedback += 1
        self._save_state()
    
    def _enter_overload_mode(self, reason: str):
        """进入过载保护"""
        self.overload_mode = True
        self.overload_reason = reason
        self._save_overload_state()
        print(f"[SmartScheduler] ⚠️ 进入过载保护: {reason}，24小时后自动解除")
    
    def manual_reset_overload(self):
        """手动解除过载"""
        self.overload_mode = False
        self.overload_reason = None
        self._reset_daily_stats()
        print("[SmartScheduler] ✅ 过载模式已手动解除")
    
    def get_source_report(self) -> Dict:
        """获取源评估报告"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_sources': len(self.metrics),
            'overload_mode': self.overload_mode,
            'overload_reason': self.overload_reason,
            'daily_stats': {
                'run_count': self.daily_run_count,
                'items_processed': self.daily_items_processed,
                'crawl_time_seconds': round(self.daily_crawl_time_seconds, 1)
            },
            'limits': {
                'min_interval_minutes': self.CONFIG['min_interval_minutes'],
                'max_interval_hours': self.CONFIG['max_interval_hours'],
                'max_items_per_run': self.CONFIG['max_items_per_run'],
            },
            'user_feedback': {
                'total': self.user_feedback_count,
                'consecutive_no_feedback': self.consecutive_no_feedback,
                'last_feedback': self.last_user_feedback_time
            },
            'sources': []
        }
        
        for source_id, metric in sorted(
            self.metrics.items(), 
            key=lambda x: x[1].avg_quality_score, 
            reverse=True
        ):
            if metric.avg_quality_score >= 0.7:
                grade = "A"
            elif metric.avg_quality_score >= 0.5:
                grade = "B"
            elif metric.avg_quality_score >= 0.3:
                grade = "C"
            else:
                grade = "D"
            
            interval_minutes = metric.current_interval_hours * 60
            
            report['sources'].append({
                'id': source_id,
                'grade': grade,
                'quality_score': round(metric.avg_quality_score, 2),
                'total_crawls': metric.total_crawls,
                'new_items': metric.new_items_found,
                'success_rate': round(metric.success_rate, 2),
                'current_interval_minutes': round(interval_minutes, 0),
                'consecutive_empty': metric.consecutive_empty,
                'recommendation': self._get_recommendation(metric)
            })
        
        return report
    
    def _get_recommendation(self, metric: SourceMetrics) -> str:
        """生成建议"""
        if metric.consecutive_empty >= self.CONFIG['max_consecutive_empty']:
            return "⏹️ 已暂停: 连续空转过多"
        elif metric.avg_quality_score < 0.3 and metric.total_crawls > 10:
            return "建议淘汰: 质量持续低于阈值"
        elif metric.current_interval_hours >= self.CONFIG['max_interval_hours'] * 0.8:
            return f"已降频至{metric.current_interval_hours:.0f}小时: 空转频繁"
        elif metric.consecutive_empty >= 3:
            return f"即将降频: 连续{metric.consecutive_empty}次空转"
        elif metric.current_interval_hours <= 0.5:  # <=30分钟
            return "⚡ 高频模式: 产出丰富"
        elif metric.avg_quality_score > 0.8 and metric.new_items_found > 20:
            return "⭐ 高质量源: 保持高频"
        elif self.consecutive_no_feedback >= self.CONFIG['user_silence_threshold']:
            return "用户沉默: 已自动降频"
        else:
            return "正常"
    
    def get_next_crawl_schedule(self) -> List[Dict]:
        """获取下次抓取计划（分钟级精度）"""
        schedule = []
        now = datetime.now()
        
        for source_id, metric in self.metrics.items():
            if metric.last_crawl:
                last = datetime.fromisoformat(metric.last_crawl)
                effective_interval_hours = metric.current_interval_hours
                
                # 应用反馈调整（转换为小时）
                if self.last_user_feedback_time:
                    hours_since_fb = (now - datetime.fromisoformat(self.last_user_feedback_time)).total_seconds() / 3600
                    if hours_since_fb < 24:
                        effective_interval_hours = max(
                            effective_interval_hours - self.CONFIG['feedback_boost_hours'], 
                            self.CONFIG['min_interval_minutes'] / 60
                        )
                
                # 用户沉默惩罚
                if self.consecutive_no_feedback >= self.CONFIG['user_silence_threshold']:
                    effective_interval_hours = min(
                        effective_interval_hours * 1.5, 
                        self.CONFIG['max_interval_hours']
                    )
                
                next_crawl = last + timedelta(hours=effective_interval_hours)
                wait_minutes = max(0, (next_crawl - now).total_seconds() / 60)
            else:
                wait_minutes = 0
            
            schedule.append({
                'source': source_id,
                'wait_minutes': round(wait_minutes, 0),
                'wait_hours': round(wait_minutes / 60, 1),
                'expected_quality': round(metric.avg_quality_score, 2),
                'consecutive_empty': metric.consecutive_empty
            })
        
        return sorted(schedule, key=lambda x: x['wait_minutes'])


# 全局实例
_scheduler_instance = None

def get_scheduler() -> SmartScheduler:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = SmartScheduler()
    return _scheduler_instance


def main():
    scheduler = get_scheduler()
    
    print("="*60)
    print("🧠 智能调度器 v2.0 状态报告（效率优先版）")
    print("="*60)
    
    report = scheduler.get_source_report()
    print(f"\n📊 系统状态:")
    print(f"   监控源: {report['total_sources']}")
    print(f"   今日运行: {report['daily_stats']['run_count']}次")
    print(f"   处理项目: {report['daily_stats']['items_processed']}")
    print(f"   执行时间: {report['daily_stats']['crawl_time_seconds']}s")
    print(f"   过载模式: {'⚠️ ' + report['overload_reason'] if report['overload_mode'] else '✅ 正常'}")
    
    limits = report.get('limits', {})
    print(f"\n⚙️ 限制配置:")
    print(f"   最小间隔: {limits.get('min_interval_minutes', 15)}分钟")
    print(f"   最大间隔: {limits.get('max_interval_hours', 48)}小时")
    print(f"   单次上限: {limits.get('max_items_per_run', 50)}条")
    
    print(f"\n👤 用户反馈:")
    print(f"   总反馈: {report['user_feedback']['total']}")
    print(f"   连续无反馈: {report['user_feedback']['consecutive_no_feedback']}次")
    
    print(f"\n📈 源评估（按质量排序）:")
    for src in report['sources'][:5]:
        interval_str = f"{src['current_interval_minutes']:.0f}分钟" if src['current_interval_minutes'] < 60 else f"{src['current_interval_minutes']/60:.1f}小时"
        print(f"   {src['grade']} {src['id']}: {interval_str} | {src['recommendation']}")
    
    print(f"\n⏰ 下次运行计划:")
    schedule = scheduler.get_next_crawl_schedule()[:3]
    for item in schedule:
        if item['wait_minutes'] < 60:
            time_str = f"{item['wait_minutes']:.0f}分钟后"
        else:
            time_str = f"{item['wait_hours']:.1f}小时后"
        empty_warn = f" (连续空转{item['consecutive_empty']}次)" if item['consecutive_empty'] > 0 else ""
        print(f"   {item['source']}: {time_str}{empty_warn}")
    
    # 🆕 显示运行历史摘要（新增于2026-03-19）
    print(f"\n📈 运行历史（最近7天）:")
    history = scheduler.get_run_history_summary(days=7)
    if 'error' in history:
        print(f"   {history['error']}")
    else:
        print(f"   总运行: {history['total_runs']}次")
        print(f"   新内容: {history['total_new_items']}条")
        print(f"   平均每次: {history['avg_items_per_run']}条")
        print(f"   平均耗时: {history['avg_run_time_seconds']}s")
    
    print("="*60)


if __name__ == "__main__":
    main()
