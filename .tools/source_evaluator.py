#!/usr/bin/env python3
"""
来源评估引擎 - 自动评估信息源质量
不是被动等待，而是主动分析和推荐
"""

import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from collections import Counter
import statistics

BASE_DIR = Path("/root/.openclaw/workspace")
DATA_DIR = BASE_DIR / ".claw-status/data"
HISTORY_DIR = BASE_DIR / ".tools/.learning"


class SourceEvaluator:
    """
    来源质量评估器
    基于多维度指标自动评分
    """
    
    def __init__(self):
        self.weights = {
            "content_quality": 0.30,   # 内容质量
            "update_frequency": 0.20,  # 更新频率
            "relevance": 0.25,         # 主题相关度
            "engagement": 0.15,        # 互动质量
            "consistency": 0.10        # 一致性
        }
    
    def evaluate_source(self, source_data: Dict) -> Dict:
        """
        评估单个来源的综合质量
        
        source_data = {
            "name": "来源名称",
            "platform": "bilibili",
            "content_samples": [...],  # 最近10条内容
            "historical_data": {...}   # 历史统计数据
        }
        """
        samples = source_data.get("content_samples", [])
        history = source_data.get("historical_data", {})
        
        scores = {
            "content_quality": self._eval_content_quality(samples),
            "update_frequency": self._eval_frequency(history),
            "relevance": self._eval_relevance(samples),
            "engagement": self._eval_engagement(samples),
            "consistency": self._eval_consistency(history)
        }
        
        # 计算加权总分
        total_score = sum(
            scores[k] * self.weights[k] 
            for k in scores
        )
        
        return {
            "total_score": round(total_score, 2),
            "max_score": 10.0,
            "dimension_scores": scores,
            "grade": self._get_grade(total_score),
            "recommendation": self._get_recommendation(total_score, scores),
            "confidence": self._calc_confidence(samples)
        }
    
    def _eval_content_quality(self, samples: List[Dict]) -> float:
        """评估内容质量 (0-10)"""
        if not samples:
            return 5.0
        
        quality_signals = []
        
        for item in samples:
            score = 5.0  # 基准分
            text = f"{item.get('title', '')} {item.get('summary', '')}"
            
            # 正面信号
            if len(text) > 100:  # 有实质内容
                score += 1.0
            if any(kw in text.lower() for kw in [
                "深度", "解析", "实践", "案例", "架构", "系统",
                "深入", "原理", "最佳", "推荐"
            ]):
                score += 1.5
            if re.search(r'\d+分钟|\d+小时', text):  # 有时长信息，通常是视频
                score += 0.5
            
            # 负面信号
            if any(kw in text for kw in ["震惊", "绝了", "必看", "强烈推荐!!!"]):
                score -= 2.0  # 标题党
            if len(text) < 30:
                score -= 1.0
            
            quality_signals.append(max(0, min(10, score)))
        
        return statistics.mean(quality_signals) if quality_signals else 5.0
    
    def _eval_frequency(self, history: Dict) -> float:
        """评估更新频率 (0-10)"""
        update_times = history.get("update_times", [])
        if len(update_times) < 2:
            return 5.0
        
        # 计算平均间隔
        intervals = []
        for i in range(1, len(update_times)):
            diff = (update_times[i] - update_times[i-1]).days
            intervals.append(diff)
        
        avg_interval = statistics.mean(intervals)
        
        # 评分：每天更新=10分，每周=7分，每月=4分
        if avg_interval <= 1:
            return 10.0
        elif avg_interval <= 3:
            return 8.0
        elif avg_interval <= 7:
            return 7.0
        elif avg_interval <= 14:
            return 5.0
        elif avg_interval <= 30:
            return 4.0
        else:
            return 2.0
    
    def _eval_relevance(self, samples: List[Dict]) -> float:
        """评估主题相关度 (0-10)"""
        if not samples:
            return 5.0
        
        # 目标主题关键词
        target_keywords = {
            "ai": 1.0, "agent": 1.0, "claude": 1.0, "llm": 1.0,
            "multi-agent": 1.0, "autonomous": 0.9, "openclaw": 1.0,
            "架构": 0.9, "系统": 0.8, "框架": 0.8, "设计": 0.7,
            "效率": 0.8, "自动化": 0.8, "工具": 0.7,
            "实践": 0.8, "案例": 0.8, "实战": 0.8,
            "编程": 0.6, "代码": 0.6, "开发": 0.6,
            "github": 0.7, "开源": 0.7, "项目": 0.6
        }
        
        relevance_scores = []
        for item in samples:
            text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
            score = 0
            for kw, weight in target_keywords.items():
                if kw in text:
                    score += weight
            # 归一化到0-10
            relevance_scores.append(min(10, score * 2))
        
        return statistics.mean(relevance_scores) if relevance_scores else 5.0
    
    def _eval_engagement(self, samples: List[Dict]) -> float:
        """评估互动质量 (0-10)"""
        if not samples:
            return 5.0
        
        engagement_scores = []
        for item in samples:
            score = 5.0
            
            # 播放量
            views = item.get("views", 0)
            if views > 100000:
                score += 2.0
            elif views > 10000:
                score += 1.5
            elif views > 1000:
                score += 0.5
            
            # 点赞/收藏比（如果有数据）
            likes = item.get("likes", 0)
            if views > 0 and likes / views > 0.05:  # 点赞率>5%
                score += 1.5
            
            engagement_scores.append(min(10, score))
        
        return statistics.mean(engagement_scores) if engagement_scores else 5.0
    
    def _eval_consistency(self, history: Dict) -> float:
        """评估内容一致性 (0-10)"""
        update_times = history.get("update_times", [])
        if len(update_times) < 3:
            return 5.0
        
        # 检查是否持续更新
        now = datetime.now()
        last_update = max(update_times) if update_times else now
        days_since_last = (now - last_update).days
        
        if days_since_last <= 7:
            return 10.0
        elif days_since_last <= 14:
            return 8.0
        elif days_since_last <= 30:
            return 6.0
        elif days_since_last <= 60:
            return 4.0
        else:
            return 2.0
    
    def _get_grade(self, score: float) -> str:
        """获取等级"""
        if score >= 8.5:
            return "S"  # 顶级来源
        elif score >= 7.0:
            return "A"  # 优质来源
        elif score >= 5.5:
            return "B"  # 良好来源
        elif score >= 4.0:
            return "C"  # 一般来源
        else:
            return "D"  # 低质来源
    
    def _get_recommendation(self, total_score: float, dimensions: Dict) -> str:
        """生成推荐建议"""
        recommendations = []
        
        if total_score >= 8.0:
            recommendations.append("⭐ 强烈推荐加入核心监控列表")
        elif total_score >= 6.0:
            recommendations.append("✅ 建议加入监控列表")
        else:
            recommendations.append("⏸️ 暂不推荐，保持观察")
        
        # 针对性建议
        if dimensions["content_quality"] < 6.0:
            recommendations.append("内容质量有待提升，优先选择深度内容")
        if dimensions["update_frequency"] < 5.0:
            recommendations.append("更新频率较低，建议降低监控频率")
        if dimensions["relevance"] >= 8.0:
            recommendations.append("主题高度相关，适合高优先级推送")
        
        return " | ".join(recommendations)
    
    def _calc_confidence(self, samples: List[Dict]) -> float:
        """计算评估置信度"""
        sample_count = len(samples)
        if sample_count >= 10:
            return 0.95
        elif sample_count >= 5:
            return 0.80
        elif sample_count >= 3:
            return 0.65
        else:
            return 0.50
    
    def compare_sources(self, sources: List[Dict]) -> List[Dict]:
        """比较多个来源，返回排序后的推荐列表"""
        evaluated = []
        for source in sources:
            result = self.evaluate_source(source)
            evaluated.append({
                **source,
                "evaluation": result
            })
        
        # 按总分排序
        evaluated.sort(
            key=lambda x: x["evaluation"]["total_score"], 
            reverse=True
        )
        return evaluated
    
    def generate_report(self, sources: List[Dict]) -> str:
        """生成评估报告"""
        evaluated = self.compare_sources(sources)
        
        lines = ["# 信息源评估报告", ""]
        lines.append(f"评估时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"评估来源数: {len(sources)}")
        lines.append("")
        
        for i, source in enumerate(evaluated, 1):
            ev = source["evaluation"]
            lines.append(f"## {i}. {source['name']} [{ev['grade']}级]")
            lines.append(f"- **综合评分**: {ev['total_score']}/10.0")
            lines.append(f"- **置信度**: {ev['confidence']:.0%}")
            lines.append(f"- **各维度评分**:")
            for dim, score in ev["dimension_scores"].items():
                lines.append(f"  - {dim}: {score:.1f}")
            lines.append(f"- **建议**: {ev['recommendation']}")
            lines.append("")
        
        return "\n".join(lines)


def demo():
    """演示评估功能"""
    evaluator = SourceEvaluator()
    
    # 模拟几个来源
    test_sources = [
        {
            "name": "慢学AI (B站)",
            "platform": "bilibili",
            "content_samples": [
                {"title": "Claude Agent架构最佳实践", "summary": "深入解析Multi-Agent系统设计模式", "views": 5000},
                {"title": "不加新工具，Claude如何扩展Agent行动空间", "summary": "探讨Agent的本质", "views": 3000},
            ],
            "historical_data": {
                "update_times": [datetime.now() - timedelta(days=i) for i in range(7)]
            }
        },
        {
            "name": "某营销号 (B站)",
            "platform": "bilibili",
            "content_samples": [
                {"title": "震惊！AI竟然能这样", "summary": "绝了！必看！", "views": 100000},
                {"title": "强烈推荐!!! 这个工具太牛了", "summary": "不看后悔", "views": 50000},
            ],
            "historical_data": {
                "update_times": [datetime.now() - timedelta(days=30)]
            }
        }
    ]
    
    print(evaluator.generate_report(test_sources))


if __name__ == "__main__":
    demo()
