#!/usr/bin/env python3
"""
MemRL 增强的 memory_search 工具
完全兼容现有接口，添加 Q 值支持
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from memrl_integration import search_memory_with_q, get_memrl_integration

def memory_search_with_q(query: str, max_results: int = 5, 
                         min_q_value: float = 0.0) -> str:
    """
    MemRL 增强的记忆搜索工具
    
    功能:
    - 两阶段检索 (语义 + Q 值)
    - 自动过滤低 Q 值记忆
    - 显示成功率和使用次数
    
    参数:
        query: 搜索查询
        max_results: 返回结果数 (默认 5)
        min_q_value: 最小 Q 值过滤 (默认 0，不过滤)
    
    返回:
        格式化的搜索结果字符串
    """
    # 执行搜索
    results = search_memory_with_q(query, max_results=max_results * 2)  # 多取一些用于过滤
    
    # 过滤低 Q 值
    if min_q_value > 0:
        results = [r for r in results if r.get("q_value", 0) >= min_q_value]
    
    # 限制数量
    results = results[:max_results]
    
    if not results:
        return f"未找到与 '{query}' 相关的记忆 (Q值 >= {min_q_value})"
    
    # 格式化输出
    lines = [
        f"🔍 记忆搜索结果: '{query}'",
        f"   找到 {len(results)} 条相关记忆 (按综合得分排序)",
        ""
    ]
    
    for i, r in enumerate(results, 1):
        q = r.get("q_value", 0.5)
        score = r.get("final_score", 0)
        usage = r.get("usage_count", 0)
        success_rate = r.get("success_rate", 0)
        
        # Q 值可视化
        q_bar = "█" * int(q * 10) + "░" * (10 - int(q * 10))
        
        lines.extend([
            f"{i}. [{r.get('source', 'unknown')}] Q:{q:.2f} {q_bar}",
            f"   综合得分: {score:.3f} | 相似度: {r.get('similarity', 0):.3f}",
            f"   使用: {usage}次 | 成功率: {success_rate*100:.0f}%",
            f"   内容: {r.get('content', '')[:150]}...",
            ""
        ])
    
    # 添加统计
    avg_q = sum(r.get("q_value", 0.5) for r in results) / len(results)
    lines.append(f"📊 平均 Q 值: {avg_q:.2f}")
    
    return "\n".join(lines)


def memory_search_legacy(query: str, max_results: int = 5) -> str:
    """
    兼容旧版接口的记忆搜索
    完全保持原有行为和输出格式
    """
    # 读取 MEMORY.md
    workspace = Path("/root/.openclaw/workspace")
    memory_md = workspace / "MEMORY.md"
    
    if not memory_md.exists():
        return f"未找到 MEMORY.md 文件"
    
    with open(memory_md) as f:
        content = f.read()
    
    # 简单文本匹配
    if query.lower() not in content.lower():
        return f"未找到与 '{query}' 相关的记忆"
    
    # 找到相关段落
    lines = content.split('\n')
    matches = []
    
    for i, line in enumerate(lines):
        if query.lower() in line.lower():
            # 获取上下文
            start = max(0, i - 2)
            end = min(len(lines), i + 5)
            context = '\n'.join(lines[start:end])
            matches.append(context)
    
    if not matches:
        return f"未找到与 '{query}' 相关的详细内容"
    
    # 格式化输出
    result = [
        f"找到 {len(matches)} 处匹配:",
        ""
    ]
    
    for i, match in enumerate(matches[:max_results], 1):
        result.append(f"{i}. {match[:300]}...")
        result.append("")
    
    return "\n".join(result)


# 主入口函数 - 供外部调用
def memory_search(query: str, max_results: int = 5,
                  use_q_value: bool = True) -> str:
    """
    统一的 memory_search 接口
    
    参数:
        query: 搜索查询
        max_results: 返回结果数
        use_q_value: 是否使用 MemRL (默认 True)
    
    返回:
        格式化的搜索结果
    """
    if use_q_value:
        return memory_search_with_q(query, max_results)
    else:
        return memory_search_legacy(query, max_results)


# 命令行测试
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        query = sys.argv[1]
        max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        
        print(memory_search(query, max_results))
    else:
        # 测试
        print("=" * 60)
        print("MemRL memory_search 测试")
        print("=" * 60)
        
        # 先添加一些测试数据
        from memrl_memory import get_memrl_memory
        mem = get_memrl_memory()
        
        # 添加测试记忆
        mem.add_experience(
            query="部署博客",
            experience="用 git push 部署到 GitHub 比 API 更稳定可靠",
            reward=1.0,
            tags=["deploy", "git", "github"]
        )
        
        mem.add_experience(
            query="调试代码",
            experience="先打印日志定位问题，再修改代码",
            reward=0.9,
            tags=["debug", "coding"]
        )
        
        # 测试搜索
        print("\n测试1: 搜索 '部署'")
        print(memory_search("部署", max_results=3))
        
        print("\n" + "=" * 60)
        print("\n测试2: 搜索 '调试'")
        print(memory_search("调试", max_results=3))
        
        print("\n" + "=" * 60)
        print("\n测试3: 高 Q 值过滤 (min_q=0.8)")
        print(memory_search_with_q("部署", max_results=3, min_q_value=0.8))
