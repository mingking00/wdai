#!/usr/bin/env python3
"""
WDai Code Security v3.6 (evo-005集成)
集成代码安全约束
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from wdai_v35_eval import WDaiSystemV35
from code_security import CodeReviewEngine
import time


class WDaiSystemV36(WDaiSystemV35):
    """
    WDai v3.6
    新增：代码安全与性能约束 (evo-005)
    """
    
    _instance = None
    
    def __init__(self):
        if self._initialized:
            return
        
        # 先初始化父类（v3.5）
        super().__init__()
        
        print("\n" + "="*60)
        print("🔥 升级至 WDai v3.6")
        print("="*60)
        
        # 初始化代码审查引擎
        print("🚀 启用代码安全约束...")
        self.code_reviewer = CodeReviewEngine()
        
        print("✅ 代码安全约束已集成")
        print("   - 安全检查: SQL注入、XSS、命令注入、硬编码密钥")
        print("   - 性能检查: 嵌套循环、低效操作、内存问题")
        print("   - 风格检查: PEP8、命名规范、行长度")
        print("   - 质量评分: 0-100% 综合评分")
        print("="*60)
    
    def review_code(self, code: str, filename: str = "<unknown>") -> dict:
        """代码审查接口"""
        return self.code_reviewer.review(code, filename)
    
    def quick_security_check(self, code: str) -> dict:
        """快速安全检查"""
        result = self.code_reviewer.review(code)
        
        # 只返回安全和性能问题
        critical_issues = [
            i for i in result['issues'] 
            if i['category'] in ['security', 'performance'] 
            and i['severity'] in ['critical', 'high']
        ]
        
        return {
            'pass': len(critical_issues) == 0,
            'critical_count': len(critical_issues),
            'issues': critical_issues,
            'score': result['score']
        }
    
    def get_code_review_stats(self) -> dict:
        """获取代码审查统计"""
        return self.code_reviewer.get_stats()


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("WDai Code Security v3.6 - 集成测试")
    print("="*60)
    
    # 创建系统
    system = WDaiSystemV36()
    
    # 测试代码
    test_code = '''
def process_data(user_input, items):
    # SQL注入风险
    query = f"SELECT * FROM table WHERE id = {user_input}"
    
    # 性能问题
    result = []
    for i in items:
        for j in items:
            result.append(i + j)
    
    return result
'''
    
    print("\n🧪 测试代码审查...")
    result = system.review_code(test_code, "test.py")
    
    print(f"\n📊 结果")
    print(f"   评分: {result['score']:.0%}")
    print(f"   通过: {'✅' if result['pass'] else '❌'}")
    print(f"   问题数: {result['summary']['total']}")
    
    # 快速检查
    print("\n🧪 测试快速安全检查...")
    quick = system.quick_security_check(test_code)
    print(f"   安全通过: {'✅' if quick['pass'] else '❌'}")
    print(f"   严重问题: {quick['critical_count']}")
    
    print("\n" + "="*60)
    print("✅ v3.6 代码安全约束集成测试完成")
    print("="*60)
