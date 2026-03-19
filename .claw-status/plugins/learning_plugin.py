"""
Learning Plugin - 自动学习插件
统一记录错误、纠正和最佳实践
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from framework import UniversalPlugin, ToolContext, TaskContext
from typing import Dict, List
from pathlib import Path
from datetime import datetime
import json


class LearningPlugin(UniversalPlugin):
    """
    自动学习插件
    统一记录错误、用户纠正和最佳实践
    """
    
    name = "auto_learning"
    version = "2.0.0"
    priority = 40
    
    DB_PATH = Path("/root/.openclaw/workspace/.claw-status/data/learnings.json")
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.db = self._load_db()
        self.error_threshold = self.config.get("error_threshold", 3)
        self.auto_promote = self.config.get("auto_promote", True)
    
    def _load_db(self) -> Dict:
        """加载学习数据库"""
        if self.DB_PATH.exists():
            with open(self.DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "version": "2.0",
            "errors": [],
            "corrections": [],
            "best_practices": [],
            "patterns": {}
        }
    
    def _save_db(self):
        """保存学习数据库"""
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, indent=2, ensure_ascii=False)
    
    def on_tool_error(self, context: ToolContext, error: Exception):
        """
        工具错误时记录
        """
        error_record = {
            "id": f"err_{len(self.db['errors']) + 1:04d}",
            "tool": context.tool_name,
            "params": self._sanitize_params(context.params),
            "error_type": type(error).__name__,
            "error_message": str(error)[:200],
            "timestamp": datetime.now().isoformat(),
            "task_type": context.metadata.get("task_type", "unknown")
        }
        
        self.db["errors"].append(error_record)
        
        # 检查是否达到高频错误阈值
        self._check_error_pattern(error_record)
        
        self._save_db()
        self.logger(f"📝 记录错误: {error_record['error_type']}")
    
    def record_correction(self, original: str, correction: str, context: str = ""):
        """
        记录用户纠正
        可由外部调用
        """
        correction_record = {
            "id": f"corr_{len(self.db['corrections']) + 1:04d}",
            "original": original[:500],
            "correction": correction[:500],
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        self.db["corrections"].append(correction_record)
        
        # 检查是否可以提炼为原则
        if self.auto_promote:
            self._check_promotable(correction_record)
        
        self._save_db()
        self.logger(f"📝 记录用户纠正: {correction[:50]}...")
    
    def record_best_practice(self, practice: str, context: str = "", tags: List[str] = None):
        """
        记录最佳实践
        可由外部调用
        """
        practice_record = {
            "id": f"bp_{len(self.db['best_practices']) + 1:04d}",
            "practice": practice[:500],
            "context": context,
            "tags": tags or [],
            "timestamp": datetime.now().isoformat(),
            "use_count": 0
        }
        
        self.db["best_practices"].append(practice_record)
        self._save_db()
        self.logger(f"📝 记录最佳实践: {practice[:50]}...")
    
    def on_task_complete(self, context: TaskContext):
        """
        任务完成时分析是否有可学习的内容
        """
        # 分析任务结果，提取模式
        if context.success:
            self._analyze_success_pattern(context)
        else:
            self._analyze_failure_pattern(context)
    
    def _check_error_pattern(self, error_record: Dict):
        """检查是否形成错误模式"""
        tool = error_record["tool"]
        error_type = error_record["error_type"]
        
        # 统计同类错误
        similar_errors = [
            e for e in self.db["errors"]
            if e["tool"] == tool and e["error_type"] == error_type
        ]
        
        if len(similar_errors) >= self.error_threshold:
            pattern_key = f"{tool}:{error_type}"
            
            if pattern_key not in self.db["patterns"]:
                self.db["patterns"][pattern_key] = {
                    "tool": tool,
                    "error_type": error_type,
                    "count": len(similar_errors),
                    "first_seen": similar_errors[0]["timestamp"],
                    "status": "identified"
                }
                self.logger(f"🔍 发现错误模式: {pattern_key} ({len(similar_errors)}次)")
    
    def _check_promotable(self, correction: Dict):
        """检查纠正是否可以升级为原则"""
        # 简单检查：如果纠正涉及"应该"、"必须"等词
        content = correction["correction"].lower()
        if any(w in content for w in ["应该", "必须", "不要", "避免"]):
            # 可以升级
            self.logger(f"💡 纠正可能可升级为原则: {correction['id']}")
    
    def _analyze_success_pattern(self, context: TaskContext):
        """分析成功模式"""
        # 记录成功的工具链组合
        tool_chain = [t.tool_name for t in context.tool_calls]
        
        if len(tool_chain) >= 2:
            pattern_key = "->".join(tool_chain)
            
            if pattern_key not in self.db["patterns"]:
                self.db["patterns"][pattern_key] = {
                    "type": "success_chain",
                    "tools": tool_chain,
                    "count": 1,
                    "task_type": context.task_type
                }
            else:
                self.db["patterns"][pattern_key]["count"] += 1
    
    def _analyze_failure_pattern(self, context: TaskContext):
        """分析失败模式"""
        # 记录失败的工具链
        tool_chain = [t.tool_name for t in context.tool_calls]
        
        if tool_chain:
            pattern_key = f"fail:{tool_chain[-1]}"
            
            if pattern_key not in self.db["patterns"]:
                self.db["patterns"][pattern_key] = {
                    "type": "failure_point",
                    "tool": tool_chain[-1],
                    "count": 1,
                    "task_type": context.task_type
                }
    
    def _sanitize_params(self, params: Dict) -> Dict:
        """清理参数（去除敏感信息）"""
        sensitive_keys = ["token", "api_key", "password", "secret"]
        sanitized = {}
        
        for key, value in params.items():
            if any(sk in key.lower() for sk in sensitive_keys):
                sanitized[key] = "***"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def get_learning_report(self) -> Dict:
        """生成学习报告"""
        errors_by_tool = {}
        for e in self.db["errors"]:
            tool = e["tool"]
            errors_by_tool[tool] = errors_by_tool.get(tool, 0) + 1
        
        # 识别高频错误
        frequent_errors = [
            {"tool": t, "count": c}
            for t, c in errors_by_tool.items()
            if c >= self.error_threshold
        ]
        
        return {
            "total_errors": len(self.db["errors"]),
            "total_corrections": len(self.db["corrections"]),
            "total_best_practices": len(self.db["best_practices"]),
            "identified_patterns": len(self.db["patterns"]),
            "frequent_errors": frequent_errors,
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于错误模式生成建议
        for pattern_key, pattern in self.db["patterns"].items():
            if pattern.get("type") == "failure_point" and pattern.get("count", 0) >= 3:
                recommendations.append(
                    f"工具 {pattern['tool']} 多次失败，考虑寻找替代方案"
                )
        
        return recommendations


if __name__ == "__main__":
    # 测试
    plugin = LearningPlugin()
    
    # 模拟记录错误
    from framework import ToolContext
    context = ToolContext(
        tool_name="web_search",
        params={"query": "test"}
    )
    
    plugin.on_tool_error(context, Exception("API rate limit"))
    
    # 模拟记录纠正
    plugin.record_correction(
        original="应该这样做",
        correction="不对，应该那样做",
        context="测试任务"
    )
    
    print(plugin.get_learning_report())
