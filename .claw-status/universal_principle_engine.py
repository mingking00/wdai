#!/usr/bin/env python3
"""
通用原则执行框架 (Universal Principle Enforcement Framework)
适用于所有Agent、所有任务、所有场景
"""

import json
import os
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Callable, Optional, Any, Union
from datetime import datetime
from collections import defaultdict
import hashlib

class PriorityLevel(Enum):
    """原则优先级层级 - 通用"""
    P0_SAFETY = 0      # 绝对优先：安全、伦理、法律
    P1_META = 1        # 元能力：创新、认知、第一性原理
    P2_STRATEGY = 2    # 执行策略：复用、简单、验证
    P3_QUALITY = 3     # 质量优化：现实检查、学习
    P4_PREFERENCE = 4  # 偏好风格：用户习惯、输出格式

class TaskType(Enum):
    """任务类型 - 用于上下文判断"""
    CODE = "code"           # 编程开发
    RESEARCH = "research"   # 调研分析
    WRITE = "write"         # 写作文档
    DATA = "data"           # 数据处理
    DEPLOY = "deploy"       # 部署运维
    COMMUNICATE = "comm"    # 沟通交流
    ANALYZE = "analyze"     # 分析诊断
    CREATE = "create"       # 创意创作
    UNKNOWN = "unknown"     # 未知类型

@dataclass
class Principle:
    """原则定义 - 通用版本"""
    name: str
    level: PriorityLevel
    weight: int
    description: str
    trigger: str  # 触发条件
    check_func_name: str = ""  # 检查函数名
    applies_to: List[TaskType] = field(default_factory=lambda: list(TaskType))  # 适用任务类型
    violation_penalty: int = 1
    auto_trigger: bool = True  # 是否自动触发
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "level": self.level.name,
            "weight": self.weight,
            "description": self.description,
            "trigger": self.trigger,
            "applies_to": [t.value for t in self.applies_to],
            "auto_trigger": self.auto_trigger
        }

@dataclass
class MethodRecord:
    """方法执行记录"""
    method_name: str
    task_type: str
    count: int = 0
    successes: int = 0
    failures: int = 0
    first_attempt: str = ""
    last_attempt: str = ""
    error_patterns: List[str] = field(default_factory=list)
    
    def is_locked(self, threshold: int = 3) -> bool:
        return self.failures >= threshold

@dataclass  
class ViolationRecord:
    """违规记录"""
    principle_name: str
    task_id: str
    task_type: str
    context: str
    severity: int
    timestamp: str
    resolution: str = ""  # 如何解决

class UniversalPrincipleEngine:
    """
    通用原则执行引擎
    适用于所有Agent、所有任务类型
    """
    
    def __init__(self, agent_id: str = "default"):
        self.agent_id = agent_id
        self.principles: List[Principle] = []
        self.methods: Dict[str, MethodRecord] = {}
        self.violations: List[ViolationRecord] = []
        self.current_task: Optional[Dict] = None
        
        self.state_dir = "/root/.openclaw/workspace/.claw-status"
        self.state_file = f"{self.state_dir}/universal_principles_{agent_id}.json"
        
        self._init_principles()
        self._load_state()
    
    def _init_principles(self):
        """初始化通用原则库"""
        
        # P0 - 安全与伦理（所有任务）
        self.principles.append(Principle(
            name="安全与伦理",
            level=PriorityLevel.P0_SAFETY,
            weight=float('inf'),
            description="不泄露隐私、不执行破坏性操作、不编造信息",
            trigger="所有任务",
            applies_to=list(TaskType),
            violation_penalty=100
        ))
        
        # P1 - 元能力层
        self.principles.append(Principle(
            name="创新能力",
            level=PriorityLevel.P1_META,
            weight=100,
            description="同一方法失败3次后，强制换完全不同的方法",
            trigger="method_failure >= 3",
            applies_to=list(TaskType),
            violation_penalty=50
        ))
        
        self.principles.append(Principle(
            name="双路径认知",
            level=PriorityLevel.P1_META,
            weight=90,
            description="根据任务复杂度选择System1(快)或System2(慢)思考",
            trigger="任务开始时",
            applies_to=[TaskType.CODE, TaskType.ANALYZE, TaskType.RESEARCH],
            violation_penalty=20
        ))
        
        self.principles.append(Principle(
            name="第一性原理",
            level=PriorityLevel.P1_META,
            weight=80,
            description="质疑假设、解构本质、从0重构",
            trigger="设计/架构任务",
            applies_to=[TaskType.CODE, TaskType.CREATE, TaskType.ANALYZE],
            violation_penalty=15
        ))
        
        # P2 - 执行策略层
        self.principles.append(Principle(
            name="已有能力优先",
            level=PriorityLevel.P2_STRATEGY,
            weight=50,
            description="优先使用已有技能和工具，避免重复造轮子",
            trigger="任务开始前",
            applies_to=list(TaskType),
            violation_penalty=10
        ))
        
        self.principles.append(Principle(
            name="简单优先",
            level=PriorityLevel.P2_STRATEGY,
            weight=45,
            description="能用10行不用100行，能用1个不用5个",
            trigger="方案选择时",
            applies_to=list(TaskType),
            violation_penalty=8
        ))
        
        self.principles.append(Principle(
            name="检查与验证",
            level=PriorityLevel.P2_STRATEGY,
            weight=40,
            description="交付前必须验证结果，报告成功前必须确认",
            trigger="交付前",
            applies_to=list(TaskType),
            violation_penalty=20
        ))
        
        # P3 - 质量优化层
        self.principles.append(Principle(
            name="物理现实检查",
            level=PriorityLevel.P3_QUALITY,
            weight=20,
            description="涉及真实世界时，检查时间、资源、可行性",
            trigger="涉及外部系统/真实世界",
            applies_to=[TaskType.DEPLOY, TaskType.COMMUNICATE, TaskType.DATA],
            violation_penalty=5
        ))
        
        self.principles.append(Principle(
            name="纠错学习",
            level=PriorityLevel.P3_QUALITY,
            weight=15,
            description="每个任务后提取经验、更新模式、预测未来",
            trigger="任务完成后",
            applies_to=list(TaskType),
            violation_penalty=3
        ))
        
        # P4 - 偏好风格层
        self.principles.append(Principle(
            name="用户偏好匹配",
            level=PriorityLevel.P4_PREFERENCE,
            weight=5,
            description="直接、无寒暄、结构化输出",
            trigger="交互时",
            applies_to=[TaskType.COMMUNICATE, TaskType.WRITE],
            violation_penalty=1
        ))
    
    def classify_task(self, task_description: str) -> TaskType:
        """自动分类任务类型"""
        task_lower = task_description.lower()
        
        # 代码相关
        if any(kw in task_lower for kw in ['代码', '编程', 'deploy', 'build', 'function', 'api', 'git']):
            return TaskType.CODE
        
        # 研究相关
        if any(kw in task_lower for kw in ['研究', '调研', 'search', 'analyze', 'compare', 'research']):
            return TaskType.RESEARCH
        
        # 写作相关
        if any(kw in task_lower for kw in ['写', '文档', 'doc', 'write', 'summary', 'report']):
            return TaskType.WRITE
        
        # 数据相关
        if any(kw in task_lower for kw in ['数据', 'csv', 'json', 'database', 'extract']):
            return TaskType.DATA
        
        # 部署相关
        if any(kw in task_lower for kw in ['部署', 'upload', 'server', 'vercel', 'github']):
            return TaskType.DEPLOY
        
        # 沟通相关
        if any(kw in task_lower for kw in ['消息', '发送', '通知', 'email', 'message']):
            return TaskType.COMMUNICATE
        
        # 创意相关
        if any(kw in task_lower for kw in ['创建', '设计', '画', 'create', 'design', 'art']):
            return TaskType.CREATE
        
        return TaskType.UNKNOWN
    
    def get_applicable_principles(self, task_type: TaskType) -> List[Principle]:
        """获取适用于当前任务类型的原则"""
        return [p for p in self.principles if task_type in p.applies_to]
    
    def resolve_conflict(self, principles: List[Principle], context: Dict) -> Principle:
        """解决原则冲突"""
        # P0绝对优先
        for p in principles:
            if p.level == PriorityLevel.P0_SAFETY:
                return p
        
        # 按权重排序
        sorted_p = sorted(principles, key=lambda p: (p.level.value, -p.weight))
        return sorted_p[0] if sorted_p else None
    
    def pre_task_check(self, task_description: str) -> Dict:
        """任务前检查 - 通用版本"""
        task_type = self.classify_task(task_description)
        applicable = self.get_applicable_principles(task_type)
        
        results = {
            "task_type": task_type.value,
            "approved": True,
            "checks": [],
            "warnings": []
        }
        
        # P0检查
        safety = next((p for p in applicable if p.level == PriorityLevel.P0_SAFETY), None)
        if safety:
            if self._safety_check(task_description):
                results["checks"].append({"principle": safety.name, "status": "pass", "level": "P0"})
            else:
                results["checks"].append({"principle": safety.name, "status": "fail", "level": "P0"})
                results["approved"] = False
        
        # 其他原则检查
        for p in applicable:
            if p.level != PriorityLevel.P0_SAFETY:
                results["checks"].append({
                    "principle": p.name,
                    "status": "applicable",
                    "level": p.level.name,
                    "trigger": p.trigger
                })
        
        # 记录当前任务
        self.current_task = {
            "description": task_description,
            "type": task_type.value,
            "start_time": datetime.now().isoformat()
        }
        
        return results
    
    def record_method_attempt(self, method_name: str, success: bool, error: str = "") -> Dict:
        """记录方法执行结果"""
        task_type = self.current_task["type"] if self.current_task else "unknown"
        key = f"{task_type}:{method_name}"
        
        if key not in self.methods:
            self.methods[key] = MethodRecord(
                method_name=method_name,
                task_type=task_type,
                first_attempt=datetime.now().isoformat()
            )
        
        record = self.methods[key]
        record.count += 1
        record.last_attempt = datetime.now().isoformat()
        
        if success:
            record.successes += 1
            self._save_state()  # 保存状态
            return {"status": "success", "method": method_name}
        else:
            record.failures += 1
            if error:
                record.error_patterns.append(error[:100])  # 限制长度
            
            self._save_state()  # 保存状态
            
            # 检查是否触发创新
            if record.is_locked():
                return {
                    "status": "MUST_INNOVATE",
                    "method": method_name,
                    "failures": record.failures,
                    "message": f"方法 '{method_name}' 已失败{record.failures}次，必须换完全不同的方法",
                    "alternatives": self._suggest_alternatives(method_name, task_type)
                }
            
            return {
                "status": "retry",
                "method": method_name,
                "failures": record.failures,
                "max_retries": 3
            }
    
    def record_violation(self, principle_name: str, context: str, severity: int = 1):
        """记录原则违规"""
        violation = ViolationRecord(
            principle_name=principle_name,
            task_id=self._get_task_id(),
            task_type=self.current_task["type"] if self.current_task else "unknown",
            context=context,
            severity=severity,
            timestamp=datetime.now().isoformat()
        )
        self.violations.append(violation)
        self._save_state()
    
    def pre_delivery_check(self, output: Any) -> Dict:
        """交付前检查"""
        failed = []
        
        # 验证检查
        if not self._verify_output(output):
            failed.append("检查验证")
            self.record_violation("检查验证", "pre_delivery", 2)
        
        # 简单性检查（如果是代码/数据）
        if self.current_task and self.current_task["type"] in ["code", "data"]:
            if not self._simplicity_check(output):
                failed.append("简单优先")
        
        return {
            "approved": len(failed) == 0,
            "failed_checks": failed
        }
    
    def get_summary(self) -> Dict:
        """获取执行摘要"""
        locked_methods = [k for k, v in self.methods.items() if v.is_locked()]
        
        return {
            "agent_id": self.agent_id,
            "active": True,
            "principles_loaded": len(self.principles),
            "methods_tracked": len(self.methods),
            "locked_methods": locked_methods,
            "total_violations": len(self.violations),
            "current_task": self.current_task
        }
    
    def _safety_check(self, task: str) -> bool:
        """安全检查"""
        unsafe = ['删除所有', 'rm -rf /', '暴露密码', '发送给其他人', 'drop database']
        return not any(kw in task.lower() for kw in unsafe)
    
    def _verify_output(self, output: Any) -> bool:
        """验证输出"""
        if output is None:
            return False
        if isinstance(output, str) and len(output.strip()) == 0:
            return False
        return True
    
    def _simplicity_check(self, output: Any) -> bool:
        """简单性检查 - 简化版本"""
        return True  # 实际实现需要更复杂逻辑
    
    def _suggest_alternatives(self, method: str, task_type: str) -> List[str]:
        """建议替代方案"""
        alternatives = {
            "github_api": ["git_push", "github_cli", "manual_upload"],
            "web_scrape": ["api_call", "cached_data", "manual_extract"],
            "npm_install": ["yarn", "pnpm", "offline_package"],
            "default": ["try_different_tool", "change_protocol", "manual_operation"]
        }
        return alternatives.get(method, alternatives["default"])
    
    def _get_task_id(self) -> str:
        """生成任务ID"""
        if self.current_task:
            desc = self.current_task.get("description", "")
            return hashlib.md5(desc.encode()).hexdigest()[:8]
        return "unknown"
    
    def _save_state(self):
        """保存状态到磁盘"""
        state = {
            "agent_id": self.agent_id,
            "methods": {k: asdict(v) for k, v in self.methods.items()},
            "violations": [asdict(v) for v in self.violations[-100:]],  # 只保留最近100条
            "last_update": datetime.now().isoformat()
        }
        
        os.makedirs(self.state_dir, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def _load_state(self):
        """从磁盘加载状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    
                    # 恢复方法记录
                    for k, v in state.get("methods", {}).items():
                        self.methods[k] = MethodRecord(**v)
                    
                    # 恢复违规记录
                    for v in state.get("violations", []):
                        self.violations.append(ViolationRecord(**v))
                        
            except Exception as e:
                print(f"加载状态失败: {e}")

# 全局实例管理
_engines = {}

def get_engine(agent_id: str = "default") -> UniversalPrincipleEngine:
    """获取引擎实例"""
    if agent_id not in _engines:
        _engines[agent_id] = UniversalPrincipleEngine(agent_id)
    return _engines[agent_id]

def initialize_all_agents():
    """初始化所有Agent"""
    # 检测所有已注册的Agent
    state_dir = "/root/.openclaw/workspace/.claw-status"
    agents = []
    
    if os.path.exists(state_dir):
        for f in os.listdir(state_dir):
            if f.startswith("universal_principles_") and f.endswith(".json"):
                agent_id = f.replace("universal_principles_", "").replace(".json", "")
                agents.append(agent_id)
    
    # 初始化每个Agent
    for agent_id in agents:
        get_engine(agent_id)
    
    return agents

if __name__ == "__main__":
    # 测试
    engine = get_engine("test")
    
    print("=" * 60)
    print("通用原则执行框架测试")
    print("=" * 60)
    
    # 测试1: 任务分类
    tasks = [
        "部署博客到GitHub",
        "研究最新AI框架",
        "写一份报告",
        "分析CSV数据"
    ]
    
    print("\n任务分类测试:")
    for task in tasks:
        task_type = engine.classify_task(task)
        print(f"  '{task}' -> {task_type.value}")
    
    # 测试2: 任务前检查
    print("\n任务前检查:")
    result = engine.pre_task_check("部署应用到服务器")
    print(f"  任务类型: {result['task_type']}")
    print(f"  检查项: {len(result['checks'])}")
    
    # 测试3: 方法失败
    print("\n方法失败测试:")
    for i in range(1, 4):
        result = engine.record_method_attempt("api_upload", success=False, error="timeout")
        print(f"  第{i}次: {result['status']}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print(f"引擎状态: {engine.get_summary()}")
