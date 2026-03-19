# MCP-CLI Bridge Framework
## 通用化设计文档

## 核心概念

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM / Agent                              │
│  "调用 fetch_web_page --url https://example.com"            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  MCP-CLI Bridge                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Discovery   │───→│   Adapter    │───→│   Executor   │  │
│  │  (--list)    │    │(Schema Convert)│   │(Subprocess)  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Tool Providers                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Web Tools│  │ File Ops │  │ GitHub   │  │ Database │    │
│  │ (Python) │  │ (Rust)   │  │ (Go)     │  │ (Node)   │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 架构分层

### Layer 1: Protocol Layer (MCP)
- 保持 MCP 协议标准
- JSON-RPC 2.0 消息格式
- 工具定义 Schema (简化版)

### Layer 2: Bridge Layer (核心)
- **Discovery**: 按需发现工具 (`--list`, `--help`)
- **Adapter**: Schema ↔ CLI 参数转换
- **Executor**: 子进程管理 + 结果解析

### Layer 3: Provider Layer (工具实现)
- 任何可执行文件
- 支持多语言 (Python, Go, Rust, Node, Bash)
- 只需实现标准 CLI 接口

## 工具定义格式 (mcp-tool.yaml)

```yaml
name: web_fetcher
description: Fetch and parse web pages
version: 1.0.0

# CLI 配置
cli:
  command: web-fetcher
  subcommand: fetch  # 可选
  
# 参数定义 (映射到 CLI flags)
parameters:
  - name: url
    type: string
    required: true
    cli_flag: --url
    description: Target URL to fetch
    
  - name: format
    type: enum
    enum: [markdown, html, text]
    default: markdown
    cli_flag: --format
    description: Output format
    
  - name: timeout
    type: integer
    default: 30
    cli_flag: --timeout
    description: Request timeout in seconds

# 输出格式
output:
  type: object
  schema:
    content: string
    title: string
    links: array
    status_code: integer
```

## CLI 接口规范

每个工具提供者必须实现：

```bash
# 1. 工具发现
tool-name --list
# 输出: JSON 格式的工具列表

# 2. 参数帮助
tool-name --help
# 输出: 标准 POSIX help + JSON schema

# 3. 执行调用
tool-name --param1 value1 --param2 value2
# 输出: JSON 结果

# 4. 批量执行 (可选)
tool-name --batch < batch_input.json
# 输出: JSON Lines 结果
```

## Bridge 核心组件

### 1. Discovery Manager

```python
class DiscoveryManager:
    """按需发现工具，替代预加载 schema"""
    
    def discover(self, tool_path: str) -> ToolSchema:
        """执行 --list 获取工具定义"""
        result = subprocess.run(
            [tool_path, "--list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return ToolSchema.parse(result.stdout)
    
    def get_help(self, tool_path: str, subcommand: str = None) -> str:
        """获取参数帮助"""
        cmd = [tool_path]
        if subcommand:
            cmd.append(subcommand)
        cmd.append("--help")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout
```

### 2. Adapter (转换器)

```python
class MCPToCLIAdapter:
    """MCP JSON-RPC ↔ CLI 命令转换"""
    
    def mcp_call_to_cli(self, mcp_request: dict) -> List[str]:
        """转换 MCP 调用为 CLI 参数"""
        tool_name = mcp_request["name"]
        params = mcp_request["parameters"]
        
        # 查找工具配置
        tool_config = self.registry.get(tool_name)
        
        # 构建命令
        cmd = [tool_config.cli.command]
        if tool_config.cli.subcommand:
            cmd.append(tool_config.cli.subcommand)
        
        # 转换参数
        for param_name, value in params.items():
            param_config = tool_config.get_param(param_name)
            flag = param_config.cli_flag
            
            if param_config.type == "boolean":
                if value:
                    cmd.append(flag)
            elif param_config.type == "array":
                for item in value:
                    cmd.extend([flag, str(item)])
            else:
                cmd.extend([flag, str(value)])
        
        return cmd
    
    def cli_output_to_mcp(self, stdout: str, stderr: str, exit_code: int) -> dict:
        """转换 CLI 输出为 MCP 响应"""
        if exit_code != 0:
            return {
                "error": {
                    "code": -32000,
                    "message": f"Tool execution failed: {stderr}",
                    "data": {"exit_code": exit_code}
                }
            }
        
        try:
            result = json.loads(stdout)
            return {"result": result}
        except json.JSONDecodeError:
            # 非 JSON 输出，包装为文本
            return {"result": {"content": stdout}}
```

### 3. Executor (执行器)

```python
class CLIExecutor:
    """管理子进程执行"""
    
    def __init__(self, timeout: int = 30, max_workers: int = 10):
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_workers)
    
    async def execute(self, cmd: List[str]) -> ExecutionResult:
        """执行 CLI 命令"""
        async with self.semaphore:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self.timeout
                )
                
                return ExecutionResult(
                    stdout=stdout.decode(),
                    stderr=stderr.decode(),
                    exit_code=proc.returncode
                )
            except asyncio.TimeoutError:
                proc.kill()
                return ExecutionResult(
                    stdout="",
                    stderr=f"Timeout after {self.timeout}s",
                    exit_code=-1
                )
```

## 使用示例

### 1. 工具提供者开发 (Python)

```python
#!/usr/bin/env python3
# web_fetcher.py
import argparse
import json
import sys
import requests
from bs4 import BeautifulSoup

def main():
    parser = argparse.ArgumentParser(description="Web page fetcher")
    parser.add_argument("--list", action="store_true", help="List available tools")
    parser.add_argument("--url", type=str, help="Target URL")
    parser.add_argument("--format", choices=["markdown", "html", "text"], 
                       default="markdown")
    parser.add_argument("--timeout", type=int, default=30)
    
    args = parser.parse_args()
    
    if args.list:
        # 输出工具定义
        print(json.dumps({
            "name": "web_fetch",
            "description": "Fetch and parse web pages",
            "version": "1.0.0",
            "parameters": [
                {"name": "url", "type": "string", "required": True},
                {"name": "format", "type": "string", "enum": ["markdown", "html", "text"]},
                {"name": "timeout", "type": "integer", "default": 30}
            ]
        }))
        return
    
    if not args.url:
        parser.print_help()
        sys.exit(1)
    
    # 执行获取
    try:
        response = requests.get(args.url, timeout=args.timeout)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        result = {
            "url": args.url,
            "title": soup.title.string if soup.title else "",
            "content": soup.get_text(),
            "status_code": response.status_code,
            "links": [a.get('href') for a in soup.find_all('a', href=True)]
        }
        
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 2. Bridge 配置 (bridge.yaml)

```yaml
# Bridge 配置
name: my-bridge
version: 1.0.0

# 工具提供者注册
providers:
  - name: web_tools
    path: /opt/tools/web_fetcher.py
    type: python
    
  - name: file_ops
    path: /opt/tools/file_ops
    type: binary
    
  - name: github
    path: /opt/tools/github_cli
    type: go_binary

# 执行配置
execution:
  timeout: 30
  max_workers: 10
  working_dir: /tmp/mcp-cli

# 缓存配置 (可选)
cache:
  enabled: true
  ttl: 300  # schema 缓存5分钟
  
# 日志配置
logging:
  level: info
  format: json
```

### 3. 客户端使用

```python
from mcp_cli_bridge import BridgeClient

# 创建客户端
client = BridgeClient("bridge.yaml")

# 发现可用工具
tools = await client.discover_tools()
print(f"Available tools: {[t.name for t in tools]}")

# 调用工具 (LLM 只需生成自然语言意图，Bridge 处理转换)
result = await client.call(
    tool="web_fetch",
    params={"url": "https://example.com", "format": "markdown"}
)

print(result.content)
```

## 性能优化

### 1. Schema 缓存
```python
@lru_cache(maxsize=100)
def get_tool_schema(tool_path: str) -> ToolSchema:
    """缓存工具定义，避免重复 --list"""
    return discovery_manager.discover(tool_path)
```

### 2. 连接池 (对于长连接工具)
```python
class PersistentProvider:
    """支持持久化连接的工具提供者"""
    
    def __init__(self, socket_path: str):
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.connect(socket_path)
    
    def call(self, method: str, params: dict) -> dict:
        request = {"method": method, "params": params}
        self.socket.send(json.dumps(request).encode())
        response = self.socket.recv(65536)
        return json.loads(response)
```

### 3. 批量执行
```python
# 单次 CLI 调用多个请求
tool-name --batch << 'EOF'
{"method": "fetch", "params": {"url": "https://a.com"}}
{"method": "fetch", "params": {"url": "https://b.com"}}
EOF
```

## 扩展设计

### 1. 权限控制
```yaml
# 在 bridge.yaml 中添加权限
providers:
  - name: file_ops
    path: /opt/tools/file_ops
    permissions:
      - read: /home/user/**
      - write: /home/user/workspace/**
      - deny: /etc/**
```

### 2. 中间件机制
```python
class Middleware:
    """拦截和修改调用"""
    
    def before_call(self, cmd: List[str]) -> List[str]:
        # 添加审计日志
        audit_log.info(f"Executing: {' '.join(cmd)}")
        return cmd
    
    def after_call(self, result: ExecutionResult) -> ExecutionResult:
        # 结果过滤/脱敏
        if "password" in result.stdout:
            result.stdout = "[REDACTED]"
        return result
```

### 3. 多版本管理
```yaml
providers:
  - name: web_tools
    versions:
      v1: /opt/tools/web_fetcher_v1.py
      v2: /opt/tools/web_fetcher_v2.py
    default: v2
```

## 与标准 MCP 的对比

| 特性 | 标准 MCP | MCP-CLI Bridge |
|------|---------|----------------|
| 工具定义 | 预加载 schema | 按需发现 (`--list`) |
| 调用方式 | JSON-RPC over stdio | CLI subprocess |
| 语言支持 | 需 SDK | 任何可执行文件 |
| 上下文占用 | 大 (schema 在 prompt) | 小 (只需 tool name) |
| 启动延迟 | 低 | 中 (进程启动) |
| 调试难度 | 中 (需抓包) | 低 (直接看命令) |
| 适用场景 | 高频/低延迟 | 低频/多语言/简化 |

## 实现路线图

### Phase 1: Core (MVP)
- [ ] Discovery Manager
- [ ] Basic Adapter (JSON ↔ CLI)
- [ ] Process Executor
- [ ] YAML Config

### Phase 2: Optimization
- [ ] Schema Cache
- [ ] Batch Execution
- [ ] Async Support
- [ ] Error Recovery

### Phase 3: Ecosystem
- [ ] Provider Registry
- [ ] Middleware System
- [ ] Permission Control
- [ ] Monitoring/Observability

### Phase 4: Advanced
- [ ] Persistent Connections
- [ ] Streaming Support
- [ ] Multi-version Management
- [ ] Remote Provider Support

## 参考实现

```bash
# 项目结构
mcp-cli-bridge/
├── bridge/                 # 核心桥接逻辑
│   ├── discovery.py
│   ├── adapter.py
│   └── executor.py
├── providers/              # 官方工具集
│   ├── web/
│   ├── file/
│   └── git/
├── sdk/                    # 开发SDK
│   ├── python/
│   ├── go/
│   └── rust/
├── cli/                    # Bridge CLI
│   └── main.py
└── tests/
```

## 结论

MCP-CLI Bridge 把协议复杂度和实现复杂度解耦：
- **协议层**：保持 MCP 标准，生态兼容
- **实现层**：用 CLI 简化，降低门槛
- **优化层**：按需发现、缓存、批量化，抵消 CLI 开销

核心价值：**用 CLI 的简洁，获得 MCP 的生态**。
