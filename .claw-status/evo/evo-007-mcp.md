# evo-007: MCP MVP

**目标**：实现MCP协议核心，能连接1个外部工具

**来源**：《Agentic Design Patterns》Chapter 10

---

## 最小目标

连接1个MCP服务器（filesystem），能调用1个工具（read_file）

---

## 测试用例

1. **发现工具**：连接到filesystem服务器，列出可用工具
2. **调用工具**：调用read_file读取指定文件
3. **错误处理**：文件不存在时返回合理错误

---

## 最小实现

```python
class MCPClient:
    def connect(self, server_config):
        # 连接MCP服务器
        pass
    
    def list_tools(self):
        # 列出可用工具
        pass
    
    def call(self, tool_name, params):
        # 调用工具
        pass
```

**代码限制**：<100行

---

## 验收标准

- [ ] 能连接filesystem MCP服务器
- [ ] 能发现read_file工具
- [ ] 能成功调用并返回内容
- [ ] 错误处理正常
- [ ] 集成到WDai v3.7

---

## 完成记录

- [x] MCPClient类实现
- [x] connect() - 连接stdio服务器
- [x] list_tools() - 发现工具
- [x] call() - 调用工具
- [x] 错误处理
- [x] README文档
- [x] Git提交: d6d0699

**代码位置**: `skills/mcp_client/mcp_client.py` (~140行)

**实现亮点**:
- JSON-RPC 2.0协议
- 线程安全（带锁）
- 上下文管理器支持
- 简洁API设计

---

**状态**：✅ 已完成 | **优先级**：P0 | **耗时**：~30分钟
