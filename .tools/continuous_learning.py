#!/usr/bin/env python3
"""
Continuous Learning Loop - 持续学习循环
实现自动化的反馈收集和模式更新
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict

class ContinuousLearning:
    """
    持续学习系统
    
    功能：
    1. 每轮对话后自动评估
    2. 识别改进机会
    3. 积累学习模式
    4. 定期生成学习报告
    """
    
    def __init__(self, memory_dir: str = ".learning"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        
        self.session_log = self.memory_dir / "session_log.jsonl"
        self.patterns_file = self.memory_dir / "learned_patterns.json"
        self.improvements_file = self.memory_dir / "improvements.json"
        
        self.current_session = []
        self.session_start = datetime.now().isoformat()
    
    def log_interaction(self, query: str, response: str, feedback: str = None):
        """记录一次交互"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response[:200],  # 截断保存
            "feedback": feedback,
            "session_id": self.session_start
        }
        
        self.current_session.append(entry)
        
        # 追加到日志文件
        with open(self.session_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def analyze_session(self) -> Dict:
        """
        分析当前会话
        
        识别：
        - 高频错误类型
        - 改进趋势
        - 新知识领域
        """
        if not self.current_session:
            return {"status": "no_data"}
        
        total = len(self.current_session)
        with_feedback = sum(1 for e in self.current_session if e['feedback'])
        corrections = sum(1 for e in self.current_session 
                        if e.get('feedback') and any(kw in e['feedback'] 
                        for kw in ['不对', '错了', '不对，', 'no']))
        
        # 提取查询类型分布
        query_types = {}
        for entry in self.current_session:
            qtype = self._classify_query(entry['query'])
            query_types[qtype] = query_types.get(qtype, 0) + 1
        
        return {
            "total_interactions": total,
            "feedback_rate": with_feedback / total if total > 0 else 0,
            "correction_rate": corrections / total if total > 0 else 0,
            "query_types": query_types,
            "suggestions": self._generate_suggestions(corrections, query_types)
        }
    
    def _classify_query(self, query: str) -> str:
        """分类查询类型"""
        keywords = {
            "coding": ["代码", "python", "java", "程序", "函数", "bug"],
            "concept": ["什么", "解释", "原理", "为什么"],
            "howto": ["怎么", "如何", "步骤", "教程"],
            "opinion": ["怎么看", "你觉得", "建议"],
            "fact": ["是", "多少", "数据", "事实"]
        }
        
        for qtype, words in keywords.items():
            if any(w in query for w in words):
                return qtype
        return "general"
    
    def _generate_suggestions(self, corrections: int, query_types: Dict) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if corrections > 2:
            suggestions.append("近期纠正较多，建议检查回答策略")
        
        if query_types.get('opinion', 0) > 3:
            suggestions.append("主观问题较多，建议明确标注不确定性")
        
        if query_types.get('fact', 0) > 3:
            suggestions.append("事实性问题较多，建议增加验证步骤")
        
        return suggestions
    
    def update_patterns(self, new_pattern: Dict):
        """更新学习到的模式"""
        patterns = self._load_patterns()
        
        pattern_id = f"pattern_{int(time.time())}"
        patterns[pattern_id] = {
            **new_pattern,
            "created_at": datetime.now().isoformat(),
            "use_count": 1
        }
        
        with open(self.patterns_file, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, ensure_ascii=False, indent=2)
    
    def _load_patterns(self) -> Dict:
        """加载已学习的模式"""
        if self.patterns_file.exists():
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def get_learning_report(self) -> str:
        """生成学习报告"""
        analysis = self.analyze_session()
        patterns = self._load_patterns()
        
        report = []
        report.append("📚 **持续学习报告**")
        report.append(f"会话时间: {self.session_start}")
        report.append("")
        report.append(f"📊 本次会话统计:")
        report.append(f"  - 总交互: {analysis['total_interactions']}")
        report.append(f"  - 反馈率: {analysis['feedback_rate']*100:.1f}%")
        report.append(f"  - 纠正率: {analysis['correction_rate']*100:.1f}%")
        report.append("")
        report.append(f"📈 查询类型分布:")
        for qtype, count in analysis['query_types'].items():
            report.append(f"  - {qtype}: {count}")
        report.append("")
        
        if analysis['suggestions']:
            report.append(f"💡 改进建议:")
            for suggestion in analysis['suggestions']:
                report.append(f"  - {suggestion}")
        
        if patterns:
            report.append(f"")
            report.append(f"🧠 已积累 {len(patterns)} 个学习模式")
        
        return "\n".join(report)

def demo():
    """演示持续学习"""
    print("=" * 70)
    print("🔄 持续学习循环演示")
    print("=" * 70)
    
    learning = ContinuousLearning()
    
    # 模拟会话
    interactions = [
        ("Python怎么写循环？", "用for或while", "对的"),
        ("AI安全吗？", "AI相对安全但需要谨慎", "可以更详细吗"),
        ("明天天气？", "我不确定", "不对，我是问怎么查"),
    ]
    
    for query, response, feedback in interactions:
        learning.log_interaction(query, response, feedback)
        print(f"✓ 记录: {query[:20]}...")
    
    # 生成报告
    print("\n" + "-" * 70)
    print(learning.get_learning_report())
    
    # 保存一个模式
    learning.update_patterns({
        "type": "correction",
        "pattern": "天气查询",
        "lesson": "用户问天气时，应该提供查询方法而不是直接回答"
    })
    
    print("\n✅ 已保存学习模式")

if __name__ == "__main__":
    demo()
