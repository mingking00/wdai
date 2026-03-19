#!/usr/bin/env python3
"""
直接运行 Agent Kernel 测试
不通过 OpenClaw exec 工具
"""

import sys
import os
import subprocess
import time

# 切换到工作目录
os.chdir('/root/.openclaw/workspace/.wdai-runtime')

# 设置 Python 路径
sys.path.insert(0, '/root/.openclaw/workspace/.wdai-runtime')

# 现在导入并运行
from agent_kernel import get_kernel

print('=' * 60)
print('Agent Kernel 测试')
print('=' * 60)
print()

# 创建并启动内核
print('🚀 启动内核...')
kernel = get_kernel()
kernel.start()
print('✅ 内核已启动')
print()

# 提交任务
print('📋 提交任务...')
task1 = kernel.submit_task('code', '部署博客', {'method': 'git_push'})
task2 = kernel.submit_task('research', '搜索资料', {'method': 'web_search'})
task3 = kernel.submit_task('code', '尝试github_api', {'method': 'github_api'})
print(f'  - 任务1: {task1[:8]} (git_push)')
print(f'  - 任务2: {task2[:8]} (web_search)')
print(f'  - 任务3: {task3[:8]} (github_api - 预期失败)')
print()

# 等待执行
print('⏳ 等待任务执行 (8秒)...')
time.sleep(8)

# 查看状态
print()
print('=' * 60)
print('执行结果')
print('=' * 60)

status = kernel.get_status()
print()
print('📊 Agent 统计:')
for aid, agent in status['agents'].items():
    completed = agent['stats']['tasks_completed']
    failed = agent['stats']['tasks_failed']
    if completed > 0 or failed > 0:
        print(f'  {aid:12} 完成:{completed} 失败:{failed}')

print()
print('📋 任务统计:')
print(f'  待处理: {status["tasks"]["pending"]}')
print(f'  活跃:   {status["tasks"]["active"]}')
print(f'  已完成: {status["tasks"]["completed"]}')

# 停止内核
print()
print('🛑 停止内核...')
kernel.stop()

print()
print('=' * 60)
print('✅ 测试完成')
print('=' * 60)
