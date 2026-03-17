"""
IER-KG 经验自动摘要系统
基于规则和模板生成经验摘要

功能：
1. 自动提取经验核心要点
2. 生成结构化摘要
3. 支持多种经验类型
4. 关键信息提取
"""

import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class ExperienceSummary:
    """经验摘要"""
    exp_id: str
    exp_name: str
    
    # 摘要内容
    one_liner: str      # 一句话总结
    key_points: List[str]  # 关键要点
    when_to_use: str    # 适用场景
    code_snippet: str   # 核心代码片段
    related_patterns: List[str]  # 相关模式
    
    # 元信息
    summary_length: int  # 摘要长度
    completeness: float  # 完整度评分 (0-1)


class ExperienceSummarizer:
    """
    经验摘要生成器
    
    基于规则提取关键信息，生成结构化摘要
    """
    
    def __init__(self):
        # 类型特定的提取规则
        self.type_rules = {
            "shortcut": {
                "keywords": ["快捷", "快速", "简化", "技巧"],
                "template": "使用{name}可以快速{action}"
            },
            "pattern": {
                "keywords": ["模式", "设计", "结构", "组织"],
                "template": "{name}模式用于解决{problem}"
            },
            "anti_pattern": {
                "keywords": ["避免", "不要", "问题", "风险"],
                "template": "避免{name}，因为它会导致{consequence}"
            },
            "tool": {
                "keywords": ["工具", "库", "框架", "使用"],
                "template": "使用{name}来{purpose}"
            },
            "optimization": {
                "keywords": ["优化", "性能", "提升", "改进"],
                "template": "通过{name}可以优化{aspect}"
            }
        }
    
    def generate_summary(self, exp) -> ExperienceSummary:
        """
        生成经验摘要
        
        Args:
            exp: 经验对象
            
        Returns:
            经验摘要
        """
        exp_id = getattr(exp, 'id', 'unknown')
        exp_name = getattr(exp, 'name', '未命名')
        exp_type = getattr(exp, 'exp_type', 'unknown')
        description = getattr(exp, 'description', '')
        context = getattr(exp, 'context', '')
        solution = getattr(exp, 'solution', '')
        code_example = getattr(exp, 'code_example', '')
        tags = getattr(exp, 'tags', [])
        
        # 生成一句话总结
        one_liner = self._generate_one_liner(exp_name, exp_type, description, solution)
        
        # 提取关键要点
        key_points = self._extract_key_points(description, context, solution)
        
        # 确定适用场景
        when_to_use = self._extract_when_to_use(context, description)
        
        # 提取核心代码片段
        code_snippet = self._extract_code_snippet(code_example)
        
        # 识别相关模式
        related_patterns = self._extract_related_patterns(description, tags)
        
        # 计算完整度
        completeness = self._calculate_completeness(
            one_liner, key_points, when_to_use, code_snippet
        )
        
        # 计算摘要长度
        summary_text = f"{one_liner} {' '.join(key_points)} {when_to_use}"
        summary_length = len(summary_text)
        
        return ExperienceSummary(
            exp_id=exp_id,
            exp_name=exp_name,
            one_liner=one_liner,
            key_points=key_points,
            when_to_use=when_to_use,
            code_snippet=code_snippet,
            related_patterns=related_patterns,
            summary_length=summary_length,
            completeness=completeness
        )
    
    def _generate_one_liner(self, name: str, exp_type: str, 
                           description: str, solution: str) -> str:
        """生成一句话总结"""
        # 优先使用解决方案的第一句
        if solution:
            first_sentence = solution.split('。')[0].split('.')[0]
            if len(first_sentence) > 10:
                return f"{name}: {first_sentence[:80]}"
        
        # 使用描述
        if description:
            first_sentence = description.split('。')[0].split('.')[0]
            if len(first_sentence) > 10:
                return f"{name}: {first_sentence[:80]}"
        
        # 使用类型模板
        type_key = str(exp_type).lower()
        if type_key in self.type_rules:
            template = self.type_rules[type_key]["template"]
            return template.replace("{name}", name).replace("{action}", "完成任务")
        
        return f"{name}: 一种编程经验"
    
    def _extract_key_points(self, description: str, context: str, 
                           solution: str) -> List[str]:
        """提取关键要点"""
        points = []
        
        # 从描述中提取
        if description:
            # 提取列表项
            list_items = re.findall(r'[\-\*•]\s*([^\n]+)', description)
            points.extend(list_items[:3])
            
            # 提取数字标记的要点
            num_items = re.findall(r'\d+\.\s*([^\n]+)', description)
            points.extend(num_items[:3])
        
        # 从解决方案中提取
        if solution and len(points) < 3:
            sentences = re.split(r'[。\.\n]+', solution)
            for sent in sentences[:3]:
                sent = sent.strip()
                if len(sent) > 15 and len(sent) < 100:
                    points.append(sent)
        
        # 去重并限制数量
        unique_points = []
        seen = set()
        for p in points[:5]:
            key = p[:20]
            if key not in seen:
                seen.add(key)
                unique_points.append(p)
        
        return unique_points
    
    def _extract_when_to_use(self, context: str, description: str) -> str:
        """提取适用场景"""
        text = f"{context} {description}"
        
        # 查找"适用"、"场景"、"当"等关键词
        patterns = [
            r'适用[于:]([^。]+)',
            r'场景[:：]([^。]+)',
            r'当([^。]{10,50})时',
            r'适用于([^。]{10,50})',
            r'在([^。]{10,50})情况下'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()[:100]
        
        # 如果没有明确标记，使用上下文的前半部分
        if context:
            return context[:100]
        
        return "适用于相关编程任务"
    
    def _extract_code_snippet(self, code_example: str) -> str:
        """提取核心代码片段"""
        if not code_example:
            return ""
        
        # 如果代码较短，直接返回
        if len(code_example) < 200:
            return code_example.strip()
        
        # 提取第一个函数/类定义
        func_match = re.search(r'(def\s+\w+\([^)]*\):[^}]+?)(?=\n\ndef|\nclass|$)', 
                               code_example, re.DOTALL)
        if func_match:
            snippet = func_match.group(1).strip()
            if len(snippet) < 300:
                return snippet
        
        # 提取第一个类定义
        class_match = re.search(r'(class\s+\w+[^:]*:[^}]+?)(?=\n\nclass|\n\ndef|$)', 
                                code_example, re.DOTALL)
        if class_match:
            snippet = class_match.group(1).strip()
            if len(snippet) < 300:
                return snippet
        
        # 返回前200字符
        return code_example[:200].strip() + "..."
    
    def _extract_related_patterns(self, description: str, tags: List[str]) -> List[str]:
        """提取相关模式"""
        related = []
        
        # 从tags中找相关模式
        pattern_keywords = ["装饰器", "工厂", "单例", "观察者", "策略", 
                           "适配器", "代理", "迭代器", "生成器"]
        for tag in tags:
            for kw in pattern_keywords:
                if kw in tag:
                    related.append(tag)
        
        # 从描述中找相关模式
        for kw in pattern_keywords:
            if kw in description and kw not in related:
                related.append(kw + "模式")
        
        return related[:3]
    
    def _calculate_completeness(self, one_liner: str, key_points: List[str],
                               when_to_use: str, code_snippet: str) -> float:
        """计算摘要完整度"""
        score = 0.0
        
        if one_liner and len(one_liner) > 10:
            score += 0.25
        
        if key_points:
            score += min(0.25, len(key_points) * 0.08)
        
        if when_to_use and len(when_to_use) > 5:
            score += 0.25
        
        if code_snippet and len(code_snippet) > 10:
            score += 0.25
        
        return score
    
    def format_summary(self, summary: ExperienceSummary, 
                      format_type: str = "markdown") -> str:
        """
        格式化摘要输出
        
        Args:
            summary: 经验摘要
            format_type: 输出格式 (markdown/text/json)
        """
        if format_type == "json":
            return json.dumps({
                "exp_id": summary.exp_id,
                "exp_name": summary.exp_name,
                "one_liner": summary.one_liner,
                "key_points": summary.key_points,
                "when_to_use": summary.when_to_use,
                "code_snippet": summary.code_snippet,
                "related_patterns": summary.related_patterns,
                "completeness": summary.completeness
            }, ensure_ascii=False, indent=2)
        
        elif format_type == "text":
            lines = [
                f"【{summary.exp_name}】",
                f"一句话: {summary.one_liner}",
                f"适用场景: {summary.when_to_use}",
                "关键要点:"
            ]
            for i, point in enumerate(summary.key_points, 1):
                lines.append(f"  {i}. {point}")
            
            if summary.code_snippet:
                lines.extend(["核心代码:", summary.code_snippet[:200]])
            
            return "\n".join(lines)
        
        else:  # markdown
            lines = [
                f"### 📌 {summary.exp_name}",
                "",
                f"> {summary.one_liner}",
                "",
                f"**适用场景**: {summary.when_to_use}",
                "",
                "**关键要点**:",
            ]
            for point in summary.key_points:
                lines.append(f"- {point}")
            
            if summary.code_snippet:
                lines.extend(["", "**核心代码**:", "```python", summary.code_snippet[:200], "```"])
            
            if summary.related_patterns:
                lines.extend(["", f"**相关模式**: {', '.join(summary.related_patterns)}"])
            
            lines.append(f"\n*完整度: {summary.completeness:.0%}*")
            
            return "\n".join(lines)


class BatchSummarizer:
    """批量摘要生成器"""
    
    def __init__(self):
        self.summarizer = ExperienceSummarizer()
    
    def summarize_all(self, experiences: Dict) -> Dict[str, ExperienceSummary]:
        """批量生成所有经验的摘要"""
        summaries = {}
        
        for exp_id, exp in experiences.items():
            try:
                summary = self.summarizer.generate_summary(exp)
                summaries[exp_id] = summary
            except Exception as e:
                print(f"[Summarizer] 生成摘要失败 {exp_id}: {e}")
        
        return summaries
    
    def generate_summary_report(self, experiences: Dict) -> Dict:
        """生成摘要统计报告"""
        summaries = self.summarize_all(experiences)
        
        if not summaries:
            return {"message": "无经验数据"}
        
        total = len(summaries)
        avg_completeness = sum(s.completeness for s in summaries.values()) / total
        
        # 完整度分布
        completeness_dist = {
            "high (80%+)": sum(1 for s in summaries.values() if s.completeness >= 0.8),
            "medium (50-80%)": sum(1 for s in summaries.values() if 0.5 <= s.completeness < 0.8),
            "low (<50%)": sum(1 for s in summaries.values() if s.completeness < 0.5)
        }
        
        # Top完整度的经验
        top_complete = sorted(summaries.values(), 
                             key=lambda x: x.completeness, 
                             reverse=True)[:5]
        
        return {
            "total_experiences": total,
            "avg_completeness": round(avg_completeness, 2),
            "completeness_distribution": completeness_dist,
            "top_complete": [
                {"name": s.exp_name, "completeness": round(s.completeness, 2)}
                for s in top_complete
            ]
        }


# 便捷函数
def summarize_experience(exp) -> str:
    """单条经验摘要（便捷函数）"""
    summarizer = ExperienceSummarizer()
    summary = summarizer.generate_summary(exp)
    return summarizer.format_summary(summary, "markdown")


def batch_summarize(experiences: Dict) -> Dict[str, str]:
    """批量生成摘要"""
    batch = BatchSummarizer()
    summaries = batch.summarize_all(experiences)
    
    return {
        exp_id: batch.summarizer.format_summary(summary, "markdown")
        for exp_id, summary in summaries.items()
    }


if __name__ == "__main__":
    # 测试
    class MockExp:
        def __init__(self):
            self.id = "exp_001"
            self.name = "使用@lru_cache优化"
            self.description = "使用functools.lru_cache装饰器缓存函数结果，避免重复计算。"
            self.context = "当函数有昂贵的计算且输入重复时"
            self.solution = "在函数定义前添加@lru_cache装饰器，可以指定maxsize参数。"
            self.code_example = '''@lru_cache(maxsize=128)
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)'''
            self.tags = ["性能优化", "缓存", "装饰器"]
            self.exp_type = "optimization"
    
    exp = MockExp()
    summary_text = summarize_experience(exp)
    print(summary_text)
