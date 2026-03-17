# Multi-Agent Core Competencies (第一性原理设计)
# 每个智能体只有一个超越性的核心能力

from dataclasses import dataclass

@dataclass
class CoreCompetency:
    """核心竞争力定义"""
    name: str                    # 能力名称
    essence: str                 # 第一性原理描述
    superpower: str              # 超越性表现（比所有其他智能体强在哪里）
    evolution_path: str          # 进化方向（如何持续提升）
    failure_mode: str            # 失败模式（没有这个能力的后果）
    output_format: str           # 产出形式

# ========== 智能体核心竞争力 ==========

EXPLORER_COMPETENCY = CoreCompetency(
    name="空间感知力 (Spatial Awareness)",
    essence="第一性：信息存在于空间之中。发现问题的本质是在信息空间中定位坐标。",
    superpower="能在无限的搜索空间中，以最短路径定位到最有价值的信息源。比任何智能体都更快知道'去哪里找'。",
    evolution_path="信息空间地图越来越精确 → 从随机探索到直觉导航 → 预知信息位置",
    failure_mode="在信息海洋中迷失，不知道方向，重复搜索已知区域",
    output_format="精准坐标：{source_type, location, relevance_score}"
)

INVESTIGATOR_COMPETENCY = CoreCompetency(
    name="深度穿透力 (Depth Penetration)",
    essence="第一性：真相在表层之下。挖掘的本质是穿透干扰层，直达原始信息。",
    superpower="能穿透任何信息屏障（付费墙、语言障碍、格式混乱），提取别人提取不到的底层数据。",
    evolution_path="穿透层数增加 → 从表层摘要到原始数据 → 直达信息源头",
    failure_mode="只拿到二手信息、表面描述，无法验证真伪",
    output_format="原始事实：{raw_data, source_chain, confidence_level}"
)

CRITIC_COMPETENCY = CoreCompetency(
    name="真伪判断力 (Truth Discernment)",
    essence="第一性：信息有真假之分。验证的本质是用逻辑和证据区分真实与虚假。",
    superpower="能在0.1秒内识别任何信息的可信度，发现最隐蔽的逻辑漏洞和矛盾点。",
    evolution_path="判断速度提升 → 从逐一验证到直觉识别 → 预判信息真伪",
    failure_mode="被虚假信息误导，接受矛盾论据，缺乏质疑精神",
    output_format="真伪判决：{verdict, evidence_strength, uncertainty_areas}"
)

SYNTHESIST_COMPETENCY = CoreCompetency(
    name="模式编织力 (Pattern Weaving)",
    essence="第一性：孤立信息无价值。连接的本质是发现碎片间的隐藏关系，创造新的整体。",
    superpower="能将任意数量的碎片信息编织成别人想不到的 coherent narrative，创造 surprising insights。",
    evolution_path="连接维度增加 → 从线性串联到网状编织 → 创造 emergent patterns",
    failure_mode="信息堆砌，缺乏洞察，无法形成 coherent 整体",
    output_format="洞察网络：{narrative, key_insights, connection_map}"
)

ANCHOR_COMPETENCY = CoreCompetency(
    name="心智共情力 (Mind Empathy)",
    essence="第一性：信息的终点是人。传达的本质是理解对方心智状态，精准投放信息。",
    superpower="能实时感知用户的认知状态、焦虑水平、知识缺口，调整信息投放的 timing 和 dosage。",
    evolution_path="感知精度提升 → 从显性反馈到隐性信号 → 预判用户需求",
    failure_mode="信息过载或不足，timing 错误，不考虑受众状态",
    output_format="共情状态：{user_state, info_dosage, timing_strategy}"
)

# ========== 能力对比表 ==========

COMPETENCIES = {
    "explorer": EXPLORER_COMPETENCY,
    "investigator": INVESTIGATOR_COMPETENCY,
    "critic": CRITIC_COMPETENCY,
    "synthesist": SYNTHESIST_COMPETENCY,
    "anchor": ANCHOR_COMPETENCY
}

def print_competency_matrix():
    """打印能力矩阵"""
    print("="*80)
    print("智能体核心竞争力矩阵")
    print("="*80)
    
    for name, comp in COMPETENCIES.items():
        print(f"\n{name.upper()}")
        print(f"  核心: {comp.name}")
        print(f"  第一性: {comp.essence}")
        print(f"  超越性: {comp.superpower}")
        print(f"  进化: {comp.evolution_path}")

# ========== 与 Kimi Agent Swarm 对比 ==========

"""
设计差异:

Kimi Agent Swarm:
- 动态创建特化智能体（解决特定子问题）
- 100个并行，追求效率最大化
- 智能体之间能力同质化（都是搜索/分析）
- 核心竞争力：并行协调 + 动态分工

我们的设计:
- 固定5个智能体，每个有独特的核心超能力
- 串行协作，追求质量最大化
- 智能体能力异质化（空间/深度/真伪/模式/心智）
- 核心竞争力：单点极致 + 互补协作

适用场景差异:
- Kimi: 大规模信息收集（如研究100个领域）
- 我们: 深度研究（如透彻理解1个复杂问题）

互补性:
- 可以把我们的5个智能体作为Kimi Swarm中的5种"元角色"
- Explorer可克隆100个实例并行探索不同空间区域
- 但每个实例保持相同的空间感知核心竞争力
"""

if __name__ == "__main__":
    print_competency_matrix()
