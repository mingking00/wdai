# 三体交互阅读器 - 在线版

> 纯前端PDF阅读器，支持本地PDF文件交互式阅读

🔗 **在线访问**: https://three-body-reader.vercel.app (部署后更新)

---

## 🚀 快速开始

### 1. 访问网站
打开浏览器，访问部署后的网址

### 2. 上传PDF
- 点击"上传PDF"按钮
- 或将PDF文件拖拽到页面

### 3. 开始阅读
- 左侧章节导航快速跳转
- 点击角色查看人物介绍
- 点击概念了解科幻设定

---

## 📖 支持的PDF

你可以阅读任何PDF文件：
- 小说/文学作品
- 学术论文
- 技术文档
- 扫描版PDF（仅显示，无文本层）

**注意**: PDF文件仅在本地处理，不会上传到任何服务器

---

## 🛠️ 本地运行

```bash
# 克隆仓库
git clone https://github.com/yourusername/three-body-reader.git
cd three-body-reader

# 启动本地服务器
python3 -m http.server 8080

# 访问 http://localhost:8080
```

---

## 📦 部署到自己的Vercel账号

### 方式1: 使用Vercel CLI

```bash
# 安装Vercel CLI
npm i -g vercel

# 登录
vercel login

# 部署
cd three-body-reader
vercel --prod
```

### 方式2: GitHub + Vercel自动部署

1. Fork本仓库到你的GitHub
2. 登录 [vercel.com](https://vercel.com)
3. 点击 "New Project"
4. 导入GitHub仓库
5. 点击 "Deploy"

---

## 📝 配置说明

### 自定义章节

编辑 `reader.js` 中的 `chapterData` 对象：

```javascript
const chapterData = {
  'part1': {
    title: '第一部',
    chapters: [
      { name: '第一章', page: 1 },
      { name: '第二章', page: 15 }
    ]
  }
};
```

### 自定义角色

编辑 `reader.js` 中的 `characters` 对象添加新角色。

### 自定义概念

编辑 `reader.js` 中的 `concepts` 对象添加新概念。

---

## 🎨 自定义主题

编辑 `style.css` 修改颜色：

```css
:root {
  --primary: #2C3E50;      /* 主色调 */
  --accent: #E74C3C;       /* 强调色 */
  --bg-primary: #1A1A2E;   /* 背景色 */
  --text-primary: #EAEAEA; /* 文字色 */
}
```

---

## 📄 技术栈

- **PDF渲染**: PDF.js (Mozilla)
- **部署**: Vercel
- **样式**: 纯CSS3
- **逻辑**: 原生JavaScript

---

## ⚠️ 隐私说明

- PDF文件完全在本地处理
- 不会上传到任何服务器
- 无追踪代码
- 无Cookie

---

## 📜 开源协议

MIT License

---

*给岁月以文明*
