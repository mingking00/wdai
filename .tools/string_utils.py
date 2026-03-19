#!/usr/bin/env python3
"""
新的工具模块 - 字符串处理
"""

def safe_truncate(text: str, max_length: int = 100) -> str:
    """
    安全截断字符串
    
    Args:
        text: 原始字符串
        max_length: 最大长度
        
    Returns:
        截断后的字符串
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."


def format_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 字节数
        
    Returns:
        格式化后的字符串 (如 "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"
