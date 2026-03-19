#!/usr/bin/env python3
"""
灵感摄取系统 - 配置管理器
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# 默认配置路径
DEFAULT_CONFIG_PATH = Path(__file__).parent / "config" / "inspiration_config.json"


class ConfigManager:
    """配置管理器 - 管理灵感摄取系统的所有配置"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except Exception as e:
                print(f"[ConfigManager] 配置加载失败: {e}")
                self._config = self._default_config()
        else:
            self._config = self._default_config()
            self._save_config()
    
    def _save_config(self):
        """保存配置到文件"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ConfigManager] 配置保存失败: {e}")
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            "system": {
                "name": "灵感摄取系统",
                "version": "1.0.0",
                "auto_crawl": True,
                "require_human_review": True,
                "default_priority": "medium"
            },
            "arxiv": {
                "enabled": True,
                "categories": ["cs.AI", "cs.CL", "cs.LG"],
                "keywords": ["agent", "llm", "rag", "reasoning"],
                "min_quality_score": 0.6,
                "max_papers_per_run": 50,
                "download_pdf": False
            },
            "github": {
                "enabled": True,
                "monitored_repos": [],
                "trending_languages": ["python", "typescript"],
                "min_stars": 500,
                "check_releases": True,
                "check_trending": True,
                "api_token_env": "GITHUB_TOKEN"
            },
            "analysis": {
                "deduplication": {
                    "enabled": True,
                    "title_similarity_threshold": 0.85,
                    "content_similarity_threshold": 0.80
                },
                "quality_scoring": {
                    "enabled": True,
                    "weights": {
                        "relevance": 0.30,
                        "novelty": 0.25,
                        "impact": 0.25,
                        "timeliness": 0.20
                    }
                }
            },
            "queue": {
                "max_pending": 100,
                "auto_archive_rejected": True,
                "archive_after_days": 30
            },
            "evo_integration": {
                "enabled": True,
                "auto_trigger_on_approval": True,
                "default_evo_priority": "medium"
            }
        }
    
    # ============ 便捷访问方法 ============
    
    @property
    def system(self) -> Dict[str, Any]:
        return self._config.get("system", {})
    
    @property
    def arxiv(self) -> Dict[str, Any]:
        return self._config.get("arxiv", {})
    
    @property
    def github(self) -> Dict[str, Any]:
        return self._config.get("github", {})
    
    @property
    def analysis(self) -> Dict[str, Any]:
        return self._config.get("analysis", {})
    
    @property
    def queue(self) -> Dict[str, Any]:
        return self._config.get("queue", {})
    
    @property
    def evo_integration(self) -> Dict[str, Any]:
        return self._config.get("evo_integration", {})
    
    # ============ 配置获取 ============
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项 (支持点号路径, e.g., 'arxiv.enabled')"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """设置配置项 (支持点号路径)"""
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save_config()
    
    def get_all(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config.copy()
    
    # ============ arXiv配置 ============
    
    def arxiv_enabled(self) -> bool:
        return self.arxiv.get("enabled", True)
    
    def arxiv_categories(self) -> List[str]:
        return self.arxiv.get("categories", ["cs.AI", "cs.CL", "cs.LG"])
    
    def arxiv_keywords(self) -> List[str]:
        return self.arxiv.get("keywords", [])
    
    def arxiv_exclude_keywords(self) -> List[str]:
        return self.arxiv.get("exclude_keywords", [])
    
    def arxiv_min_quality_score(self) -> float:
        return self.arxiv.get("min_quality_score", 0.6)
    
    def arxiv_max_papers(self) -> int:
        return self.arxiv.get("max_papers_per_run", 50)
    
    def arxiv_download_pdf(self) -> bool:
        return self.arxiv.get("download_pdf", False)
    
    # ============ GitHub配置 ============
    
    def github_enabled(self) -> bool:
        return self.github.get("enabled", True)
    
    def github_token(self) -> Optional[str]:
        """从环境变量获取GitHub Token"""
        env_var = self.github.get("api_token_env", "GITHUB_TOKEN")
        return os.getenv(env_var)
    
    def github_monitored_repos(self) -> List[Dict[str, Any]]:
        return self.github.get("monitored_repos", [])
    
    def github_trending_languages(self) -> List[str]:
        return self.github.get("trending_languages", ["python", "typescript"])
    
    def github_min_stars(self) -> int:
        return self.github.get("min_stars", 500)
    
    def github_check_releases(self) -> bool:
        return self.github.get("check_releases", True)
    
    def github_check_trending(self) -> bool:
        return self.github.get("check_trending", True)
    
    # ============ 分析配置 ============
    
    def dedup_enabled(self) -> bool:
        return self.analysis.get("deduplication", {}).get("enabled", True)
    
    def dedup_title_threshold(self) -> float:
        return self.analysis.get("deduplication", {}).get("title_similarity_threshold", 0.85)
    
    def dedup_content_threshold(self) -> float:
        return self.analysis.get("deduplication", {}).get("content_similarity_threshold", 0.80)
    
    def quality_weights(self) -> Dict[str, float]:
        return self.analysis.get("quality_scoring", {}).get("weights", {
            "relevance": 0.30,
            "novelty": 0.25,
            "impact": 0.25,
            "timeliness": 0.20
        })
    
    def min_quality_score(self) -> float:
        return self.analysis.get("quality_scoring", {}).get("min_score_for_queue", 0.65)
    
    # ============ 队列配置 ============
    
    def queue_max_pending(self) -> int:
        return self.queue.get("max_pending", 100)
    
    def queue_auto_archive(self) -> bool:
        return self.queue.get("auto_archive_rejected", True)
    
    # ============ Evo集成配置 ============
    
    def evo_enabled(self) -> bool:
        return self.evo_integration.get("enabled", True)
    
    def evo_auto_trigger(self) -> bool:
        return self.evo_integration.get("auto_trigger_on_approval", True)
    
    def evo_task_template(self) -> str:
        return self.evo_integration.get("evo_task_template", 
            "Based on inspiration: {title}\n\nSource: {url}\n\nSummary:\n{summary}")
    
    # ============ 系统配置 ============
    
    def require_human_review(self) -> bool:
        return self.system.get("require_human_review", True)
    
    def auto_crawl(self) -> bool:
        return self.system.get("auto_crawl", True)
    
    # ============ 配置更新 ============
    
    def update(self, updates: Dict[str, Any]):
        """批量更新配置"""
        self._deep_update(self._config, updates)
        self._save_config()
    
    def _deep_update(self, base: Dict, updates: Dict):
        """深度更新字典"""
        for key, value in updates.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def reset_to_defaults(self):
        """重置为默认配置"""
        self._config = self._default_config()
        self._save_config()


# 全局配置实例
_config_instance: Optional[ConfigManager] = None


def get_config(config_path: Optional[Path] = None) -> ConfigManager:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager(config_path)
    return _config_instance


def reload_config():
    """重新加载配置"""
    global _config_instance
    _config_instance = None
    return get_config()