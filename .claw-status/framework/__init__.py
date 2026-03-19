"""
wdai Universal Framework - 通用底层框架核心
统一事件总线 + 插件系统
"""

from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import importlib.util
import inspect


@dataclass
class ToolContext:
    """工具调用上下文"""
    tool_name: str
    params: Dict[str, Any]
    task_id: Optional[str] = None
    token_usage: int = 0
    suggested_params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskContext:
    """任务上下文"""
    task_id: str
    task_type: str
    description: str
    start_time: datetime = field(default_factory=datetime.now)
    tool_calls: List[ToolContext] = field(default_factory=list)
    result: Any = None
    success: bool = False


@dataclass
class InterceptResult:
    """拦截结果"""
    should_proceed: bool
    reason: str = ""
    alternative: Optional[Dict] = None
    modified_params: Optional[Dict] = None
    
    @classmethod
    def proceed(cls, modified_params: Optional[Dict] = None):
        return cls(should_proceed=True, modified_params=modified_params)
    
    @classmethod
    def block(cls, reason: str, alternative: Optional[Dict] = None):
        return cls(should_proceed=False, reason=reason, alternative=alternative)


class UniversalPlugin:
    """
    通用插件基类
    所有插件必须继承此类
    """
    
    name: str = "base_plugin"
    version: str = "1.0.0"
    priority: int = 50  # 优先级: 数字越小越先执行
    enabled: bool = True
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.logger = lambda msg: print(f"[{self.name}] {msg}")
    
    def on_tool_before(self, context: ToolContext) -> InterceptResult:
        """
        工具调用前处理
        返回 InterceptResult.proceed() 或 InterceptResult.block()
        """
        return InterceptResult.proceed()
    
    def on_tool_after(self, context: ToolContext, result: Any):
        """工具调用后处理"""
        pass
    
    def on_tool_error(self, context: ToolContext, error: Exception):
        """工具调用错误处理"""
        pass
    
    def on_task_start(self, context: TaskContext):
        """任务开始时处理"""
        pass
    
    def on_task_complete(self, context: TaskContext):
        """任务完成时处理"""
        pass
    
    def on_task_fail(self, context: TaskContext, error: Exception):
        """任务失败时处理"""
        pass
    
    def on_config_change(self, config: Dict):
        """配置变更时处理"""
        self.config = config


class UniversalEventBus:
    """
    统一事件总线
    协调所有插件的事件处理
    """
    
    def __init__(self):
        self.plugins: List[UniversalPlugin] = []
        self.event_history: List[Dict] = []
    
    def register_plugin(self, plugin: UniversalPlugin):
        """注册插件"""
        if not isinstance(plugin, UniversalPlugin):
            raise ValueError(f"Plugin must inherit from UniversalPlugin: {plugin}")
        
        self.plugins.append(plugin)
        # 按优先级排序
        self.plugins.sort(key=lambda p: p.priority)
        print(f"✅ Registered plugin: {plugin.name} (priority: {plugin.priority})")
    
    def unregister_plugin(self, plugin_name: str):
        """注销插件"""
        self.plugins = [p for p in self.plugins if p.name != plugin_name]
        print(f"📝 Unregistered plugin: {plugin_name}")
    
    def emit_tool_before(self, context: ToolContext) -> InterceptResult:
        """
        工具调用前事件
        依次询问所有插件，如果有插件阻止，则返回阻止结果
        """
        for plugin in self.plugins:
            if not plugin.enabled:
                continue
            
            try:
                result = plugin.on_tool_before(context)
                if not result.should_proceed:
                    self._log_event("tool_before_blocked", {
                        "plugin": plugin.name,
                        "tool": context.tool_name,
                        "reason": result.reason
                    })
                    return result
                
                # 应用参数修改
                if result.modified_params:
                    context.params.update(result.modified_params)
                    
            except Exception as e:
                self._log_event("plugin_error", {
                    "plugin": plugin.name,
                    "phase": "tool_before",
                    "error": str(e)
                })
        
        return InterceptResult.proceed()
    
    def emit_tool_after(self, context: ToolContext, result: Any):
        """工具调用后事件"""
        for plugin in self.plugins:
            if not plugin.enabled:
                continue
            
            try:
                plugin.on_tool_after(context, result)
            except Exception as e:
                self._log_event("plugin_error", {
                    "plugin": plugin.name,
                    "phase": "tool_after",
                    "error": str(e)
                })
    
    def emit_tool_error(self, context: ToolContext, error: Exception):
        """工具调用错误事件"""
        for plugin in self.plugins:
            if not plugin.enabled:
                continue
            
            try:
                plugin.on_tool_error(context, error)
            except Exception as e:
                self._log_event("plugin_error", {
                    "plugin": plugin.name,
                    "phase": "tool_error",
                    "error": str(e)
                })
    
    def emit_task_start(self, context: TaskContext):
        """任务开始事件"""
        for plugin in self.plugins:
            if not plugin.enabled:
                continue
            try:
                plugin.on_task_start(context)
            except Exception as e:
                self._log_event("plugin_error", {
                    "plugin": plugin.name,
                    "phase": "task_start",
                    "error": str(e)
                })
    
    def emit_task_complete(self, context: TaskContext):
        """任务完成事件"""
        for plugin in self.plugins:
            if not plugin.enabled:
                continue
            try:
                plugin.on_task_complete(context)
            except Exception as e:
                self._log_event("plugin_error", {
                    "plugin": plugin.name,
                    "phase": "task_complete",
                    "error": str(e)
                })
    
    def _log_event(self, event_type: str, data: Dict):
        """记录事件"""
        self.event_history.append({
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        })


class PluginRegistry:
    """
    插件注册表
    自动发现和加载插件
    """
    
    def __init__(self, event_bus: UniversalEventBus):
        self.event_bus = event_bus
        self.loaded_plugins: Dict[str, UniversalPlugin] = {}
    
    def discover_and_load(self, plugins_dir: str, config: Dict = None):
        """
        自动发现并加载所有插件
        """
        plugins_path = Path(plugins_dir)
        if not plugins_path.exists():
            print(f"⚠️ Plugins directory not found: {plugins_dir}")
            return
        
        for plugin_file in plugins_path.glob("*_plugin.py"):
            self._load_plugin_file(plugin_file, config)
    
    def _load_plugin_file(self, file_path: Path, config: Dict = None):
        """加载单个插件文件"""
        try:
            spec = importlib.util.spec_from_file_location(
                file_path.stem, 
                file_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找插件类
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, UniversalPlugin) and 
                    obj is not UniversalPlugin):
                    
                    # 获取插件配置
                    plugin_config = config.get(obj.name, {}) if config else {}
                    
                    # 实例化并注册
                    plugin = obj(plugin_config)
                    self.event_bus.register_plugin(plugin)
                    self.loaded_plugins[obj.name] = plugin
                    break
                    
        except Exception as e:
            print(f"❌ Failed to load plugin {file_path}: {e}")
    
    def get_plugin(self, name: str) -> Optional[UniversalPlugin]:
        """获取已加载的插件"""
        return self.loaded_plugins.get(name)
    
    def list_plugins(self) -> List[str]:
        """列出所有已加载的插件"""
        return list(self.loaded_plugins.keys())


class ConfigStore:
    """
    配置存储
    统一管理所有配置
    """
    
    def __init__(self, config_path: str = None):
        self.config_path = Path(config_path) if config_path else None
        self.config: Dict = {}
        self.load()
    
    def load(self):
        """加载配置"""
        if self.config_path and self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = self._default_config()
    
    def save(self):
        """保存配置"""
        if self.config_path:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get(self, key: str, default=None):
        """获取配置项"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        self.config[key] = value
        self.save()
    
    def get_plugin_config(self, plugin_name: str) -> Dict:
        """获取插件配置"""
        plugins = self.config.get("plugins", {})
        return plugins.get(plugin_name, {})
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            "version": "2.0",
            "framework": {
                "auto_wrap": True,
                "log_events": True
            },
            "plugins": {}
        }


class UniversalFramework:
    """
    通用框架主类
    统一入口
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_path: str = None):
        if self._initialized:
            return
        
        self.config = ConfigStore(config_path)
        self.event_bus = UniversalEventBus()
        self.registry = PluginRegistry(self.event_bus)
        self._initialized = True
        
        print("🚀 Universal Framework initialized")
    
    def discover_plugins(self, plugins_dir: str = ".claw-status/plugins"):
        """发现并加载插件"""
        config = self.config.get("plugins", {})
        self.registry.discover_and_load(plugins_dir, config)
    
    def load_plugin(self, plugin: UniversalPlugin):
        """手动加载插件"""
        self.event_bus.register_plugin(plugin)
    
    def tool_call(self, tool_name: str, **params) -> Dict[str, Any]:
        """
        统一的工具调用入口
        自动触发所有插件
        """
        context = ToolContext(
            tool_name=tool_name,
            params=params
        )
        
        # 1. 调用前检查
        intercept = self.event_bus.emit_tool_before(context)
        
        if not intercept.should_proceed:
            return {
                "success": False,
                "error": intercept.reason,
                "alternative": intercept.alternative,
                "blocked_by_framework": True
            }
        
        # 2. 执行实际调用
        try:
            result = self._execute_tool(tool_name, context.params)
            
            # 3. 调用后处理
            self.event_bus.emit_tool_after(context, result)
            
            return {
                "success": True,
                "result": result,
                "params_used": context.params
            }
            
        except Exception as e:
            # 4. 错误处理
            self.event_bus.emit_tool_error(context, e)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _execute_tool(self, tool_name: str, params: Dict) -> Any:
        """
        实际执行工具调用
        这里会调用实际的工具实现
        """
        # 这里需要根据 tool_name 分发到实际实现
        # 暂时返回模拟结果
        return {"status": "executed", "tool": tool_name}
    
    def start_task(self, task_type: str, description: str) -> TaskContext:
        """开始任务"""
        import uuid
        context = TaskContext(
            task_id=str(uuid.uuid4())[:8],
            task_type=task_type,
            description=description
        )
        self.event_bus.emit_task_start(context)
        return context
    
    def complete_task(self, context: TaskContext, result: Any, success: bool = True):
        """完成任务"""
        context.result = result
        context.success = success
        
        if success:
            self.event_bus.emit_task_complete(context)
        else:
            self.event_bus.emit_task_fail(context, Exception(str(result)))
    
    def get_stats(self) -> Dict:
        """获取框架统计"""
        return {
            "plugins_loaded": len(self.registry.list_plugins()),
            "plugin_names": self.registry.list_plugins(),
            "events_logged": len(self.event_bus.event_history)
        }


# 便捷函数
def get_framework(config_path: str = None) -> UniversalFramework:
    """获取框架实例"""
    return UniversalFramework(config_path)


if __name__ == "__main__":
    # 测试
    fw = get_framework()
    print(fw.get_stats())
