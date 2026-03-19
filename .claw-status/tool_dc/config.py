"""
Tool-DC Configuration Module
基于论文: "Try, Check and Retry: A Divide-and-Conquer Framework for Boosting Long-context Tool-Calling Performance of LLMs"
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class ToolDCConfig:
    """Tool-DC 配置类
    
    基于论文实验结果的最佳实践配置
    """
    
    # ============ 分组参数 ============
    max_groups: int = 5  # K 值，论文推荐 5，适用于大多数场景
    
    # ============ 检索器配置 ============
    retriever_type: str = "bm25"  # 可选: "bm25", "embedding", "hybrid"
    top_k_retrieval: int = 10  # 初始检索的候选工具数
    
    # ============ 降级策略 ============
    fallback_threshold: int = 5  # 工具数低于此值不启用 Tool-DC，直接 ReAct
    
    # ============ 验证配置 ============
    strict_mode: bool = True  # 严格模式：任何验证失败即丢弃候选
    validate_function_name: bool = True
    validate_required_params: bool = True
    validate_data_types: bool = True
    
    # ============ 性能优化 ============
    parallel_inference: bool = True  # 并行执行各组推理
    max_workers: int = 5  # 并行工作线程数
    
    # ============ 缓存配置 ============
    enable_cache: bool = True
    cache_ttl: int = 300  # 缓存时间(秒)
    
    # ============ 调试 ============
    verbose_logging: bool = True
    log_level: str = "INFO"
    
    # ============ Prompt 配置 ============
    try_prompt_template: Optional[str] = None  # 自定义 Try Stage Prompt
    retry_prompt_template: Optional[str] = None  # 自定义 Retry Stage Prompt
    
    # ============ 重试策略 ============
    max_retry_attempts: int = 1  # 失败后的重试次数
    enable_self_correction: bool = True  # 启用自我纠正


# 默认配置实例
DEFAULT_CONFIG = ToolDCConfig()

# 轻量级配置（适用于低延迟场景）
LIGHTWEIGHT_CONFIG = ToolDCConfig(
    max_groups=3,
    parallel_inference=False,
    enable_cache=False,
    verbose_logging=False
)

# 高精度配置（适用于复杂场景）
HIGH_ACCURACY_CONFIG = ToolDCConfig(
    max_groups=8,
    strict_mode=True,
    validate_function_name=True,
    validate_required_params=True,
    validate_data_types=True,
    enable_self_correction=True
)
