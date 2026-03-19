#!/usr/bin/env python3
"""
联邦学习与自适应阈值系统 v1.3-1.4

增强功能:
1. 联邦学习 - 多用户间安全共享规则改进，不泄露隐私
2. 自适应阈值 - 根据用户水平动态调整检测严格度
3. 个性化策略 - 不同用户不同交互模式
4. 群体智慧 - 从多用户数据中提取共性模式

Author: wdai
Version: 1.3-1.4
"""

import json
import hashlib
import numpy as np
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import copy


@dataclass
class FederatedUpdate:
    """联邦学习更新包"""
    update_id: str
    user_hash: str  # 用户匿名标识
    rule_improvements: Dict  # 规则改进 (梯度/调整)
    timestamp: str
    privacy_budget: float  # 差分隐私预算
    
    def anonymize(self) -> 'FederatedUpdate':
        """匿名化处理"""
        # 添加差分隐私噪声
        noisy_improvements = {}
        for rule_id, improvement in self.rule_improvements.items():
            if isinstance(improvement, (int, float)):
                # 添加拉普拉斯噪声
                noise = np.random.laplace(0, 1.0 / self.privacy_budget)
                noisy_improvements[rule_id] = improvement + noise
            else:
                noisy_improvements[rule_id] = improvement
        
        return FederatedUpdate(
            update_id=self.update_id,
            user_hash="anonymous",  # 隐藏真实身份
            rule_improvements=noisy_improvements,
            timestamp=self.timestamp,
            privacy_budget=self.privacy_budget
        )


class FederatedLearningServer:
    """联邦学习服务器"""
    
    def __init__(self, data_dir: str = ".claw-status/federated"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 聚合后的全局模型
        self.global_rules: Dict[str, Dict] = {}
        
        # 用户更新历史
        self.updates: List[FederatedUpdate] = []
        
        # 共识规则
        self.consensus_rules: Set[str] = set()
        
        self._load_global_model()
    
    def _load_global_model(self):
        """加载全局模型"""
        model_file = self.data_dir / "global_model.json"
        if model_file.exists():
            try:
                with open(model_file, 'r') as f:
                    self.global_rules = json.load(f)
            except Exception as e:
                print(f"[FederatedServer] 加载模型失败: {e}")
    
    def _save_global_model(self):
        """保存全局模型"""
        model_file = self.data_dir / "global_model.json"
        with open(model_file, 'w') as f:
            json.dump(self.global_rules, f, indent=2, ensure_ascii=False)
    
    def receive_update(self, update: FederatedUpdate, min_users: int = 3):
        """接收用户更新"""
        # 匿名化
        anon_update = update.anonymize()
        self.updates.append(anon_update)
        
        print(f"[FederatedServer] 接收更新: {update.update_id} (隐私预算: {update.privacy_budget})")
        
        # 检查是否达到聚合阈值
        if len(self.updates) >= min_users:
            self._aggregate_updates()
    
    def _aggregate_updates(self):
        """聚合更新 (联邦平均)"""
        print(f"[FederatedServer] 聚合 {len(self.updates)} 个用户更新")
        
        # 按规则分组
        rule_updates = defaultdict(list)
        for update in self.updates:
            for rule_id, improvement in update.rule_improvements.items():
                rule_updates[rule_id].append(improvement)
        
        # 计算平均改进
        for rule_id, improvements in rule_updates.items():
            if len(improvements) >= 3:  # 至少3个用户同意
                avg_improvement = np.mean(improvements)
                
                if rule_id not in self.global_rules:
                    self.global_rules[rule_id] = {}
                
                self.global_rules[rule_id]['aggregated_improvement'] = avg_improvement
                self.global_rules[rule_id]['consensus_count'] = len(improvements)
                self.global_rules[rule_id]['last_updated'] = datetime.now().isoformat()
                
                # 达成共识
                if len(improvements) >= 5:
                    self.consensus_rules.add(rule_id)
        
        # 清空已处理的更新
        self.updates = []
        
        # 保存
        self._save_global_model()
        
        print(f"[FederatedServer] 聚合完成，共识规则: {len(self.consensus_rules)}")
    
    def get_global_update(self, user_id: str) -> Dict:
        """获取全局更新"""
        # 用户只能看到聚合后的结果，无法反推其他用户数据
        return {
            'global_rules': self.global_rules,
            'consensus_rules': list(self.consensus_rules),
            'timestamp': datetime.now().isoformat()
        }
    
    def extract_common_patterns(self) -> List[Dict]:
        """提取跨用户共性模式"""
        patterns = []
        
        # 分析高频误报模式
        for rule_id, rule_data in self.global_rules.items():
            if rule_data.get('consensus_count', 0) >= 5:
                patterns.append({
                    'pattern_id': rule_id,
                    'confidence': rule_data.get('aggregated_improvement', 0),
                    'affected_users': rule_data.get('consensus_count', 0),
                    'is_consensus': rule_id in self.consensus_rules
                })
        
        return sorted(patterns, key=lambda x: x['confidence'], reverse=True)


class AdaptiveThresholdManager:
    """自适应阈值管理器"""
    
    def __init__(self):
        # 基础阈值
        self.base_thresholds = {
            'contamination_detection': 0.5,
            'user_verification': 0.7,
            'auto_rollback': 0.5
        }
        
        # 用户自适应阈值
        self.user_thresholds: Dict[str, Dict[str, float]] = {}
        
        # 阈值调整历史
        self.adjustment_history: List[Dict] = []
    
    def get_thresholds_for_user(self, user_profile: Dict) -> Dict[str, float]:
        """根据用户画像获取自适应阈值"""
        user_id = user_profile.get('user_id', 'default')
        
        if user_id in self.user_thresholds:
            return self.user_thresholds[user_id]
        
        # 根据用户水平计算自适应阈值
        level = user_profile.get('level', 'intermediate')
        
        if level == 'expert':
            # 专家用户: 降低验证严格度，提高信任
            thresholds = {
                'contamination_detection': 0.3,   # 更宽松
                'user_verification': 0.5,          # 更易通过
                'auto_rollback': 0.7               # 更高容忍
            }
        elif level == 'advanced':
            thresholds = {
                'contamination_detection': 0.4,
                'user_verification': 0.6,
                'auto_rollback': 0.6
            }
        elif level == 'intermediate':
            thresholds = self.base_thresholds.copy()
        else:  # beginner
            # 新手用户: 提高验证严格度，更多保护
            thresholds = {
                'contamination_detection': 0.7,   # 更严格
                'user_verification': 0.8,          # 更多确认
                'auto_rollback': 0.3               # 更低容忍
            }
        
        self.user_thresholds[user_id] = thresholds
        return thresholds
    
    def adjust_based_on_feedback(self,
                                 user_id: str,
                                 threshold_type: str,
                                 feedback: str,
                                 success: bool):
        """基于反馈调整阈值"""
        if user_id not in self.user_thresholds:
            return
        
        current = self.user_thresholds[user_id][threshold_type]
        
        if feedback == 'too_strict':
            # 太严格，降低阈值
            adjustment = -0.05
        elif feedback == 'too_loose':
            # 太宽松，提高阈值
            adjustment = 0.05
        else:
            adjustment = 0
        
        new_value = max(0.1, min(0.9, current + adjustment))
        self.user_thresholds[user_id][threshold_type] = new_value
        
        # 记录
        self.adjustment_history.append({
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'threshold_type': threshold_type,
            'old_value': current,
            'new_value': new_value,
            'feedback': feedback
        })
        
        print(f"[AdaptiveThreshold] {user_id} {threshold_type}: {current:.2f} -> {new_value:.2f}")


class PersonalizedStrategyEngine:
    """个性化策略引擎"""
    
    def __init__(self):
        self.strategies = {
            'expert': {
                'explanation_level': 'minimal',      # 少解释
                'provide_alternatives': True,        # 多给选项
                'focus_on_tradeoffs': True,          # 关注权衡
                'auto_execute': True,                # 自动执行
                'confirmation_frequency': 'low'      # 少确认
            },
            'advanced': {
                'explanation_level': 'concise',
                'provide_alternatives': True,
                'focus_on_tradeoffs': True,
                'auto_execute': False,
                'confirmation_frequency': 'medium'
            },
            'intermediate': {
                'explanation_level': 'standard',
                'provide_alternatives': False,
                'focus_on_tradeoffs': False,
                'auto_execute': False,
                'confirmation_frequency': 'medium'
            },
            'beginner': {
                'explanation_level': 'detailed',     # 详细解释
                'provide_alternatives': False,
                'focus_on_tradeoffs': False,
                'auto_execute': False,
                'confirmation_frequency': 'high'     # 多确认
            }
        }
    
    def get_strategy(self, user_level: str) -> Dict:
        """获取用户策略"""
        return self.strategies.get(user_level, self.strategies['intermediate'])
    
    def customize_strategy(self,
                          user_id: str,
                          base_level: str,
                          custom_preferences: Dict) -> Dict:
        """定制策略"""
        base = self.strategies.get(base_level, self.strategies['intermediate']).copy()
        base.update(custom_preferences)
        return base


class FederatedDefenseSystem:
    """联邦防御系统 v1.3-1.4"""
    
    def __init__(self, primary_user_id: str = "wdai"):
        self.primary_user_id = primary_user_id
        
        # 导入增强防御系统
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        from enhanced_defense import EnhancedDefenseSystem
        
        self.base_system = EnhancedDefenseSystem(primary_user_id)
        
        # 新增组件
        self.federated_server = FederatedLearningServer()
        self.threshold_manager = AdaptiveThresholdManager()
        self.strategy_engine = PersonalizedStrategyEngine()
        
        # 联邦学习客户端状态
        self.local_updates: List[Dict] = []
        self.privacy_budget: float = 1.0  # 差分隐私预算
    
    def process_with_personalization(self,
                                    content: str,
                                    source: str,
                                    user_id: str,
                                    user_profile: Dict) -> Dict:
        """带个性化的处理"""
        # 1. 获取自适应阈值
        thresholds = self.threshold_manager.get_thresholds_for_user(user_profile)
        
        # 2. 获取个性化策略
        user_level = user_profile.get('level', 'intermediate')
        strategy = self.strategy_engine.get_strategy(user_level)
        
        # 3. 基础处理
        result = self.base_system.process_with_learning(
            content=content,
            source=source,
            user_id=user_id
        )
        
        # 4. 应用自适应阈值
        if 'confidence' in result:
            # 根据用户水平调整有效阈值
            adjusted_threshold = thresholds.get('contamination_detection', 0.5)
            result['effective_threshold'] = adjusted_threshold
            result['threshold_adjusted'] = True
        
        # 5. 添加个性化策略
        result['personalized_strategy'] = strategy
        result['recommendation'] = self._generate_recommendation(strategy, result)
        
        return result
    
    def _generate_recommendation(self, strategy: Dict, result: Dict) -> str:
        """生成个性化建议"""
        if strategy['explanation_level'] == 'minimal':
            return "直接执行" if result.get('allowed') else "已拦截"
        elif strategy['explanation_level'] == 'detailed':
            return f"检测详情: {result.get('reasoning', 'N/A')}。建议: {'通过' if result.get('allowed') else '拒绝'}"
        else:
            return result.get('reasoning', '处理完成')
    
    def submit_federated_update(self,
                                user_id: str,
                                rule_improvements: Dict):
        """提交联邦学习更新"""
        # 消耗隐私预算
        if self.privacy_budget <= 0:
            print(f"[FederatedClient] {user_id} 隐私预算已耗尽")
            return
        
        update = FederatedUpdate(
            update_id=hashlib.sha256(f"{user_id}:{datetime.now()}".encode()).hexdigest()[:16],
            user_hash=hashlib.sha256(user_id.encode()).hexdigest()[:16],
            rule_improvements=rule_improvements,
            timestamp=datetime.now().isoformat(),
            privacy_budget=self.privacy_budget / 10  # 每次消耗1/10
        )
        
        self.privacy_budget -= update.privacy_budget
        
        # 发送到服务器
        self.federated_server.receive_update(update)
        
        print(f"[FederatedClient] {user_id} 提交更新，剩余预算: {self.privacy_budget:.2f}")
    
    def sync_global_model(self) -> Dict:
        """同步全局模型"""
        return self.federated_server.get_global_update(self.primary_user_id)
    
    def get_federated_report(self) -> Dict:
        """获取联邦学习报告"""
        return {
            'global_rules_count': len(self.federated_server.global_rules),
            'consensus_rules_count': len(self.federated_server.consensus_rules),
            'common_patterns': len(self.federated_server.extract_common_patterns()),
            'privacy_budget_remaining': self.privacy_budget,
            'adaptive_users': len(self.threshold_manager.user_thresholds)
        }


def test_federated_system():
    """测试联邦学习系统"""
    print("="*70)
    print("🌐 联邦学习与自适应阈值系统测试 v1.3-1.4")
    print("="*70)
    
    system = FederatedDefenseSystem(primary_user_id="wdai")
    
    # 测试1: 个性化策略
    print("\n--- 测试1: 个性化策略 ---")
    
    user_profiles = [
        {'user_id': 'expert_user', 'level': 'expert', 'technical_depth': 9.0},
        {'user_id': 'beginner_user', 'level': 'beginner', 'technical_depth': 2.0}
    ]
    
    for profile in user_profiles:
        thresholds = system.threshold_manager.get_thresholds_for_user(profile)
        strategy = system.strategy_engine.get_strategy(profile['level'])
        
        print(f"\n用户: {profile['user_id']} ({profile['level']})")
        print(f"  检测阈值: {thresholds['contamination_detection']:.2f}")
        print(f"  解释级别: {strategy['explanation_level']}")
        print(f"  自动执行: {strategy['auto_execute']}")
    
    # 测试2: 联邦学习
    print("\n--- 测试2: 联邦学习 ---")
    
    # 模拟3个用户提交更新
    for i in range(3):
        improvements = {
            'rule_001': 0.1 * (i + 1),
            'rule_002': 0.05 * (i + 1)
        }
        system.submit_federated_update(f"user_{i}", improvements)
    
    # 同步全局模型
    global_model = system.sync_global_model()
    print(f"\n全局模型同步完成")
    print(f"  共识规则: {len(global_model['consensus_rules'])}")
    
    # 测试3: 共性模式提取
    print("\n--- 测试3: 共性模式提取 ---")
    patterns = system.federated_server.extract_common_patterns()
    print(f"发现共性模式: {len(patterns)}")
    for p in patterns[:3]:
        print(f"  {p['pattern_id']}: 置信度={p['confidence']:.2f}, 用户数={p['affected_users']}")
    
    # 测试4: 个性化处理
    print("\n--- 测试4: 带个性化的处理 ---")
    result = system.process_with_personalization(
        content="帮我设计一个分布式系统架构",
        source="user_direct",
        user_id="expert_user",
        user_profile={'user_id': 'expert_user', 'level': 'expert'}
    )
    
    print(f"有效阈值: {result.get('effective_threshold', 'N/A')}")
    print(f"个性化策略: {result.get('personalized_strategy', {}).get('explanation_level')}")
    print(f"建议: {result.get('recommendation', 'N/A')}")
    
    # 总报告
    print("\n" + "="*70)
    print("📊 联邦防御系统报告")
    print("="*70)
    report = system.get_federated_report()
    for key, value in report.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*70)
    print("✅ 测试完成")
    print("="*70)


if __name__ == "__main__":
    test_federated_system()
