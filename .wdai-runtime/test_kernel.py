#!/usr/bin/env python3
"""
Agent Kernel 测试脚本
直接运行，不通过exec工具
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.wdai-runtime')

from agent_kernel import get_kernel
import time

print('=== Agent Kernel 测试 ===')
print()

# 创建并启动内核
kernel = get_kernel()
kernel.start()

print('✅ 内核已启动')
print()

# 提交任务
print('📋 提交任务 1: 部署博客（git_push）')
task1 = kernel.submit_task('code', '部署博客到GitHub', {'method': 'git_push'})

print('📋 提交任务 2: 搜索资料（web_search）')
task2 = kernel.submit_task('research', '搜索最新AI论文', {'method': 'web_search'})

print('📋 提交任务 3: 尝试github_api（预期失败）')
task3 = kernel.submit_task('code', '尝试github_api部署', {'method': 'github_api'})

print()
print('⏳ 等待任务执行（约8秒）...')
time.sleep(8)

# 查看状态
print()
print('=== 执行结果 ===')
status = kernel.get_status()

print()
print('📊 Agent统计:')
for aid, agent in status['agents'].items():
    if agent['stats']['tasks_completed'] > 0 or agent['stats']['tasks_failed'] > 0:
        print(f'  {aid}: 完成{agent["stats"]["tasks_completed"]} 失败{agent["stats"]["tasks_failed"]}')

print()
print('📋 任务统计:')
print(f'  待处理: {status["tasks"]["pending"]}')
print(f'  活跃: {status["tasks"]["active"]}')
print(f'  已完成: {status["tasks"]["completed"]}')

# 停止内核
kernel.stop()

print()
print('✅ 测试完成')
print()
print('💡 说明:')
print('  - git_push 和 web_search 任务应该成功')
print('  - github_api 任务应该失败（因为方法被锁定）')
print('  - Coordinator自动分配任务给Coder')
print('  - Coder执行后Reviewer自动检查')
print('  - 失败时Reflector和Evolution介入')
