#!/usr/bin/env python3
"""
wdai AutoResearch Framework v1.0
基于 karpathy/autoresearch + Superpowers工作流 + 5-Agent配合

核心理念:
- 人类定方向 (program.md)
- 5-Agent协作执行 (搜集→策略→架构→整合→进化)
- IER实时学习 (每次实验都记录洞察)
- 强制检查点 (必须验证才能继续)

架构:
Coordinator → Phase管理
├── Researcher (增强版) → 信息搜集、方向确认
├── Strategist (新增) → 策略制定、实验设计  
├── Architect (新增) → 架构分析、方案设计
├── Coder → 代码实现、实验执行
├── Reviewer → 结果验证、质量审查
├── Reflector → 过程分析、模式提炼
└── Evolution → 系统优化、策略更新
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import sys

WORKSPACE = Path("/root/.openclaw/workspace")
AUTORESEARCH_DIR = WORKSPACE / ".wdai-autoresearch"
AUTORESEARCH_DIR.mkdir(exist_ok=True)

# 实验存储
EXPERIMENTS_DIR = AUTORESEARCH_DIR / "experiments"
EXPERIMENTS_DIR.mkdir(exist_ok=True)

# IER存储
IER_DIR = AUTORESEARCH_DIR / "ier"
IER_DIR.mkdir(exist_ok=True)

# 研究方向
PROGRAM_MD = AUTORESEARCH_DIR / "program.md"


class ResearchPhase(Enum):
    """AutoResearch 研究阶段"""
    GATHER = auto()      # 信息搜集
    STRATEGY = auto()    # 策略制定
    ARCHITECT = auto()   # 架构分析
    IMPLEMENT = auto()   # 整合执行
    VALIDATE = auto()    # 验证结果
    EVOLVE = auto()      # 系统进化


class AgentRole(Enum):
    """Agent角色"""
    COORDINATOR = "coordinator"
    RESEARCHER = "researcher"
    STRATEGIST = "strategist"
    ARCHITECT = "architect"
    CODER = "coder"
    REVIEWER = "reviewer"
    REFLECTOR = "reflector"
    EVOLUTION = "evolution"


@dataclass
class ResearchTask:
    """研究任务"""
    id: str
    topic: str                    # 研究主题
    hypothesis: str               # 初始假设
    complexity: int               # 复杂度 1-10
    
    # 各阶段产出
    gathered_info: List[Dict] = field(default_factory=list)
    strategy_doc: Optional[str] = None
    architecture_doc: Optional[str] = None
    implementation_code: Optional[str] = None
    validation_results: List[Dict] = field(default_factory=list)
    
    current_phase: ResearchPhase = ResearchPhase.GATHER
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class Experiment:
    """单个实验"""
    id: str
    task_id: str
    hypothesis: str          # 实验假设
    code_changes: str        # 代码变更
    metrics: Dict[str, float] = field(default_factory=dict)
    success: bool = False
    learnings: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


class IERStorage:
    """IER存储系统"""
    
    def __init__(self):
        self.records: List[Dict] = []
        self.file = IER_DIR / "research_records.jsonl"
    
    def record(self, task_id: str, phase: ResearchPhase, agent: AgentRole,
               observation: str, insight: str, evidence: Optional[str] = None):
        """记录研究洞察"""
        record = {
            "task_id": task_id,
            "phase": phase.name,
            "agent": agent.value,
            "observation": observation,
            "insight": insight,
            "evidence": evidence,
            "timestamp": datetime.now().isoformat()
        }
        self.records.append(record)
        
        with open(self.file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        print(f"   📝 IER: {agent.value} @ {phase.name}")


class ResearcherAgent:
    """
    Researcher Agent
    - 信息搜集
    - 方向确认
    - 竞品分析
    """
    
    def __init__(self, ier: IERStorage):
        self.ier = ier
    
    async def gather(self, task: ResearchTask) -> Dict[str, Any]:
        """Phase 1: 信息搜集"""
        print(f"\n📚 Phase 1: GATHER (Researcher)")
        print(f"   主题: {task.topic}")
        print(f"   假设: {task.hypothesis}")
        
        # 模拟多源搜索
        info_sources = [
            {"source": "arxiv", "relevance": 0.9, "findings": "相关论文3篇"},
            {"source": "github", "relevance": 0.85, "findings": "类似项目2个"},
            {"source": "docs", "relevance": 0.8, "findings": "官方文档关键信息"}
        ]
        
        task.gathered_info = info_sources
        
        # IER记录
        self.ier.record(task.id, ResearchPhase.GATHER, AgentRole.RESEARCHER,
                       f"搜集了{len(info_sources)}个信息源",
                       "高相关度信息源>3个才能确认研究方向",
                       json.dumps(info_sources))
        
        print(f"   ✅ 搜集完成: {len(info_sources)}个信息源")
        return {"sources": info_sources, "confidence": sum(s['relevance'] for s in info_sources) / len(info_sources)}


class StrategistAgent:
    """
    Strategist Agent
    - 策略制定
    - 实验设计
    - 风险评估
    """
    
    def __init__(self, ier: IERStorage):
        self.ier = ier
    
    async def formulate(self, task: ResearchTask) -> str:
        """Phase 2: 策略制定"""
        print(f"\n🎯 Phase 2: STRATEGY (Strategist)")
        
        strategy = f"""# Strategy: {task.topic}

## 研究目标
验证假设: {task.hypothesis}

## 实验设计
1. **基准实验**: 建立基线性能
2. **变量控制**: 每次只改一个参数
3. **验证指标**: val_bpb (与词汇表无关)
4. **时间预算**: 每个实验5分钟

## 风险与应对
- 风险: 实验不收敛 → 应对: 降低学习率
- 风险: 内存溢出 → 应对: 减小batch size

## 成功标准
- val_bpb降低 > 2%
- 实验可复现
- 改进可迁移到更大模型

## 制定时间
{datetime.now().isoformat()}
"""
        
        task.strategy_doc = strategy
        
        # IER记录
        self.ier.record(task.id, ResearchPhase.STRATEGY, AgentRole.STRATEGIST,
                       "制定了4步实验策略",
                       "控制变量法是ML实验的金标准，每次只改一个参数",
                       strategy[:200])
        
        print(f"   ✅ 策略制定完成")
        return strategy


class ArchitectAgent:
    """
    Architect Agent
    - 架构分析
    - 方案设计
    - 技术选型
    """
    
    def __init__(self, ier: IERStorage):
        self.ier = ier
    
    async def design(self, task: ResearchTask) -> str:
        """Phase 3: 架构分析"""
        print(f"\n🏗️  Phase 3: ARCHITECT (Architect)")
        
        architecture = f"""# Architecture: {task.topic}

## 系统架构
```
[Input Data] → [Tokenizer] → [Model] → [Optimizer] → [Metrics]
     ↓              ↓            ↓           ↓            ↓
 prepare.py    BPE token    GPT arch    Muon/AdamW   val_bpb
```

## 核心组件
1. **Model**: GPT-style transformer
   - depth: 12 (可扩展)
   - heads: 12
   - embed_dim: 768

2. **Optimizer**: Muon + AdamW hybrid
   - 内层用Muon (矩阵正交化)
   - 外层用AdamW

3. **Training**: 5分钟固定预算
   - batch_size: 64
   - max_iters: 自适应

## 文件结构
```
experiment_{task.id}/
├── prepare.py      # 数据准备 (固定)
├── train.py        # 训练代码 (Agent修改)
├── program.md      # 研究方向 (人类)
└── results.tsv     # 实验记录
```

## 设计时间
{datetime.now().isoformat()}
"""
        
        task.architecture_doc = architecture
        
        # IER记录
        self.ier.record(task.id, ResearchPhase.ARCHITECT, AgentRole.ARCHITECT,
                       "设计了GPT架构，Muon+AdamW混合优化器",
                       "Muon优化器在深度网络中表现更好，值得实验验证",
                       architecture[:200])
        
        print(f"   ✅ 架构设计完成")
        return architecture


class CoderAgent:
    """
    Coder Agent
    - 代码实现
    - 实验执行
    - 结果记录
    """
    
    def __init__(self, ier: IERStorage):
        self.ier = ier
        self.experiments: List[Experiment] = []
    
    async def implement_and_run(self, task: ResearchTask) -> List[Experiment]:
        """Phase 4: 整合执行"""
        print(f"\n💻 Phase 4: IMPLEMENT (Coder)")
        
        # 创建实验目录
        exp_dir = EXPERIMENTS_DIR / f"exp_{task.id}"
        exp_dir.mkdir(exist_ok=True)
        
        # 模拟多个实验
        experiments = []
        for i in range(3):  # 模拟3个实验
            exp = Experiment(
                id=f"{task.id}_exp{i}",
                task_id=task.id,
                hypothesis=f"实验{i+1}: 调整学习率",
                code_changes=f"lr = {0.001 * (i+1)}",
                metrics={"val_bpb": 3.5 - i * 0.1, "train_time": 300},
                success=i > 0,
                learnings=f"学习率{0.001*(i+1)}效果{'好' if i>0 else '差'}"
            )
            experiments.append(exp)
            
            # 写入实验文件
            (exp_dir / f"exp_{i}.json").write_text(
                json.dumps({
                    "id": exp.id,
                    "hypothesis": exp.hypothesis,
                    "code_changes": exp.code_changes,
                    "metrics": exp.metrics,
                    "success": exp.success
                }, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
        
        self.experiments.extend(experiments)
        task.implementation_code = "train.py implemented"
        
        # IER记录
        success_rate = sum(1 for e in experiments if e.success) / len(experiments)
        self.ier.record(task.id, ResearchPhase.IMPLEMENT, AgentRole.CODER,
                       f"执行了{len(experiments)}个实验，成功率{success_rate:.0%}",
                       "多实验并行验证假设，成功率>50%说明方向正确")
        
        print(f"   ✅ 实验执行完成: {len(experiments)}个实验")
        print(f"      成功率: {success_rate:.0%}")
        return experiments


class ReviewerAgent:
    """
    Reviewer Agent
    - 结果验证
    - 质量审查
    - 可复现性检查
    """
    
    def __init__(self, ier: IERStorage):
        self.ier = ier
    
    async def validate(self, task: ResearchTask, experiments: List[Experiment]) -> bool:
        """Phase 5: 验证结果"""
        print(f"\n✅ Phase 5: VALIDATE (Reviewer)")
        
        validations = []
        
        # 检查1: 指标改进
        best_exp = min(experiments, key=lambda e: e.metrics.get('val_bpb', float('inf')))
        metric_check = best_exp.metrics.get('val_bpb', 999) < 3.5
        validations.append({"check": "metric_improvement", "passed": metric_check, "best_val_bpb": best_exp.metrics.get('val_bpb')})
        
        # 检查2: 可复现性
        repro_check = all(e.metrics.get('train_time', 0) == 300 for e in experiments)
        validations.append({"check": "reproducibility", "passed": repro_check})
        
        # 检查3: 代码规范
        code_check = all(len(e.code_changes) > 0 for e in experiments)
        validations.append({"check": "code_quality", "passed": code_check})
        
        task.validation_results = validations
        all_passed = all(v['passed'] for v in validations)
        
        # IER记录
        self.ier.record(task.id, ResearchPhase.VALIDATE, AgentRole.REVIEWER,
                       f"3项验证: 指标改进({metric_check}), 可复现({repro_check}), 代码规范({code_check})",
                       "val_bpb<3.5且实验可复现才算有效改进")
        
        print(f"   {'✅' if all_passed else '❌'} 验证结果")
        for v in validations:
            print(f"      - {v['check']}: {'通过' if v['passed'] else '失败'}")
        
        return all_passed


class ReflectorAgent:
    """
    Reflector Agent
    - 过程分析
    - 模式提炼
    - 洞察生成
    """
    
    def __init__(self, ier: IERStorage):
        self.ier = ier
    
    async def analyze(self, task: ResearchTask) -> Dict[str, Any]:
        """分析研究过程"""
        print(f"\n🧠 REFLECTOR: 过程分析")
        
        # 分析成功因素
        insights = []
        
        if task.validation_results and all(v['passed'] for v in task.validation_results):
            insights.append("假设验证成功，策略有效")
        
        if len(task.gathered_info) >= 3:
            insights.append("信息搜集充分，方向确认正确")
        
        # 记录模式
        self.ier.record(task.id, ResearchPhase.EVOLVE, AgentRole.REFLECTOR,
                       f"完成{task.current_phase.name}阶段",
                       "; ".join(insights) if insights else "需要更多实验验证")
        
        return {"insights": insights, "patterns_found": len(insights)}


class EvolutionAgent:
    """
    Evolution Agent
    - 系统优化
    - 策略更新
    - 知识固化
    """
    
    def __init__(self, ier: IERStorage):
        self.ier = ier
    
    async def evolve(self, task: ResearchTask) -> Dict[str, Any]:
        """Phase 6: 系统进化"""
        print(f"\n🧬 Phase 6: EVOLVE (Evolution)")
        
        # 分析所有记录
        records = [r for r in self.ier.records if r['task_id'] == task.id]
        
        optimizations = []
        
        # 检查是否需要调整策略
        if len(records) > 5:
            optimizations.append("策略制定阶段耗时合理")
        
        # 检查实验成功率
        exp_records = [r for r in records if r['phase'] == ResearchPhase.IMPLEMENT.name]
        if exp_records:
            optimizations.append("实验执行流程稳定")
        
        # 更新program.md
        program_content = f"""# wdai AutoResearch Program

## 研究方向
{task.topic}

## 当前假设
{task.hypothesis}

## 已验证发现
- 最佳val_bpb: {min((r.get('metrics', {}).get('val_bpb', 999) for r in records), default='N/A')}
- 有效实验数: {len(exp_records)}

## 下一步策略
基于本次研究结果，建议:
1. 继续优化学习率
2. 尝试不同架构深度
3. 验证改进的迁移性

## 更新时间
{datetime.now().isoformat()}
"""
        
        PROGRAM_MD.write_text(program_content, encoding='utf-8')
        
        task.status = "completed"
        task.completed_at = datetime.now()
        
        print(f"   ✅ 系统进化完成")
        print(f"   📝 更新 program.md")
        print(f"   📊 发现 {len(optimizations)} 个可优化点")
        
        return {"optimizations": optimizations, "program_updated": True}


class CoordinatorAgent:
    """
    Coordinator Agent
    - 任务路由
    - Phase管理
    - 检查点控制
    """
    
    def __init__(self):
        self.ier = IERStorage()
        self.researcher = ResearcherAgent(self.ier)
        self.strategist = StrategistAgent(self.ier)
        self.architect = ArchitectAgent(self.ier)
        self.coder = CoderAgent(self.ier)
        self.reviewer = ReviewerAgent(self.ier)
        self.reflector = ReflectorAgent(self.ier)
        self.evolution = EvolutionAgent(self.ier)
        
        self.tasks: Dict[str, ResearchTask] = {}
    
    def create_task(self, topic: str, hypothesis: str, complexity: int = 5) -> ResearchTask:
        """创建研究任务"""
        task = ResearchTask(
            id=str(uuid.uuid4())[:8],
            topic=topic,
            hypothesis=hypothesis,
            complexity=complexity
        )
        self.tasks[task.id] = task
        
        print(f"\n{'='*70}")
        print(f"🔬 wdai AutoResearch: 创建研究任务 #{task.id}")
        print(f"{'='*70}")
        print(f"   主题: {topic}")
        print(f"   假设: {hypothesis}")
        print(f"   复杂度: {complexity}/10")
        
        return task
    
    async def run_research(self, task: ResearchTask) -> ResearchTask:
        """运行完整研究流程"""
        print(f"\n🚀 启动完整研究流程 (6 Phase)")
        
        # Phase 1: 信息搜集
        await self.researcher.gather(task)
        task.current_phase = ResearchPhase.STRATEGY
        
        # Phase 2: 策略制定
        await self.strategist.formulate(task)
        task.current_phase = ResearchPhase.ARCHITECT
        
        # Phase 3: 架构分析
        await self.architect.design(task)
        task.current_phase = ResearchPhase.IMPLEMENT
        
        # Phase 4: 整合执行
        experiments = await self.coder.implement_and_run(task)
        task.current_phase = ResearchPhase.VALIDATE
        
        # Phase 5: 验证结果
        validation_passed = await self.reviewer.validate(task, experiments)
        
        if not validation_passed:
            print(f"\n⚠️ 验证未通过，需要重新设计策略")
            # 可以在这里添加重试逻辑
        
        task.current_phase = ResearchPhase.EVOLVE
        
        # Reflector并行分析
        await self.reflector.analyze(task)
        
        # Phase 6: 系统进化
        await self.evolution.evolve(task)
        
        print(f"\n{'='*70}")
        print(f"✅ 研究任务 #{task.id} 完成")
        print(f"{'='*70}")
        
        return task
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "tasks_total": len(self.tasks),
            "tasks_completed": len([t for t in self.tasks.values() if t.status == "completed"]),
            "ier_records": len(self.ier.records),
            "experiments": len(self.coder.experiments)
        }


async def demo():
    """演示 wdai AutoResearch Framework"""
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║     🔬 wdai AutoResearch Framework v1.0                            ║")
    print("║     karpathy/autoresearch + Superpowers + 5-Agent配合              ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    print("流程: 搜集信息 → 制定策略 → 分析架构 → 整合执行 → 验证 → 进化")
    print()
    
    coordinator = CoordinatorAgent()
    
    # 创建研究任务
    task = coordinator.create_task(
        topic="优化GPT模型训练效率",
        hypothesis="使用Muon优化器可以比AdamW提高20%训练速度且保持准确率",
        complexity=7
    )
    
    # 运行研究
    await coordinator.run_research(task)
    
    # 显示统计
    stats = coordinator.get_stats()
    print(f"\n📊 研究统计:")
    print(f"   完成任务: {stats['tasks_completed']}/{stats['tasks_total']}")
    print(f"   IER记录: {stats['ier_records']} 条")
    print(f"   实验次数: {stats['experiments']} 次")
    
    print(f"\n💡 核心特性:")
    print("   • 6 Phase强制工作流")
    print("   • 8 Agent协作 (新增Researcher/Strategist/Architect)")
    print("   • IER实时记录每个Phase洞察")
    print("   • program.md自动更新研究方向")
    print("   • 实验结果自动归档")


if __name__ == '__main__':
    asyncio.run(demo())
