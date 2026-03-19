"""
WDai Skills Adapter

将 WDai/OpenClaw Skills 自动转换为 Tool-DC 的 Tool 对象
"""

import json
import re
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from ..models import Tool, ToolParam, ToolParamType


class WDaiSkillAdapter:
    """
    WDai Skills 适配器
    
    自动将各种格式的 Skill 定义转换为 Tool 对象
    
    支持的格式：
    1. OpenAPI / OpenAI Function Schema
    2. Python 函数（通过类型注解和 docstring）
    3. JSON Schema
    4. 自定义字典格式
    """
    
    # OpenAPI 类型到 ToolParamType 的映射
    TYPE_MAPPING = {
        "string": ToolParamType.STRING,
        "str": ToolParamType.STRING,
        "integer": ToolParamType.INTEGER,
        "int": ToolParamType.INTEGER,
        "number": ToolParamType.NUMBER,
        "float": ToolParamType.NUMBER,
        "boolean": ToolParamType.BOOLEAN,
        "bool": ToolParamType.BOOLEAN,
        "array": ToolParamType.ARRAY,
        "list": ToolParamType.ARRAY,
        "object": ToolParamType.OBJECT,
        "dict": ToolParamType.OBJECT,
    }
    
    @classmethod
    def from_openai_schema(cls, schema: Dict[str, Any]) -> Tool:
        """
        从 OpenAI Function Schema 转换
        
        Args:
            schema: OpenAI 函数定义格式
                {
                    "name": "function_name",
                    "description": "function description",
                    "parameters": {
                        "type": "object",
                        "properties": {...},
                        "required": [...]
                    }
                }
                
        Returns:
            Tool: 转换后的 Tool 对象
        """
        name = schema.get("name", "")
        description = schema.get("description", "")
        
        parameters = []
        required_params = []
        
        params_schema = schema.get("parameters", {})
        properties = params_schema.get("properties", {})
        required = params_schema.get("required", [])
        
        for param_name, param_info in properties.items():
            param_type = cls._parse_type(param_info.get("type", "string"))
            param_desc = param_info.get("description", "")
            param_required = param_name in required
            param_enum = param_info.get("enum")
            
            param = ToolParam(
                name=param_name,
                type=param_type,
                description=param_desc,
                required=param_required,
                enum=param_enum
            )
            parameters.append(param)
            
            if param_required:
                required_params.append(param_name)
        
        return Tool(
            name=name,
            description=description,
            parameters=parameters,
            required_params=required_params
        )
    
    @classmethod
    def from_openapi_schema(cls, path: Union[str, Path]) -> List[Tool]:
        """
        从 OpenAPI/Swagger JSON 文件转换
        
        Args:
            path: OpenAPI JSON 文件路径
            
        Returns:
            List[Tool]: 工具列表
        """
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            spec = json.load(f)
        
        tools = []
        
        # 提取 paths 作为工具
        paths = spec.get("paths", {})
        for route, methods in paths.items():
            for method, details in methods.items():
                if method in ("get", "post", "put", "delete", "patch"):
                    tool = cls._openapi_path_to_tool(route, method, details)
                    tools.append(tool)
        
        return tools
    
    @classmethod
    def _openapi_path_to_tool(
        cls, 
        route: str, 
        method: str, 
        details: Dict
    ) -> Tool:
        """将 OpenAPI path 转换为 Tool"""
        # 生成工具名
        name = f"{method}_{route.replace('/', '_').replace('{', '').replace('}', '')}"
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        name = name.lower()
        
        description = details.get("summary", details.get("description", f"{method.upper()} {route}"))
        
        parameters = []
        required_params = []
        
        # 提取参数
        for param in details.get("parameters", []):
            param_name = param.get("name", "")
            param_type = cls._parse_type(param.get("schema", {}).get("type", "string"))
            param_desc = param.get("description", "")
            param_required = param.get("required", False)
            
            parameters.append(ToolParam(
                name=param_name,
                type=param_type,
                description=param_desc,
                required=param_required
            ))
            
            if param_required:
                required_params.append(param_name)
        
        # 提取请求体参数
        request_body = details.get("requestBody", {})
        if request_body:
            content = request_body.get("content", {})
            json_content = content.get("application/json", {})
            schema = json_content.get("schema", {})
            
            if schema.get("type") == "object":
                properties = schema.get("properties", {})
                required = schema.get("required", [])
                
                for prop_name, prop_info in properties.items():
                    parameters.append(ToolParam(
                        name=prop_name,
                        type=cls._parse_type(prop_info.get("type", "string")),
                        description=prop_info.get("description", ""),
                        required=prop_name in required
                    ))
                    
                    if prop_name in required:
                        required_params.append(prop_name)
        
        return Tool(
            name=name,
            description=description,
            parameters=parameters,
            required_params=required_params
        )
    
    @classmethod
    def from_python_function(cls, func) -> Tool:
        """
        从 Python 函数转换
        
        通过 inspect 获取参数信息和 docstring
        
        Args:
            func: Python 函数
            
        Returns:
            Tool: 转换后的 Tool
        """
        import inspect
        
        name = func.__name__
        description = inspect.getdoc(func) or f"调用 {name} 函数"
        
        sig = inspect.signature(func)
        parameters = []
        required_params = []
        
        for param_name, param in sig.parameters.items():
            # 跳过 self/cls
            if param_name in ("self", "cls"):
                continue
            
            # 获取类型
            param_type = ToolParamType.STRING  # 默认字符串
            if param.annotation != inspect.Parameter.empty:
                param_type = cls._python_type_to_param_type(param.annotation)
            
            # 是否必填
            param_required = param.default == inspect.Parameter.empty
            
            # 获取默认值
            default = None
            if param.default != inspect.Parameter.empty:
                default = param.default
            
            parameters.append(ToolParam(
                name=param_name,
                type=param_type,
                description="",
                required=param_required,
                default=default
            ))
            
            if param_required:
                required_params.append(param_name)
        
        return Tool(
            name=name,
            description=description,
            parameters=parameters,
            required_params=required_params
        )
    
    @classmethod
    def _python_type_to_param_type(cls, py_type) -> ToolParamType:
        """将 Python 类型转换为 ToolParamType"""
        type_name = getattr(py_type, "__name__", str(py_type)).lower()
        
        # 处理 Optional[X]
        if hasattr(py_type, "__origin__"):
            origin = py_type.__origin__
            if origin is Union:
                # 获取 Union 中的非 None 类型
                args = getattr(py_type, "__args__", ())
                for arg in args:
                    if arg is not type(None):
                        return cls._python_type_to_param_type(arg)
        
        return cls.TYPE_MAPPING.get(type_name, ToolParamType.STRING)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Tool:
        """
        从自定义字典转换
        
        支持多种字段名变体：
        - name / function_name / tool_name
        - description / desc / doc
        - parameters / params / args / arguments
        """
        # 字段名映射
        name_keys = ["name", "function_name", "tool_name", "func_name"]
        desc_keys = ["description", "desc", "doc", "docstring", "summary"]
        param_keys = ["parameters", "params", "args", "arguments", "properties"]
        required_keys = ["required", "required_params", "required_parameters"]
        
        # 提取名称
        name = ""
        for key in name_keys:
            if key in data:
                name = data[key]
                break
        
        # 提取描述
        description = ""
        for key in desc_keys:
            if key in data:
                description = data[key]
                break
        
        # 提取参数
        parameters = []
        required_params = []
        
        for key in param_keys:
            if key in data:
                params_data = data[key]
                
                # 处理不同格式
                if isinstance(params_data, dict):
                    # 格式: {"param_name": {"type": "string", ...}}
                    for param_name, param_info in params_data.items():
                        param = cls._parse_param_dict(param_name, param_info)
                        parameters.append(param)
                        if param.required:
                            required_params.append(param_name)
                            
                elif isinstance(params_data, list):
                    # 格式: [{"name": "param_name", "type": "string", ...}]
                    for param_info in params_data:
                        if isinstance(param_info, dict):
                            param_name = param_info.get("name", "")
                            param = cls._parse_param_dict(param_name, param_info)
                            parameters.append(param)
                            if param.required:
                                required_params.append(param_name)
                
                break
        
        # 提取必填参数列表
        for key in required_keys:
            if key in data:
                required_params = data[key]
                break
        
        return Tool(
            name=name,
            description=description,
            parameters=parameters,
            required_params=required_params
        )
    
    @classmethod
    def _parse_param_dict(cls, name: str, info: Dict) -> ToolParam:
        """解析参数字典"""
        # 类型
        type_val = info.get("type", "string")
        if isinstance(type_val, str):
            param_type = cls._parse_type(type_val)
        else:
            param_type = ToolParamType.STRING
        
        # 描述
        desc_keys = ["description", "desc", "doc"]
        description = ""
        for key in desc_keys:
            if key in info:
                description = info[key]
                break
        
        # 是否必填
        required = info.get("required", False)
        
        # 默认值
        default = info.get("default")
        
        # 枚举值
        enum = info.get("enum")
        
        return ToolParam(
            name=name,
            type=param_type,
            description=description,
            required=required,
            default=default,
            enum=enum
        )
    
    @classmethod
    def _parse_type(cls, type_str: str) -> ToolParamType:
        """解析类型字符串"""
        type_str = type_str.lower()
        return cls.TYPE_MAPPING.get(type_str, ToolParamType.STRING)
    
    @classmethod
    def batch_convert(
        cls, 
        items: List[Dict[str, Any]], 
        format_type: str = "auto"
    ) -> List[Tool]:
        """
        批量转换
        
        Args:
            items: 要转换的项目列表
            format_type: 格式类型 ("openai", "openapi", "dict", "auto")
            
        Returns:
            List[Tool]: 转换后的工具列表
        """
        tools = []
        
        for item in items:
            try:
                if format_type == "openai":
                    tool = cls.from_openai_schema(item)
                elif format_type == "dict":
                    tool = cls.from_dict(item)
                elif format_type == "auto":
                    # 自动检测格式
                    if "function" in item or "name" in item and "parameters" in item:
                        tool = cls.from_openai_schema(item)
                    else:
                        tool = cls.from_dict(item)
                else:
                    tool = cls.from_dict(item)
                
                tools.append(tool)
                
            except Exception as e:
                print(f"转换失败: {e}, 项目: {item}")
                continue
        
        return tools


class WDaiSkillRegistry:
    """
    WDai Skills 注册表
    
    自动扫描和转换 WDai Skills 目录中的工具定义
    """
    
    def __init__(self, skills_dir: Optional[Path] = None):
        """
        初始化注册表
        
        Args:
            skills_dir: Skills 目录路径，默认从环境推断
        """
        self.skills_dir = skills_dir or self._find_skills_dir()
        self.adapter = WDaiSkillAdapter()
        self.tools: List[Tool] = []
        self._tool_map: Dict[str, Tool] = {}
    
    def _find_skills_dir(self) -> Path:
        """查找 Skills 目录"""
        # 尝试多个可能的位置
        possible_paths = [
            Path("/root/.openclaw/workspace/skills"),
            Path.home() / ".openclaw" / "workspace" / "skills",
            Path.cwd() / "skills",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        # 默认返回第一个
        return possible_paths[0]
    
    def scan_skills(self) -> List[Tool]:
        """
        扫描 Skills 目录
        
        查找以下格式的工具定义：
        1. skill.json (OpenAI 格式)
        2. tools.json (工具列表)
        3. __init__.py (从函数提取)
        
        Returns:
            List[Tool]: 发现的工具
        """
        self.tools = []
        
        if not self.skills_dir.exists():
            print(f"Skills 目录不存在: {self.skills_dir}")
            return self.tools
        
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            
            # 尝试多种格式的定义文件
            definition_files = [
                skill_dir / "skill.json",
                skill_dir / "tools.json",
                skill_dir / "tools.yaml",
                skill_dir / "openapi.json",
            ]
            
            for def_file in definition_files:
                if def_file.exists():
                    try:
                        tools = self._load_tools_from_file(def_file)
                        self.tools.extend(tools)
                        break
                    except Exception as e:
                        print(f"加载 {def_file} 失败: {e}")
        
        # 构建索引
        self._build_index()
        
        return self.tools
    
    def _load_tools_from_file(self, path: Path) -> List[Tool]:
        """从文件加载工具定义"""
        suffix = path.suffix.lower()
        
        if suffix == ".json":
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检测格式
            if isinstance(data, list):
                return self.adapter.batch_convert(data, "auto")
            elif isinstance(data, dict):
                # 可能是 OpenAPI 格式
                if "paths" in data:
                    return self.adapter.from_openapi_schema(path)
                else:
                    return [self.adapter.from_dict(data)]
        
        elif suffix in (".yaml", ".yml"):
            try:
                import yaml
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if isinstance(data, list):
                    return self.adapter.batch_convert(data, "dict")
                else:
                    return [self.adapter.from_dict(data)]
            except ImportError:
                print("需要安装 PyYAML: pip install pyyaml")
                return []
        
        return []
    
    def _build_index(self):
        """构建工具名到工具的映射"""
        self._tool_map = {tool.name: tool for tool in self.tools}
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """根据名称获取工具"""
        return self._tool_map.get(name)
    
    def register_tool(self, tool: Tool):
        """注册单个工具"""
        self.tools.append(tool)
        self._tool_map[tool.name] = tool
    
    def to_openai_format(self) -> List[Dict]:
        """转换为 OpenAI Function Calling 格式"""
        return [tool.to_schema() for tool in self.tools]
