#!/usr/bin/env python3
"""
OpenClaw Command Center (Lite) - 简化版任务控制中心

基于 jontsai/openclaw-command-center 核心功能实现的 Python 版本
提供实时监控、成本追踪和系统状态仪表盘

用法:
    python3 command_center_lite.py [--port 8080]
    
然后访问 http://localhost:8080
"""

import json
import os
import sys
import time
import psutil
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading

# 配置
WORKSPACE = Path("/root/.openclaw/workspace")
LOG_DIR = WORKSPACE / ".logs"

class OpenClawMetrics:
    """OpenClaw 指标收集器"""
    
    def __init__(self):
        self.session_count = 0
        self.total_cost = 0.0
        self.total_tokens = 0
        self.active_agents = []
        
    def get_system_stats(self):
        """获取系统资源统计"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "cores": psutil.cpu_count()
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "percent": round(disk.used / disk.total * 100, 1)
            }
        }
    
    def get_session_stats(self):
        """获取会话统计"""
        # 扫描 workspace 中的会话文件
        sessions = []
        for jsonl_file in WORKSPACE.glob("*.jsonl"):
            if jsonl_file.stat().st_size > 0:
                sessions.append({
                    "id": jsonl_file.stem[:8],
                    "size_mb": round(jsonl_file.stat().st_size / (1024*1024), 2),
                    "modified": datetime.fromtimestamp(jsonl_file.stat().st_mtime).isoformat()
                })
        
        return {
            "active_sessions": len(sessions),
            "sessions": sessions[-10:]  # 最近10个
        }
    
    def get_skill_stats(self):
        """获取 Skill 使用统计"""
        tools_dir = WORKSPACE / ".tools"
        skills = []
        
        if tools_dir.exists():
            for py_file in tools_dir.glob("*.py"):
                skills.append({
                    "name": py_file.stem,
                    "size_kb": round(py_file.stat().st_size / 1024, 2)
                })
        
        return {
            "total_skills": len(skills),
            "skills": skills
        }
    
    def get_cost_estimate(self):
        """估算成本"""
        # 基于 token 使用量估算
        # 假设: $0.001 per 1K tokens (Kimi 定价)
        estimated_cost = self.total_tokens * 0.000001
        
        return {
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": round(estimated_cost, 4),
            "estimated_cost_cny": round(estimated_cost * 7.2, 4)
        }
    
    def get_all_metrics(self):
        """获取所有指标"""
        return {
            "timestamp": datetime.now().isoformat(),
            "system": self.get_system_stats(),
            "sessions": self.get_session_stats(),
            "skills": self.get_skill_stats(),
            "cost": self.get_cost_estimate()
        }


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器"""
    
    metrics = OpenClawMetrics()
    
    def do_GET(self):
        """处理 GET 请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/' or path == '/index.html':
            self.serve_dashboard()
        elif path == '/api/metrics':
            self.serve_metrics()
        elif path == '/api/sse':
            self.serve_sse()
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        """服务仪表盘 HTML"""
        html = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>OpenClaw Command Center (Lite)</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            border-radius: 12px;
            border: 1px solid #475569;
        }
        .header h1 {
            font-size: 28px;
            background: linear-gradient(90deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: #1e293b;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #334155;
        }
        .card h2 {
            font-size: 14px;
            text-transform: uppercase;
            color: #94a3b8;
            margin-bottom: 15px;
            letter-spacing: 0.5px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #334155;
        }
        .metric:last-child { border-bottom: none; }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #60a5fa;
        }
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #334155;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 8px;
        }
        .progress-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        .progress-fill.cpu { background: linear-gradient(90deg, #f59e0b, #ef4444); }
        .progress-fill.memory { background: linear-gradient(90deg, #10b981, #3b82f6); }
        .progress-fill.disk { background: linear-gradient(90deg, #8b5cf6, #ec4899); }
        .status-online {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: #10b981;
            font-size: 12px;
        }
        .status-online::before {
            content: '';
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .skill-tag {
            display: inline-block;
            background: #334155;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            margin: 4px;
        }
        .timestamp {
            text-align: center;
            color: #64748b;
            font-size: 12px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 OpenClaw Command Center (Lite)</h1>
        <p>实时监控仪表盘 | MIT License</p>
        <span class="status-online">● 系统运行中</span>
    </div>
    
    <div class="grid">
        <div class="card">
            <h2>🖥️ 系统资源</h2>
            <div id="system-metrics"></div>
        </div>
        
        <div class="card">
            <h2>💰 成本估算</h2>
            <div id="cost-metrics"></div>
        </div>
        
        <div class="card">
            <h2>🤖 会话状态</h2>
            <div id="session-metrics"></div>
        </div>
        
        <div class="card">
            <h2>🛠️ Skill 工具箱</h2>
            <div id="skill-metrics"></div>
        </div>
    </div>
    
    <div class="timestamp">
        上次更新: <span id="last-update">--</span>
    </div>
    
    <script>
        async function fetchMetrics() {
            try {
                const response = await fetch('/api/metrics');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('获取指标失败:', error);
            }
        }
        
        function updateDashboard(data) {
            // 系统资源
            const sys = data.system;
            document.getElementById('system-metrics').innerHTML = `
                <div class="metric">
                    <span>CPU 使用率</span>
                    <span class="metric-value">${sys.cpu.percent.toFixed(1)}%</span>
                </div>
                <div class="progress-bar"><div class="progress-fill cpu" style="width: ${sys.cpu.percent}%"></div></div>
                <div class="metric" style="margin-top: 15px;">
                    <span>内存使用</span>
                    <span>${sys.memory.used_gb} / ${sys.memory.total_gb} GB</span>
                </div>
                <div class="progress-bar"><div class="progress-fill memory" style="width: ${sys.memory.percent}%"></div></div>
                <div class="metric" style="margin-top: 15px;">
                    <span>磁盘使用</span>
                    <span>${sys.disk.used_gb} / ${sys.disk.total_gb} GB</span>
                </div>
                <div class="progress-bar"><div class="progress-fill disk" style="width: ${sys.disk.percent}%"></div></div>
            `;
            
            // 成本
            const cost = data.cost;
            document.getElementById('cost-metrics').innerHTML = `
                <div class="metric">
                    <span>总 Token 数</span>
                    <span class="metric-value">${cost.total_tokens.toLocaleString()}</span>
                </div>
                <div class="metric">
                    <span>预估成本 (USD)</span>
                    <span style="color: #10b981; font-weight: bold;">$${cost.estimated_cost_usd}</span>
                </div>
                <div class="metric">
                    <span>预估成本 (CNY)</span>
                    <span style="color: #10b981; font-weight: bold;">¥${cost.estimated_cost_cny}</span>
                </div>
            `;
            
            // 会话
            const sessions = data.sessions;
            document.getElementById('session-metrics').innerHTML = `
                <div class="metric">
                    <span>活跃会话数</span>
                    <span class="metric-value">${sessions.active_sessions}</span>
                </div>
                <div style="margin-top: 10px; font-size: 12px; color: #64748b;">
                    ${sessions.sessions.map(s => `<div style="padding: 5px 0; border-bottom: 1px solid #334155;">
                        ${s.id} | ${s.size_mb} MB
                    </div>`).join('')}
                </div>
            `;
            
            // Skills
            const skills = data.skills;
            document.getElementById('skill-metrics').innerHTML = `
                <div class="metric">
                    <span>总 Skill 数</span>
                    <span class="metric-value">${skills.total_skills}</span>
                </div>
                <div style="margin-top: 10px;">
                    ${skills.skills.slice(0, 10).map(s => `
                        <span class="skill-tag">${s.name}</span>
                    `).join('')}
                    ${skills.total_skills > 10 ? `<span style="color: #64748b;">+${skills.total_skills - 10} more</span>` : ''}
                </div>
            `;
            
            document.getElementById('last-update').textContent = new Date().toLocaleString();
        }
        
        // 初始加载和定时刷新
        fetchMetrics();
        setInterval(fetchMetrics, 2000);
    </script>
</body>
</html>
        '''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_metrics(self):
        """服务指标数据 (JSON)"""
        metrics = self.metrics.get_all_metrics()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(metrics, ensure_ascii=False).encode())
    
    def serve_sse(self):
        """服务 Server-Sent Events (实时更新)"""
        self.send_response(200)
        self.send_header('Content-type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # 发送初始数据
        for _ in range(10):  # 发送10次更新
            metrics = self.metrics.get_all_metrics()
            data = json.dumps(metrics, ensure_ascii=False)
            self.wfile.write(f"data: {data}\n\n".encode())
            self.wfile.flush()
            time.sleep(2)
    
    def log_message(self, format, *args):
        """简化日志输出"""
        pass  # 减少控制台噪音


def run_server(port=8080):
    """启动服务器"""
    server = HTTPServer(('0.0.0.0', port), DashboardHandler)
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  🎯 OpenClaw Command Center (Lite)                           ║
║  实时监控仪表盘                                              ║
╠══════════════════════════════════════════════════════════════╣
║  访问地址: http://localhost:{port}                            ║
║                                                              ║
║  功能:                                                       ║
║  • 实时系统监控 (CPU/内存/磁盘)                              ║
║  • 会话状态追踪                                              ║
║  • Skill 工具箱概览                                          ║
║  • Token 成本估算                                            ║
║                                                              ║
║  按 Ctrl+C 停止服务                                          ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 服务已停止")
        server.shutdown()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenClaw Command Center (Lite)")
    parser.add_argument("--port", type=int, default=8080, help="服务端口号")
    args = parser.parse_args()
    
    # 检查 psutil
    try:
        import psutil
    except ImportError:
        print("📦 正在安装依赖 psutil...")
        os.system(f"{sys.executable} -m pip install psutil -q --break-system-packages")
        import psutil
    
    run_server(args.port)
