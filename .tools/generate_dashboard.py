#!/usr/bin/env python3
"""生成仪表盘 HTML 报告"""

import psutil
from pathlib import Path
from datetime import datetime

# 收集指标
WORKSPACE = Path('/root/.openclaw/workspace')

cpu = psutil.cpu_percent(interval=1)
memory = psutil.virtual_memory()
disk = psutil.disk_usage('/')

tools_dir = WORKSPACE / '.tools'
skills = [f.stem for f in tools_dir.glob('*.py')]

cpu_width = min(cpu, 100)
mem_used = memory.used // (1024**3)
mem_total = memory.total // (1024**3)
disk_used = disk.used // (1024**3)
disk_total = disk.total // (1024**3)

skill_tags = ''.join([f'<span class="skill-tag">{s}</span>' for s in skills[:12]])
more_text = f'<div style="margin-top: 10px; color: #64748b; font-size: 12px;">+{len(skills) - 12} more...</div>' if len(skills) > 12 else ''

html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>OpenClaw Command Center - 实时仪表盘</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #e2e8f0;
            padding: 30px;
            margin: 0;
            min-height: 100vh;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            border-radius: 16px;
            border: 1px solid #475569;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}
        .header h1 {{
            font-size: 32px;
            background: linear-gradient(90deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 25px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        .card {{
            background: rgba(30, 41, 59, 0.8);
            border-radius: 16px;
            padding: 25px;
            border: 1px solid #334155;
        }}
        .card h2 {{
            font-size: 14px;
            text-transform: uppercase;
            color: #94a3b8;
            margin-bottom: 20px;
            letter-spacing: 1px;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #334155;
        }}
        .metric:last-child {{ border-bottom: none; }}
        .metric-value {{
            font-size: 28px;
            font-weight: bold;
            color: #60a5fa;
        }}
        .progress-bar {{
            width: 100%;
            height: 10px;
            background: #334155;
            border-radius: 5px;
            overflow: hidden;
            margin-top: 10px;
        }}
        .progress-fill {{
            height: 100%;
            border-radius: 5px;
        }}
        .cpu {{ background: linear-gradient(90deg, #f59e0b, #ef4444); }}
        .memory {{ background: linear-gradient(90deg, #10b981, #3b82f6); }}
        .disk {{ background: linear-gradient(90deg, #8b5cf6, #ec4899); }}
        .skill-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 15px;
        }}
        .skill-tag {{
            background: linear-gradient(135deg, #334155, #475569);
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            border: 1px solid #475569;
        }}
        .timestamp {{
            text-align: center;
            color: #64748b;
            font-size: 14px;
            margin-top: 30px;
        }}
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #10b981;
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 OpenClaw Command Center</h1>
        <p style="color: #94a3b8;">实时监控仪表盘 | 系统运行中</p>
        <div style="margin-top: 15px;">
            <span class="status-badge">● Online</span>
        </div>
    </div>
    
    <div class="grid">
        <div class="card">
            <h2>🖥️ 系统资源</h2>
            <div class="metric">
                <span>CPU 使用率</span>
                <span class="metric-value">{cpu:.1f}%</span>
            </div>
            <div class="progress-bar"><div class="progress-fill cpu" style="width: {cpu_width}%"></div></div>
            
            <div class="metric" style="margin-top: 20px;">
                <span>内存使用</span>
                <span>{mem_used} / {mem_total} GB</span>
            </div>
            <div class="progress-bar"><div class="progress-fill memory" style="width: {memory.percent}%"></div></div>
            
            <div class="metric" style="margin-top: 20px;">
                <span>磁盘使用</span>
                <span>{disk_used} / {disk_total} GB</span>
            </div>
            <div class="progress-bar"><div class="progress-fill disk" style="width: {disk.percent}%"></div></div>
        </div>
        
        <div class="card">
            <h2>💰 成本估算</h2>
            <div class="metric">
                <span>总 Token 数</span>
                <span class="metric-value">0</span>
            </div>
            <div class="metric">
                <span>预估成本 (USD)</span>
                <span style="color: #10b981; font-weight: bold;">$0.0000</span>
            </div>
            <div class="metric">
                <span>预估成本 (CNY)</span>
                <span style="color: #10b981; font-weight: bold;">¥0.0000</span>
            </div>
        </div>
        
        <div class="card">
            <h2>🛠️ Skill 工具箱 ({len(skills)} 个)</h2>
            <div class="skill-list">
                {skill_tags}
            </div>
            {more_text}
        </div>
        
        <div class="card">
            <h2>📊 系统概览</h2>
            <div class="metric">
                <span>活跃会话</span>
                <span class="metric-value">1</span>
            </div>
            <div class="metric">
                <span>MCP 服务器</span>
                <span class="metric-value">6</span>
            </div>
            <div class="metric">
                <span>专家类型</span>
                <span class="metric-value">7</span>
            </div>
            <div style="margin-top: 15px; padding: 10px; background: #1e293b; border-radius: 8px; font-size: 12px;">
                <div style="color: #64748b; margin-bottom: 5px;">已部署能力:</div>
                <div style="display: flex; flex-wrap: wrap; gap: 5px;">
                    <span style="background: #334155; padding: 3px 8px; border-radius: 4px;">Crawl4AI</span>
                    <span style="background: #334155; padding: 3px 8px; border-radius: 4px;">Stagehand</span>
                    <span style="background: #334155; padding: 3px 8px; border-radius: 4px;">Docling</span>
                    <span style="background: #334155; padding: 3px 8px; border-radius: 4px;">Manus编排</span>
                    <span style="background: #334155; padding: 3px 8px; border-radius: 4px;">Skill-MoE</span>
                </div>
            </div>
        </div>
    </div>
    
    <div class="timestamp">
        最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</body>
</html>'''

output_path = Path('/root/.openclaw/workspace/.command-center/dashboard.html')
output_path.parent.mkdir(exist_ok=True)
output_path.write_text(html, encoding='utf-8')

print(f'✅ 仪表盘已生成: {output_path}')
print(f'   文件大小: {output_path.stat().st_size / 1024:.1f} KB')
print(f'   Skills: {len(skills)} 个')
print(f'   CPU: {cpu:.1f}% | 内存: {memory.percent}% | 磁盘: {disk.percent}%')
