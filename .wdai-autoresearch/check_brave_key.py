#!/usr/bin/env python3
"""
Brave API Key 检查工具
帮你验证key是否完整可用
"""

import os

print("=" * 70)
print("🔑 Brave Search API Key 检查")
print("=" * 70)

key = os.environ.get('BRAVE_API_KEY', 'BSAOqk2j2eRoo7mAlyb8ZOlSQVvvp5V')

print(f"""
当前Key信息:
├── Key: {key[:4]}****{key[-4:]}
├── 长度: {len(key)} 字符
└── 状态: {'⚠️ 可能不完整' if len(key) < 35 else '✅ 长度正常'}

标准Brave API Key格式:
├── 长度: 40-50 字符
├── 前缀: 通常以 BS 开头
└── 示例: BSxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

如何获取完整Key:
┌─────────────────────────────────────────────────────────────────────┐
│ 1. 登录 https://api.search.brave.com/                               │
│ 2. 进入 Dashboard / API Keys                                        │
│ 3. 找到你的 Key                                                     │
│ 4. 点击 "Show" 或 "Copy" 按钮                                       │
│ 5. 确保复制的是完整字符串（不是显示的部分）                          │
└─────────────────────────────────────────────────────────────────────┘

检查清单:
□ Key长度是否在40-50字符之间？
□ 是否点击了"显示完整Key"按钮？
□ 复制时是否包含了全部字符？
□ 是否有多行（需要合并）？

如果确认key完整但仍无法使用:
└─ 可能是网络限制，建议继续使用 kimi_search ✅
""")

print("=" * 70)
