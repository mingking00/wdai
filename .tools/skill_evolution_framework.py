#!/usr/bin/env python3
"""
Skill Evolution Framework - 技能进化框架
从熟练到顶级的系统化路径

核心理念 (来自用户洞察):
1. 归纳小技巧 → 模式提取
2. 创造思想工具 → 认知框架  
3. 实践验证 → 反馈循环

补充维度:
4. 教授他人 → 深度理解
5. 跨域迁移 → 通用抽象
6. 刻意练习 → 突破瓶颈
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class EvolutionStage(Enum):
    NOVICE = "novice"           # 新手 - 学习规则
    COMPETENT = "competent"     # 熟练 - 应用规则
    PROFICIENT = "proficient"   # 精通 - 识别模式
    EXPERT = "expert"           # 专家 - 创造工具
    MASTER = "master"           # 大师 - 直觉决策

@dataclass
class SkillTip:
    """小技巧 - 模式提取的基本单位"""
    id: str
    name: str
    context: str              # 什么场景下发现
    pattern: str              # 归纳的模式
    code_example: str         # 代码/实现示例
    efficiency_gain: str      # 效率提升 (如: "节省50%时间")
    verified_count: int       # 验证次数
    success_rate: float       # 成功率
    created_at: str
    
    def to_dict(self):
        return asdict(self)

@dataclass
class MentalTool:
    """思想工具 - 认知框架"""
    id: str
    name: str
    description: str
    applicability: List[str]   # 适用场景
    steps: List[str]           # 使用步骤
    tips_used: List[str]       # 组成的小技巧
    verification_log: List[Dict]  # 验证记录
    created_at: str
    
    def to_dict(self):
        return asdict(self)


class SkillEvolutionEngine:
    """技能进化引擎"""
    
    def __init__(self, skill_name: str):
        self.skill_name = skill_name
        self.workspace = f"/root/.openclaw/workspace/.learning/skills/{skill_name}"
        os.makedirs(self.workspace, exist_ok=True)
        
        self.tips_file = os.path.join(self.workspace, "tips.json")
        self.tools_file = os.path.join(self.workspace, "tools.json")
        self.evolution_log = os.path.join(self.workspace, "evolution.md")
        
        self.tips = self._load_tips()
        self.tools = self._load_tools()
    
    # ============ 阶段1: 归纳小技巧 ============
    
    def extract_tip(self, task_description: str, solution: str, result: str) -> SkillTip:
        """从实践中提取小技巧"""
        
        # 分析模式和收益
        pattern = self._extract_pattern(solution)
        efficiency = self._calculate_efficiency(task_description, solution)
        
        tip = SkillTip(
            id=f"tip-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            name=self._generate_tip_name(pattern),
            context=task_description[:100],
            pattern=pattern,
            code_example=solution[:500],
            efficiency_gain=efficiency,
            verified_count=1,
            success_rate=1.0,
            created_at=datetime.now().isoformat()
        )
        
        self.tips.append(tip)
        self._save_tips()
        
        print(f"✅ 提取小技巧: {tip.name}")
        print(f"   模式: {tip.pattern[:80]}...")
        print(f"   效率提升: {tip.efficiency_gain}")
        
        return tip
    
    def verify_tip(self, tip_id: str, new_task: str, success: bool) -> bool:
        """验证小技巧的有效性"""
        
        for tip in self.tips:
            if tip.id == tip_id:
                tip.verified_count += 1
                if success:
                    # 更新成功率 (滑动平均)
                    tip.success_rate = (tip.success_rate * (tip.verified_count - 1) + 1) / tip.verified_count
                else:
                    tip.success_rate = (tip.success_rate * (tip.verified_count - 1)) / tip.verified_count
                
                self._save_tips()
                
                status = "✅ 有效" if success else "❌ 失效"
                print(f"{status}: {tip.name} (验证{tip.verified_count}次, 成功率{tip.success_rate:.1%})")
                
                # 如果成功率低于阈值，标记为需要改进
                if tip.success_rate < 0.7 and tip.verified_count >= 3:
                    print(f"⚠️  警告: {tip.name} 成功率低，需要改进或废弃")
                
                return success
        
        return False
    
    # ============ 阶段2: 创造思想工具 ============
    
    def create_mental_tool(self, tool_name: str, tips_to_combine: List[str]) -> MentalTool:
        """将多个小技巧组合成思想工具"""
        
        # 获取相关小技巧
        selected_tips = [t for t in self.tips if t.id in tips_to_combine]
        
        if len(selected_tips) < 2:
            print("❌ 需要至少2个小技巧才能创建思想工具")
            return None
        
        # 提取通用模式
        common_pattern = self._find_common_pattern(selected_tips)
        
        tool = MentalTool(
            id=f"tool-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            name=tool_name,
            description=common_pattern,
            applicability=self._extract_applicability(selected_tips),
            steps=self._generate_steps(selected_tips),
            tips_used=tips_to_combine,
            verification_log=[],
            created_at=datetime.now().isoformat()
        )
        
        self.tools.append(tool)
        self._save_tools()
        
        print(f"\n🔧 创造思想工具: {tool.name}")
        print(f"   描述: {tool.description[:100]}...")
        print(f"   组成: {len(selected_tips)}个小技巧")
        print(f"   适用场景: {', '.join(tool.applicability[:3])}")
        
        return tool
    
    def use_tool(self, tool_id: str, context: str) -> Dict:
        """使用思想工具解决问题"""
        
        for tool in self.tools:
            if tool.id == tool_id:
                # 记录使用
                usage_record = {
                    "time": datetime.now().isoformat(),
                    "context": context[:100],
                    "steps_followed": tool.steps
                }
                tool.verification_log.append(usage_record)
                self._save_tools()
                
                print(f"\n🎯 使用工具: {tool.name}")
                print("   步骤:")
                for i, step in enumerate(tool.steps, 1):
                    print(f"   {i}. {step}")
                
                return {
                    "tool": tool,
                    "applicable": self._check_applicability(tool, context),
                    "recommendation": "建议使用" if self._check_applicability(tool, context) else "可能不适用"
                }
        
        return None
    
    def verify_tool(self, tool_id: str, success: bool, feedback: str):
        """验证思想工具的有效性"""
        
        for tool in self.tools:
            if tool.id == tool_id:
                tool.verification_log.append({
                    "time": datetime.now().isoformat(),
                    "success": success,
                    "feedback": feedback
                })
                self._save_tools()
                
                # 计算成功率
                total = len([v for v in tool.verification_log if "success" in v])
                successes = len([v for v in tool.verification_log if v.get("success")])
                rate = successes / total if total > 0 else 0
                
                status = "✅ 有效" if success else "❌ 需改进"
                print(f"{status}: {tool.name} (累计成功率: {rate:.1%})")
                
                return
    
    # ============ 阶段3: 教学与迁移 ============
    
    def teach_skill(self, audience: str = "peer") -> str:
        """生成教学内容 - 费曼技巧"""
        
        content = f"""# {self.skill_name} 技能教学

## 核心思想工具 ({len(self.tools)}个)

"""
        
        for tool in self.tools:
            success_count = len([v for v in tool.verification_log if v.get("success")])
            total_count = len([v for v in tool.verification_log if "success" in v])
            rate = success_count / total_count if total_count > 0 else 0
            
            content += f"""### {tool.name}
**验证成功率**: {rate:.1%} ({success_count}/{total_count})

**适用场景**:
{chr(10).join(f'- {a}' for a in tool.applicability[:5])}

**使用步骤**:
{chr(10).join(f'{i}. {s}' for i, s in enumerate(tool.steps, 1))}

**底层小技巧**:
{chr(10).join(f'- {t.name}' for t in self.tips if t.id in tool.tips_used)}

---

"""
        
        # 保存教学文档
        teach_file = os.path.join(self.workspace, "teaching_guide.md")
        with open(teach_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n📚 生成教学指南: {teach_file}")
        return content
    
    def extract_principles(self) -> List[Dict]:
        """提取可跨域迁移的通用原则"""
        
        principles = []
        
        for tool in self.tools:
            # 抽象通用模式
            principle = {
                "name": f"{self.skill_name}::{tool.name}",
                "abstract_pattern": self._abstract_pattern(tool.description),
                "origin_domain": self.skill_name,
                "potential_domains": self._find_similar_domains(tool),
                "verification_count": len(tool.verification_log)
            }
            principles.append(principle)
        
        # 保存原则库
        principles_file = os.path.join(self.workspace, "principles.json")
        with open(principles_file, 'w', encoding='utf-8') as f:
            json.dump(principles, f, indent=2, ensure_ascii=False)
        
        print(f"\n🔄 提取 {len(principles)} 个可迁移原则")
        return principles
    
    # ============ 辅助方法 ============
    
    def _extract_pattern(self, solution: str) -> str:
        """提取模式"""
        # 简单启发式：提取关键步骤
        lines = solution.split('\n')
        key_lines = [l for l in lines if any(kw in l.lower() for kw in ['def ', 'class ', 'if ', 'for ', 'return'])]
        return ' → '.join(key_lines[:3]) if key_lines else solution[:100]
    
    def _calculate_efficiency(self, task: str, solution: str) -> str:
        """计算效率提升"""
        # 启发式：根据代码行数估算
        lines = len(solution.split('\n'))
        if lines < 10:
            return "节省70%代码量"
        elif lines < 30:
            return "节省50%时间"
        else:
            return "提升可维护性"
    
    def _generate_tip_name(self, pattern: str) -> str:
        """生成技巧名称"""
        # 提取关键词
        keywords = []
        for kw in ['cache', 'async', 'batch', 'lazy', 'retry', 'timeout', 'validate']:
            if kw in pattern.lower():
                keywords.append(kw.title())
        
        return f"{'+'.join(keywords[:2])} Pattern" if keywords else f"Tip-{datetime.now().strftime('%H%M%S')}"
    
    def _find_common_pattern(self, tips: List[SkillTip]) -> str:
        """找到共同模式"""
        patterns = [t.pattern for t in tips]
        # 简化：返回第一个的pattern作为代表
        return f"组合技巧: {patterns[0][:50]}..."
    
    def _extract_applicability(self, tips: List[SkillTip]) -> List[str]:
        """提取适用场景"""
        contexts = [t.context for t in tips]
        # 提取关键词
        return list(set([c.split()[0] for c in contexts if c]))[:5]
    
    def _generate_steps(self, tips: List[SkillTip]) -> List[str]:
        """生成步骤"""
        return [f"应用{t.name}" for t in tips[:4]]
    
    def _check_applicability(self, tool: MentalTool, context: str) -> bool:
        """检查适用性"""
        return any(app in context for app in tool.applicability)
    
    def _abstract_pattern(self, description: str) -> str:
        """抽象通用模式"""
        # 替换具体词汇为抽象概念
        return description.replace("具体", "抽象").replace("特定", "通用")
    
    def _find_similar_domains(self, tool: MentalTool) -> List[str]:
        """找到相似领域"""
        # 启发式匹配
        return ["其他编程领域", "系统设计", "问题解决"]
    
    def _load_tips(self) -> List[SkillTip]:
        """加载小技巧"""
        if os.path.exists(self.tips_file):
            with open(self.tips_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [SkillTip(**item) for item in data]
        return []
    
    def _save_tips(self):
        """保存小技巧"""
        with open(self.tips_file, 'w', encoding='utf-8') as f:
            json.dump([t.to_dict() for t in self.tips], f, indent=2, ensure_ascii=False)
    
    def _load_tools(self) -> List[MentalTool]:
        """加载思想工具"""
        if os.path.exists(self.tools_file):
            with open(self.tools_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [MentalTool(**item) for item in data]
        return []
    
    def _save_tools(self):
        """保存思想工具"""
        with open(self.tools_file, 'w', encoding='utf-8') as f:
            json.dump([t.to_dict() for t in self.tools], f, indent=2, ensure_ascii=False)
    
    def generate_evolution_report(self) -> str:
        """生成进化报告"""
        report = f"""# {self.skill_name} 技能进化报告
生成时间: {datetime.now().isoformat()}

## 统计概览
- 小技巧数量: {len(self.tips)}
- 思想工具数量: {len(self.tools)}
- 平均验证次数: {sum(t.verified_count for t in self.tips) / len(self.tips) if self.tips else 0:.1f}
- 平均工具成功率: {sum(len([v for v in t.verification_log if v.get('success')]) / len(t.verification_log) for t in self.tools if t.verification_log) / len(self.tools) if self.tools else 0:.1%}

## 高效小技巧 (Top 5)
"""
        
        sorted_tips = sorted(self.tips, key=lambda t: t.success_rate * t.verified_count, reverse=True)[:5]
        for i, tip in enumerate(sorted_tips, 1):
            report += f"{i}. {tip.name} (成功率: {tip.success_rate:.1%}, 验证{tip.verified_count}次)\n"
        
        report += "\n## 成熟思想工具\n"
        for tool in self.tools:
            total = len([v for v in tool.verification_log if "success" in v])
            success = len([v for v in tool.verification_log if v.get("success")])
            rate = success / total if total > 0 else 0
            report += f"- {tool.name} (成功率: {rate:.1%})\n"
        
        # 保存报告
        report_file = os.path.join(self.workspace, "evolution_report.md")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📊 生成进化报告: {report_file}")
        return report


# ============ 演示 ============
def demo_skill_evolution():
    """演示技能进化过程"""
    
    print("="*70)
    print("🎯 Skill Evolution Framework Demo")
    print("   技能: Multi-Agent System Design")
    print("="*70)
    
    engine = SkillEvolutionEngine("multi-agent-design")
    
    # 阶段1: 提取小技巧
    print("\n" + "="*70)
    print("阶段1: 从实践中提取小技巧")
    print("="*70)
    
    tip1 = engine.extract_tip(
        task_description="解决多智能体冲突问题",
        solution="""
def resolve_conflict(agents):
    # 技巧: 投票机制
    votes = defaultdict(int)
    for agent in agents:
        votes[agent.preference] += agent.weight
    return max(votes, key=votes.get)
        """,
        result="冲突解决时间减少60%"
    )
    
    tip2 = engine.extract_tip(
        task_description="优化Agent响应时间",
        solution="""
async def batch_process(tasks):
    # 技巧: 批处理
    batches = chunk(tasks, size=10)
    results = await asyncio.gather(*[process(b) for b in batches])
    return flatten(results)
        """,
        result="吞吐量提升3x"
    )
    
    tip3 = engine.extract_tip(
        task_description="防止级联失败",
        solution="""
@circuit_breaker(threshold=5, timeout=60)
def call_external_service():
    # 技巧: 熔断器模式
    return service.call()
        """,
        result="系统可用性99.9%"
    )
    
    # 验证小技巧
    print("\n验证小技巧...")
    engine.verify_tip(tip1.id, "新场景测试", True)
    engine.verify_tip(tip1.id, "边界情况", True)
    engine.verify_tip(tip2.id, "大负载测试", True)
    
    # 阶段2: 创造思想工具
    print("\n" + "="*70)
    print("阶段2: 将小技巧组合成思想工具")
    print("="*70)
    
    tool = engine.create_mental_tool(
        tool_name="Resilient Multi-Agent Orchestrator",
        tips_to_combine=[tip1.id, tip2.id, tip3.id]
    )
    
    # 使用工具
    print("\n使用思想工具...")
    engine.use_tool(tool.id, "设计新的多智能体系统")
    
    # 验证工具
    print("\n验证思想工具...")
    engine.verify_tool(tool.id, True, "在生产环境表现良好")
    engine.verify_tool(tool.id, True, "扩展性优秀")
    
    # 阶段3: 教学与迁移
    print("\n" + "="*70)
    print("阶段3: 教学与跨域迁移")
    print("="*70)
    
    engine.teach_skill()
    engine.extract_principles()
    
    # 生成进化报告
    print("\n" + "="*70)
    print("阶段4: 生成进化报告")
    print("="*70)
    
    engine.generate_evolution_report()
    
    print("\n" + "="*70)
    print("✅ 技能进化演示完成")
    print("="*70)


if __name__ == "__main__":
    demo_skill_evolution()
