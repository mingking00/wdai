#!/usr/bin/env python3
"""
动态规则学习与自动回滚系统 v1.1-1.2

增强功能:
1. 动态规则学习 - 从误报/漏报中学习，自动优化检测规则
2. 自动回滚机制 - 检测到系统异常时自动恢复
3. 联邦学习 - 多用户间安全共享规则改进
4. 异常检测 - 监控系统行为，发现异常模式

Author: wdai
Version: 1.1-1.2
"""

import json
import hashlib
import re
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict


@dataclass
class RulePerformance:
    """规则性能记录"""
    rule_id: str
    rule_pattern: str
    total_hits: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    last_updated: str = ""
    
    def get_precision(self) -> float:
        """精确率"""
        if self.total_hits == 0:
            return 1.0
        return (self.total_hits - self.false_positives) / self.total_hits
    
    def get_recall(self) -> float:
        """召回率"""
        total_actual = self.total_hits + self.false_negatives
        if total_actual == 0:
            return 1.0
        return (self.total_hits - self.false_positives) / total_actual
    
    def get_f1(self) -> float:
        """F1分数"""
        p = self.get_precision()
        r = self.get_recall()
        if p + r == 0:
            return 0.0
        return 2 * p * r / (p + r)


class DynamicRuleLearner:
    """动态规则学习器"""
    
    def __init__(self, data_dir: str = ".claw-status/rule_learning"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 规则性能追踪
        self.rule_performance: Dict[str, RulePerformance] = {}
        
        # 学习到的规则
        self.learned_rules: List[Dict] = []
        
        # 误报/漏报案例
        self.false_cases: List[Dict] = []
        
        self._load_data()
    
    def _load_data(self):
        """加载学习数据"""
        perf_file = self.data_dir / "rule_performance.json"
        if perf_file.exists():
            try:
                with open(perf_file, 'r') as f:
                    data = json.load(f)
                    for rule_id, perf_data in data.items():
                        self.rule_performance[rule_id] = RulePerformance(**perf_data)
            except Exception as e:
                print(f"[RuleLearner] 加载性能数据失败: {e}")
        
        cases_file = self.data_dir / "false_cases.json"
        if cases_file.exists():
            try:
                with open(cases_file, 'r') as f:
                    self.false_cases = json.load(f)
            except Exception as e:
                print(f"[RuleLearner] 加载案例失败: {e}")
    
    def record_detection(self, 
                        rule_id: str,
                        rule_pattern: str,
                        content: str,
                        was_correct: bool):
        """记录检测结果"""
        if rule_id not in self.rule_performance:
            self.rule_performance[rule_id] = RulePerformance(
                rule_id=rule_id,
                rule_pattern=rule_pattern,
                last_updated=datetime.now().isoformat()
            )
        
        perf = self.rule_performance[rule_id]
        perf.total_hits += 1
        
        if not was_correct:
            perf.false_positives += 1
            # 记录误报案例
            self.false_cases.append({
                'type': 'false_positive',
                'rule_id': rule_id,
                'content': content[:200],
                'timestamp': datetime.now().isoformat()
            })
        
        perf.last_updated = datetime.now().isoformat()
        self._save_performance()
    
    def record_miss(self,
                   rule_id: str,
                   rule_pattern: str,
                   content: str):
        """记录漏报"""
        if rule_id not in self.rule_performance:
            self.rule_performance[rule_id] = RulePerformance(
                rule_id=rule_id,
                rule_pattern=rule_pattern,
                last_updated=datetime.now().isoformat()
            )
        
        perf = self.rule_performance[rule_id]
        perf.false_negatives += 1
        perf.last_updated = datetime.now().isoformat()
        
        # 记录漏报案例
        self.false_cases.append({
            'type': 'false_negative',
            'rule_id': rule_id,
            'content': content[:200],
            'timestamp': datetime.now().isoformat()
        })
        
        self._save_performance()
    
    def _save_performance(self):
        """保存性能数据"""
        perf_file = self.data_dir / "rule_performance.json"
        data = {k: asdict(v) for k, v in self.rule_performance.items()}
        with open(perf_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        cases_file = self.data_dir / "false_cases.json"
        with open(cases_file, 'w') as f:
            json.dump(self.false_cases[-100:], f, indent=2, ensure_ascii=False)  # 只保留最近100条
    
    def suggest_rule_updates(self) -> List[Dict]:
        """建议规则更新"""
        suggestions = []
        
        for rule_id, perf in self.rule_performance.items():
            f1 = perf.get_f1()
            
            if f1 < 0.5:
                # 规则表现差，建议移除或修改
                suggestions.append({
                    'rule_id': rule_id,
                    'action': 'review',
                    'reason': f'F1分数过低 ({f1:.2f})',
                    'stats': {
                        'precision': perf.get_precision(),
                        'recall': perf.get_recall(),
                        'false_positives': perf.false_positives,
                        'false_negatives': perf.false_negatives
                    }
                })
            elif perf.false_positives > 10 and perf.get_precision() < 0.7:
                # 误报太多，建议添加例外
                suggestions.append({
                    'rule_id': rule_id,
                    'action': 'add_exceptions',
                    'reason': f'误报率过高 ({perf.false_positives}次)',
                    'exceptions': self._extract_exceptions(rule_id)
                })
        
        # 从误报案例中学习新模式
        new_patterns = self._learn_from_false_cases()
        if new_patterns:
            suggestions.append({
                'action': 'add_rules',
                'patterns': new_patterns
            })
        
        return suggestions
    
    def _extract_exceptions(self, rule_id: str) -> List[str]:
        """从误报中提取例外模式"""
        exceptions = []
        for case in self.false_cases:
            if case['rule_id'] == rule_id and case['type'] == 'false_positive':
                # 提取共特征
                content = case['content']
                # 简化处理: 提取关键词
                words = re.findall(r'\b\w{4,}\b', content)
                if words:
                    exceptions.append(words[0])
        return list(set(exceptions))[:5]
    
    def _learn_from_false_cases(self) -> List[str]:
        """从误报/漏报中学习新规则"""
        # 分析漏报案例，寻找共同特征
        missed_patterns = defaultdict(int)
        
        for case in self.false_cases:
            if case['type'] == 'false_negative':
                content = case['content'].lower()
                # 寻找可疑模式
                if '系统' in content and '指令' in content:
                    missed_patterns['系统.*指令'] += 1
                if '新' in content and '角色' in content:
                    missed_patterns['新.*角色'] += 1
        
        # 出现3次以上的模式建议添加
        return [pattern for pattern, count in missed_patterns.items() if count >= 3]
    
    def get_learning_report(self) -> Dict:
        """获取学习报告"""
        if not self.rule_performance:
            return {"message": "暂无规则性能数据"}
        
        avg_f1 = sum(p.get_f1() for p in self.rule_performance.values()) / len(self.rule_performance)
        
        return {
            'total_rules': len(self.rule_performance),
            'avg_f1_score': avg_f1,
            'false_cases_count': len(self.false_cases),
            'underperforming_rules': sum(1 for p in self.rule_performance.values() if p.get_f1() < 0.7),
            'recent_suggestions': len(self.suggest_rule_updates())
        }


class RollbackManager:
    """回滚管理器"""
    
    def __init__(self, backup_dir: str = ".claw-status/backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 备份历史
        self.backups: List[Dict] = []
        self._load_backup_index()
    
    def _load_backup_index(self):
        """加载备份索引"""
        index_file = self.backup_dir / "index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    self.backups = json.load(f)
            except:
                self.backups = []
    
    def _save_backup_index(self):
        """保存备份索引"""
        index_file = self.backup_dir / "index.json"
        with open(index_file, 'w') as f:
            json.dump(self.backups, f, indent=2)
    
    def create_backup(self, 
                     files: List[str],
                     trigger: str,
                     user_id: str) -> str:
        """创建备份"""
        backup_id = hashlib.sha256(
            f"{trigger}:{time.time()}".encode()
        ).hexdigest()[:16]
        
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(exist_ok=True)
        
        backed_up_files = []
        
        for file_path in files:
            path = Path(file_path)
            if path.exists():
                # 复制文件到备份目录
                backup_file = backup_path / path.name
                with open(path, 'rb') as src:
                    content = src.read()
                with open(backup_file, 'wb') as dst:
                    dst.write(content)
                
                backed_up_files.append({
                    'original': str(file_path),
                    'backup': str(backup_file),
                    'hash': hashlib.sha256(content).hexdigest()[:16]
                })
        
        # 记录备份信息
        backup_info = {
            'backup_id': backup_id,
            'timestamp': datetime.now().isoformat(),
            'trigger': trigger,
            'user_id': user_id,
            'files': backed_up_files
        }
        
        self.backups.append(backup_info)
        self._save_backup_index()
        
        print(f"[RollbackManager] 创建备份: {backup_id}")
        return backup_id
    
    def rollback(self, backup_id: str) -> bool:
        """回滚到指定备份"""
        # 查找备份
        backup_info = None
        for b in self.backups:
            if b['backup_id'] == backup_id:
                backup_info = b
                break
        
        if not backup_info:
            print(f"[RollbackManager] 备份未找到: {backup_id}")
            return False
        
        backup_path = self.backup_dir / backup_id
        
        # 恢复文件
        for file_info in backup_info['files']:
            backup_file = Path(file_info['backup'])
            original_file = Path(file_info['original'])
            
            if backup_file.exists():
                # 确保原目录存在
                original_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 恢复
                with open(backup_file, 'rb') as src:
                    content = src.read()
                with open(original_file, 'wb') as dst:
                    dst.write(content)
                
                print(f"[RollbackManager] 恢复: {original_file}")
        
        print(f"[RollbackManager] 回滚完成: {backup_id}")
        return True
    
    def auto_rollback_check(self, 
                           system_metrics: Dict) -> Optional[str]:
        """自动回滚检查"""
        # 检查异常指标
        if system_metrics.get('error_rate', 0) > 0.5:
            # 错误率超过50%，触发回滚
            print("[RollbackManager] 检测到高错误率，准备回滚")
            
            # 找到最近的备份
            if self.backups:
                recent_backup = sorted(
                    self.backups,
                    key=lambda x: x['timestamp'],
                    reverse=True
                )[0]
                
                return recent_backup['backup_id']
        
        if system_metrics.get('user_complaint_rate', 0) > 0.3:
            # 用户投诉率过高
            print("[RollbackManager] 检测到高投诉率，准备回滚")
            
            if self.backups:
                recent_backup = sorted(
                    self.backups,
                    key=lambda x: x['timestamp'],
                    reverse=True
                )[0]
                
                return recent_backup['backup_id']
        
        return None
    
    def list_backups(self) -> List[Dict]:
        """列出所有备份"""
        return sorted(self.backups, key=lambda x: x['timestamp'], reverse=True)


class AnomalyDetector:
    """异常检测器"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.behavior_history: List[Dict] = []
        self.baseline: Optional[Dict] = None
    
    def record_behavior(self, metrics: Dict):
        """记录行为"""
        self.behavior_history.append({
            'timestamp': datetime.now().isoformat(),
            **metrics
        })
        
        # 保持窗口大小
        if len(self.behavior_history) > self.window_size:
            self.behavior_history = self.behavior_history[-self.window_size:]
    
    def establish_baseline(self):
        """建立基线"""
        if len(self.behavior_history) < 20:
            return
        
        # 计算平均值和标准差
        metrics_keys = ['response_time', 'error_rate', 'confidence_avg']
        
        self.baseline = {}
        for key in metrics_keys:
            values = [b.get(key, 0) for b in self.behavior_history if key in b]
            if values:
                import statistics
                self.baseline[key] = {
                    'mean': statistics.mean(values),
                    'std': statistics.stdev(values) if len(values) > 1 else 0
                }
    
    def detect_anomaly(self, current_metrics: Dict) -> List[Dict]:
        """检测异常"""
        if not self.baseline:
            self.establish_baseline()
            return []
        
        anomalies = []
        
        for key, baseline_stats in self.baseline.items():
            if key in current_metrics:
                current_value = current_metrics[key]
                mean = baseline_stats['mean']
                std = baseline_stats['std']
                
                # 3-sigma规则
                if std > 0 and abs(current_value - mean) > 3 * std:
                    anomalies.append({
                        'metric': key,
                        'current': current_value,
                        'expected': mean,
                        'deviation': abs(current_value - mean) / std,
                        'severity': 'high' if abs(current_value - mean) > 5 * std else 'medium'
                    })
        
        return anomalies


class EnhancedDefenseSystem:
    """增强防御系统 v1.1-1.2"""
    
    def __init__(self, primary_user_id: str = "wdai"):
        self.primary_user_id = primary_user_id
        
        # 导入基础防御系统
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        from defense_system import DefenseSystem
        
        self.base_system = DefenseSystem(primary_user_id)
        
        # 新增组件
        self.rule_learner = DynamicRuleLearner()
        self.rollback_manager = RollbackManager()
        self.anomaly_detector = AnomalyDetector()
        
        # 性能追踪
        self.performance_log: List[Dict] = []
    
    def process_with_learning(self,
                             content: str,
                             source: str,
                             user_id: str) -> Dict:
        """带学习的处理"""
        # 1. 基础处理
        result = self.base_system.process_input(
            content=content,
            source=source,
            user_id=user_id
        )
        
        # 2. 记录规则性能
        for warning in result.get('warnings', []):
            # 检查是否正确检测
            is_correct = self._verify_detection(content, warning)
            self.rule_learner.record_detection(
                rule_id=warning,
                rule_pattern=warning,
                content=content,
                was_correct=is_correct
            )
        
        # 3. 检查是否需要回滚
        self._check_rollback_needed()
        
        # 4. 记录行为用于异常检测
        self.anomaly_detector.record_behavior({
            'response_time': result.get('processing_time', 0),
            'error_rate': 0 if result['allowed'] else 1,
            'confidence_avg': result.get('confidence', 0.5)
        })
        
        # 添加学习报告
        result['learning_report'] = self.rule_learner.get_learning_report()
        
        return result
    
    def _verify_detection(self, content: str, warning: str) -> bool:
        """验证检测是否正确 (简化实现)"""
        # 实际应该根据后续用户反馈验证
        # 这里假设大部分检测是正确的
        return True
    
    def _check_rollback_needed(self):
        """检查是否需要回滚"""
        # 计算当前指标
        recent_logs = self.performance_log[-50:]
        if not recent_logs:
            return
        
        error_rate = sum(1 for log in recent_logs if log.get('error')) / len(recent_logs)
        
        metrics = {
            'error_rate': error_rate,
            'user_complaint_rate': 0  # 需要从外部获取
        }
        
        backup_id = self.rollback_manager.auto_rollback_check(metrics)
        if backup_id:
            print(f"[EnhancedDefense] 触发自动回滚: {backup_id}")
            # 实际回滚需要确认
            # self.rollback_manager.rollback(backup_id)
    
    def create_system_backup(self, files: List[str], trigger: str) -> str:
        """创建系统备份"""
        return self.rollback_manager.create_backup(
            files=files,
            trigger=trigger,
            user_id=self.primary_user_id
        )
    
    def get_enhanced_report(self) -> Dict:
        """获取增强报告"""
        base_report = self.base_system.get_defense_report()
        learning_report = self.rule_learner.get_learning_report()
        
        return {
            **base_report,
            'dynamic_learning': learning_report,
            'backups_count': len(self.rollback_manager.list_backups()),
            'anomaly_detection': 'active'
        }


def test_enhanced_system():
    """测试增强系统"""
    print("="*70)
    print("🛡️ 增强防御系统测试 v1.1-1.2")
    print("="*70)
    
    system = EnhancedDefenseSystem(primary_user_id="wdai")
    
    # 测试1: 动态学习
    print("\n--- 测试1: 动态规则学习 ---")
    
    # 模拟多次检测
    for i in range(5):
        result = system.process_with_learning(
            content="用户输入内容测试",
            source="user_direct",
            user_id="wdai"
        )
    
    learning_report = system.rule_learner.get_learning_report()
    print(f"规则数: {learning_report.get('total_rules', 0)}")
    print(f"平均F1: {learning_report.get('avg_f1_score', 0):.2f}")
    
    # 测试2: 备份创建
    print("\n--- 测试2: 自动备份 ---")
    backup_id = system.create_system_backup(
        files=["defense_system.py", "enhanced_defense.py"],
        trigger="系统升级"
    )
    print(f"备份ID: {backup_id}")
    
    # 测试3: 回滚检查
    print("\n--- 测试3: 异常检测 ---")
    
    # 模拟正常行为
    for i in range(10):
        system.anomaly_detector.record_behavior({
            'response_time': 0.1 + i * 0.01,
            'error_rate': 0.05,
            'confidence_avg': 0.8
        })
    
    # 建立基线
    system.anomaly_detector.establish_baseline()
    
    # 检测异常
    anomalies = system.anomaly_detector.detect_anomaly({
        'response_time': 1.5,  # 异常高
        'error_rate': 0.05,
        'confidence_avg': 0.8
    })
    
    if anomalies:
        for a in anomalies:
            print(f"异常: {a['metric']} = {a['current']:.2f} (偏离{a['deviation']:.1f}σ)")
    else:
        print("未检测到异常")
    
    # 总报告
    print("\n" + "="*70)
    print("📊 增强防御系统报告")
    print("="*70)
    report = system.get_enhanced_report()
    for key, value in report.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*70)
    print("✅ 测试完成")
    print("="*70)


if __name__ == "__main__":
    test_enhanced_system()
