#!/usr/bin/env python3
"""
Multi-Path Reasoning Optimization
多路径推理优化 - Prompt工程

核心策略:
1. 并行生成多个推理路径
2. 路径间交叉验证
3. 一致性检查和冲突仲裁
4. 基于置信度的结果选择
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json


class ReasoningPathType(Enum):
    """推理路径类型"""
    INTUITIVE = "intuitive"      # 直觉快速路径
    ANALYTICAL = "analytical"    # 分析深度路径
    CONSERVATIVE = "conservative" # 保守安全路径
    CREATIVE = "creative"        # 创新探索路径


@dataclass
class ReasoningPath:
    """单条推理路径"""
    path_type: ReasoningPathType
    reasoning: str
    conclusion: str
    confidence: float
    assumptions: List[str]
    evidence: List[str]


@dataclass
class VerificationResult:
    """验证结果"""
    is_consistent: bool
    agreement_score: float  # 0-1
    conflicts: List[Dict]
    dominant_conclusion: str
    overall_confidence: float


class MultiPathPromptBuilder:
    """
    多路径推理Prompt构建器
    
    生成多个角度的推理Prompt
    """
    
    # 基础Prompt模板
    BASE_TEMPLATE = """你正在解决一个复杂问题。请从{perspective}的角度进行推理。

问题: {question}

要求:
1. 展示完整的推理过程
2. 明确列出关键假设
3. 提供支持证据
4. 给出最终结论和置信度(0-1)

输出格式(JSON):
{{
    "reasoning": "详细推理过程",
    "conclusion": "最终结论",
    "confidence": 0.85,
    "assumptions": ["假设1", "假设2"],
    "evidence": ["证据1", "证据2"]
}}"""
    
    # 不同路径的视角定义
    PERSPECTIVES = {
        ReasoningPathType.INTUITIVE: {
            "name": "直觉快速",
            "description": "基于经验和模式识别的快速判断",
            "instructions": """
- 快速识别问题的核心模式
- 基于类似案例的经验做出判断
- 考虑第一感觉和直觉反应
- 适合时间敏感或模式明确的问题
"""
        },
        ReasoningPathType.ANALYTICAL: {
            "name": "深度分析",
            "description": "系统化、逐步的深度分析",
            "instructions": """
- 将问题分解为子问题
- 逐一分析每个组成部分
- 考虑因果关系和逻辑链条
- 适合复杂、需要严谨推理的问题
"""
        },
        ReasoningPathType.CONSERVATIVE: {
            "name": "保守安全",
            "description": "风险最小化的谨慎方案",
            "instructions": """
- 优先考虑最坏情况
- 识别所有潜在风险
- 选择最稳健、可验证的方案
- 适合高风险、错误代价大的问题
"""
        },
        ReasoningPathType.CREATIVE: {
            "name": "创新探索",
            "description": "跳出常规的创造性方案",
            "instructions": """
- 质疑默认假设
- 探索非显而易见的方案
- 考虑跨界思路
- 适合需要突破或优化的问题
"""
        }
    }
    
    def build_prompt(
        self,
        question: str,
        path_type: ReasoningPathType
    ) -> str:
        """构建单一路径的Prompt"""
        perspective = self.PERSPECTIVES[path_type]
        
        prompt = f"""{perspective['description']}

{perspective['instructions']}

---

{self.BASE_TEMPLATE.format(
    perspective=perspective['name'],
    question=question
)}"""
        
        return prompt
    
    def build_all_prompts(self, question: str) -> Dict[ReasoningPathType, str]:
        """构建所有路径的Prompt"""
        return {
            path_type: self.build_prompt(question, path_type)
            for path_type in ReasoningPathType
        }


class ConsistencyChecker:
    """
    一致性检查器
    
    检查多条推理路径的结论是否一致
    """
    
    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
    
    def check_consistency(
        self,
        paths: List[ReasoningPath]
    ) -> VerificationResult:
        """
        检查路径间一致性
        
        算法:
        1. 提取所有结论
        2. 计算结论间相似度
        3. 识别冲突点
        4. 计算整体置信度
        """
        if len(paths) < 2:
            return VerificationResult(
                is_consistent=True,
                agreement_score=1.0,
                conflicts=[],
                dominant_conclusion=paths[0].conclusion if paths else "",
                overall_confidence=paths[0].confidence if paths else 0.0
            )
        
        # 1. 结论分组
        conclusion_groups = self._group_similar_conclusions(paths)
        
        # 2. 找出主导结论
        dominant_group = max(conclusion_groups, key=lambda g: len(g['paths']))
        dominant_conclusion = dominant_group['representative']
        
        # 3. 识别冲突
        conflicts = []
        for group in conclusion_groups:
            if group != dominant_group:
                for path in group['paths']:
                    conflicts.append({
                        'path_type': path.path_type.value,
                        'conclusion': path.conclusion,
                        'vs_dominant_similarity': self._text_similarity(
                            path.conclusion,
                            dominant_conclusion
                        )
                    })
        
        # 4. 计算一致性和置信度
        agreement_ratio = len(dominant_group['paths']) / len(paths)
        
        # 加权平均置信度 (主导组权重更高)
        total_confidence = sum(
            p.confidence for p in dominant_group['paths']
        ) * agreement_ratio
        
        # 加上其他路径的惩罚
        other_confidence = sum(
            p.confidence * (1 - agreement_ratio) * 0.5  # 折中方案权重降低
            for p in paths if p not in dominant_group['paths']
        )
        
        overall_confidence = (total_confidence + other_confidence) / len(paths)
        
        return VerificationResult(
            is_consistent=agreement_ratio >= self.similarity_threshold,
            agreement_score=agreement_ratio,
            conflicts=conflicts,
            dominant_conclusion=dominant_conclusion,
            overall_confidence=overall_confidence
        )
    
    def _group_similar_conclusions(
        self,
        paths: List[ReasoningPath]
    ) -> List[Dict]:
        """将相似结论分组"""
        groups = []
        
        for path in paths:
            added = False
            for group in groups:
                similarity = self._text_similarity(
                    path.conclusion,
                    group['representative']
                )
                if similarity >= self.similarity_threshold:
                    group['paths'].append(path)
                    added = True
                    break
            
            if not added:
                groups.append({
                    'representative': path.conclusion,
                    'paths': [path]
                })
        
        return groups
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        计算两段文本的相似度
        
        使用Jaccard相似度
        """
        # 标准化
        t1 = set(text1.lower().split())
        t2 = set(text2.lower().split())
        
        if not t1 or not t2:
            return 0.0
        
        intersection = len(t1 & t2)
        union = len(t1 | t2)
        
        return intersection / union if union > 0 else 0.0


class ReasoningArbitrator:
    """
    推理仲裁器
    
    当多条路径结论不一致时，进行仲裁决策
    """
    
    # 路径权重 (可配置)
    PATH_WEIGHTS = {
        ReasoningPathType.INTUITIVE: 0.2,
        ReasoningPathType.ANALYTICAL: 0.35,
        ReasoningPathType.CONSERVATIVE: 0.25,
        ReasoningPathType.CREATIVE: 0.2
    }
    
    def arbitrate(
        self,
        paths: List[ReasoningPath],
        verification: VerificationResult
    ) -> Tuple[str, float, str]:
        """
        仲裁决策
        
        Returns:
            (最终结论, 置信度, 决策依据)
        """
        if verification.is_consistent:
            # 一致性高，使用主导结论
            return (
                verification.dominant_conclusion,
                verification.overall_confidence,
                "多路径结论一致，采用主导结论"
            )
        
        # 结论不一致，需要仲裁
        # 策略：加权投票
        
        conclusion_scores: Dict[str, float] = {}
        
        for path in paths:
            weight = self.PATH_WEIGHTS.get(path.path_type, 0.25)
            score = path.confidence * weight
            
            # 使用结论文本作为key
            # 相似结论合并
            merged = False
            for existing in list(conclusion_scores.keys()):
                if self._is_similar(path.conclusion, existing):
                    conclusion_scores[existing] += score
                    merged = True
                    break
            
            if not merged:
                conclusion_scores[path.conclusion] = score
        
        # 选择得分最高的
        best_conclusion = max(conclusion_scores, key=conclusion_scores.get)
        best_score = conclusion_scores[best_conclusion]
        
        # 归一化置信度
        total_score = sum(conclusion_scores.values())
        normalized_confidence = best_score / total_score if total_score > 0 else 0.5
        
        # 生成决策依据
        winning_paths = [
            p for p in paths
            if self._is_similar(p.conclusion, best_conclusion)
        ]
        path_names = [p.path_type.value for p in winning_paths]
        
        reasoning = f"加权仲裁: {', '.join(path_names)}支持此结论(权重{normalized_confidence:.2f})"
        
        return best_conclusion, normalized_confidence, reasoning
    
    def _is_similar(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """判断两段文本是否相似"""
        t1 = set(text1.lower().split())
        t2 = set(text2.lower().split())
        
        if not t1 or not t2:
            return False
        
        intersection = len(t1 & t2)
        union = len(t1 | t2)
        
        similarity = intersection / union if union > 0 else 0
        return similarity >= threshold


class MultiPathReasoner:
    """
    多路径推理器
    
    完整的多路径推理流程
    """
    
    def __init__(self):
        self.prompt_builder = MultiPathPromptBuilder()
        self.consistency_checker = ConsistencyChecker()
        self.arbitrator = ReasoningArbitrator()
    
    def reason(
        self,
        question: str,
        llm_func: callable,
        use_all_paths: bool = True
    ) -> Dict:
        """
        执行多路径推理
        
        Args:
            question: 问题
            llm_func: LLM调用函数
            use_all_paths: 是否使用所有4条路径
        
        Returns:
            包含推理结果的字典
        """
        # 1. 生成所有Prompt
        prompts = self.prompt_builder.build_all_prompts(question)
        
        # 2. 并行执行 (简化：顺序执行)
        paths = []
        
        path_types = list(ReasoningPathType) if use_all_paths else [
            ReasoningPathType.INTUITIVE,
            ReasoningPathType.ANALYTICAL
        ]
        
        for path_type in path_types:
            prompt = prompts[path_type]
            
            try:
                # 调用LLM
                response = llm_func(prompt)
                
                # 解析结果
                result = json.loads(response)
                
                path = ReasoningPath(
                    path_type=path_type,
                    reasoning=result.get('reasoning', ''),
                    conclusion=result.get('conclusion', ''),
                    confidence=result.get('confidence', 0.5),
                    assumptions=result.get('assumptions', []),
                    evidence=result.get('evidence', [])
                )
                paths.append(path)
                
            except Exception as e:
                print(f"⚠️ {path_type.value}路径失败: {e}")
        
        if not paths:
            return {
                'success': False,
                'error': '所有推理路径失败'
            }
        
        # 3. 一致性检查
        verification = self.consistency_checker.check_consistency(paths)
        
        # 4. 仲裁决策
        final_conclusion, confidence, reasoning = self.arbitrator.arbitrate(
            paths, verification
        )
        
        return {
            'success': True,
            'question': question,
            'paths': [
                {
                    'type': p.path_type.value,
                    'conclusion': p.conclusion,
                    'confidence': p.confidence,
                    'reasoning': p.reasoning[:200] + '...' if len(p.reasoning) > 200 else p.reasoning
                }
                for p in paths
            ],
            'verification': {
                'is_consistent': verification.is_consistent,
                'agreement_score': verification.agreement_score,
                'conflicts': verification.conflicts
            },
            'final': {
                'conclusion': final_conclusion,
                'confidence': confidence,
                'reasoning': reasoning
            }
        }
    
    def quick_reason(self, question: str, llm_func: callable) -> str:
        """快速推理 (只使用直觉和分析路径)"""
        result = self.reason(question, llm_func, use_all_paths=False)
        
        if result['success']:
            return result['final']['conclusion']
        else:
            return f"推理失败: {result.get('error', '未知错误')}"


# ==================== 模拟LLM函数 ====================

def mock_llm(prompt: str) -> str:
    """模拟LLM响应"""
    # 根据prompt内容返回不同的模拟结果
    if "直觉快速" in prompt:
        return json.dumps({
            "reasoning": "基于经验，这类问题通常采用方案A",
            "conclusion": "推荐采用方案A",
            "confidence": 0.75,
            "assumptions": ["问题与之前案例相似"],
            "evidence": ["历史成功率80%"]
        })
    elif "深度分析" in prompt:
        return json.dumps({
            "reasoning": "经过详细分析，方案A在技术上最可行",
            "conclusion": "推荐采用方案A",
            "confidence": 0.85,
            "assumptions": ["资源充足", "时间允许"],
            "evidence": ["技术文档支持", "测试验证通过"]
        })
    elif "保守安全" in prompt:
        return json.dumps({
            "reasoning": "考虑到风险，方案B虽然慢但更稳妥",
            "conclusion": "推荐采用方案B",
            "confidence": 0.70,
            "assumptions": ["不允许失败"],
            "evidence": ["零失败记录"]
        })
    else:  # 创新探索
        return json.dumps({
            "reasoning": "跳出常规，方案C可能带来突破性改进",
            "conclusion": "推荐采用方案C",
            "confidence": 0.60,
            "assumptions": ["愿意承担风险"],
            "evidence": ["理论可行性"]
        })


# ==================== 测试 ====================

if __name__ == "__main__":
    print("="*60)
    print("Multi-Path Reasoning - 测试")
    print("="*60)
    
    reasoner = MultiPathReasoner()
    
    # 测试1: 完整多路径推理
    print("\n1. 完整多路径推理")
    question = "应该选择哪个技术方案？"
    
    result = reasoner.reason(question, mock_llm)
    
    print(f"\n问题: {result['question']}")
    print(f"\n各路径结论:")
    for path in result['paths']:
        print(f"   [{path['type']}] 置信度{path['confidence']:.2f}: {path['conclusion']}")
    
    print(f"\n一致性检查:")
    print(f"   是否一致: {result['verification']['is_consistent']}")
    print(f"   一致率: {result['verification']['agreement_score']:.2%}")
    
    if result['verification']['conflicts']:
        print(f"   冲突: {len(result['verification']['conflicts'])}个")
    
    print(f"\n最终结论:")
    print(f"   结论: {result['final']['conclusion']}")
    print(f"   置信度: {result['final']['confidence']:.2f}")
    print(f"   依据: {result['final']['reasoning']}")
    
    # 测试2: 快速推理
    print("\n2. 快速推理 (2路径)")
    quick_result = reasoner.quick_reason("如何优化性能？", mock_llm)
    print(f"   结果: {quick_result}")
    
    # 测试3: Prompt示例
    print("\n3. Prompt示例")
    prompts = reasoner.prompt_builder.build_all_prompts("示例问题")
    for path_type, prompt in list(prompts.items())[:2]:
        print(f"\n[{path_type.value}]:")
        print(f"{prompt[:300]}...")
    
    print("\n" + "="*60)
    print("✅ 测试完成")
