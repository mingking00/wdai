#!/usr/bin/env python3
"""
WDai Adaptive RAG v1.0 - 集成到主系统
将自适应RAG集成到WDaiSystemV31
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from wdai_v31_complete import WDaiSystemV31
from adaptive_rag import MultiStageRAG, QueryType
from typing import Dict, Any
import hashlib
import time


class WDaiSystemV32(WDaiSystemV31):
    """
    WDai v3.2
    新增：自适应RAG (evo-001)
    """
    
    _instance = None
    
    def __init__(self):
        if self._initialized:
            return
        
        # 先初始化父类（v3.1）
        super().__init__()
        
        print("\n" + "="*60)
        print("🔥 升级至 WDai v3.2")
        print("="*60)
        
        # 用自适应RAG替换基础检索
        print("🚀 启用自适应RAG引擎...")
        self.adaptive_rag = MultiStageRAG(self.retrieval)
        
        # 更新协调器
        self.orchestrator.register_capability('adaptive_rag', self.adaptive_rag)
        
        print("✅ 自适应RAG已集成")
        print("   - 查询分类器: 5种查询类型")
        print("   - 策略选择器: 动态策略配置")
        print("   - 参数调整器: 基于反馈优化")
        print("="*60)
    
    def query(self, text: str, user_id: str = None) -> Dict:
        """
        统一查询接口 v3.2
        使用自适应RAG进行检索
        """
        query_id = hashlib.md5(f"{text}{time.time()}".encode()).hexdigest()[:16]
        
        from wdai_unified_v3 import Context
        context = Context(
            session_id=user_id or "anonymous",
            query_id=query_id,
            user_id=user_id
        )
        
        # 使用自适应RAG检索
        result = self.adaptive_rag.retrieve(text, context)
        
        # 如果需要推理，调用推理能力
        if result.success and result.data:
            # 获取分类信息
            classification = result.data.get('classification', {})
            query_type = classification.get('type', 'explanatory')
            
            # 解释性/创造性查询需要额外推理
            if query_type in ['explanatory', 'creative']:
                reasoning_result = self.reasoning.reason(text, context)
                
                # 合并结果
                return {
                    'success': True,
                    'data': {
                        'retrieval': result.data,
                        'reasoning': reasoning_result.data if reasoning_result.success else None
                    },
                    'confidence': (result.confidence + reasoning_result.confidence) / 2,
                    'query_id': query_id,
                    'adaptive_info': {
                        'type': query_type,
                        'strategy': result.data.get('strategy', {}),
                        'sources': result.sources
                    }
                }
        
        return {
            'success': result.success,
            'data': result.data,
            'error': result.error,
            'confidence': result.confidence,
            'query_id': query_id,
            'adaptive_info': {
                'type': result.data.get('classification', {}).get('type') if result.data else None,
                'strategy': result.data.get('strategy', {}) if result.data else None,
                'sources': result.sources
            }
        }
    
    def feedback(self, query_id: str, satisfied: bool):
        """用户反馈 - 触发参数调整"""
        self.adaptive_rag.feedback(query_id, 'satisfied' if satisfied else 'dissatisfied')
        
        # 同时更新学习模块
        super().provide_feedback(satisfied, query_id)
    
    def get_rag_stats(self) -> Dict:
        """获取RAG统计"""
        return self.adaptive_rag.get_stats()


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("WDai Adaptive RAG v3.2 - 集成测试")
    print("="*60)
    
    # 创建系统
    system = WDaiSystemV32()
    
    # 添加测试知识
    print("\n📚 添加测试知识...")
    test_data = [
        "WDai采用分层记忆架构：工作记忆、情景记忆、语义记忆、程序记忆",
        "向量存储使用384维本地嵌入模型，支持完全离线运行",
        "多路径推理包括：直觉路径、分析路径、保守路径、创新路径",
        "自适应RAG根据查询类型动态选择检索策略，包括5种类型识别",
        "查询分类器可以识别事实性、解释性、创造性、对比性、程序性查询",
    ]
    
    for content in test_data:
        system.add_knowledge(content, {'category': 'adaptive_rag_test'})
    
    print(f"   已添加{len(test_data)}条知识")
    
    # 测试不同类型的查询
    print("\n🧪 测试自适应检索:\n")
    
    test_queries = [
        "什么是WDai的记忆架构？",
        "为什么使用分层记忆？",
        "比较直觉路径和分析路径",
    ]
    
    for query in test_queries:
        print(f"📝 查询: {query}")
        result = system.query(query)
        
        if result['success']:
            adaptive = result.get('adaptive_info', {})
            print(f"   识别类型: {adaptive.get('type')}")
            print(f"   使用策略: {adaptive.get('strategy', {}).get('name')}")
            print(f"   检索结果: {len(adaptive.get('sources', []))}条")
            print(f"   置信度: {result['confidence']:.2f}")
        
        print()
    
    # RAG统计
    print("\n📊 RAG统计")
    stats = system.get_rag_stats()
    print(f"   总查询: {stats.get('total_queries', 0)}")
    print(f"   类型分布: {stats.get('type_distribution', {})}")
    print(f"   平均延迟: {stats.get('avg_latency_ms', 0):.1f}ms")
    
    # 系统状态
    print("\n📊 系统状态")
    status = system.get_status()
    print(f"   记忆数: {status['memories']}")
    print(f"   学习记录: {status['learning_records']}")
    
    print("\n" + "="*60)
    print("✅ v3.2 自适应RAG集成测试完成")
    print("="*60)
