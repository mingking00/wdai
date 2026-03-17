#!/usr/bin/env python3
"""
wdai Evolution Loop v2.0 - 外部反馈循环系统

核心认知: 闭门造车有局限，外界是进化的真正燃料
循环: 外部输入 → 内部进化 → 实战验证 → 反馈吸收
"""

import json
import time
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

# 进化系统目录
EVOLUTION_DIR = Path("/root/.openclaw/workspace/.evolution")
EVOLUTION_DIR.mkdir(parents=True, exist_ok=True)

class Dimension(Enum):
    """进化维度"""
    WISDOM = "wisdom"              # 智慧
    COMPREHENSIVENESS = "comprehensive"  # 全面
    EFFICIENCY = "efficiency"      # 效率

class EvolutionPhase(Enum):
    """进化阶段"""
    EXTERNAL_INPUT = "external_input"    # 外部输入
    INTERNAL_EVOLUTION = "internal"      # 内部进化
    REAL_WORLD_VALIDATION = "validation" # 实战验证
    FEEDBACK_INTEGRATION = "feedback"    # 反馈吸收
    IDLE = "idle"                        # 空闲

@dataclass
class ExternalInfo:
    """外部高质量信息"""
    source: str
    title: str
    url: str
    relevance_score: float
    collected_at: float
    insights: List[str] = field(default_factory=list)

@dataclass
class PracticeOpportunity:
    """实战机会"""
    opportunity_id: str
    name: str
    type: str  # "user_task", "exploration", "open_source"
    description: str
    expected_value: float
    required_skills: List[str]
    estimated_effort: str
    created_at: float = field(default_factory=time.time)

@dataclass
class ExternalFeedback:
    """外部反馈"""
    timestamp: float
    task_completion_rate: float
    user_satisfaction: float
    code_reuse_count: int
    external_recognition: int
    user_comments: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)

@dataclass
class ValidationResult:
    """验证结果"""
    project_id: str
    effectiveness_score: float
    user_rating: float
    lessons_learned: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

class ExternalInputCollector:
    """
    外部输入收集器
    主动寻找高质量信息和实战机会
    """
    
    def __init__(self, evolution_dir: Path = EVOLUTION_DIR):
        self.evolution_dir = evolution_dir
        self.input_log = evolution_dir / "external_inputs.json"
        self.opportunities_file = evolution_dir / "practice_opportunities.json"
        
    def collect_all(self) -> Tuple[List[ExternalInfo], List[PracticeOpportunity]]:
        """收集所有外部输入"""
        print("[ExternalInput] 收集外部输入...")
        
        # 收集高质量信息
        info_list = self._collect_high_quality_info()
        print(f"  收集到 {len(info_list)} 条高质量信息")
        
        # 识别实战机会
        opportunities = self._identify_practice_opportunities()
        print(f"  识别到 {len(opportunities)} 个实战机会")
        
        return info_list, opportunities
    
    def _collect_high_quality_info(self) -> List[ExternalInfo]:
        """收集高质量信息"""
        info_list = []
        
        # 扫描技能库作为信息源
        info_list.extend(self._scan_skills_repository())
        
        # 扫描记忆文件中的洞察
        info_list.extend(self._scan_memory_insights())
        
        # 保存到日志
        self._save_external_info(info_list)
        
        return info_list
    
    def _scan_skills_repository(self) -> List[ExternalInfo]:
        """扫描技能仓库获取最佳实践"""
        info_list = []
        skills_dir = Path("/root/.openclaw/skills")
        
        if skills_dir.exists():
            for skill_dir in skills_dir.glob("*"):
                if skill_dir.is_dir():
                    skill_file = skill_dir / "SKILL.md"
                    if skill_file.exists():
                        info_list.append(ExternalInfo(
                            source="skills_repository",
                            title=f"Skill: {skill_dir.name}",
                            url=str(skill_file),
                            relevance_score=0.7,
                            collected_at=time.time(),
                            insights=["可学习的技能模式"]
                        ))
        
        return info_list
    
    def _scan_memory_insights(self) -> List[ExternalInfo]:
        """扫描记忆中的洞察"""
        info_list = []
        memory_dir = Path("/root/.openclaw/workspace/memory/daily")
        
        if memory_dir.exists():
            # 获取最近7天的记忆
            recent_files = sorted(memory_dir.glob("*.md"))[-7:]
            for mem_file in recent_files:
                info_list.append(ExternalInfo(
                    source="memory_insights",
                    title=f"Memory: {mem_file.stem}",
                    url=str(mem_file),
                    relevance_score=0.9,
                    collected_at=time.time(),
                    insights=["历史经验和教训"]
                ))
        
        return info_list
    
    def _identify_practice_opportunities(self) -> List[PracticeOpportunity]:
        """识别实战机会"""
        opportunities = []
        
        # 机会1: 技能缺口练习
        opportunities.append(PracticeOpportunity(
            opportunity_id=f"opp_{int(time.time())}_1",
            name="扩展技能覆盖",
            type="exploration",
            description="当前工具覆盖率仅24%，需要主动学习新技能",
            expected_value=0.8,
            required_skills=["skill_discovery", "skill_learning"],
            estimated_effort="medium"
        ))
        
        # 机会2: 优化现有代码
        opportunities.append(PracticeOpportunity(
            opportunity_id=f"opp_{int(time.time())}_2",
            name="代码质量提升",
            type="exploration",
            description="改进evolution_loop.py的代码质量和错误处理",
            expected_value=0.7,
            required_skills=["code_refactoring", "error_handling"],
            estimated_effort="low"
        ))
        
        # 机会3: 用户任务复盘
        opportunities.append(PracticeOpportunity(
            opportunity_id=f"opp_{int(time.time())}_3",
            name="用户交互优化",
            type="user_task",
            description="分析最近用户交互，找出改进点",
            expected_value=0.9,
            required_skills=["user_analysis", "interaction_design"],
            estimated_effort="medium"
        ))
        
        # 保存到文件
        self._save_opportunities(opportunities)
        
        return opportunities
    
    def _save_external_info(self, info_list: List[ExternalInfo]):
        """保存外部信息"""
        data = [asdict(info) for info in info_list]
        
        existing = []
        if self.input_log.exists():
            with open(self.input_log, 'r') as f:
                existing = json.load(f)
        
        existing.extend(data)
        # 只保留最近100条
        existing = existing[-100:]
        
        with open(self.input_log, 'w') as f:
            json.dump(existing, f, indent=2)
    
    def _save_opportunities(self, opportunities: List[PracticeOpportunity]):
        """保存实战机会"""
        data = [asdict(opp) for opp in opportunities]
        
        with open(self.opportunities_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def gather_external_feedback(self) -> ExternalFeedback:
        """收集外部反馈"""
        print("[ExternalInput] 收集外部反馈...")
        
        # 计算任务完成率（基于execution_results.json）
        results_file = self.evolution_dir / "execution_results.json"
        completion_rate = 0.0
        if results_file.exists():
            with open(results_file, 'r') as f:
                results = json.load(f)
                if results:
                    success_count = sum(1 for r in results if r.get("success"))
                    completion_rate = success_count / len(results)
        
        feedback = ExternalFeedback(
            timestamp=time.time(),
            task_completion_rate=completion_rate,
            user_satisfaction=0.0,  # 需要用户主动评分
            code_reuse_count=0,     # 需要追踪
            external_recognition=0  # 需要追踪
        )
        
        print(f"  任务完成率: {completion_rate:.2%}")
        
        return feedback

class RealWorldValidator:
    """
    实战验证器
    将改进应用到真实场景，收集反馈
    """
    
    def __init__(self, evolution_dir: Path = EVOLUTION_DIR):
        self.evolution_dir = evolution_dir
        self.validation_log = evolution_dir / "validation_results.json"
        
    def validate_with_practice(self, opportunity: PracticeOpportunity) -> ValidationResult:
        """
        通过实战项目验证
        """
        print(f"[Validator] 验证机会: {opportunity.name}")
        
        # 根据机会类型执行不同的验证
        if opportunity.type == "exploration":
            result = self._run_exploration_project(opportunity)
        elif opportunity.type == "user_task":
            result = self._analyze_user_interactions(opportunity)
        else:
            result = self._generic_validation(opportunity)
        
        # 保存验证结果
        self._save_validation_result(result)
        
        return result
    
    def _run_exploration_project(self, opportunity: PracticeOpportunity) -> ValidationResult:
        """运行探索性项目"""
        print(f"  运行探索项目: {opportunity.description}")
        
        # 示例：运行技能扫描器
        if "技能" in opportunity.description or "工具" in opportunity.description:
            scanner_path = self.evolution_dir / "auto_skill_scanner.py"
            if scanner_path.exists():
                import subprocess
                try:
                    result = subprocess.run(
                        ["python3", str(scanner_path)],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    return ValidationResult(
                        project_id=opportunity.opportunity_id,
                        effectiveness_score=0.8 if result.returncode == 0 else 0.3,
                        user_rating=0.0,
                        lessons_learned=["技能扫描器运行成功" if result.returncode == 0 else "需要修复扫描器"],
                        recommendations=["继续扩展技能库"]
                    )
                except Exception as e:
                    return ValidationResult(
                        project_id=opportunity.opportunity_id,
                        effectiveness_score=0.2,
                        user_rating=0.0,
                        lessons_learned=[f"运行失败: {str(e)}"],
                        recommendations=["改进错误处理"]
                    )
        
        return ValidationResult(
            project_id=opportunity.opportunity_id,
            effectiveness_score=0.5,
            user_rating=0.0,
            lessons_learned=["探索项目完成"],
            recommendations=["继续优化"]
        )
    
    def _analyze_user_interactions(self, opportunity: PracticeOpportunity) -> ValidationResult:
        """分析用户交互"""
        print(f"  分析用户交互模式")
        
        # 读取最近的记忆文件分析交互
        memory_dir = Path("/root/.openclaw/workspace/memory/daily")
        recent_interactions = 0
        
        if memory_dir.exists():
            recent_files = sorted(memory_dir.glob("*.md"))[-3:]
            recent_interactions = len(recent_files)
        
        return ValidationResult(
            project_id=opportunity.opportunity_id,
            effectiveness_score=0.7 if recent_interactions > 0 else 0.3,
            user_rating=0.0,
            lessons_learned=[f"分析了 {recent_interactions} 次近期交互"],
            recommendations=["增加用户反馈收集机制"]
        )
    
    def _generic_validation(self, opportunity: PracticeOpportunity) -> ValidationResult:
        """通用验证"""
        return ValidationResult(
            project_id=opportunity.opportunity_id,
            effectiveness_score=0.5,
            user_rating=0.0,
            lessons_learned=["需要更具体的验证方法"],
            recommendations=["定义明确的验证指标"]
        )
    
    def _save_validation_result(self, result: ValidationResult):
        """保存验证结果"""
        results = []
        if self.validation_log.exists():
            with open(self.validation_log, 'r') as f:
                results = json.load(f)
        
        results.append(asdict(result))
        
        with open(self.validation_log, 'w') as f:
            json.dump(results, f, indent=2)

class EvolutionLoopV2:
    """
    v2.0 外部反馈循环主控制器
    """
    
    def __init__(self):
        self.evolution_dir = EVOLUTION_DIR
        self.external_collector = ExternalInputCollector(self.evolution_dir)
        self.validator = RealWorldValidator(self.evolution_dir)
        
        self.current_phase = EvolutionPhase.IDLE
        
    def start(self):
        """启动v2.0进化循环"""
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║           wdai Evolution Loop v2.0 启动                      ║")
        print("║     外部反馈循环: 从闭门造车到开放进化                      ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        print()
        
        self.run_cycle()
    
    def run_cycle(self):
        """执行一次完整的v2.0进化循环"""
        cycle_id = f"v2evo_{int(time.time())}"
        print(f"[EvolutionLoopV2] 开始外部反馈循环: {cycle_id}")
        print()
        
        # Phase 1: 外部输入
        self.current_phase = EvolutionPhase.EXTERNAL_INPUT
        print("=" * 65)
        print("📥 Phase 1: 外部输入")
        print("=" * 65)
        external_info, opportunities = self.external_collector.collect_all()
        print()
        
        # Phase 2: 内部进化 (调用v1.x)
        self.current_phase = EvolutionPhase.INTERNAL_EVOLUTION
        print("=" * 65)
        print("⚙️  Phase 2: 内部进化 (调用v1.x)")
        print("=" * 65)
        # 这里可以调用v1.x的进化循环
        print("  (内部进化逻辑 - 使用现有的evolution_loop.py)")
        print()
        
        # Phase 3: 实战验证
        self.current_phase = EvolutionPhase.REAL_WORLD_VALIDATION
        print("=" * 65)
        print("🎯 Phase 3: 实战验证")
        print("=" * 65)
        validation_results = []
        for opp in opportunities[:2]:  # 验证前2个机会
            result = self.validator.validate_with_practice(opp)
            validation_results.append(result)
            print(f"  {opp.name}: 效果评分 {result.effectiveness_score:.2f}")
        print()
        
        # Phase 4: 反馈吸收
        self.current_phase = EvolutionPhase.FEEDBACK_INTEGRATION
        print("=" * 65)
        print("🔄 Phase 4: 反馈吸收")
        print("=" * 65)
        feedback = self.external_collector.gather_external_feedback()
        self._integrate_feedback(feedback, validation_results)
        print()
        
        # 生成洞察
        self._generate_insights(external_info, validation_results)
        
        self.current_phase = EvolutionPhase.IDLE
        print("=" * 65)
        print(f"[EvolutionLoopV2] 外部反馈循环 {cycle_id} 完成")
        print("=" * 65)
    
    def _integrate_feedback(self, feedback: ExternalFeedback, results: List[ValidationResult]):
        """整合反馈"""
        print("[反馈整合] 分析反馈并调整进化方向...")
        
        # 分析验证结果
        avg_effectiveness = sum(r.effectiveness_score for r in results) / len(results) if results else 0
        
        # 生成调整建议
        adjustments = []
        if avg_effectiveness < 0.5:
            adjustments.append("当前改进效果不佳，需要重新评估方法")
        if feedback.task_completion_rate < 0.7:
            adjustments.append("任务完成率偏低，需要加强错误处理")
        
        print(f"  平均效果评分: {avg_effectiveness:.2f}")
        print(f"  调整建议: {adjustments if adjustments else '继续当前方向'}")
        
        # 保存到调整日志
        adjustment_log = self.evolution_dir / "adjustments.json"
        log_entry = {
            "timestamp": time.time(),
            "avg_effectiveness": avg_effectiveness,
            "task_completion_rate": feedback.task_completion_rate,
            "adjustments": adjustments
        }
        
        logs = []
        if adjustment_log.exists():
            with open(adjustment_log, 'r') as f:
                logs = json.load(f)
        logs.append(log_entry)
        
        with open(adjustment_log, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def _generate_insights(self, info_list: List[ExternalInfo], results: List[ValidationResult]):
        """生成进化洞察"""
        print("[洞察生成] 从外部输入中提取洞察...")
        
        insights = []
        
        # 从外部信息提取
        for info in info_list[:3]:
            insights.append(f"从 {info.source} 学习: {info.title}")
        
        # 从验证结果提取
        for result in results:
            insights.extend(result.lessons_learned)
        
        print(f"  生成了 {len(insights)} 条洞察")
        
        # 保存洞察
        insights_file = self.evolution_dir / "v2_insights.json"
        data = {
            "timestamp": time.time(),
            "insights": insights
        }
        
        with open(insights_file, 'w') as f:
            json.dump(data, f, indent=2)

def main():
    """主函数"""
    loop = EvolutionLoopV2()
    loop.start()
    
    print()
    print("💡 v2.0外部反馈循环建立完成")
    print("   下一步: 在真实用户任务中验证改进效果")

if __name__ == "__main__":
    main()
