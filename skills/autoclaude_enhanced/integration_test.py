#!/usr/bin/env python3
"""
AutoClaude 冲突解决系统集成测试
模拟真实运行环境，验证系统稳定性
"""

import sys
import os
import asyncio
import time
import random
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conflict_resolution_v2 import (
    SemanticMergeStrategy,
    ConflictPredictor,
    ConflictMemory,
    ConflictCoordinator,
    ConflictReport,
    ConflictType,
    ConflictSeverity,
    Task,
    MergeResult,
    AutoClaudeIntegration
)

class MockLLM:
    """模拟LLM客户端"""
    def generate(self, prompt: str) -> str:
        return """def unified_function():
    # 协调后的实现
    pass"""

class MockAgent:
    """模拟Agent"""
    def __init__(self, agent_id: str, domain: str):
        self.id = agent_id
        self.domain = domain
        self.completed_tasks = []
        self.modified_files = {}
    
    async def execute_task(self, task: Task, coordinator: ConflictCoordinator) -> Dict:
        """执行任务，使用文件锁"""
        results = []
        
        for file_path in task.target_files:
            # 尝试获取文件锁
            if not coordinator.acquire_file_lock(self.id, file_path):
                return {
                    'success': False,
                    'error': f'无法获取文件锁: {file_path}',
                    'agent': self.id
                }
            
            try:
                # 模拟代码修改
                modified_code = self._generate_modification(file_path, task)
                self.modified_files[file_path] = modified_code
                results.append({
                    'file': file_path,
                    'status': 'modified',
                    'lines_changed': random.randint(5, 50)
                })
            finally:
                coordinator.release_file_lock(file_path)
        
        self.completed_tasks.append(task.id)
        return {
            'success': True,
            'agent': self.id,
            'task': task.id,
            'results': results
        }
    
    def _generate_modification(self, file_path: str, task: Task) -> str:
        """生成模拟代码修改"""
        return f"# Modified by {self.id}\n# Task: {task.description}\n"

class IntegrationTest:
    """集成测试套件"""
    
    def __init__(self):
        self.coordinator = ConflictCoordinator(MockLLM())
        self.results = []
    
    async def run_all_tests(self):
        """运行所有集成测试"""
        print("=" * 60)
        print("AutoClaude 冲突解决系统 - 集成测试")
        print("=" * 60)
        
        tests = [
            ("场景1: 无冲突并行执行", self.test_no_conflict_parallel),
            ("场景2: 文件冲突检测与解决", self.test_file_conflict_resolution),
            ("场景3: 高风险任务串行化", self.test_high_risk_serialization),
            ("场景4: 历史冲突复用", self.test_conflict_memory_reuse),
            ("场景5: 复杂场景混合测试", self.test_complex_scenario),
            ("场景6: 压力测试 - 多Agent并发", self.test_stress_concurrent),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            print(f"\n【{name}】")
            try:
                await test_func()
                print(f"  ✓ {name} - 通过")
                passed += 1
            except Exception as e:
                print(f"  ✗ {name} - 失败: {e}")
                failed += 1
        
        print("\n" + "=" * 60)
        print(f"集成测试结果: {passed} 通过, {failed} 失败")
        print("=" * 60)
        
        return failed == 0
    
    async def test_no_conflict_parallel(self):
        """场景1: 无冲突的任务并行执行"""
        # 创建3个Agent，各自修改不同文件
        agents = [
            MockAgent(f"Agent-{i}", f"domain-{i}")
            for i in range(3)
        ]
        
        tasks = [
            Task(f"T{i}", agents[i].id, f"任务{i}", [f"file{i}.py"], [], f"domain-{i}")
            for i in range(3)
        ]
        
        # 预测冲突
        coordination = await self.coordinator.coordinate_task_assignment(tasks)
        
        # 应该没有高风险冲突
        high_risk = [c for c in coordination['predicted_conflicts'] 
                    if c['severity'] in ['HIGH', 'CRITICAL']]
        assert len(high_risk) == 0, "不应该有高风险冲突"
        
        # 并行执行所有任务
        results = await asyncio.gather(*[
            agent.execute_task(task, self.coordinator)
            for agent, task in zip(agents, tasks)
        ])
        
        # 所有任务应该成功
        assert all(r['success'] for r in results), "所有任务应该成功"
    
    async def test_file_conflict_resolution(self):
        """场景2: 文件冲突检测与解决"""
        # 创建2个Agent，都修改同一个文件
        agent1 = MockAgent("Agent-1", "backend")
        agent2 = MockAgent("Agent-2", "backend")
        
        tasks = [
            Task("T1", agent1.id, "添加JWT认证", ["auth.py"], [], "backend"),
            Task("T2", agent2.id, "添加密码哈希", ["auth.py"], [], "backend"),
        ]
        
        # 预测冲突
        coordination = await self.coordinator.coordinate_task_assignment(tasks)
        
        # 应该检测到文件重叠冲突
        conflicts = coordination['predicted_conflicts']
        assert len(conflicts) > 0, "应该检测到冲突"
        assert any('auth.py' in str(c.get('reasons', [])) for c in conflicts), \
            "应该检测到auth.py的冲突"
        
        # 使用语义合并策略
        strategy = SemanticMergeStrategy(MockLLM())
        
        base = "class AuthManager:\n    pass"
        version_a = "class AuthManager:\n    def jwt_auth(self): pass"
        version_b = "class AuthManager:\n    def hash_pwd(self): pass"
        
        result = strategy.semantic_merge(base, version_a, version_b, "Agent-1", "Agent-2")
        
        assert result.success, "合并应该成功"
        assert result.strategy == 'orthogonal_merge', "应该是正交合并"
    
    async def test_high_risk_serialization(self):
        """场景3: 高风险任务自动串行化"""
        tasks = [
            Task("T1", "Agent-1", "修改核心模块", ["core.py", "utils.py"], [], "core"),
            Task("T2", "Agent-2", "修改核心模块", ["core.py"], [], "core"),
            Task("T3", "Agent-3", "修改工具函数", ["utils.py"], [], "utils"),
        ]
        
        coordination = await self.coordinator.coordinate_task_assignment(tasks)
        assignments = coordination['optimized_assignments']
        
        # T1和T2有core.py重叠，应该被分到sequential批次
        sequential_batches = [a for a in assignments if a['type'] == 'sequential']
        
        # 验证高风险任务被正确处理
        assert coordination['risk_score'] > 0, "应该有风险分数"
    
    async def test_conflict_memory_reuse(self):
        """场景4: 历史冲突复用"""
        memory = ConflictMemory()
        
        # 存储一个解决方案
        conflict = ConflictReport(
            type=ConflictType.FILE_OVERLAP,
            severity=ConflictSeverity.HIGH,
            file_path="src/auth.py",
            involved_agents=["Agent-1", "Agent-2"],
            details={'function': 'login'}
        )
        
        resolution = MergeResult(
            success=True,
            content="# 协调后的代码",
            strategy="semantic_merge",
            conflicts=[]
        )
        
        memory.store_resolution(conflict, resolution)
        
        # 查找相似冲突
        similar = ConflictReport(
            type=ConflictType.FILE_OVERLAP,
            severity=ConflictSeverity.HIGH,
            file_path="src/auth.py",
            involved_agents=["Agent-3", "Agent-4"],
            details={'function': 'oauth'}
        )
        
        cached = memory.find_similar_resolution(similar)
        
        assert cached is not None, "应该找到历史方案"
        assert cached['resolution_code'] == "# 协调后的代码"
        
        # 更新成功率
        memory.update_success_rate("semantic_merge", True)
        memory.update_success_rate("semantic_merge", True)
        memory.update_success_rate("semantic_merge", False)
        
        stats = memory.success_rates['semantic_merge']
        assert stats['success'] == 2 and stats['total'] == 3
    
    async def test_complex_scenario(self):
        """场景5: 复杂场景混合测试"""
        # 创建多个Agent和任务，模拟真实场景
        agents = [MockAgent(f"Agent-{i}", f"domain-{i%3}") for i in range(5)]
        
        tasks = [
            Task(f"T{i}", agents[i].id, f"复杂任务{i}", 
                 [f"file{i%3}.py", f"shared{i%2}.py"], 
                 [], 
                 f"domain-{i%3}")
            for i in range(5)
        ]
        
        # 预测并优化
        coordination = await self.coordinator.coordinate_task_assignment(tasks)
        
        # 应该有优化后的分配方案
        assert len(coordination['optimized_assignments']) > 0
        
        # 执行所有任务（按批次）
        all_results = []
        for assignment in coordination['optimized_assignments']:
            batch_tasks = [t for t in tasks if t.id in assignment['tasks']]
            
            if assignment['type'] == 'sequential':
                # 串行执行
                for task in batch_tasks:
                    agent = next(a for a in agents if a.id == task.agent_id)
                    result = await agent.execute_task(task, self.coordinator)
                    all_results.append(result)
            else:
                # 并行执行
                batch_results = await asyncio.gather(*[
                    next(a for a in agents if a.id == t.agent_id).execute_task(t, self.coordinator)
                    for t in batch_tasks
                ])
                all_results.extend(batch_results)
        
        # 大部分任务应该成功
        success_rate = sum(1 for r in all_results if r['success']) / len(all_results)
        assert success_rate >= 0.8, f"成功率应该>=80%，实际{success_rate*100:.0f}%"
    
    async def test_stress_concurrent(self):
        """场景6: 压力测试 - 多Agent并发"""
        num_agents = 10
        num_tasks = 20
        
        agents = [MockAgent(f"Agent-{i}", f"domain-{i%5}") for i in range(num_agents)]
        
        # 创建任务，故意制造一些冲突
        tasks = []
        for i in range(num_tasks):
            agent = agents[i % num_agents]
            # 50%的任务会修改共享文件
            if i % 2 == 0:
                files = [f"shared_{i%3}.py"]
            else:
                files = [f"unique_{i}.py"]
            
            tasks.append(Task(
                f"Stress-T{i}", 
                agent.id, 
                f"压力测试任务{i}",
                files,
                [],
                f"domain-{i%5}"
            ))
        
        # 预测冲突
        coordination = await self.coordinator.coordinate_task_assignment(tasks)
        
        start_time = time.time()
        
        # 按优化后的批次执行
        all_results = []
        for assignment in coordination['optimized_assignments']:
            batch_tasks = [t for t in tasks if t.id in assignment['tasks']]
            
            if assignment['type'] == 'sequential':
                for task in batch_tasks:
                    agent = next(a for a in agents if a.id == task.agent_id)
                    result = await agent.execute_task(task, self.coordinator)
                    all_results.append(result)
            else:
                results = await asyncio.gather(*[
                    next(a for a in agents if a.id == t.agent_id).execute_task(t, self.coordinator)
                    for t in batch_tasks
                ])
                all_results.extend(results)
        
        elapsed = time.time() - start_time
        
        # 统计结果
        successful = sum(1 for r in all_results if r['success'])
        failed = len(all_results) - successful
        
        print(f"    执行统计: {successful}/{len(all_results)} 成功, {failed} 失败")
        print(f"    执行时间: {elapsed:.2f}s")
        print(f"    预测冲突数: {len(coordination['predicted_conflicts'])}")
        
        # 成功率应该很高
        assert successful / len(all_results) >= 0.9, f"成功率应该>=90%"

async def main():
    """主入口"""
    test = IntegrationTest()
    success = await test.run_all_tests()
    
    if success:
        print("\n✓ 所有集成测试通过！系统运行正常。")
        return 0
    else:
        print("\n✗ 存在集成测试失败，需要检查。")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
