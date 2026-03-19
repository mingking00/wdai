# Kimi MCP Server - Phase 3 Final: Resources, Prompts & OpenClaw Integration
# Phase 3最终部分：完整Resources/Prompts + OpenClaw集成设计

from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import os

# 导入现有实现
from mcp_transport import MCPProtocolHandler as BaseProtocolHandler
from extended_tools import KimiMCPExtendedServer


class EnhancedMCPProtocolHandler(BaseProtocolHandler):
    """增强版MCP协议处理器 - 完整Resources和Prompts支持"""
    
    def __init__(self, server: KimiMCPExtendedServer):
        super().__init__(server)
        self.resources_manager = ResourcesManager()
        self.prompts_manager = PromptsManager()
    
    def _handle_resources_list(self, req_id: Optional[int], params: Dict) -> Any:
        """增强版resources/list - 返回完整资源列表"""
        resources = self.resources_manager.list_resources()
        return super()._create_response(req_id, {"resources": resources})
    
    def _handle_resources_read(self, req_id: Optional[int], params: Dict) -> Any:
        """增强版resources/read - 读取资源内容"""
        uri = params.get("uri")
        content = self.resources_manager.read_resource(uri)
        
        return super()._create_response(req_id, {
            "contents": [{
                "uri": uri,
                "mimeType": content.get("mimeType", "text/plain"),
                "text": content.get("text", "")
            }]
        })
    
    def _handle_prompts_list(self, req_id: Optional[int], params: Dict) -> Any:
        """增强版prompts/list - 返回完整提示模板列表"""
        prompts = self.prompts_manager.list_prompts()
        return super()._create_response(req_id, {"prompts": prompts})
    
    def _handle_prompts_get(self, req_id: Optional[int], params: Dict) -> Any:
        """增强版prompts/get - 获取完整提示模板"""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        prompt = self.prompts_manager.get_prompt(name, arguments)
        return super()._create_response(req_id, prompt)
    
    def _create_response(self, req_id: Optional[int], result: Dict) -> Any:
        """创建响应辅助方法"""
        from mcp_transport import MCPResponse
        return MCPResponse(id=req_id, result=result)


class ResourcesManager:
    """资源管理器 - 完整Resources支持"""
    
    def __init__(self, workspace: str = "/root/.openclaw/workspace"):
        self.workspace = workspace
        self.resources = self._init_resources()
    
    def _init_resources(self) -> List[Dict]:
        """初始化可用资源"""
        return [
            {
                "uri": "memory://long-term",
                "name": "长期记忆",
                "description": "用户的长期记忆数据库 (MEMORY.md)",
                "mimeType": "text/markdown"
            },
            {
                "uri": "memory://session/current",
                "name": "当前会话",
                "description": "当前对话会话的记忆",
                "mimeType": "application/json"
            },
            {
                "uri": f"file://{self.workspace}/SOUL.md",
                "name": "SOUL.md",
                "description": "我的核心人格定义",
                "mimeType": "text/markdown"
            },
            {
                "uri": f"file://{self.workspace}/IDENTITY.md",
                "name": "IDENTITY.md",
                "description": "身份定义文件",
                "mimeType": "text/markdown"
            },
            {
                "uri": f"file://{self.workspace}/USER.md",
                "name": "USER.md",
                "description": "用户画像",
                "mimeType": "text/markdown"
            },
            {
                "uri": "learnings://all",
                "name": "学习记录",
                "description": "所有学习记录和沉淀",
                "mimeType": "text/markdown"
            },
            {
                "uri": "tools://list",
                "name": "可用工具列表",
                "description": "所有MCP Tools的完整列表",
                "mimeType": "application/json"
            },
            {
                "uri": "docs://mcp-protocol",
                "name": "MCP协议文档",
                "description": "Model Context Protocol规范",
                "mimeType": "text/markdown"
            }
        ]
    
    def list_resources(self) -> List[Dict]:
        """列出所有可用资源"""
        return self.resources
    
    def read_resource(self, uri: str) -> Dict[str, str]:
        """读取资源内容"""
        # memory:// 资源
        if uri.startswith("memory://"):
            return self._read_memory_resource(uri)
        
        # file:// 资源
        elif uri.startswith("file://"):
            return self._read_file_resource(uri)
        
        # learnings:// 资源
        elif uri.startswith("learnings://"):
            return self._read_learnings_resource(uri)
        
        # tools:// 资源
        elif uri.startswith("tools://"):
            return self._read_tools_resource(uri)
        
        # docs:// 资源
        elif uri.startswith("docs://"):
            return self._read_docs_resource(uri)
        
        else:
            return {
                "mimeType": "text/plain",
                "text": f"Unknown resource URI: {uri}"
            }
    
    def _read_memory_resource(self, uri: str) -> Dict[str, str]:
        """读取记忆资源"""
        if uri == "memory://long-term":
            path = f"{self.workspace}/MEMORY.md"
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {"mimeType": "text/markdown", "text": content}
            return {"mimeType": "text/plain", "text": "MEMORY.md not found"}
        
        elif uri == "memory://session/current":
            # 返回当前会话信息
            return {
                "mimeType": "application/json",
                "text": json.dumps({
                    "session_id": "current",
                    "timestamp": datetime.now().isoformat(),
                    "workspace": self.workspace
                }, indent=2)
            }
        
        return {"mimeType": "text/plain", "text": f"Memory resource not found: {uri}"}
    
    def _read_file_resource(self, uri: str) -> Dict[str, str]:
        """读取文件资源"""
        file_path = uri.replace("file://", "")
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 根据扩展名判断mime类型
            mime_type = "text/plain"
            if file_path.endswith('.md'):
                mime_type = "text/markdown"
            elif file_path.endswith('.json'):
                mime_type = "application/json"
            elif file_path.endswith('.py'):
                mime_type = "text/x-python"
            
            return {"mimeType": mime_type, "text": content}
        
        return {"mimeType": "text/plain", "text": f"File not found: {file_path}"}
    
    def _read_learnings_resource(self, uri: str) -> Dict[str, str]:
        """读取学习记录资源"""
        learnings_dir = f"{self.workspace}/.learnings"
        
        if uri == "learnings://all":
            if os.path.exists(learnings_dir):
                files = []
                for f in os.listdir(learnings_dir):
                    if f.endswith('.md'):
                        files.append(f"- {f}")
                
                content = "# Learning Records\n\n" + "\n".join(files)
                return {"mimeType": "text/markdown", "text": content}
            return {"mimeType": "text/plain", "text": "No learnings found"}
        
        return {"mimeType": "text/plain", "text": f"Learning resource not found: {uri}"}
    
    def _read_tools_resource(self, uri: str) -> Dict[str, str]:
        """读取工具列表资源"""
        if uri == "tools://list":
            server = KimiMCPExtendedServer()
            tools = server.list_all_tools()
            
            tools_info = []
            for tool in tools:
                tools_info.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "category": tool.get("category", "Other")
                })
            
            return {
                "mimeType": "application/json",
                "text": json.dumps({
                    "total": len(tools_info),
                    "tools": tools_info
                }, indent=2)
            }
        
        return {"mimeType": "text/plain", "text": f"Tools resource not found: {uri}"}
    
    def _read_docs_resource(self, uri: str) -> Dict[str, str]:
        """读取文档资源"""
        if uri == "docs://mcp-protocol":
            doc_content = """# Model Context Protocol (MCP)

## Overview

MCP is an open protocol that standardizes how applications provide context to LLMs.

## Core Concepts

- **Tools**: Functions that LLMs can call
- **Resources**: Data that LLMs can access
- **Prompts**: Templates for LLM interactions

## Protocol Version

Current version: 2024-11-05

## Resources

Resources are identified by URIs:
- `file://` - Local files
- `memory://` - Memory storage
- `http://` / `https://` - Web resources

## Tools

Tools are invoked with:
- `name`: Tool identifier
- `arguments`: Tool parameters

## Official Documentation

https://modelcontextprotocol.io
"""
            return {"mimeType": "text/markdown", "text": doc_content}
        
        return {"mimeType": "text/plain", "text": f"Docs resource not found: {uri}"}


class PromptsManager:
    """提示模板管理器 - 完整Prompts支持"""
    
    def __init__(self):
        self.prompts = self._init_prompts()
    
    def _init_prompts(self) -> Dict[str, Dict]:
        """初始化提示模板库"""
        return {
            "deep_research": {
                "name": "deep_research",
                "description": "深度研究模式 - 系统性研究主题",
                "arguments": [
                    {
                        "name": "topic",
                        "description": "研究主题",
                        "required": True
                    },
                    {
                        "name": "depth",
                        "description": "研究深度 (quick/standard/deep)",
                        "required": False
                    }
                ],
                "template": """你是一个专业研究员。请对以下主题进行深度研究：

主题：{{topic}}
深度：{{depth}}

请遵循以下研究框架：
1. 定义研究范围和核心问题
2. 收集多元来源信息（至少3个不同来源）
3. 批判性分析信息的可信度和时效性
4. 综合不同观点，识别共识和分歧
5. 形成结构化研究报告

输出格式：
- 执行摘要
- 关键发现（分点列出）
- 证据来源
- 研究局限性
- 后续研究建议

使用System 2慢路径思考，确保深度和准确性。"""
            },
            
            "code_review": {
                "name": "code_review",
                "description": "代码审查模式 - 专业代码评审",
                "arguments": [
                    {
                        "name": "code",
                        "description": "要审查的代码",
                        "required": True
                    },
                    {
                        "name": "language",
                        "description": "编程语言",
                        "required": True
                    }
                ],
                "template": """你是一个资深软件工程师。请审查以下代码：

语言：{{language}}

代码：
```{{language}}
{{code}}
```

请从以下维度进行评审：

1. **安全性**
   - 是否存在安全漏洞？
   - 输入验证是否充分？
   - 敏感信息是否妥善保护？

2. **性能**
   - 时间复杂度是否合理？
   - 空间使用是否高效？
   - 是否存在性能瓶颈？

3. **可维护性**
   - 代码是否清晰易读？
   - 命名是否规范？
   - 函数/类职责是否单一？

4. **正确性**
   - 逻辑是否正确？
   - 边界条件是否处理？
   - 错误处理是否完善？

5. **最佳实践**
   - 是否符合语言惯用法？
   - 是否遵循设计原则？

请提供：
- 总体评分 (1-10)
- 关键问题（如有）
- 具体改进建议
- 重构示例（如适用）"""
            },
            
            "creative_explore": {
                "name": "creative_explore",
                "description": "创意探索模式 - 多角度思考",
                "arguments": [
                    {
                        "name": "topic",
                        "description": "探索主题",
                        "required": True
                    },
                    {
                        "name": "perspectives",
                        "description": "思考角度数量",
                        "required": False
                    }
                ],
                "template": """你是一个创意探索者。请对以下主题进行多角度思考：

主题：{{topic}}
角度数：{{perspectives}}

请从至少{{perspectives}}个不同角度探索这个主题：

**角度1：技术视角**
- 技术实现的可行性
- 现有技术栈的支持
- 技术挑战和解决方案

**角度2：用户视角**
- 用户需求和痛点
- 用户体验考量
- 用户接受度预测

**角度3：商业视角**
- 市场机会分析
- 竞争优势评估
- 商业模式可行性

**角度4：社会视角**
- 社会影响分析
- 伦理考量
- 长期社会价值

**角度5：创新视角**
- 创新点识别
- 突破常规的可能性
- 颠覆性潜力评估

对于每个角度：
1. 简要说明该角度的核心观点
2. 提供2-3个具体洞察
3. 识别潜在机会或风险

最后：
- 整合各角度的交叉发现
- 提出一个创新的综合方案
- 指出最值得深入探索的方向"""
            },
            
            "learning_mode": {
                "name": "learning_mode",
                "description": "学习模式 - 系统性学习新主题",
                "arguments": [
                    {
                        "name": "topic",
                        "description": "学习主题",
                        "required": True
                    },
                    {
                        "name": "level",
                        "description": "学习水平 (beginner/intermediate/advanced)",
                        "required": False
                    }
                ],
                "template": """启动学习模式。

主题：{{topic}}
水平：{{level}}

学习框架：

**阶段1：建立认知框架**
- 这个领域的基本概念是什么？
- 核心术语和定义
- 领域的边界和关联

**阶段2：探索关键资源**
- 推荐的入门资源
- 权威文档和论文
- 社区和讨论区

**阶段3：实践应用**
- 动手实践建议
- 小项目/练习想法
- 常见陷阱和避免方法

**阶段4：深化理解**
- 进阶主题
- 前沿研究方向
- 待解决的问题

**阶段5：知识整合**
- 创建知识地图
- 与其他领域的联系
- 个人学习路径建议

学习方式：
- 自动执行，无需确认
- 每10轮进行v2.0评估
- System 2深度思考关键概念
- 持续记录到MEMORY.md

配置：
- 自动执行：开启
- 评估周期：10轮
- 深度模式：{{level}}"""
            },
            
            "bug_hunt": {
                "name": "bug_hunt",
                "description": "Bug排查模式 - 系统化问题诊断",
                "arguments": [
                    {
                        "name": "problem",
                        "description": "问题描述",
                        "required": True
                    },
                    {
                        "name": "context",
                        "description": "问题上下文",
                        "required": False
                    }
                ],
                "template": """你是一个资深调试专家。请系统性地诊断以下问题：

**问题描述**：
{{problem}}

**上下文**：
{{context}}

诊断框架：

**步骤1：问题澄清**
- 问题的确切表现是什么？
- 预期行为 vs 实际行为
- 问题的可复现性如何？

**步骤2：信息收集**
- 相关日志和错误信息
- 环境配置（OS、版本、依赖）
- 最近变更（代码、配置、数据）

**步骤3：假设生成**
- 列出所有可能的原因（至少5个）
- 按概率排序
- 每个假设的支持证据

**步骤4：假设验证**
- 设计验证实验
- 最小化复现步骤
- 逐步排除不可能的原因

**步骤5：解决方案**
- 根因分析
- 解决方案（短期+长期）
- 预防措施

**步骤6：验证修复**
- 测试修复方案
- 确保没有引入新问题
- 文档化解决过程

输出：
- 根因（Root Cause）
- 修复方案
- 预防措施
- 学习总结"""
            },
            
            "first_principles": {
                "name": "first_principles",
                "description": "第一性原理思考 - 本质解构",
                "arguments": [
                    {
                        "name": "problem",
                        "description": "要解构的问题",
                        "required": True
                    }
                ],
                "template": """使用第一性原理思考方法解构问题。

**原始问题**：
{{problem}}

**思考过程**：

1. **质疑假设**
   - 这个问题基于哪些假设？
   - 这些假设都成立吗？
   - 如果假设不成立会怎样？

2. **解构到本质**
   - 问题的最基本组成部分是什么？
   - 物理/数学/逻辑上的基本约束
   - 不可再简化的基本事实

3. **识别本质约束**
   - 哪些约束是物理定律？
   - 哪些是人为规则？
   - 哪些是历史惯性？

4. **从零重构**
   - 如果从头设计，最优解是什么？
   - 忽略现有方案，理想状态是什么？
   - 如何逐步逼近理想状态？

5. **创新方案生成**
   - 基于本质约束，有什么新可能？
   - 现有方案有哪些可以打破的？
   - 跨领域类比有什么启发？

输出格式：
- 识别出的关键假设
- 问题的本质组成
- 重构的最优方案
- 实施路径

思考原则：
- "这是唯一的解决方法吗？"
- "最基本的真理是什么？"
- "如果不知道任何现有方案，我会怎么做？"
"""
            }
        }
    
    def list_prompts(self) -> List[Dict]:
        """列出所有可用提示模板"""
        return [
            {
                "name": name,
                "description": prompt["description"],
                "arguments": prompt.get("arguments", [])
            }
            for name, prompt in self.prompts.items()
        ]
    
    def get_prompt(self, name: str, arguments: Dict = None) -> Dict:
        """获取提示模板（带参数替换）"""
        if name not in self.prompts:
            return {
                "description": "Unknown prompt",
                "messages": []
            }
        
        prompt_def = self.prompts[name]
        template = prompt_def["template"]
        
        # 参数替换
        if arguments:
            for key, value in arguments.items():
                placeholder = f"{{{{{key}}}}}"
                template = template.replace(placeholder, str(value))
        
        # 处理未替换的占位符（使用默认值）
        import re
        template = re.sub(r'\{\{\w+\}\}', '', template)
        
        return {
            "description": prompt_def["description"],
            "messages": [
                {
                    "role": "system",
                    "content": {
                        "type": "text",
                        "text": template
                    }
                }
            ]
        }


# OpenClaw集成设计方案
class OpenClawIntegrationSpec:
    """OpenClaw官方集成规范"""
    
    @staticmethod
    def get_integration_config() -> Dict:
        """获取OpenClaw集成配置规范"""
        return {
            "version": "1.0",
            "description": "Kimi MCP Server integration with OpenClaw",
            
            "config_file": {
                "path": "/root/.openclaw/config/mcp.yaml",
                "format": "yaml"
            },
            
            "server_registration": {
                "type": "mcp_server",
                "name": "kimi-tools",
                "enabled": True,
                "transport": {
                    "type": "stdio",  # 或 "http"
                    "stdio": {
                        "command": "python3",
                        "args": [
                            "/root/.openclaw/workspace/kimi-mcp-server/src/mcp_transport.py",
                            "--transport", "stdio"
                        ]
                    },
                    "http": {
                        "url": "http://localhost:8080",
                        "endpoints": {
                            "mcp": "/mcp",
                            "health": "/health"
                        }
                    }
                }
            },
            
            "capabilities": {
                "tools": {
                    "auto_discover": True,
                    "cache_ttl": 300
                },
                "resources": {
                    "enabled": True,
                    "allowed_schemes": ["file", "memory", "workspace"]
                },
                "prompts": {
                    "enabled": True,
                    "templates_dir": "/root/.openclaw/prompts"
                }
            },
            
            "security": {
                "allowed_paths": [
                    "/root/.openclaw/workspace",
                    "/tmp"
                ],
                "blocked_paths": [
                    "/etc",
                    "/root/.ssh"
                ],
                "max_file_size": 10485760,  # 10MB
                "timeout": 30
            },
            
            "logging": {
                "level": "info",
                "file": "/root/.openclaw/logs/mcp-server.log"
            }
        }
    
    @staticmethod
    def get_cli_commands() -> Dict:
        """获取CLI命令规范"""
        return {
            "mcp": {
                "description": "Manage MCP servers",
                "subcommands": {
                    "list": "List registered MCP servers",
                    "add": "Add a new MCP server",
                    "remove": "Remove an MCP server",
                    "start": "Start MCP server",
                    "stop": "Stop MCP server",
                    "status": "Check MCP server status"
                }
            }
        }


# 创建示例配置文件
def generate_openclaw_config() -> str:
    """生成OpenClaw配置文件内容"""
    config = """# OpenClaw MCP Integration Configuration
# Kimi MCP Server v2.0

mcp:
  servers:
    kimi:
      name: "Kimi Tools"
      description: "Kimi Claw MCP Server with 23 Tools"
      version: "2.0.0"
      enabled: true
      
      transport:
        type: stdio  # 选项: stdio, http
        
        stdio:
          command: python3
          args:
            - /root/.openclaw/workspace/kimi-mcp-server/src/mcp_transport.py
            - --transport
            - stdio
          env:
            WORKSPACE: /root/.openclaw/workspace
        
        http:
          url: http://localhost:8080
          timeout: 30
          retries: 3
      
      capabilities:
        tools:
          enabled: true
          auto_discover: true
        
        resources:
          enabled: true
          allowed_schemes:
            - file
            - memory
            - workspace
          base_paths:
            - /root/.openclaw/workspace
        
        prompts:
          enabled: true
      
      security:
        allowed_paths:
          - /root/.openclaw/workspace
          - /tmp
        blocked_paths:
          - /etc
          - /root/.ssh
          - /root/.openclaw/agents
        max_file_size: 10485760

  # 全局MCP设置
  settings:
    default_server: kimi
    tool_timeout: 30
    max_concurrent_tools: 5
    log_level: info

# 集成示例
integration:
  examples:
    claude_desktop:
      config_path: ~/Library/Application Support/Claude/claude_desktop_config.json
      content:
        mcpServers:
          kimi:
            command: python3
            args:
              - /root/.openclaw/workspace/kimi-mcp-server/src/mcp_transport.py
              - --transport
              - stdio
"""
    return config


if __name__ == "__main__":
    # 测试Resources和Prompts
    print("=" * 60)
    print("Resources and Prompts Test")
    print("=" * 60)
    
    # Test Resources
    print("\n📁 Resources Test:")
    resources_mgr = ResourcesManager()
    resources = resources_mgr.list_resources()
    print(f"   Total resources: {len(resources)}")
    for r in resources[:3]:
        print(f"   • {r['name']}: {r['uri']}")
    
    # Test reading resource
    content = resources_mgr.read_resource("memory://long-term")
    print(f"\n   Read memory://long-term: {len(content['text'])} chars")
    
    # Test Prompts
    print("\n📝 Prompts Test:")
    prompts_mgr = PromptsManager()
    prompts = prompts_mgr.list_prompts()
    print(f"   Total prompts: {len(prompts)}")
    for p in prompts:
        print(f"   • {p['name']}: {p['description']}")
    
    # Test getting prompt
    prompt = prompts_mgr.get_prompt("deep_research", {"topic": "AI", "depth": "deep"})
    print(f"\n   Generated prompt length: {len(prompt['messages'][0]['content']['text'])} chars")
    
    # Show OpenClaw config
    print("\n🔧 OpenClaw Integration Config:")
    config = generate_openclaw_config()
    print(config[:500] + "...")
    
    print("\n✅ Phase 3 Final Complete!")
