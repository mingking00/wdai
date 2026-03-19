#!/usr/bin/env python3
"""
Core Loop - 核心工作循环

发现问题 → 改良解决 → 创新(如必要) → 纠错学习 → 预测未来 → 循环
"""

from typing import Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class LoopIteration:
    """循环迭代记录"""
    timestamp: str
    problem: str
    solution: str
    innovation: bool
    error_found: Optional[str]
    lesson: Optional[str]
    prediction: Optional[str]

class CoreLoop:
    """
    核心工作循环
    
    5步循环:
    1. Detect - 发现问题
    2. Solve - 改良解决
    3. Innovate - 创新(如必要)
    4. Correct - 纠错学习
    5. Predict - 预测未来
    """
    
    def __init__(self):
        self.iterations = []
    
    def iterate(self, 
                problem: str,
                solve_func: Callable[[], Any],
                context: str = "") -> dict:
        """
        执行一次循环迭代
        
        Args:
            problem: 发现的问题
            solve_func: 解决函数
            context: 上下文
        
        Returns:
            迭代结果
        """
        print(f"\n🔍 Step 1: 发现问题 - {problem}")
        
        # Step 2: 改良解决
        print(f"🔧 Step 2: 改良解决...")
        try:
            result = solve_func()
            solution = f"成功: {result}"
            innovation = False
        except Exception as e:
            # 简单方案失败，需要创新
            print(f"   简单方案失败: {e}")
            print(f"💡 Step 3: 创新解决...")
            result = self._innovate_solve(problem, e)
            solution = f"创新解决: {result}"
            innovation = True
        
        # Step 4: 纠错学习
        print(f"📚 Step 4: 纠错学习...")
        error_found = self._check_for_errors(problem, solution)
        lesson = self._extract_lesson(problem, error_found)
        
        if error_found:
            print(f"   发现错误: {error_found}")
            print(f"   学习教训: {lesson}")
        
        # Step 5: 预测未来
        print(f"🔮 Step 5: 预测未来...")
        prediction = self._predict_future(problem, lesson)
        print(f"   预测: {prediction}")
        
        # 记录迭代
        iteration = LoopIteration(
            timestamp=datetime.now().isoformat(),
            problem=problem,
            solution=solution,
            innovation=innovation,
            error_found=error_found,
            lesson=lesson,
            prediction=prediction
        )
        self.iterations.append(iteration)
        
        return {
            "problem": problem,
            "solution": solution,
            "innovation": innovation,
            "lesson": lesson,
            "prediction": prediction
        }
    
    def _innovate_solve(self, problem: str, error: Exception) -> str:
        """创新解决 - 当简单方案失败时"""
        # 实际实现会根据具体问题创新
        return f"通过新方案解决{problem}"
    
    def _check_for_errors(self, problem: str, solution: str) -> Optional[str]:
        """检查错误"""
        # 自检: 是否过度复杂？是否有效？
        if "创建" in solution and "文件" in solution:
            return "可能过度创建文件"
        return None
    
    def _extract_lesson(self, problem: str, error: Optional[str]) -> Optional[str]:
        """提取教训"""
        if error == "可能过度创建文件":
            return "简单方案优先，避免过度工程化"
        return None
    
    def _predict_future(self, problem: str, lesson: Optional[str]) -> str:
        """预测未来"""
        if "过度工程化" in str(lesson):
            return "未来遇到类似问题，先问'能用10行代码解决吗？'"
        return "持续关注类似问题"
    
    def get_stats(self) -> dict:
        """获取循环统计"""
        total = len(self.iterations)
        innovations = sum(1 for i in self.iterations if i.innovation)
        errors = sum(1 for i in self.iterations if i.error_found)
        
        return {
            "total_iterations": total,
            "innovations": innovations,
            "errors_found": errors,
            "efficiency": (total - innovations) / total if total > 0 else 0
        }


# ==================== 实际应用示例 ====================

def demo_core_loop():
    """演示核心循环在今天的实际应用"""
    
    loop = CoreLoop()
    
    print("=" * 70)
    print("🔄 Core Loop Demo - 今天的工作实例")
    print("=" * 70)
    
    # 实例1: 过度工程化问题
    print("\n" + "=" * 70)
    print("实例1: 过度创建系统文件")
    print("=" * 70)
    
    result1 = loop.iterate(
        problem="创建了9个系统文件，过度工程化",
        solve_func=lambda: "合并为2个简单文件",
        context="不确定性检测系统"
    )
    
    # 实例2: 视频学习
    print("\n" + "=" * 70)
    print("实例2: 视频学习简化")
    print("=" * 70)
    
    result2 = loop.iterate(
        problem="视频学习系统过于复杂(5个Agent)",
        solve_func=lambda: "简化为直接提取",
        context="C-JEPA视频学习"
    )
    
    # 统计
    print("\n" + "=" * 70)
    print("📊 循环统计")
    print("=" * 70)
    
    stats = loop.get_stats()
    print(f"总迭代: {stats['total_iterations']}")
    print(f"创新次数: {stats['innovations']}")
    print(f"发现错误: {stats['errors_found']}")
    print(f"简单解决率: {stats['efficiency']*100:.0f}%")
    
    print("\n" + "=" * 70)
    print("✅ Core Loop 演示完成")
    print("=" * 70)
    
    return loop


if __name__ == "__main__":
    demo_core_loop()
