"""
MCP Client MVP

最小MCP协议实现，支持连接filesystem服务器
"""

import json
import subprocess
import threading
import time
from typing import Dict, List, Optional, Any


class MCPClient:
    """MCP协议客户端 - 最小实现"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.tools: List[Dict] = []
        self.message_id = 0
        self._lock = threading.Lock()
    
    def connect(self, command: List[str], env: Optional[Dict] = None) -> bool:
        """
        连接MCP服务器
        
        Args:
            command: 启动服务器的命令，如 ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
            env: 环境变量
        """
        try:
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            
            # 发送初始化请求
            init_result = self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "wdai-mcp", "version": "0.1.0"}
            })
            
            if init_result:
                # 获取工具列表
                self._refresh_tools()
                return True
            
            return False
            
        except Exception as e:
            print(f"连接失败: {e}")
            return False
    
    def _send_request(self, method: str, params: Dict) -> Optional[Dict]:
        """发送JSON-RPC请求"""
        with self._lock:
            self.message_id += 1
            msg_id = self.message_id
        
        request = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": method,
            "params": params
        }
        
        try:
            # 发送请求
            request_line = json.dumps(request) + "\n"
            self.process.stdin.write(request_line)
            self.process.stdin.flush()
            
            # 读取响应（简化版，假设响应在一行内）
            response_line = self.process.stdout.readline()
            if not response_line:
                return None
            
            response = json.loads(response_line)
            return response.get("result")
            
        except Exception as e:
            print(f"请求失败: {e}")
            return None
    
    def _refresh_tools(self):
        """刷新工具列表"""
        result = self._send_request("tools/list", {})
        if result:
            self.tools = result.get("tools", [])
    
    def list_tools(self) -> List[Dict]:
        """列出可用工具"""
        return self.tools
    
    def call(self, tool_name: str, params: Dict[str, Any]) -> Optional[Dict]:
        """
        调用工具
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            
        Returns:
            工具执行结果
        """
        result = self._send_request("tools/call", {
            "name": tool_name,
            "arguments": params
        })
        
        if result:
            # 解析工具结果
            content = result.get("content", [])
            if content:
                return {
                    "success": True,
                    "content": content[0].get("text", "") if content else "",
                    "raw": result
                }
        
        return {"success": False, "error": "调用失败"}
    
    def disconnect(self):
        """断开连接"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            self.process = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


# 便捷函数
def create_filesystem_client(path: str = "/tmp") -> MCPClient:
    """创建filesystem MCP客户端"""
    client = MCPClient()
    success = client.connect([
        "npx", "-y", "@modelcontextprotocol/server-filesystem",
        path
    ])
    return client if success else None


if __name__ == "__main__":
    # 测试用例
    print("=" * 50)
    print("MCP Client MVP 测试")
    print("=" * 50)
    
    # 注意：需要Node.js环境
    client = MCPClient()
    
    # 尝试连接（如果npx不可用会失败）
    print("\n1. 连接测试")
    if client.connect(["echo", "MCP服务器未安装"]):
        print("   ✓ 连接成功")
        
        print("\n2. 工具发现")
        tools = client.list_tools()
        print(f"   发现 {len(tools)} 个工具")
        for tool in tools[:3]:  # 只显示前3个
            print(f"   - {tool.get('name', 'unknown')}")
        
        print("\n3. 断开连接")
        client.disconnect()
        print("   ✓ 断开成功")
    else:
        print("   ℹ 连接失败（需要安装MCP服务器）")
    
    print("\n" + "=" * 50)
    print("MCP Client MVP 实现完成")
    print("=" * 50)
