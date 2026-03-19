"""
认知安全系统集成示例

展示如何在实际 Agent 中使用认知安全系统
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')

from typing import Dict, Any
from core.agent_system.cognitive_safety import (
    CognitiveSafetySystem,
    validate_before_send,
    CONTEXT_TEMPLATES
)


def demo_validation():
    """演示验证功能"""
    print("="*70)
    print("认知安全系统 - 验证演示")
    print("="*70)
    
    safety = CognitiveSafetySystem()
    
    # 场景1: 危险的编造
    print("\n" + "-"*70)
    print("场景1: 引用图片但未读取")
    print("-"*70)
    
    response1 = "根据图片，这是B站评论区的撕逼对话，浅色回复说'人家以前是演员'..."
    context1 = CONTEXT_TEMPLATES['image_not_read']
    
    result1 = safety.validate_response(response1, context1)
    
    print(f"\n原文: {response1[:60]}...")
    print(f"是否安全: {result1['is_safe']}")
    print(f"违规数: {len(result1['violations'])}")
    
    for v in result1['violations']:
        print(f"  ⚠️ [{v.type.name}] {v.message}")
    
    if result1['block_reason']:
        print(f"\n🚫 阻断原因: {result1['block_reason']}")
    
    # 场景2: 安全的回复
    print("\n" + "-"*70)
    print("场景2: 诚实承认不确定")
    print("-"*70)
    
    response2 = "我需要先读取图片才能回答，请稍等..."
    context2 = CONTEXT_TEMPLATES['image_not_read']
    
    result2 = safety.validate_response(response2, context2)
    
    print(f"\n原文: {response2}")
    print(f"是否安全: {result2['is_safe']}")
    print(f"违规数: {len(result2['violations'])}")
    
    # 场景3: 自动修复
    print("\n" + "-"*70)
    print("场景3: 绝对化表述（自动修复）")
    print("-"*70)
    
    response3 = "这肯定是B站的评论，毫无疑问是网友撕逼。"
    context3 = {'verified': False}
    
    result3 = safety.validate_response(response3, context3)
    
    print(f"\n原文: {response3}")
    print(f"是否安全: {result3['is_safe']}")
    print(f"修正后: {result3['corrected_response']}")
    
    for v in result3['violations']:
        print(f"  ⚠️ [{v.type.name}] {v.message}")


def demo_safe_agent_pattern():
    """
    演示安全的 Agent 模式
    
    这是应该采用的正确模式
    """
    print("\n" + "="*70)
    print("安全 Agent 模式 - 正确使用示例")
    print("="*70)
    
    class SafeAgent:
        """
        安全的 Agent 基类
        
        所有 Agent 都应该继承这个模式
        """
        
        def __init__(self, name: str):
            self.name = name
            self.safety = CognitiveSafetySystem()
        
        def process_request(self, request: Dict[str, Any]) -> str:
            """
            处理请求的标准流程
            """
            # 步骤1: 检查是否有外部数据需要读取
            if 'image_path' in request:
                print(f"\n[步骤1] 发现图片引用: {request['image_path']}")
                print("[步骤1] 必须先读取图片...")
                # 实际应该调用 read 工具
                # image_content = read(request['image_path'])
                # 这里模拟
                print("[步骤1] ✅ 图片已读取")
                image_read = True
            else:
                image_read = False
            
            # 步骤2: 生成草稿回复
            draft = self._generate_draft(request)
            print(f"\n[步骤2] 生成草稿:\n{draft[:100]}...")
            
            # 步骤3: 构建上下文
            context = {
                'image_read': image_read,
                'file_read': False,
                'verified': image_read,  # 只有读了图片才算验证
                'has_read_tool': True,
            }
            
            # 步骤4: 安全检查
            print("\n[步骤3] 执行安全检查...")
            result = self.safety.validate_response(draft, context)
            
            if not result['is_safe']:
                print(f"⚠️ 发现 {len(result['violations'])} 个违规:")
                for v in result['violations']:
                    print(f"   - {v.type.name}: {v.message}")
                
                if result['block_reason']:
                    print(f"\n🚫 阻断！原因: {result['block_reason']}")
                    print("\n必须修正后才能发送！")
                    
                    # 修正方案
                    corrected = self._fix_response(draft, result['violations'])
                    print(f"\n✅ 已修正:\n{corrected}")
                    return corrected
            else:
                print("✅ 安全检查通过")
            
            return draft
        
        def _generate_draft(self, request: Dict) -> str:
            """生成草稿（示例）"""
            if 'image_path' in request:
                # 危险：假设图片已读
                return "根据图片内容，这是一个技术视频截图..."
            return "处理完成"
        
        def _fix_response(self, draft: str, violations: list) -> str:
            """修正回复"""
            # 根据违规类型修正
            for v in violations:
                if v.type.name == 'UNVERIFIED_EXTERNAL_DATA':
                    return "我需要先读取图片才能给出准确回答，请稍等..."
            return draft
    
    # 测试
    agent = SafeAgent("test-agent")
    
    # 危险请求：有图片但没读
    request = {
        'content': '分析这张图片',
        'image_path': '/path/to/image.jpg'
    }
    
    print("\n发送请求:", request)
    response = agent.process_request(request)
    print("\n最终回复:", response)


def demo_checkpoint_system():
    """
    演示检查点系统
    """
    print("\n" + "="*70)
    print("检查点系统 - 强制检查清单")
    print("="*70)
    
    checkpoints = {
        '起点验证': [
            '□ 这个信息我亲眼确认过吗？',
            '□ 如果前提错了，整段话还有意义吗？',
        ],
        '工具使用': [
            '□ 有外部数据（图片/文件）吗？',
            '□ 有read工具可用吗？',
            '□ 我已经读取了吗？',
        ],
        '不确定性': [
            '□ 这段话里有推测吗？',
            '□ 我显化标注了不确定性吗？',
            '□ 有绝对化表述（肯定/一定/绝对）吗？',
        ],
        '编造检测': [
            '□ 有我想象出来的细节吗？',
            '□ 有具体对话/数字但没有来源吗？',
            '□ 如果用户纠正，我会崩溃吗？',
        ],
        '最终检查': [
            '□ 回复前执行了 validate_before_send 吗？',
            '□ 发现违规时我修正了吗？',
            '□ 修正后再次检查了吗？',
        ]
    }
    
    for category, items in checkpoints.items():
        print(f"\n{category}:")
        for item in items:
            print(f"  {item}")


def run_all_demos():
    """运行所有演示"""
    demo_validation()
    demo_safe_agent_pattern()
    demo_checkpoint_system()
    
    print("\n" + "="*70)
    print("演示完成")
    print("="*70)
    print("\n核心原则:")
    print("1. 看到外部数据 → 立即用工具读取")
    print("2. 不确定时 → 显化标注，不假装确定")
    print("3. 发送前 → 执行 validate_before_send")
    print("4. 发现违规 → 修正后再发送")


if __name__ == "__main__":
    run_all_demos()
