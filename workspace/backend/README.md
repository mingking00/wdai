# Vibero Reader - AI双语小说学习器

一个AI驱动的双语小说阅读器，支持自动分析小说结构、提取人物和概念、AI翻译。

---

## 🚀 快速开始

### 1. 启动后端服务

**Mac/Linux:**
```bash
cd backend
chmod +x start.sh
./start.sh
```

**Windows:**
```bash
cd backend
start.bat
```

或者手动启动：
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### 2. 打开浏览器

访问: http://localhost:5000

---

## ⚙️ 配置AI翻译

### 获取Kimi API Key

1. 访问 https://platform.moonshot.cn/
2. 登录账号
3. 进入 "控制台" → "API Key管理"
4. 创建新的API Key
5. 复制密钥

### 在阅读器中配置

1. 点击右上角 ⚙️ 设置按钮
2. 选择 AI Provider（默认Kimi）
3. 粘贴 API Key
4. 点击保存

---

## 📖 使用方法

### 上传小说

1. 点击 "Upload Chinese Novel (TXT)"
2. 选择中文小说TXT文件
3. 系统自动：
   - 分析章节结构
   - 提取关键术语
   - 翻译内容（需配置API）

### 阅读功能

- **章节导航**: 左侧点击切换章节
- **双语对照**: 工具栏切换显示模式
- **术语详解**: 点击文中高亮术语查看详情
- **人物图谱**: 左侧查看所有角色

---

## 💰 API费用

Kimi API价格：
- 约 ¥0.012 / 1K tokens
- 一本10万字小说翻译约需 ¥5-10

新用户有15元免费额度。

---

## 🔧 支持的AI服务

| 服务 | Base URL | Model |
|------|----------|-------|
| Kimi | https://api.moonshot.cn/v1 | moonshot-v1-8k |
| OpenAI | https://api.openai.com/v1 | gpt-3.5-turbo |
| 自定义 | 你的API地址 | 你的模型 |

---

## 🛠️ 技术栈

- **前端**: HTML/CSS/JavaScript (原生)
- **后端**: Python + Flask
- **AI**: 支持Kimi/OpenAI/自定义

---

## ⚠️ 注意事项

- 首次使用需要先启动后端服务
- API密钥只存储在浏览器本地
- 小说内容不会被上传到服务器
- 翻译通过后端代理调用AI服务

---

## 📁 文件结构

```
backend/
├── app.py              # Flask后端
├── requirements.txt    # Python依赖
├── start.sh           # Mac/Linux启动脚本
├── start.bat          # Windows启动脚本
└── templates/
    └── index.html     # 前端页面
```

---

## 🆘 常见问题

**Q: 启动后无法访问？**  
A: 确保端口5000没有被占用，或修改app.py中的端口号

**Q: API配置后翻译失败？**  
A: 检查API Key是否正确，以及账户余额是否充足

**Q: 支持什么格式的小说？**  
A: 纯文本TXT文件，章节名建议包含"第X章"或"Chapter X"
