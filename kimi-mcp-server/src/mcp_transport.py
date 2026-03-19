# Kimi MCP Server - Phase 3 Transport Implementation
# MCP Transport层实现：stdio + HTTP

import json
import sys
import asyncio
from typing import Optional, Dict, Any, AsyncIterator
from dataclasses import dataclass
from datetime import datetime
import socket
import threading

# 导入所有Tools
from extended_tools import KimiMCPExtendedServer


@dataclass
class MCPRequest:
    """MCP请求数据类"""
    jsonrpc: str
    id: Optional[int]
    method: str
    params: Dict[str, Any]


@dataclass
class MCPResponse:
    """MCP响应数据类"""
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    result: Optional[Dict] = None
    error: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        data = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.result is not None:
            data["result"] = self.result
        if self.error is not None:
            data["error"] = self.error
        return data


class MCPProtocolHandler:
    """MCP协议处理器"""
    
    def __init__(self, server: KimiMCPExtendedServer):
        self.server = server
        self.initialized = False
        self.client_capabilities = {}
    
    def handle_request(self, request_dict: Dict) -> MCPResponse:
        """处理MCP请求"""
        try:
            # 验证JSON-RPC格式
            if request_dict.get("jsonrpc") != "2.0":
                return MCPResponse(
                    id=request_dict.get("id"),
                    error={"code": -32600, "message": "Invalid Request"}
                )
            
            method = request_dict.get("method")
            req_id = request_dict.get("id")
            params = request_dict.get("params", {})
            
            # 路由到对应处理方法
            handlers = {
                "initialize": self._handle_initialize,
                "initialized": self._handle_initialized,
                "tools/list": self._handle_tools_list,
                "tools/call": self._handle_tools_call,
                "resources/list": self._handle_resources_list,
                "resources/read": self._handle_resources_read,
                "prompts/list": self._handle_prompts_list,
                "prompts/get": self._handle_prompts_get,
            }
            
            handler = handlers.get(method)
            if handler:
                return handler(req_id, params)
            else:
                return MCPResponse(
                    id=req_id,
                    error={"code": -32601, "message": f"Method not found: {method}"}
                )
        
        except Exception as e:
            return MCPResponse(
                id=request_dict.get("id"),
                error={"code": -32603, "message": f"Internal error: {str(e)}"}
            )
    
    def _handle_initialize(self, req_id: Optional[int], params: Dict) -> MCPResponse:
        """处理initialize请求"""
        self.client_capabilities = params.get("capabilities", {})
        
        result = {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "kimi-mcp-server",
                "version": "2.0.0"
            },
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {}
            }
        }
        
        return MCPResponse(id=req_id, result=result)
    
    def _handle_initialized(self, req_id: Optional[int], params: Dict) -> MCPResponse:
        """处理initialized通知"""
        self.initialized = True
        # 通知不需要响应
        return MCPResponse(id=req_id, result={})
    
    def _handle_tools_list(self, req_id: Optional[int], params: Dict) -> MCPResponse:
        """处理tools/list请求"""
        tools = self.server.list_all_tools()
        
        # 转换为MCP标准格式
        mcp_tools = []
        for tool in tools:
            mcp_tool = {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "inputSchema": {
                    "type": "object",
                    "properties": tool.get("parameters", {})
                }
            }
            mcp_tools.append(mcp_tool)
        
        return MCPResponse(id=req_id, result={"tools": mcp_tools})
    
    def _handle_tools_call(self, req_id: Optional[int], params: Dict) -> MCPResponse:
        """处理tools/call请求"""
        tool_name = params.get("name")
        tool_params = params.get("arguments", {})
        
        # 调用Tool
        result = self.server.call_tool(tool_name, tool_params)
        
        # 转换为MCP格式
        if result.get("success"):
            mcp_result = {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2, ensure_ascii=False)
                    }
                ],
                "isError": False
            }
        else:
            mcp_result = {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: {result.get('error')}"
                    }
                ],
                "isError": True
            }
        
        return MCPResponse(id=req_id, result=mcp_result)
    
    def _handle_resources_list(self, req_id: Optional[int], params: Dict) -> MCPResponse:
        """处理resources/list请求"""
        resources = [
            {
                "uri": "memory://long-term",
                "name": "Long-term Memory",
                "mimeType": "application/json"
            },
            {
                "uri": "workspace://files",
                "name": "Workspace Files",
                "mimeType": "text/plain"
            }
        ]
        return MCPResponse(id=req_id, result={"resources": resources})
    
    def _handle_resources_read(self, req_id: Optional[int], params: Dict) -> MCPResponse:
        """处理resources/read请求"""
        uri = params.get("uri")
        
        # 简化实现
        if uri == "memory://long-term":
            result = self.server.call_tool("agent_memory_search", {"query": "", "max_results": 10})
            content = json.dumps(result, indent=2)
        else:
            content = f"Resource {uri} not implemented"
        
        return MCPResponse(id=req_id, result={
            "contents": [{"uri": uri, "mimeType": "text/plain", "text": content}]
        })
    
    def _handle_prompts_list(self, req_id: Optional[int], params: Dict) -> MCPResponse:
        """处理prompts/list请求"""
        prompts = [
            {
                "name": "deep_research",
                "description": "深度研究模式"
            },
            {
                "name": "code_review",
                "description": "代码审查模式"
            }
        ]
        return MCPResponse(id=req_id, result={"prompts": prompts})
    
    def _handle_prompts_get(self, req_id: Optional[int], params: Dict) -> MCPResponse:
        """处理prompts/get请求"""
        prompt_name = params.get("name")
        
        prompts = {
            "deep_research": {
                "description": "深度研究模式",
                "messages": [
                    {
                        "role": "system",
                        "content": {
                            "type": "text",
                            "text": "你是一个专业研究员。请对以下主题进行深度研究：1)使用System 2慢路径思考 2)至少使用3个不同来源 3)提供结构化报告"
                        }
                    }
                ]
            }
        }
        
        return MCPResponse(id=req_id, result=prompts.get(prompt_name, {}))


class StdioTransport:
    """Stdio传输实现"""
    
    def __init__(self, protocol_handler: MCPProtocolHandler):
        self.protocol = protocol_handler
        self.running = False
    
    def run(self):
        """运行stdio服务器"""
        self.running = True
        
        # 发送服务器就绪信息（可选）
        sys.stderr.write("Kimi MCP Server (stdio) started\n")
        sys.stderr.flush()
        
        while self.running:
            try:
                # 读取一行输入
                line = sys.stdin.readline()
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # 解析JSON请求
                try:
                    request_dict = json.loads(line)
                except json.JSONDecodeError as e:
                    self._send_error(None, -32700, f"Parse error: {e}")
                    continue
                
                # 处理请求
                response = self.protocol.handle_request(request_dict)
                
                # 发送响应（如果是请求而非通知）
                if request_dict.get("id") is not None:
                    self._send_response(response)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                sys.stderr.write(f"Error: {e}\n")
                sys.stderr.flush()
    
    def _send_response(self, response: MCPResponse):
        """发送响应"""
        response_json = json.dumps(response.to_dict(), ensure_ascii=False)
        sys.stdout.write(response_json + "\n")
        sys.stdout.flush()
    
    def _send_error(self, req_id: Optional[int], code: int, message: str):
        """发送错误响应"""
        response = MCPResponse(
            id=req_id,
            error={"code": code, "message": message}
        )
        self._send_response(response)


class HTTPTransport:
    """HTTP传输实现（使用纯Python）"""
    
    def __init__(self, protocol_handler: MCPProtocolHandler, host: str = "127.0.0.1", port: int = 8080):
        self.protocol = protocol_handler
        self.host = host
        self.port = port
        self.server = None
    
    async def run(self):
        """运行HTTP服务器"""
        import socket
        import threading
        
        # 创建socket服务器
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(5)
        
        print(f"Kimi MCP Server (HTTP) started on http://{self.host}:{self.port}")
        print(f"MCP Endpoint: http://{self.host}:{self.port}/mcp")
        print(f"Health Check: http://{self.host}:{self.port}/health")
        
        try:
            while True:
                client, addr = sock.accept()
                # 为每个客户端创建线程
                thread = threading.Thread(target=self._handle_client, args=(client,))
                thread.daemon = True
                thread.start()
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            sock.close()
    
    def _handle_client(self, client: socket.socket):
        """处理HTTP客户端请求"""
        try:
            # 接收HTTP请求
            data = client.recv(4096).decode('utf-8')
            
            if not data:
                return
            
            # 解析HTTP请求
            lines = data.split('\r\n')
            request_line = lines[0]
            parts = request_line.split()
            
            if len(parts) < 2:
                self._send_http_response(client, 400, "Bad Request")
                return
            
            method = parts[0]
            path = parts[1]
            
            # 路由处理
            if path == "/health":
                self._handle_health(client)
            elif path == "/mcp":
                self._handle_mcp(client, method, lines, data)
            elif path == "/":
                self._handle_root(client)
            else:
                self._send_http_response(client, 404, "Not Found")
        
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client.close()
    
    def _handle_health(self, client: socket.socket):
        """健康检查端点"""
        stats = self.protocol.server.get_stats()
        health = {
            "status": "healthy",
            "server": "kimi-mcp-server",
            "version": "2.0.0",
            "tools_count": stats['total_tools'],
            "timestamp": datetime.now().isoformat()
        }
        self._send_json_response(client, 200, health)
    
    def _handle_root(self, client: socket.socket):
        """根路径"""
        info = {
            "name": "Kimi MCP Server",
            "version": "2.0.0",
            "description": "MCP Server with 23 Tools",
            "endpoints": {
                "/mcp": "MCP Protocol Endpoint (POST)",
                "/health": "Health Check (GET)"
            }
        }
        self._send_json_response(client, 200, info)
    
    def _handle_mcp(self, client: socket.socket, method: str, lines: list, raw_data: str):
        """MCP协议端点"""
        if method != "POST":
            self._send_http_response(client, 405, "Method Not Allowed")
            return
        
        # 提取请求体
        try:
            # 查找Content-Length
            content_length = 0
            for line in lines:
                if line.lower().startswith("content-length:"):
                    content_length = int(line.split(":")[1].strip())
                    break
            
            if content_length > 0:
                # 从raw_data提取body
                header_end = raw_data.find('\r\n\r\n')
                if header_end != -1:
                    body = raw_data[header_end + 4:header_end + 4 + content_length]
                else:
                    body = "{}"
            else:
                body = "{}"
            
            # 解析JSON-RPC请求
            request_dict = json.loads(body)
            
            # 处理请求
            response = self.protocol.handle_request(request_dict)
            
            # 发送响应
            self._send_json_response(client, 200, response.to_dict())
        
        except json.JSONDecodeError as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"}
            }
            self._send_json_response(client, 400, error_response)
        
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Internal error: {e}"}
            }
            self._send_json_response(client, 500, error_response)
    
    def _send_json_response(self, client: socket.socket, status_code: int, data: Dict):
        """发送JSON响应"""
        body = json.dumps(data, indent=2, ensure_ascii=False)
        self._send_http_response(client, status_code, body, content_type="application/json")
    
    def _send_http_response(self, client: socket.socket, status_code: int, body: str, content_type: str = "text/plain"):
        """发送HTTP响应"""
        status_text = {200: "OK", 400: "Bad Request", 404: "Not Found", 405: "Method Not Allowed", 500: "Internal Server Error"}.get(status_code, "Unknown")
        
        response = f"HTTP/1.1 {status_code} {status_text}\r\n"
        response += f"Content-Type: {content_type}; charset=utf-8\r\n"
        response += f"Content-Length: {len(body.encode('utf-8'))}\r\n"
        response += "Connection: close\r\n"
        response += "\r\n"
        response += body
        
        client.sendall(response.encode('utf-8'))


class MCPTransportServer:
    """MCP传输服务器主类"""
    
    def __init__(self, transport_type: str = "stdio", host: str = "127.0.0.1", port: int = 8080):
        self.transport_type = transport_type
        self.host = host
        self.port = port
        
        # 创建服务器和协议处理器
        self.server = KimiMCPExtendedServer()
        self.protocol = MCPProtocolHandler(self.server)
    
    def run(self):
        """运行服务器"""
        if self.transport_type == "stdio":
            transport = StdioTransport(self.protocol)
            transport.run()
        
        elif self.transport_type == "http":
            transport = HTTPTransport(self.protocol, self.host, self.port)
            asyncio.run(transport.run())
        
        else:
            print(f"Unknown transport type: {self.transport_type}")
            sys.exit(1)


# 命令行入口
def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Kimi MCP Server")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio",
                       help="Transport type (default: stdio)")
    parser.add_argument("--host", default="127.0.0.1",
                       help="HTTP host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080,
                       help="HTTP port (default: 8080)")
    
    args = parser.parse_args()
    
    # 创建并运行服务器
    mcp_server = MCPTransportServer(
        transport_type=args.transport,
        host=args.host,
        port=args.port
    )
    
    mcp_server.run()


if __name__ == "__main__":
    main()
