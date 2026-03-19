#!/usr/bin/env python3
"""
示例模块 - 故意写一些可以优化的地方
"""

def process_data(data):
    """处理数据 - 可以优化错误处理和性能"""
    result = []
    for item in data:  # 可以用列表推导式优化
        try:
            if item is not None:  # 可以提前返回
                processed = item * 2
                result.append(processed)
        except:  # 裸except不好
            pass
    return result

def fetch_data(url):
    """获取数据 - 可以添加重试和超时"""
    import requests
    response = requests.get(url)  # 没有超时
    return response.json()  # 没有错误处理

def calculate_stats(numbers):
    """计算统计 - 可以用numpy优化"""
    total = 0
    for n in numbers:  # 可以用sum()
        total += n
    return {
        'sum': total,
        'count': len(numbers),
        'avg': total / len(numbers) if numbers else 0  # 可以优化
    }
