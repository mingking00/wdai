# AI双语阅读器 (AI Bilingual Reader)

基于 **epub.js** 构建的浏览器端双语小说阅读器，支持AI翻译、术语高亮和智能解释。

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ 核心功能

### 📖 阅读功能
- **EPUB解析**：完整的EPUB电子书解析和渲染
- **TXT支持**：纯文本小说文件直接阅读
- **目录导航**：章节跳转、目录树展示（EPUB）
- **阅读设置**：字体大小、行高、主题（浅色/深色/sepia）
- **响应式设计**：适配桌面和移动设备

### 🌐 双语对照
- **AI翻译**：支持多种AI翻译服务
- **双语模式**：左右分栏显示中英文
- **翻译缓存**：本地存储翻译结果，避免重复请求

### 📚 术语系统
- **智能高亮**：自动识别并高亮文中术语
- **点击解释**：点击术语查看详细解释
- **术语分类**：人物、概念、地点分类管理
- **可扩展**：支持自定义术语表

## 🚀 快速开始

### 方式一：直接打开
```bash
# 下载项目后直接用浏览器打开
cd bilingual-reader
open index.html
```

### 方式二：本地服务器（推荐）
```bash
# Python 3
python -m http.server 8080

# Node.js
npx serve .

# PHP
php -S localhost:8080
```

然后访问 `http://localhost:8080`

## 📖 使用方法

### 1. 加载书籍
- 点击「📚 打开书籍」按钮
- 选择 EPUB 或 TXT 格式文件

### 2. 配置翻译服务

点击右上角「⚙️ 设置」：

1. **选择翻译服务**：
   - Demo模式（假翻译）- 演示用，内容无意义
   - OpenAI GPT - 推荐，翻译质量高
   - Claude - Anthropic的AI，质量也很高
   - Google Translate - 传统机器翻译
   - DeepL - 欧洲语言翻译质量高

2. **输入API Key**（选择非Demo服务后显示）

### 3. 获取API Key

#### OpenAI (推荐)
1. 访问 https://platform.openai.com
2. 注册/登录账号
3. 进入 API Keys 页面
4. 点击 "Create new secret key"
5. 复制 key 粘贴到设置中

#### Claude
1. 访问 https://console.anthropic.com
2. 注册/登录账号
3. 进入 API Keys 页面获取

#### Google Translate
1. 访问 https://console.cloud.google.com
2. 创建项目并启用 Cloud Translation API
3. 创建 API Key

#### DeepL
1. 访问 https://www.deepl.com/pro-api
2. 注册开发者账号
3. 获取 API Key

### 4. 开始翻译
- 点击「🤖」按钮翻译
- 选择**翻译范围**：
  - **仅当前章节**（最快，推荐）
  - **前10章**
  - **前20章**
  - **全部章节**（最慢，耗API额度）

### 5. 快捷键
- `←/→` 或 `空格`：上一章/下一章
- `Ctrl/Cmd + B`：切换双语模式
- `Ctrl/Cmd + T`：翻译当前章节
- `Ctrl/Cmd + G`：打开术语表
- `ESC`：关闭弹窗

## 💰 API费用参考

| 服务 | 价格 | 特点 |
|------|------|------|
| OpenAI GPT-3.5 | $0.002/1K tokens | 质量高，速度快 |
| Claude Haiku | $0.25/1M tokens | 性价比高 |
| Google Translate | $20/1M字符 | 稳定可靠 |
| DeepL | 免费版: 50万字符/月 | 欧洲语言优秀 |

**估算**：一本10万字的小说翻译费用约 $2-5

## 🔒 隐私说明

- **API Key** 只保存在你的浏览器本地存储中
- **不会上传到任何服务器**
- 翻译内容通过HTTPS直接发送到对应的AI服务商

## 🔧 扩展开发

### 自定义术语

打开浏览器控制台：

```javascript
// 添加新术语
glossaryManager.addTerm('新术语', {
    name: '新术语',
    nameEn: 'New Term',
    type: 'concept',
    description: '术语解释内容...',
    tags: ['标签1', '标签2']
});

// 导出术语表
const json = glossaryManager.exportToJSON();
console.log(json);

// 导入术语表
glossaryManager.importFromJSON(jsonString);
```

### 添加新的翻译服务

在 `translator.js` 中添加新方法：

```javascript
async myTranslateService(text, from, to) {
    const response = await fetch('YOUR_API_ENDPOINT', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text, source: from, target: to })
    });
    
    const data = await response.json();
    return data.translation;
}
```

## 📝 注意事项

1. **API Key安全**：Key只保存在本地浏览器，清除缓存会丢失
2. **网络要求**：使用真实翻译需要能访问对应的AI服务
3. **费用控制**：大量翻译前请确认API额度充足
4. **翻译限制**：每个段落单独翻译，长段落可能被截断

## 🔮 未来计划

- [ ] 在线词典集成（划词翻译）
- [ ] 阅读进度同步
- [ ] 批注和高亮功能
- [ ] TTS语音朗读
- [ ] 生词本和复习系统
- [ ] 云同步功能

## 📄 许可

MIT License - 可自由使用、修改和分发

---

**享受阅读！📖✨**