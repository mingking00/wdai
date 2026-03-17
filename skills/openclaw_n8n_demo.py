#!/usr/bin/env python3
"""
OpenClaw + n8n 完整集成示例

展示如何在 OpenClaw 中使用 n8n 作为执行引擎
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import json
import requests
from typing import Dict, Any, Optional


class OpenClawN8NExecutor:
    """
    OpenClaw 的 n8n 执行引擎
    
    封装 n8n 调用，为 OpenClaw 提供自动化能力
    """
    
    def __init__(self, n8n_base_url: str = "http://localhost:5678"):
        self.base_url = n8n_base_url.rstrip("/")
        self.webhook_url = f"{self.base_url}/webhook/openclaw-execute"
    
    def execute_task(self, task_type: str, data: Dict[str, Any], 
                    task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task_type: 任务类型 (ai, email, web, data)
            data: 任务数据
            task_id: 任务ID（可选）
        """
        payload = {
            "taskId": task_id or f"task-{hash(str(data)) % 100000}",
            "type": task_type,
            "data": data
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "n8n 未启动，请运行: docker run -p 5678:5678 n8nio/n8n",
                "taskId": payload["taskId"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "taskId": payload["taskId"]
            }
    
    # ==================== 便捷方法 ====================
    
    def ai_process(self, text: str, prompt: Optional[str] = None) -> str:
        """AI 处理文本"""
        result = self.execute_task("ai", {
            "text": text,
            "prompt": prompt or "处理以下内容"
        })
        return result.get("result", "") if result.get("success") else result.get("error", "处理失败")
    
    def web_request(self, url: str, method: str = "GET", 
                   headers: Optional[Dict] = None) -> Dict:
        """执行 Web 请求"""
        result = self.execute_task("web", {
            "url": url,
            "method": method,
            "headers": headers or {}
        })
        return result
    
    def process_data(self, data: Dict) -> Dict:
        """数据处理"""
        result = self.execute_task("data", data)
        return result
    
    def send_email(self, to: str, subject: str, body: str) -> bool:
        """发送邮件（需要配置邮箱）"""
        result = self.execute_task("email", {
            "to": to,
            "subject": subject,
            "body": body
        })
        return result.get("success", False)


def demo_openclaw_integration():
    """演示 OpenClaw 集成"""
    
    print("🤖 OpenClaw + n8n 集成演示")
    print("=" * 60)
    
    # 初始化执行器
    executor = OpenClawN8NExecutor()
    
    # 示例 1: AI 处理
    print("\n[示例 1] AI 文本处理")
    print("-" * 60)
    print("OpenClaw: '帮我总结这段内容'")
    
    text = """
    n8n 是一个开源的工作流自动化工具，可以连接 400+ 应用和服务。
    它支持可视化编排、自定义代码、AI Agent 等功能。
    与 Zapier 不同，n8n 可以自托管，数据完全可控。
    """
    
    result = executor.ai_process(
        text=text,
        prompt="用一句话总结"
    )
    
    print(f"n8n 执行结果: {result}")
    
    # 示例 2: Web 请求
    print("\n[示例 2] Web 请求")
    print("-" * 60)
    print("OpenClaw: '获取 GitHub API 信息'")
    
    result = executor.web_request(
        url="https://api.github.com",
        method="GET"
    )
    
    if result.get("success"):
        print(f"✅ 请求成功")
        print(f"响应: {json.dumps(result.get('result', {}), indent=2)[:200]}...")
    else:
        print(f"❌ 请求失败: {result.get('error')}")
    
    # 示例 3: 数据处理
    print("\n[示例 3] 数据处理")
    print("-" * 60)
    print("OpenClaw: '处理销售数据'")
    
    sales_data = {
        "orders": [
            {"id": 1, "amount": 100, "customer": "A"},
            {"id": 2, "amount": 200, "customer": "B"},
            {"id": 3, "amount": 150, "customer": "A"}
        ]
    }
    
    result = executor.process_data(sales_data)
    print(f"处理结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 示例 4: 通用任务执行
    print("\n[示例 4] 通用任务")
    print("-" * 60)
    print("OpenClaw: '执行自定义任务'")
    
    result = executor.execute_task(
        task_type="custom",
        data={"action": "test", "params": {"foo": "bar"}}
    )
    
    print(f"任务结果: {json.dumps(result, indent=2, ensure_ascii=False)}")


def show_integration_code():
    """展示集成代码"""
    
    print("\n\n" + "=" * 60)
    print("💻 集成代码示例")
    print("=" * 60)
    
    code = '''
# 在 OpenClaw 中使用 n8n

from skills.n8n_skill import N8NSkill

class OpenClawAgent:
    def __init__(self):
        self.n8n = N8NSkill(
            base_url="http://localhost:5678"
        )
    
    def handle_user_request(self, user_input: str):
        """处理用户请求"""
        
        # 1. 理解用户意图
        if "邮件" in user_input:
            # 创建邮件自动化工作流
            workflow = self.n8n.create_from_template(
                template_id="email_auto_reply",
                name="邮件助手"
            )
            # 激活工作流
            self.n8n.activate_workflow(workflow.id)
            return f"已创建邮件助手: {workflow.id}"
        
        elif "报告" in user_input:
            # 创建定时报告工作流
            workflow = self.n8n.create_from_template(
                template_id="scheduled_report",
                name="日报生成器"
            )
            return f"已创建报告生成器: {workflow.id}"
        
        elif "分析" in user_input:
            # 直接执行 AI 分析
            result = self.n8n.run_task(
                task_description=user_input
            )
            return result
        
        else:
            # 通用处理
            return "我可以帮你创建邮件自动化、报告生成或数据分析工作流"


# 使用示例
agent = OpenClawAgent()

# 用户说: "帮我创建一个邮件自动回复"
response = agent.handle_user_request("帮我创建一个邮件自动回复")
print(response)
# 输出: 已创建邮件助手: workflow-xxxx

# 用户说: "生成昨天的销售报告"
response = agent.handle_user_request("生成昨天的销售报告")
print(response)
'''
    
    print(code)


def show_real_world_scenarios():
    """展示真实场景"""
    
    print("\n\n" + "=" * 60)
    print("🌍 真实应用场景")
    print("=" * 60)
    
    scenarios = [
        {
            "name": "智能客服系统",
            "flow": """
用户: "订单什么时候到？"
  ↓
OpenClaw: 理解意图 → 查询订单状态
  ↓
n8n: 执行 Workflow
  - 查询数据库 (Postgres)
  - 获取物流信息 (HTTP API)
  - 生成回复 (AI)
  ↓
OpenClaw: "您的订单预计明天送达..."
"""
        },
        {
            "name": "自动化日报",
            "flow": """
定时触发 (每天 18:00)
  ↓
n8n Workflow:
  - 从 GitHub 获取今日提交
  - 从钉钉获取任务完成情况  
  - 从邮件获取沟通记录
  - AI 生成日报摘要
  - 发送邮件给团队
  ↓
团队收到: "今日工作总结..."
"""
        },
        {
            "name": "数据监控告警",
            "flow": """
定时检查 (每 5 分钟)
  ↓
n8n Workflow:
  - 查询数据库指标
  - 对比阈值
  - 发现异常 → AI 分析原因
  - 生成告警信息
  - 发送钉钉 + 邮件
  ↓
运维收到: "服务器 CPU 异常..."
"""
        },
        {
            "name": "内容审核",
            "flow": """
用户上传内容
  ↓
OpenClaw: 调用 n8n 审核
  ↓
n8n Workflow:
  - AI 检测敏感内容
  - 置信度 > 0.8 → 自动通过
  - 置信度 0.5-0.8 → 人工审核
  - 置信度 < 0.5 → 拒绝
  ↓
OpenClaw: 返回审核结果
"""
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📌 {scenario['name']}")
        print(scenario['flow'])


def main():
    """主入口"""
    # 演示集成
    demo_openclaw_integration()
    
    # 展示代码
    show_integration_code()
    
    # 展示场景
    show_real_world_scenarios()
    
    # 总结
    print("\n\n" + "=" * 60)
    print("🎯 集成价值")
    print("=" * 60)
    print("""
1. OpenClaw 擅长: 自然语言理解、复杂推理、人机交互
2. n8n 擅长: 工作流编排、系统集成、定时任务
3. 结合后:
   - 用户说一句话 → OpenClaw 理解 → 生成 n8n 工作流
   - n8n 自动执行 → 连接 400+ 应用
   - OpenClaw 监控结果 → 向用户汇报

部署检查清单:
  □ 启动 n8n: docker run -p 5678:5678 n8nio/n8n
  □ 导入工作流: /tmp/openclaw_executor_workflow.json
  □ 配置凭证: OpenAI, 数据库, 邮箱等
  □ 测试调用: python3 openclaw_n8n_demo.py
  □ 集成到 OpenClaw: from skills.n8n_skill import N8NSkill

下一步:
  1. 部署 n8n 实例
  2. 配置所需凭证
  3. 在 OpenClaw 中使用 N8NSkill
  4. 创建你的第一个自动化工作流
    """)


if __name__ == "__main__":
    main()
