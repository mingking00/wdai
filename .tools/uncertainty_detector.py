#!/usr/bin/env python3
"""
Simple Uncertainty Detector - 简化版

合并: uncertainty_detector_v2 + confidence_assessor + enhanced + deployment
核心功能: 检测高风险查询，必要时添加声明
"""

import re
from typing import Optional

class UncertaintyDetector:
    """简单的不确定性检测器"""
    
    def __init__(self):
        # 高风险关键词
        self.risky_keywords = {
            "medical": ["药", "病", "治疗", "症状", "医生", "医院", "诊断"],
            "legal": ["法律", "律师", "诉讼", "合同", "法规", "违法"],
            "financial": ["投资", "股票", "基金", "理财", "赚钱", "收益"],
        }
        
        # 时效性敏感
        self.time_keywords = ["2026", "2027", "2028", "2029", "2030", "最新", "最近"]
        
        # 不确定性表达
        self.uncertain_words = ["可能", "也许", "大概", "不确定", "应该", "我觉得"]
    
    def detect(self, query: str) -> tuple[bool, str]:
        """
        检测是否需要声明不确定性
        
        Returns: (should_declare, disclaimer)
        """
        query_lower = query.lower()
        
        # 1. 检查高风险领域
        for domain, keywords in self.risky_keywords.items():
            for kw in keywords:
                if kw in query_lower:
                    return True, f"⚠️ 涉及{domain}领域，建议咨询专业人士。"
        
        # 2. 检查时效性
        for kw in self.time_keywords:
            if kw in query_lower:
                return True, "⏰ 我的知识截止到2025年4月，对于最新信息可能不准确。"
        
        # 3. 检查不确定性表达
        for kw in self.uncertain_words:
            if kw in query_lower:
                return True, "💭 基于有限信息，我的回答仅供参考。"
        
        return False, ""
    
    def wrap_response(self, query: str, response: str) -> str:
        """包装响应，自动添加声明"""
        should_declare, disclaimer = self.detect(query)
        
        if should_declare:
            return f"{disclaimer}\n\n{response}"
        return response


# 全局实例
detector = UncertaintyDetector()

def detect_uncertainty(query: str) -> str:
    """快速检测"""
    _, disclaimer = detector.detect(query)
    return disclaimer
