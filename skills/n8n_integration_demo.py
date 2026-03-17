#!/usr/bin/env python3
"""
n8n + OpenClaw 集成示例

展示如何将 n8n 作为 OpenClaw 的执行引擎
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from n8n_skill import N8NSkill


def demo_natural_language_to_workflow():
    """演示：自然语言 → 工作流 → 执行"""
    
    print("🎯 Demo: OpenClaw + n8n 集成")
    print("=" * 60)
    
    skill = N8NSkill()
    
    # 场景 1：用户用自然语言描述需求
    user_requests = [
        "帮我创建一个邮件自动回复的工作流",
        "需要一个 Webhook API 来接收数据并用 AI 处理",
        "定时生成数据报告并发送到邮箱",
        "Slack 机器人，自动回复消息",
        "把 Google Sheets 的数据同步到数据库"
    ]
    
    print("\n📋 用户请求场景:")
    print("-" * 60)
    
    for i, request in enumerate(user_requests, 1):
        print(f"\n{i}. 用户说: \"{request}\"")
        
        # OpenClaw 理解意图，生成工作流配置
        config = skill.generate_workflow_from_description(request)
        
        print(f"   🔍 解析结果:")
        print(f"      模板: {config['template_name']}")
        print(f"      名称: {config['name']}")
        print(f"      所需凭证: {', '.join(config['required_credentials'])}")
        print(f"      节点: {len(config['nodes'])} 个")
    
    # 场景 2：自动创建并执行
    print("\n" + "=" * 60)
    print("场景 2: 自动创建并部署")
    print("=" * 60)
    
    request = "创建一个邮件助手"
    print(f"\n用户请求: \"{request}\"")
    print("\n执行流程:")
    print("  1️⃣  OpenClaw 解析请求 → 确定使用 'email_auto_reply' 模板")
    print("  2️⃣  生成工作流 JSON → 包含 IMAP 触发 + AI 处理 + SMTP 发送")
    print("  3️⃣  调用 n8n API → POST /api/v1/workflows")
    print("  4️⃣  工作流创建成功 → 返回 workflow_id")
    print("  5️⃣  可选: 激活工作流 → POST /workflows/{id}/activate")
    
    # 显示工作流结构
    config = skill.generate_workflow_from_description(request)
    print("\n📊 工作流结构:")
    print("-" * 60)
    for node in config['nodes']:
        print(f"  [{node['id']}] {node['name']} ({node['type']})")
    
    print("\n🔗 连接关系:")
    for source, targets in config['connections'].items():
        for target_list in targets.get('main', []):
            for target in target_list:
                print(f"  {source} → {target['node']}")
    
    # 场景 3：执行监控
    print("\n" + "=" * 60)
    print("场景 3: 执行与监控")
    print("=" * 60)
    
    print("\n当工作流触发时:")
    print("  📨 收到新邮件")
    print("  ⚙️  n8n 执行工作流")
    print("  🤖 AI 生成回复")
    print("  📤 发送回复邮件")
    print("  📊 OpenClaw 可查询执行状态 → GET /executions/{id}")
    
    print("\n监控数据:")
    print("  - 执行状态: success / error / running")
    print("  - 执行时间: startedAt → stoppedAt")
    print("  - 输入/输出数据")
    print("  - 错误日志（如有）")


def demo_integration_patterns():
    """演示：集成模式"""
    
    print("\n\n" + "=" * 60)
    print("🔄 集成模式: OpenClaw ↔ n8n")
    print("=" * 60)
    
    patterns = [
        {
            "name": "模式 1: OpenClaw 生成 → n8n 执行",
            "flow": [
                "用户: '帮我自动化邮件处理'",
                "OpenClaw: 理解意图 → 生成 n8n 工作流 JSON",
                "OpenClaw: 调用 n8n API 创建工作流",
                "n8n: 独立运行，触发并执行",
                "OpenClaw: 查询执行历史，向用户报告"
            ]
        },
        {
            "name": "模式 2: n8n 触发 → OpenClaw 处理",
            "flow": [
                "n8n: Webhook 接收外部数据",
                "n8n: HTTP Request → 调用 OpenClaw API",
                "OpenClaw: 接收数据，执行复杂推理",
                "OpenClaw: 返回结果给 n8n",
                "n8n: 继续后续工作流"
            ]
        },
        {
            "name": "模式 3: Human-in-the-loop",
            "flow": [
                "n8n: AI 生成决策建议",
                "n8n: 发送请求到 OpenClaw（人工确认）",
                "OpenClaw: 展示给用户，等待确认",
                "用户: 确认 / 修改 / 拒绝",
                "OpenClaw: 返回用户决策给 n8n",
                "n8n: 根据决策继续或终止"
            ]
        },
        {
            "name": "模式 4: 复杂编排",
            "flow": [
                "OpenClaw: 解析复杂任务，拆分为子任务",
                "OpenClaw: 为每个子任务创建 n8n 工作流",
                "n8n: 并行/串行执行多个工作流",
                "OpenClaw: 监控整体进度，协调依赖关系",
                "OpenClaw: 汇总结果，生成最终报告"
            ]
        }
    ]
    
    for pattern in patterns:
        print(f"\n{pattern['name']}")
        print("-" * 60)
        for step in pattern['flow']:
            print(f"  {step}")


def demo_use_cases():
    """演示：实际应用场景"""
    
    print("\n\n" + "=" * 60)
    print("💼 实际应用场景")
    print("=" * 60)
    
    use_cases = [
        {
            "title": "📧 智能邮件助手",
            "trigger": "收到新邮件",
            "actions": [
                "AI 分类邮件（重要/普通/垃圾）",
                "重要邮件 → 生成摘要 → 发送钉钉",
                "简单询问 → AI 生成回复 → 人工确认 → 发送",
                "复杂问题 → 创建待办 → 通知人工处理"
            ]
        },
        {
            "title": "📊 日报生成器",
            "trigger": "每天 18:00",
            "actions": [
                "从 GitHub 拉取今日提交",
                "从钉钉获取今日任务完成情况",
                "从邮件获取今日沟通记录",
                "AI 生成日报摘要",
                "发送邮件给团队"
            ]
        },
        {
            "title": "🤖 客服机器人",
            "trigger": "用户发送消息（Slack/钉钉/网页）",
            "actions": [
                "查询知识库（RAGFlow）",
                "AI 生成回答",
                "置信度 > 0.8 → 直接回复",
                "置信度 < 0.8 → 转人工",
                "记录对话到 CRM"
            ]
        },
        {
            "title": "📈 数据监控预警",
            "trigger": "每小时检查 / 或 Webhook 接收",
            "actions": [
                "查询数据库指标",
                "对比阈值",
                "异常时 → AI 分析原因",
                "生成预警报告",
                "发送邮件 + Slack 通知"
            ]
        }
    ]
    
    for case in use_cases:
        print(f"\n{case['title']}")
        print(f"触发器: {case['trigger']}")
        print("执行流程:")
        for i, action in enumerate(case['actions'], 1):
            print(f"  {i}. {action}")


def main():
    """主入口"""
    demo_natural_language_to_workflow()
    demo_integration_patterns()
    demo_use_cases()
    
    print("\n\n" + "=" * 60)
    print("✨ 总结")
    print("=" * 60)
    print("""
OpenClaw + n8n 集成价值:

1. 自然语言交互
   用户说一句话 → OpenClaw 理解 → 自动生成工作流

2. 可视化编排
   n8n 提供 400+ 集成，拖拽式构建复杂流程

3. AI 能力增强
   内置 LangChain，支持 Agent、RAG、多步推理

4. 灵活执行模式
   - 定时执行（Schedule）
   - 事件触发（Webhook）
   - 手动执行（Manual）
   - AI 触发（智能判断）

5. 监控与审计
   完整的执行历史、日志、错误追踪

下一步:
  1. 部署 n8n: docker run -p 5678:5678 n8nio/n8n
  2. 配置凭证: Gmail, Slack, OpenAI 等
  3. 使用 OpenClaw 生成并部署工作流
    """)


if __name__ == "__main__":
    main()
