# MCP与A2A协议深度实现报告

**研究时间**: 2026-03-10  
**协议**: Model Context Protocol (MCP) + Agent2Agent Protocol (A2A)  
**状态**: 2025年11月最新规范

---

## 一、MCP (Model Context Protocol) 实现详解

### 1.1 协议概述

**MCP**是Anthropic于2024年11月发布的开放标准，2025年12月捐赠给Linux Foundation的Agentic AI Foundation (AAIF)。

**核心定位**: AI的"USB-C" —— 标准化LLM应用与外部数据源/工具的连接

**通信基础**: JSON-RPC 2.0

### 1.2 架构组件

```
┌─────────────────────────────────────────┐
│              Host (宿主应用)               │
│  ┌─────────────────────────────────┐    │
│  │         Client (客户端)          │    │
│  │  ┌─────────────────────────┐    │    │
│  │  │    MCP Server (服务器)   │    │    │
│  │  │  ┌─────────────────┐    │    │    │
│  │  │  │  External Tool  │    │    │    │
│  │  │  │  (GitHub/Slack/ │    │    │    │
│  │  │  │   Database...)  │    │    │    │
│  │  │  └─────────────────┘    │    │    │
│  │  └─────────────────────────┘    │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

**三种核心能力**:
| 能力 | 说明 | 示例 |
|------|------|------|
| **Tools** | AI可调用的函数 | `get_forecast(location)` |
| **Resources** | AI可读取的数据 | 文件内容、数据库记录 |
| **Prompts** | 可复用的提示模板 | " weather report format" |

**客户端能力** (反向提供):
| 能力 | 说明 |
|------|------|
| **Sampling** | 服务器可请求LLM调用 |
| **Roots** | 服务器可访问的URI/文件边界 |
| **Elicitation** | 服务器可向用户请求额外信息 |

### 1.3 传输机制

**方式1: Stdio (标准输入输出)**
```python
# Python SDK示例
from mcp import ClientSession, StdioServerParameters

server_params = StdioServerParameters(
    command="python",
    args=["my_server.py"]
)

async with ClientSession(server_params) as session:
    await session.initialize()
    tools = await session.list_tools()
```

**方式2: StreamableHTTP (HTTP + SSE)**
```python
# HTTP + Server-Sent Events
session = await ClientSession.connect(
    "https://mcp-server.example.com/sse"
)
```

**选择指南**:
| 场景 | 推荐传输 | 原因 |
|------|---------|------|
| 本地工具 | Stdio | 轻量、安全隔离 |
| 远程服务 | HTTP/SSE | 可扩展、跨网络 |
| 高并发 | 无状态HTTP | 负载均衡友好 |

### 1.4 服务器实现示例

**Python (FastMCP)**:
```python
from fastmcp import FastMCP

mcp = FastMCP(server_name="Demo Server")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Greet by name"""
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run()
```

**TypeScript SDK**:
```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";

const server = new Server({
  name: "demo-server",
  version: "1.0.0"
});

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [{
      name: "add",
      description: "Add two numbers",
      inputSchema: { type: "object", properties: { a: {type: "number"}, b: {type: "number"} } }
    }]
  };
});
```

### 1.5 客户端集成流程

```python
async def mcp_client_workflow():
    # 1. 连接服务器
    session = await ClientSession.connect(server_params)
    await session.initialize()
    
    # 2. 发现能力
    tools = await session.list_tools()
    resources = await session.list_resources()
    
    # 3. 提供给LLM
    llm = OpenAI()
    response = llm.chat(
        messages=user_input,
        functions=convert_to_openai_functions(tools)
    )
    
    # 4. 处理工具调用
    if response.tool_calls:
        for call in response.tool_calls:
            result = await session.call_tool(
                call.name, 
                call.arguments
            )
            # 将结果返回给LLM
    
    # 5. 获取最终回答
    final_response = llm.chat(messages=updated_messages)
```

### 1.6 2025年11月规范更新

**新增核心功能**:

| 功能 | 说明 | 意义 |
|------|------|------|
| **Tasks** | 长时工作流触发与轮询 | 支持异步复杂任务 |
| **Sampling改进** | 服务器可使用Tools | 服务器端推理能力 |
| **M2M Auth** | 机器对机器认证 | 企业级安全 |
| **Cross App Access** | 跨应用访问控制 | 更细粒度权限 |

**安全增强**:
- 不再强制DCR (Dynamic Client Registration)
- 更好的OAuth 2.1支持
- 企业预批准客户端

---

## 二、A2A (Agent2Agent Protocol) 实现详解

### 2.1 协议概述

**A2A**是Google于2025年4月发布的开放协议，50+技术伙伴支持。

**核心定位**: 代理间直接协作的标准协议

**通信基础**: JSON-RPC 2.0 over HTTPS

### 2.2 核心概念

**Agent Card (代理卡片)**:
```json
{
  "name": "Smart Travel Assistant",
  "description": "Professional travel planning service",
  "provider": "TravelTech Inc.",
  "url": "https://api.travelagent.com/a2a",
  "version": "1.0.0",
  "capabilities": ["streaming", "pushNotifications"],
  "authentication": {
    "schemes": ["Bearer"]
  },
  "skills": [
    {
      "id": "flight-booking",
      "name": "Flight Booking",
      "description": "Search and book flights",
      "inputModes": ["text", "data"],
      "outputModes": ["text", "data"]
    }
  ]
}
```

**发现机制**:
- 标准端点: `/.well-known/agent.json`
- 或注册到中心化A2A Registry

### 2.3 任务生命周期

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ submitted │ → │ working │ → │ completed │
│   (提交)   │    │ (处理中) │    │ (已完成) │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
      │              │              │
      ↓              ↓              ↓
   input         updates         result
  (输入)        (状态更新)        (结果)
```

**核心方法**:
| 方法 | 说明 |
|------|------|
| `tasks/send` | 同步发送任务 |
| `tasks/sendSubscribe` | 异步流式任务 (SSE) |
| `tasks/get` | 查询任务状态 |
| `tasks/cancel` | 取消任务 |

### 2.4 实现示例

**Python服务器**:
```python
from a2a import A2AServer, Task

class CurrencyAgent(A2AServer):
    async def handle_task(self, task: Task) -> Task:
        # 解析输入
        amount = task.input["amount"]
        from_curr = task.input["from"]
        to_curr = task.input["to"]
        
        # 执行转换
        result = await convert_currency(amount, from_curr, to_curr)
        
        # 返回结果
        task.output = {"result": result}
        task.status = "completed"
        return task

# 启动
agent = CurrencyAgent()
app = agent.app  # FastAPI应用
```

**客户端调用**:
```bash
# 1. 获取Agent Card
curl https://currency-agent:10000/.well-known/agent.json

# 2. 发送任务 (流式)
curl -X POST https://currency-agent:10000/tasks/sendSubscribe \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "input": {
      "amount": "50",
      "from": "USD",
      "to": "JPY"
    }
  }'
```

### 2.5 安全机制

**短生命周期认证**:
```json
{
  "authentication": {
    "schemes": ["Bearer"],
    "token_ttl": "5m"
  }
}
```

**每次调用携带Scoped Token**:
```bash
TOKEN=$(generate_token --ttl 5m --aud currency-agent)
curl -H "Authorization: Bearer $TOKEN" ...
```

### 2.6 与MCP的关系

| 维度 | MCP | A2A |
|------|-----|-----|
| **层级** | 工具/资源层 | 代理层 |
| **关系** | Client-Server | Peer-to-Peer |
| **关注点** | 能力暴露 | 协作协商 |
| **互补** | A2A代理可使用MCP工具 | MCP服务器可被A2A代理调用 |

**集成模式**:
```
A2A Agent A ──A2A协议──→ A2A Agent B
     │                       │
     └─MCP──→ MCP Server (工具)
```

---

## 三、SDK与工具生态

### 3.1 MCP SDK

| 语言 | 包名 | 状态 |
|------|------|------|
| Python | `mcp` / `fastmcp` | 官方 |
| TypeScript | `@modelcontextprotocol/sdk` | 官方 |
| Java | `mcp-java-sdk` | 官方 |
| C# | `ModelContextProtocol` | 官方 |

### 3.2 A2A SDK

| 语言 | 包名 | 状态 |
|------|------|------|
| Python | `a2a-python` | 官方 |
| JavaScript | `a2a-js` | 官方 |
| Java | `a2a-java` | 社区 |
| .NET | `A2A.NET` | 社区 |

### 3.3 调试工具

**MCP Inspector**:
- Anthropic官方GUI工具
- 测试服务器连接、工具调用

**A2A Inspector**:
- Web-based调试工具
- 实时检查Agent Card和JSON-RPC通信
- Agent Card可视化

---

## 四、实际部署考量

### 4.1 生产环境检查清单

**MCP**:
- [ ] 服务器认证与授权
- [ ] 输入验证与沙箱
- [ ] 超时与错误处理
- [ ] 日志与审计
- [ ] 速率限制

**A2A**:
- [ ] 短生命周期Token
- [ ] HTTPS强制
- [ ] Agent Card验证
- [ ] 任务超时管理
- [ ] 失败重试策略

### 4.2 性能优化

**MCP**:
- 无状态HTTP传输支持水平扩展
- 工具结果缓存
- 批量资源获取

**A2A**:
- 流式响应减少延迟
- 连接池复用
- Agent Card缓存

---

## 五、我的实现可能性分析

### 5.1 作为MCP Client

**可行**: 我可以作为MCP Host，连接外部MCP Servers

**需要的OpenClaw支持**:
```yaml
# 假设配置
mcp:
  servers:
    - name: filesystem
      command: npx -y @modelcontextprotocol/server-filesystem
      args: ["/home/user/workspace"]
    - name: github
      command: npx -y @modelcontextprotocol/server-github
      env:
        GITHUB_TOKEN: ${GITHUB_TOKEN}
```

**实现难度**: 中等 (需要SDK集成)

### 5.2 作为A2A Agent

**可行**: 我可以暴露A2A端点，与其他代理协作

**需要的OpenClaw支持**:
- HTTP服务器能力 (目前我有webhook接收能力)
- Agent Card生成
- 任务状态管理

**实现难度**: 较高 (需要持久化任务状态)

### 5.3 当前可行方案

**阶段1: 内部MCP模拟**
- 将我的Skills包装为内部MCP Tools
- 统一工具发现和调用接口

**阶段2: 顺序A2A模拟**
- 通过`sessions_spawn`创建"远程Agent"
- 通过`sessions_send`发送"任务"
- 模拟A2A的消息模式

---

## 六、结论与行动建议

### 关键洞察

1. **MCP**已成为事实标准 (OpenAI、Google、Microsoft均支持)
2. **A2A**补充MCP，专注代理间协作
3. **两者结合**是完整的互操作方案
4. **2026年**将全面普及

### 我的演进路径

| 阶段 | 目标 | 时间 |
|------|------|------|
| 1 | 内部工具MCP化 | 短期 |
| 2 | 多会话A2A模拟 | 中期 |
| 3 | 原生协议支持 | 长期 |

### 立即行动

是否要我：
1. **设计我的内部MCP接口**？
2. **创建一个A2A模拟演示**（多会话协作）？
3. **实现一个具体协议客户端**（如连接GitHub MCP Server）？
