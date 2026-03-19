# MCP Client MVP

最小MCP协议实现，支持连接外部工具服务器。

## 功能

- ✅ 连接MCP服务器（stdio模式）
- ✅ 发现并列出可用工具
- ✅ 调用工具并获取结果
- ✅ 错误处理

## 快速开始

```python
from mcp_client import MCPClient

# 创建客户端
client = MCPClient()

# 连接filesystem服务器
client.connect([
    "npx", "-y", "@modelcontextprotocol/server-filesystem",
    "/tmp"
])

# 列出工具
tools = client.list_tools()
print(f"可用工具: {len(tools)}")

# 调用read_file工具
result = client.call("read_file", {"path": "/tmp/test.txt"})
print(result["content"])

# 断开连接
client.disconnect()
```

## 依赖

- Python 3.8+
- Node.js + npx (用于运行MCP服务器)

## 安装MCP服务器

```bash
# filesystem服务器
npm install -g @modelcontextprotocol/server-filesystem

# 或其他服务器
npx -y @modelcontextprotocol/server-filesystem /tmp
```

## 实现细节

- 代码行数: ~140行（包含注释和测试）
- 核心代码: ~100行
- 协议版本: 2024-11-05

## 文件

- `mcp_client.py` - 主实现
