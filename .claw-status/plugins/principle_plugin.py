"""
Principle Engine Plugin - 原则执行插件
配置驱动的原则系统
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from framework import UniversalPlugin, InterceptResult, ToolContext, TaskContext
from typing import Dict, List
from datetime import datetime


class PrinciplePlugin(UniversalPlugin):
    """
    原则执行引擎插件
    动态加载原则配置，支持优先级和冲突解决
    """
    
    name = "principle_engine"
    version = "2.0.0"
    priority = 10  # 最高优先级，最先执行
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.principles = self._load_principles()
        self.violations: List[Dict] = []
    
    def _load_principles(self) -> List[Dict]:
        """加载原则配置"""
        default_principles = [
            {
                "id": "P0",
                "name": "安全与伦理",
                "weight": 1000,
                "check": "safety_check",
                "description": "不泄露隐私，不执行破坏性操作"
            },
            {
                "id": "P1",
                "name": "创新能力",
                "weight": 100,
                "check": "innovation_check",
                "description": "同一方法失败3次强制换路"
            },
            {
                "id": "P2",
                "name": "已有能力优先",
                "weight": 50,
                "check": "capability_check",
                "description": "优先使用已验证的方法"
            },
            {
                "id": "P3",
                "name": "验证本能",
                "weight": 80,
                "check": "verification_check",
                "description": "报告成功前必须验证结果"
            }
        ]
        
        # 从配置加载，如果没有则使用默认
        return self.config.get("principles", default_principles)
    
    def on_tool_before(self, context: ToolContext) -> InterceptResult:
        """
        工具调用前检查所有原则
        """
        violations = []
        
        for principle in self.principles:
            if not principle.get("enabled", True):
                continue
            
            check_method = getattr(self, f"_{principle['check']}", None)
            if check_method:
                violation = check_method(context, principle)
                if violation:
                    violations.append({
                        "principle": principle["id"],
                        "name": principle["name"],
                        "reason": violation,
                        "weight": principle["weight"]
                    })
        
        # 按权重排序
        violations.sort(key=lambda v: v["weight"], reverse=True)
        
        if violations:
            # 记录违规
            self.violations.extend(violations)
            
            # P0违规必须阻止
            p0_violations = [v for v in violations if v["principle"] == "P0"]
            if p0_violations:
                return InterceptResult.block(
                    reason=f"🚫 P0原则违规: {p0_violations[0]['reason']}",
                    alternative={"action": "ask_user_confirmation"}
                )
            
            # 其他违规警告但允许继续
            self.logger(f"⚠️ 原则警告: {violations[0]['name']} - {violations[0]['reason']}")
        
        return InterceptResult.proceed()
    
    def on_task_complete(self, context: TaskContext):
        """
        任务完成时检查验证原则
        """
        # 检查P3: 验证本能
        if not self._has_verification(context):
            self.logger("⚠️ P3警告: 任务完成但未检测到验证步骤")
    
    def _safety_check(self, context: ToolContext, principle: Dict) -> str:
        """P0: 安全与伦理检查"""
        tool = context.tool_name
        params = context.params
        
        # 检查破坏性操作
        if tool == "exec":
            cmd = params.get("command", "")
            dangerous = ["rm -rf", "dd if=", "mkfs", "> /dev"]
            for d in dangerous:
                if d in cmd:
                    return f"检测到危险命令: {d}"
        
        # 检查隐私泄露
        if tool == "message" and params.get("channel") in ["public", "broadcast"]:
            content = str(params.get("message", ""))
            private_keywords = ["password", "token", "secret", "key", "api_key"]
            for kw in private_keywords:
                if kw in content.lower():
                    return f"可能泄露敏感信息: {kw}"
        
        return None
    
    def _innovation_check(self, context: ToolContext, principle: Dict) -> str:
        """P1: 创新能力检查"""
        # 实际检查由FingerprintPlugin处理
        # 这里只做标记
        return None
    
    def _capability_check(self, context: ToolContext, principle: Dict) -> str:
        """P2: 已有能力优先检查"""
        # 实际检查由FingerprintPlugin处理
        return None
    
    def _verification_check(self, context: ToolContext, principle: Dict) -> str:
        """P3: 验证本能检查"""
        # 任务完成后检查，这里跳过
        return None
    
    def _has_verification(self, context: TaskContext) -> bool:
        """检查任务是否有验证步骤"""
        # 简单检查：是否有verify/read等验证类工具调用
        verification_tools = ["read", "verify", "check", "test"]
        for tool_call in context.tool_calls:
            if any(v in tool_call.tool_name.lower() for v in verification_tools):
                return True
        return False
    
    def get_violations_report(self) -> Dict:
        """获取违规报告"""
        return {
            "total_violations": len(self.violations),
            "violations": self.violations,
            "by_principle": self._group_by_principle()
        }
    
    def _group_by_principle(self) -> Dict:
        """按原则分组违规"""
        grouped = {}
        for v in self.violations:
            pid = v["principle"]
            if pid not in grouped:
                grouped[pid] = []
            grouped[pid].append(v)
        return grouped


if __name__ == "__main__":
    # 测试
    plugin = PrinciplePlugin()
    
    # 测试安全检测
    context = ToolContext(
        tool_name="exec",
        params={"command": "rm -rf /tmp/test"}
    )
    result = plugin.on_tool_before(context)
    print(f"Dangerous command check: {result.should_proceed}")
    
    # 测试正常命令
    context2 = ToolContext(
        tool_name="read",
        params={"file_path": "/tmp/test.txt"}
    )
    result2 = plugin.on_tool_before(context2)
    print(f"Normal command check: {result2.should_proceed}")
