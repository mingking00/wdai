#!/usr/bin/env python3
"""
灵感进化引擎 - 风险评估框架

定义什么是"低风险"，提供决策依据

Author: wdai
Version: 1.0
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path
import json


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"         # 可自动实施
    MEDIUM = "medium"   # 需要确认
    HIGH = "high"       # 必须人工评审


@dataclass
class RiskAssessment:
    """风险评估结果"""
    level: RiskLevel
    score: int  # 0-100，分数越高风险越高
    factors: List[Dict]  # 各维度评分详情
    reasoning: str  # 评估理由
    requires_approval: bool


class RiskAssessmentFramework:
    """
    风险评估框架
    
    多维度评估方案风险，给出量化评分
    """
    
    # 风险维度定义
    DIMENSIONS = {
        'scope': {
            'name': '影响范围',
            'description': '修改会影响多少文件/功能',
            'weight': 0.25,
            'criteria': {
                'single_file': 10,      # 单文件修改
                'module_level': 30,     # 模块级别
                'system_wide': 60,      # 系统范围
                'infrastructure': 80,   # 基础设施
            }
        },
        'criticality': {
            'name': '关键程度',
            'description': '修改的是核心功能还是边缘功能',
            'weight': 0.30,
            'criteria': {
                'experimental': 10,     # 实验性功能
                'utility': 25,          # 工具函数
                'feature': 40,          # 普通功能
                'core_logic': 70,       # 核心逻辑
                'data_layer': 80,       # 数据层
                'scheduling': 85,       # 调度系统
            }
        },
        'complexity': {
            'name': '实施复杂度',
            'description': '修改的复杂程度',
            'weight': 0.20,
            'criteria': {
                'config_change': 10,    # 配置修改
                'simple_addition': 20,  # 简单添加
                'refactor': 40,         # 重构
                'new_integration': 50,  # 新集成
                'architectural': 70,    # 架构变更
            }
        },
        'reversibility': {
            'name': '可逆性',
            'description': '出问题时能否快速回滚',
            'weight': 0.15,
            'criteria': {
                'fully_reversible': 10,  # 完全可逆
                'backup_available': 25,  # 有备份
                'partial_reversible': 50, # 部分可逆
                'breaking_change': 80,   # 破坏性变更
            }
        },
        'testing': {
            'name': '测试覆盖',
            'description': '修改是否容易验证',
            'weight': 0.10,
            'criteria': {
                'auto_verifiable': 10,   # 自动可验证
                'unit_tested': 20,       # 有单元测试
                'manual_verifiable': 40,  # 可手动验证
                'hard_to_test': 70,      # 难测试
            }
        }
    }
    
    # 风险阈值
    THRESHOLDS = {
        'low_max': 35,      # 35分以下为低风险
        'medium_max': 65,   # 65分以下为中等风险
        # 超过65分为高风险
    }
    
    def __init__(self):
        pass
    
    def assess_plan(self, plan: Dict) -> RiskAssessment:
        """
        评估优化方案的风险等级
        
        Args:
            plan: 优化方案字典
            
        Returns:
            RiskAssessment 评估结果
        """
        factors = []
        total_score = 0
        
        # 评估每个维度
        for dim_key, dim_config in self.DIMENSIONS.items():
            score, reasoning = self._assess_dimension(dim_key, plan)
            weighted_score = score * dim_config['weight']
            total_score += weighted_score
            
            factors.append({
                'dimension': dim_config['name'],
                'raw_score': score,
                'weight': dim_config['weight'],
                'weighted_score': round(weighted_score, 1),
                'reasoning': reasoning
            })
        
        # 确定风险等级
        if total_score <= self.THRESHOLDS['low_max']:
            level = RiskLevel.LOW
            requires_approval = False
        elif total_score <= self.THRESHOLDS['medium_max']:
            level = RiskLevel.MEDIUM
            requires_approval = True
        else:
            level = RiskLevel.HIGH
            requires_approval = True
        
        # 生成评估理由
        reasoning = self._generate_reasoning(factors, level)
        
        return RiskAssessment(
            level=level,
            score=round(total_score),
            factors=factors,
            reasoning=reasoning,
            requires_approval=requires_approval
        )
    
    def _assess_dimension(self, dimension: str, plan: Dict) -> tuple:
        """评估单个维度"""
        dim_config = self.DIMENSIONS[dimension]
        
        if dimension == 'scope':
            return self._assess_scope(plan)
        elif dimension == 'criticality':
            return self._assess_criticality(plan)
        elif dimension == 'complexity':
            return self._assess_complexity(plan)
        elif dimension == 'reversibility':
            return self._assess_reversibility(plan)
        elif dimension == 'testing':
            return self._assess_testing(plan)
        
        return 50, "默认中等风险"
    
    def _assess_scope(self, plan: Dict) -> tuple:
        """评估影响范围"""
        changes = plan.get('changes', [])
        target = plan.get('target_system', '')
        
        # 统计修改的文件数
        file_count = len(changes)
        
        # 检查是否涉及核心系统
        core_systems = ['scheduler', 'healing', 'runner']
        is_core = any(sys in target.lower() for sys in core_systems)
        
        if file_count == 1 and not is_core:
            return 10, "单文件修改，非核心系统"
        elif file_count <= 3 and not is_core:
            return 30, "少量文件修改"
        elif is_core:
            return 60, f"涉及核心系统 ({target})"
        else:
            return 40, f"多文件修改 ({file_count}个)"
    
    def _assess_criticality(self, plan: Dict) -> tuple:
        """评估关键程度"""
        target = plan.get('target_system', '').lower()
        title = plan.get('title', '').lower()
        
        # 核心系统检测
        if 'scheduler' in target:
            return 85, "调度系统是核心，影响全局运行"
        elif 'healing' in target:
            return 80, "自愈系统关键，错误可能导致雪崩"
        elif 'data' in target or 'database' in target:
            return 80, "数据层关键，影响数据完整性"
        
        # 功能类型检测
        if 'crawler' in target or 'fetch' in title:
            return 40, "抓取器功能，相对独立"
        elif 'config' in target or 'setting' in title:
            return 25, "配置修改，影响可控"
        elif 'test' in target or 'mock' in title:
            return 10, "测试相关，低风险"
        
        return 40, "普通功能修改"
    
    def _assess_complexity(self, plan: Dict) -> tuple:
        """评估复杂度"""
        steps = plan.get('implementation_steps', [])
        changes = plan.get('changes', [])
        
        step_count = len(steps)
        
        # 检查变更类型
        has_refactor = any(c.get('action') == 'refactor' for c in changes)
        has_architectural = any(c.get('action') == 'architectural' for c in changes)
        has_new_integration = any(c.get('action') == 'add_source' for c in changes)
        
        if has_architectural:
            return 70, "架构级别变更，复杂度高"
        elif has_refactor:
            return 40, "代码重构，需要仔细验证"
        elif has_new_integration:
            return 50, "新集成，需要测试接口"
        elif step_count <= 3:
            return 20, "简单修改，步骤少"
        else:
            return 30, "标准复杂度"
    
    def _assess_reversibility(self, plan: Dict) -> tuple:
        """评估可逆性"""
        changes = plan.get('changes', [])
        
        # 检查是否有破坏性变更
        has_breaking = any(c.get('action') in ['remove', 'delete'] for c in changes)
        has_data_change = any(c.get('action') == 'data_migration' for c in changes)
        
        # 检查是否有备份机制
        mentions_backup = 'backup' in str(plan).lower()
        
        if has_breaking:
            return 80, "包含破坏性变更，难以回滚"
        elif has_data_change:
            return 70, "涉及数据变更，回滚复杂"
        elif mentions_backup:
            return 25, "有备份机制，可恢复"
        else:
            return 40, "标准可逆性"
    
    def _assess_testing(self, plan: Dict) -> tuple:
        """评估测试难度"""
        target = plan.get('target_system', '').lower()
        
        # 检查是否容易自动验证
        auto_verifiable = [
            'config', 'setting', 'constant',
            'documentation', 'comment'
        ]
        
        # 检查是否需要外部依赖
        needs_external = any(kw in target for kw in ['api', 'network', 'external'])
        
        if any(kw in target for kw in auto_verifiable):
            return 10, "配置类修改，容易验证"
        elif needs_external:
            return 60, "涉及外部依赖，测试复杂"
        else:
            return 25, "可单元测试验证"
    
    def _generate_reasoning(self, factors: List[Dict], level: RiskLevel) -> str:
        """生成评估理由"""
        # 找出最高分的维度
        max_factor = max(factors, key=lambda x: x['raw_score'])
        min_factor = min(factors, key=lambda x: x['raw_score'])
        
        reasoning = f"风险等级: {level.value.upper()}\n"
        reasoning += f"主要风险点: {max_factor['dimension']} ({max_factor['raw_score']}分) - {max_factor['reasoning']}\n"
        reasoning += f"安全因素: {min_factor['dimension']} ({min_factor['raw_score']}分) - {min_factor['reasoning']}\n"
        
        return reasoning
    
    def get_assessment_report(self, plan: Dict) -> str:
        """生成详细的评估报告"""
        assessment = self.assess_plan(plan)
        
        lines = []
        lines.append("="*60)
        lines.append("🛡️ 风险评估报告")
        lines.append("="*60)
        lines.append("")
        
        # 方案信息
        lines.append(f"方案: {plan.get('title', 'Unknown')}")
        lines.append(f"目标系统: {plan.get('target_system', 'Unknown')}")
        lines.append("")
        
        # 风险等级
        level_emoji = {
            RiskLevel.LOW: "🟢",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.HIGH: "🔴"
        }
        lines.append(f"风险等级: {level_emoji[assessment.level]} {assessment.level.value.upper()}")
        lines.append(f"综合评分: {assessment.score}/100")
        lines.append(f"需要审批: {'是' if assessment.requires_approval else '否'}")
        lines.append("")
        
        # 详细维度
        lines.append("评分详情:")
        for factor in assessment.factors:
            bar = "█" * int(factor['raw_score'] / 10) + "░" * (10 - int(factor['raw_score'] / 10))
            lines.append(f"  {factor['dimension']:12} {bar} {factor['raw_score']:2}分 ({factor['reasoning']})")
        
        lines.append("")
        lines.append("评估结论:")
        lines.append(assessment.reasoning)
        
        lines.append("")
        lines.append("="*60)
        
        return "\n".join(lines)


# 决策清单模板
DECISION_CHECKLIST = """
# 优化方案决策清单

## 方案信息
- **标题**: {title}
- **目标系统**: {target_system}
- **风险等级**: {risk_level}
- **综合评分**: {score}/100

## 自动评估结果
{risk_assessment}

## 人工决策清单

### 安全确认 (必须全部通过才能实施)
- [ ] 已阅读方案描述和技术细节
- [ ] 理解修改的影响范围
- [ ] 确认有回滚方案或备份
- [ ] 评估业务影响时间窗口

### 实施条件
- [ ] 测试环境已准备
- [ ] 回滚流程已验证
- [ ] 监控告警已配置
- [ ] 相关人员已通知

### 决策选项
- [ ] **批准实施** - 风险可控，可以自动/手动实施
- [ ] **需要修改** - 方案需要调整后重新评估
- [ ] **拒绝实施** - 风险过高，暂不实施
- [ ] **延期处理** - 当前不适合，延后处理

### 备注
{notes}

---
评估时间: {timestamp}
决策人: ________________
"""


def main():
    """测试风险评估框架"""
    print("="*60)
    print("🛡️ 风险评估框架测试")
    print("="*60)
    
    framework = RiskAssessmentFramework()
    
    # 测试方案1: 低风险
    plan_low = {
        'title': '添加MCP Protocol监控源',
        'target_system': 'crawler_mcp',
        'changes': [
            {'file': 'crawler_mcp.py', 'action': 'create', 'details': '新文件'},
        ],
        'implementation_steps': [
            '1. 创建抓取器文件',
            '2. 添加到调度器配置',
        ]
    }
    
    print("\n📋 测试方案1: 添加新监控源")
    print(framework.get_assessment_report(plan_low))
    
    # 测试方案2: 高风险
    plan_high = {
        'title': '重构调度器核心算法',
        'target_system': 'scheduler',
        'changes': [
            {'file': 'scheduler.py', 'action': 'refactor', 'details': '重写调度逻辑'},
            {'file': 'data/scheduler', 'action': 'data_migration', 'details': '数据迁移'},
        ],
        'implementation_steps': [
            '1. 设计新算法',
            '2. 重写核心代码',
            '3. 数据迁移',
            '4. 全面测试',
        ]
    }
    
    print("\n📋 测试方案2: 重构核心调度器")
    print(framework.get_assessment_report(plan_high))


if __name__ == "__main__":
    main()
