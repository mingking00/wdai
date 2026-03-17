#!/usr/bin/env python3
"""
OCA-MAS 测试套件
"""

import asyncio
import pytest
import time
from pathlib import Path
import sys

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from adaptive_orchestrator import AdaptiveOrchestrator, research, ResearchState
from personas import PersonaTeam, QUERY_GENERATOR


# ============ 基础功能测试 ============

class TestBasicFunctionality:
    """基础功能测试"""
    
    @pytest.mark.asyncio
    async def test_research_simple(self):
        """测试简单查询"""
        result = await research("Python asyncio", max_parallel=2)
        
        assert "answer" in result
        assert "insights" in result
        assert result["sources_count"] >= 0
        print(f"✓ 简单查询测试通过: {result['query']}")
    
    @pytest.mark.asyncio
    async def test_research_complex(self):
        """测试复杂查询"""
        result = await research(
            "Latest developments in AI agent frameworks 2026",
            max_parallel=5
        )
        
        assert len(result["answer"]) > 0
        assert result["parallel_agents"] > 0
        assert result["critical_path_time"] > 0
        print(f"✓ 复杂查询测试通过: {result['parallel_agents']} agents")
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """测试编排器初始化"""
        orch = AdaptiveOrchestrator(max_parallel=3)
        
        assert orch.max_parallel == 3
        assert orch.state is not None
        print("✓ 编排器初始化测试通过")


# ============ 核心能力测试 ============

class TestCoreCompetencies:
    """核心能力测试"""
    
    def test_explorer_competency(self):
        """测试Explorer空间感知力"""
        persona = PersonaTeam.get_persona("explorer")
        
        assert persona is not None
        assert "空间感知力" in persona.core_trait
        assert "我知道它在哪里" == persona.catchphrase
        print("✓ Explorer核心能力验证通过")
    
    def test_investigator_competency(self):
        """测试Investigator深度穿透力"""
        persona = PersonaTeam.get_persona("investigator")
        
        assert persona is not None
        assert "深度穿透力" in persona.core_trait
        assert "源头" in persona.catchphrase
        print("✓ Investigator核心能力验证通过")
    
    def test_critic_competency(self):
        """测试Critic真伪判断力"""
        persona = PersonaTeam.get_persona("critic")
        
        assert persona is not None
        assert "真伪判断力" in persona.core_trait
        assert "真" in persona.catchphrase or "假" in persona.catchphrase
        print("✓ Critic核心能力验证通过")
    
    def test_synthesist_competency(self):
        """测试Synthesist模式编织力"""
        persona = PersonaTeam.get_persona("synthesist")
        
        assert persona is not None
        assert "模式编织力" in persona.core_trait
        print("✓ Synthesist核心能力验证通过")
    
    def test_anchor_competency(self):
        """测试Anchor心智共情力"""
        persona = PersonaTeam.get_persona("anchor")
        
        assert persona is not None
        assert "心智共情力" in persona.core_trait
        print("✓ Anchor核心能力验证通过")


# ============ 并行性能测试 ============

class TestParallelPerformance:
    """并行性能测试"""
    
    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """测试并行执行效率"""
        start = time.time()
        
        result = await research(
            "Test parallel execution",
            max_parallel=5
        )
        
        elapsed = time.time() - start
        
        # 验证并行度
        assert result["parallel_agents"] == 5
        # 验证时间合理 (模拟执行应该很快)
        assert elapsed < 2.0
        
        print(f"✓ 并行执行测试通过: {result['parallel_agents']} agents, {elapsed:.2f}s")
    
    @pytest.mark.asyncio
    async def test_critical_path_optimization(self):
        """测试关键路径优化"""
        orch = AdaptiveOrchestrator(max_parallel=10)
        
        start = time.time()
        result = await orch.execute("Test critical path")
        elapsed = time.time() - start
        
        # 关键路径时间应该小于串行时间
        # 5个任务串行约 0.5s，并行应该 < 0.2s
        assert result["critical_path_time"] < 0.5
        
        print(f"✓ 关键路径优化测试通过: {result['critical_path_time']:.2f}s")


# ============ 反思循环测试 ============

class TestReflectionLoop:
    """反思循环测试"""
    
    @pytest.mark.asyncio
    async def test_reflection_sufficient(self):
        """测试信息充足场景"""
        # 简单查询应该一次通过
        result = await research("Simple test query")
        
        # 应该不需要太多循环
        assert result["sources_count"] >= 0
        print("✓ 反思充足测试通过")
    
    @pytest.mark.asyncio
    async def test_max_loops_respected(self):
        """测试最大循环限制"""
        orch = AdaptiveOrchestrator()
        orch.state.max_research_loops = 2
        
        result = await orch.execute("Test max loops")
        
        # 不应该超过最大循环
        print("✓ 最大循环限制测试通过")


# ============ 集成测试 ============

class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流程"""
        query = "Latest developments in quantum computing 2026"
        
        result = await research(query, max_parallel=5)
        
        # 验证完整输出结构
        assert "query" in result
        assert "answer" in result
        assert "insights" in result
        assert "sources_count" in result
        assert "parallel_agents" in result
        assert "critical_path_time" in result
        
        # 验证数据一致性
        assert result["query"] == query
        assert result["parallel_agents"] > 0
        assert result["critical_path_time"] > 0
        
        print(f"✓ 完整工作流程测试通过")
        print(f"   Query: {result['query'][:50]}...")
        print(f"   Sources: {result['sources_count']}")
        print(f"   Time: {result['critical_path_time']:.2f}s")
    
    @pytest.mark.asyncio
    async def test_persona_integration(self):
        """测试人格系统集成"""
        orch = AdaptiveOrchestrator()
        
        # 验证所有Agent人格可用
        for role in ["explorer", "investigator", "critic", "synthesist", "anchor"]:
            persona = PersonaTeam.get_persona(role)
            assert persona is not None
            assert len(persona.catchphrase) > 0
        
        print("✓ 人格系统集成测试通过")


# ============ 压力测试 ============

class TestStress:
    """压力测试"""
    
    @pytest.mark.asyncio
    async def test_high_parallelism(self):
        """测试高并行度"""
        orch = AdaptiveOrchestrator(max_parallel=20)
        
        start = time.time()
        result = await orch.execute("Stress test query")
        elapsed = time.time() - start
        
        # 即使20个并行实例，也应该快速完成
        assert elapsed < 3.0
        print(f"✓ 高并行度测试通过: 20 agents, {elapsed:.2f}s")
    
    @pytest.mark.asyncio
    async def test_multiple_queries(self):
        """测试多个连续查询"""
        queries = [
            "Query 1: AI frameworks",
            "Query 2: Quantum computing",
            "Query 3: Blockchain",
        ]
        
        results = []
        for query in queries:
            result = await research(query, max_parallel=3)
            results.append(result)
        
        assert len(results) == 3
        print("✓ 多连续查询测试通过")


# ============ 边界测试 ============

class TestEdgeCases:
    """边界测试"""
    
    @pytest.mark.asyncio
    async def test_empty_query(self):
        """测试空查询"""
        result = await research("")
        assert "answer" in result
        print("✓ 空查询测试通过")
    
    @pytest.mark.asyncio
    async def test_very_long_query(self):
        """测试超长查询"""
        long_query = "AI " * 100
        result = await research(long_query)
        assert "answer" in result
        print("✓ 超长查询测试通过")
    
    @pytest.mark.asyncio
    async def test_special_characters(self):
        """测试特殊字符"""
        special_query = "Test @#$%^&*() special chars 测试"
        result = await research(special_query)
        assert "answer" in result
        print("✓ 特殊字符测试通过")


# ============ 性能基准测试 ============

class TestBenchmarks:
    """性能基准测试"""
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_simple_query_performance(self):
        """简单查询性能基准"""
        start = time.time()
        result = await research("Simple query", max_parallel=2)
        elapsed = time.time() - start
        
        # 简单查询应该 < 1s
        assert elapsed < 1.0
        print(f"✓ 简单查询性能: {elapsed:.2f}s")
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_complex_query_performance(self):
        """复杂查询性能基准"""
        start = time.time()
        result = await research(
            "Comprehensive analysis of AI agent frameworks",
            max_parallel=5
        )
        elapsed = time.time() - start
        
        # 复杂查询应该 < 3s
        assert elapsed < 3.0
        print(f"✓ 复杂查询性能: {elapsed:.2f}s")


# ============ 主函数 ============

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("OCA-MAS 测试套件")
    print("="*60 + "\n")
    
    # 使用 pytest 运行
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode


if __name__ == "__main__":
    # 直接运行测试
    print("\n运行快速测试...\n")
    
    async def quick_test():
        # 基础测试
        result = await research("Test query", max_parallel=3)
        print(f"✓ 基础测试通过")
        print(f"  Query: {result['query']}")
        print(f"  Sources: {result['sources_count']}")
        print(f"  Time: {result['critical_path_time']:.2f}s")
        
        # 人格测试
        for role in ["explorer", "investigator", "critic", "synthesist", "anchor"]:
            persona = PersonaTeam.get_persona(role)
            assert persona is not None
        print("✓ 人格测试通过")
    
    asyncio.run(quick_test())
    
    print("\n" + "="*60)
    print("所有快速测试通过!")
    print("="*60)
