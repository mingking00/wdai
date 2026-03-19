"""
验证工具包 - Validation Toolkit
可复用的假设验证框架
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum
import json
import time

class ValidationLevel(Enum):
    QUICK = "quick"      # 5分钟内快速验证
    STANDARD = "standard" # 30分钟内标准验证
    DEEP = "deep"        # 深度验证，可能需要数小时

class EvidenceType(Enum):
    LITERATURE = "literature"      # 文献/研究支持
    EXPERIMENT = "experiment"      # 实验数据
    EXPERT = "expert"              # 专家意见
    OBSERVATION = "observation"    # 观察数据
    SIMULATION = "simulation"      # 模拟结果

@dataclass
class Evidence:
    type: EvidenceType
    source: str
    confidence: float  # 0-1
    description: str
    timestamp: str
    
@dataclass  
class ValidationResult:
    hypothesis: str
    validated: bool
    confidence: float
    evidences: List[Evidence]
    time_spent_minutes: float
    recommendations: List[str]

class ValidationToolkit:
    """假设验证工具包"""
    
    def __init__(self):
        self.history: List[ValidationResult] = []
    
    def validate(self, 
                 hypothesis: str,
                 level: ValidationLevel = ValidationLevel.STANDARD,
                 search_fn = None) -> ValidationResult:
        """
        执行验证流程
        
        Args:
            hypothesis: 待验证的假设
            level: 验证深度
            search_fn: 搜索函数 (用于收集证据)
        """
        start_time = time.time()
        evidences = []
        
        # 1. 文献查证
        if search_fn:
            lit_results = search_fn(hypothesis)
            for result in lit_results[:3]:
                evidences.append(Evidence(
                    type=EvidenceType.LITERATURE,
                    source=result.get('url', 'unknown'),
                    confidence=0.7,
                    description=result.get('summary', '')[:200],
                    timestamp=time.strftime('%Y-%m-%d')
                ))
        
        # 2. 置信度计算
        if evidences:
            avg_confidence = sum(e.confidence for e in evidences) / len(evidences)
            validated = avg_confidence > 0.6
        else:
            avg_confidence = 0.0
            validated = False
        
        time_spent = (time.time() - start_time) / 60
        
        result = ValidationResult(
            hypothesis=hypothesis,
            validated=validated,
            confidence=avg_confidence,
            evidences=evidences,
            time_spent_minutes=time_spent,
            recommendations=self._generate_recommendations(validated, evidences)
        )
        
        self.history.append(result)
        return result
    
    def _generate_recommendations(self, validated: bool, evidences: List[Evidence]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if not validated:
            recommendations.append("假设置信度不足，需要更多证据支持")
        
        if len(evidences) < 2:
            recommendations.append("证据数量不足，建议寻找更多来源")
            
        evidence_types = set(e.type for e in evidences)
        if len(evidence_types) < 2:
            recommendations.append("证据类型单一，建议多样化证据来源")
            
        return recommendations
    
    def export_report(self, path: str):
        """导出验证报告"""
        report = {
            "total_validations": len(self.history),
            "success_rate": sum(1 for r in self.history if r.validated) / max(len(self.history), 1),
            "validations": [
                {
                    "hypothesis": r.hypothesis,
                    "validated": r.validated,
                    "confidence": r.confidence,
                    "evidence_count": len(r.evidences),
                    "time_spent": r.time_spent_minutes
                }
                for r in self.history
            ]
        }
        with open(path, 'w') as f:
            json.dump(report, f, indent=2)

# 使用示例
if __name__ == "__main__":
    toolkit = ValidationToolkit()
    
    # 示例：验证一个假设
    result = toolkit.validate(
        hypothesis="MCP adoption will reach 90% of enterprises by end of 2025",
        level=ValidationLevel.QUICK,
        search_fn=lambda q: [{"url": "example.com", "summary": "Market analysis shows rapid adoption"}]
    )
    
    print(f"假设: {result.hypothesis}")
    print(f"验证结果: {'✅ 通过' if result.validated else '❌ 未通过'}")
    print(f"置信度: {result.confidence:.2%}")
    print(f"耗时: {result.time_spent_minutes:.1f}分钟")
