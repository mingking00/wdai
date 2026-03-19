#!/usr/bin/env python3
"""
WDai RAG Eval v3.5 (evo-004集成)
集成RAG评估框架
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from wdai_v34_vector import WDaiSystemV34
from rag_evaluation import RAGEvaluator, ABTestFramework, RetrievalEvaluator
import time


class WDaiSystemV35(WDaiSystemV34):
    """
    WDai v3.5
    新增：RAG评估框架 (evo-004)
    """
    
    _instance = None
    
    def __init__(self):
        if self._initialized:
            return
        
        # 先初始化父类（v3.4）
        super().__init__()
        
        print("\n" + "="*60)
        print("🔥 升级至 WDai v3.5")
        print("="*60)
        
        # 初始化评估器
        print("🚀 启用RAG评估框架...")
        self.rag_evaluator = RAGEvaluator()
        self.retrieval_eval = RetrievalEvaluator()
        self.ab_test = ABTestFramework()
        
        # 评估历史
        self.evaluation_history = []
        
        print("✅ RAG评估框架已集成")
        print("   - 检索质量: Precision, Recall, F1, MAP, MRR")
        print("   - 生成质量: 事实准确性、流畅度、幻觉率")
        print("   - 端到端: 忠实度、相关性")
        print("   - A/B测试: 自动化对比实验")
        print("="*60)
    
    def evaluate_retrieval(self, query: str, 
                          retrieved_docs: list,
                          relevant_docs: list) -> dict:
        """评估检索质量"""
        metrics = self.retrieval_eval.evaluate(retrieved_docs, relevant_docs)
        
        result = {
            'query': query,
            'timestamp': time.time(),
            'metrics': metrics.to_dict()
        }
        
        self.evaluation_history.append(result)
        return result
    
    def evaluate_rag_pipeline(self, query: str,
                             retrieved_docs: list,
                             generated_answer: str,
                             relevant_docs: list,
                             doc_contents: list = None) -> dict:
        """评估完整RAG流程"""
        metrics = self.rag_evaluator.evaluate(
            query=query,
            retrieved_docs=retrieved_docs,
            generated_answer=generated_answer,
            relevant_docs=relevant_docs,
            doc_contents=doc_contents
        )
        
        result = {
            'query': query,
            'timestamp': time.time(),
            'metrics': metrics.to_dict()
        }
        
        self.evaluation_history.append(result)
        return result
    
    def create_ab_test(self, name: str, description: str, metric: str) -> str:
        """创建A/B测试"""
        return self.ab_test.create_experiment(
            name=name,
            description=description,
            metric_name=metric
        )
    
    def add_ab_result(self, exp_id: str, variant: str, value: float):
        """添加A/B测试结果"""
        self.ab_test.add_result(exp_id, variant, value)
    
    def analyze_ab_test(self, exp_id: str) -> dict:
        """分析A/B测试结果"""
        return self.ab_test.analyze(exp_id).to_dict()
    
    def get_evaluation_stats(self) -> dict:
        """获取评估统计"""
        if not self.evaluation_history:
            return {'total_evaluations': 0}
        
        # 计算平均分
        avg_scores = {
            'retrieval_f1': [],
            'factual_accuracy': [],
            'faithfulness': [],
            'overall': []
        }
        
        for eval in self.evaluation_history:
            m = eval.get('metrics', {})
            if 'retrieval' in m:
                avg_scores['retrieval_f1'].append(m['retrieval'].get('f1', 0))
            if 'generation' in m:
                avg_scores['factual_accuracy'].append(m['generation'].get('factual_accuracy', 0))
            avg_scores['faithfulness'].append(m.get('faithfulness', 0))
            avg_scores['overall'].append(m.get('overall_score', 0))
        
        return {
            'total_evaluations': len(self.evaluation_history),
            'avg_retrieval_f1': sum(avg_scores['retrieval_f1']) / len(avg_scores['retrieval_f1']) if avg_scores['retrieval_f1'] else 0,
            'avg_factual_accuracy': sum(avg_scores['factual_accuracy']) / len(avg_scores['factual_accuracy']) if avg_scores['factual_accuracy'] else 0,
            'avg_faithfulness': sum(avg_scores['faithfulness']) / len(avg_scores['faithfulness']) if avg_scores['faithfulness'] else 0,
            'avg_overall': sum(avg_scores['overall']) / len(avg_scores['overall']) if avg_scores['overall'] else 0
        }


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("WDai RAG Eval v3.5 - 集成测试")
    print("="*60)
    
    # 创建系统
    system = WDaiSystemV35()
    
    # 测试1: 检索评估
    print("\n🧪 测试: 检索质量评估")
    result = system.evaluate_retrieval(
        query="WDai的记忆架构",
        retrieved_docs=['doc1', 'doc2', 'doc3'],
        relevant_docs=['doc1', 'doc4']
    )
    print(f"   检索F1: {result['metrics']['f1']:.2%}")
    
    # 测试2: 完整RAG评估
    print("\n🧪 测试: 完整RAG评估")
    result = system.evaluate_rag_pipeline(
        query="WDai的记忆架构是什么？",
        retrieved_docs=['doc1', 'doc2'],
        generated_answer="WDai采用分层记忆架构。",
        relevant_docs=['doc1'],
        doc_contents=["WDai采用分层记忆架构，包括工作记忆和长期记忆"]
    )
    print(f"   综合得分: {result['metrics']['overall_score']:.2%}")
    
    # 测试3: A/B测试
    print("\n🧪 测试: A/B测试")
    exp_id = system.create_ab_test(
        name="检索策略对比",
        description="对比基础检索 vs 混合检索",
        metric="overall_score"
    )
    print(f"   实验ID: {exp_id}")
    
    # 添加结果
    for i in range(20):
        system.add_ab_result(exp_id, 'a', 0.7 + i * 0.01)
        system.add_ab_result(exp_id, 'b', 0.75 + i * 0.01)
    
    ab_result = system.analyze_ab_test(exp_id)
    print(f"   A均值: {ab_result['metrics_a']['mean']:.2%}")
    print(f"   B均值: {ab_result['metrics_b']['mean']:.2%}")
    print(f"   胜者: {ab_result['winner']}")
    
    # 统计
    print("\n📊 评估统计")
    stats = system.get_evaluation_stats()
    print(f"   总评估数: {stats['total_evaluations']}")
    print(f"   平均综合得分: {stats.get('avg_overall', 0):.2%}")
    
    print("\n" + "="*60)
    print("✅ v3.5 RAG评估集成测试完成")
    print("="*60)
