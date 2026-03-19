# Next.js 架构分析

## 基本信息

| 属性 | 值 |
|------|-----|
| 项目名称 | Next.js |
| GitHub | https://github.com/vercel/next.js |
| 语言 | TypeScript (54.8%), Rust (13.5%), JavaScript (30.4%) |
| Stars | 138k+ |
| Forks | 30.6k+ |
| 维护方 | Vercel |
| 许可证 | MIT |

---

## 项目结构

```
next.js/
├── .agents/              # AI Agent配置
├── .cargo/               # Rust Cargo配置
├── .github/              # GitHub配置和工作流
├── .vscode/              # VSCode配置
├── apps/                 # 测试应用
│   ├── next/            # Next.js主应用
│   └── next-nested-builds/
├── bench/                # 性能基准测试
├── crates/               # Rust代码
│   └── next-core/       # Turbopack核心
├── docs/                 # 文档
├── errors/               # 错误消息定义
├── examples/             # 官方示例 (数十个)
├── packages/             # 核心包
│   ├── next/            # Next.js核心
│   ├── eslint-config/   # ESLint配置
│   └── font/            # 字体优化
├── turbopack/            # Turbopack构建系统
├── test/                 # 测试套件
├── scripts/              # 构建和发布脚本
├── pnpm-workspace.yaml   # pnpm工作区配置
├── lerna.json            # Lerna配置
├── turbo.json            # Turborepo配置
└── Cargo.toml            # Rust工作区配置
```

---

## 模块划分策略

### 1. 包结构 (Packages)

| 包名 | 职责 | 说明 |
|------|------|------|
| `next` | 核心框架 | 路由、渲染、API Routes |
| `eslint-config-next` | Lint规则 | 推荐的ESLint配置 |
| `@next/font` | 字体优化 | Google字体本地化和优化 |

### 2. 代码目录结构 (packages/next)

```
packages/next/
├── src/
│   ├── bin/             # CLI入口 (next命令)
│   ├── build/           # 构建逻辑
│   ├── cli/             # 命令行处理
│   ├── client/          # 客户端代码
│   ├── export/          # 静态导出
│   ├── lib/             # 工具函数
│   ├── server/          # 服务端代码
│   ├── shared/          # 共享代码
│   └── trace/           # 性能追踪
```

### 3. 运行时架构

```
┌─────────────────────────────────────────┐
│           App Router (app/)             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │Layout   │ │Page     │ │Loading  │   │
│  │Server   │ │Server   │ │UI       │   │
│  └─────────┘ └─────────┘ └─────────┘   │
├─────────────────────────────────────────┤
│           Pages Router (pages/)         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │SSR      │ │SSG      │ │ISR      │   │
│  │getServer│ │getStatic│ │revalidate│  │
│  └─────────┘ └─────────┘ └─────────┘   │
├─────────────────────────────────────────┤
│           Rendering Layer               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │RSC      │ │RSC Payload│ │HTML    │  │
│  │(Server) │ │(Stream)  │ │(Client)│   │
│  └─────────┘ └─────────┘ └─────────┘   │
├─────────────────────────────────────────┤
│           Build System                  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │Turbopack│ │SWC      │ │Webpack  │   │
│  │(Rust)   │ │(Rust)   │ │(JS)     │   │
│  └─────────┘ └─────────┘ └─────────┘   │
└─────────────────────────────────────────┘
```

---

## 依赖管理

### 构建工具链
- **包管理**: pnpm (workspace)
- **任务编排**: Turborepo
- **版本管理**: Lerna
- **构建**: Turbopack (Rust) + SWC (Rust)

### 关键依赖
```json
{
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "@swc/core": "编译器核心",
    "webpack": "可选构建工具"
  }
}
```

---

## 接口设计

### 1. 文件系统约定 API

```typescript
// app/page.tsx - 页面组件
export default function Page() {
  return <div>Hello World</div>
}

// app/layout.tsx - 布局组件
export default function Layout({ children }) {
  return <html><body>{children}</body></html>
}

// app/loading.tsx - 加载状态
export default function Loading() {
  return <div>Loading...</div>
}
```

### 2. 数据获取 API

```typescript
// Server Component 数据获取
async function getData() {
  const res = await fetch('https://api.example.com/data')
  return res.json()
}

export default async function Page() {
  const data = await getData()
  return <div>{data.title}</div>
}
```

### 3. 配置接口 (next.config.js)

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  // 图片优化配置
  images: {
    domains: ['example.com'],
    formats: ['image/webp'],
  },
  // 重定向配置
  async redirects() {
    return [
      { source: '/old', destination: '/new', permanent: true }
    ]
  },
  // 环境变量
  env: {
    CUSTOM_KEY: 'value',
  },
}

module.exports = nextConfig
```

---

## 扩展性机制

### 1. 插件系统

```javascript
// next.config.js - 插件配置
const withMDX = require('@next/mdx')({
  extension: /\.mdx?$/
})

module.exports = withMDX({
  pageExtensions: ['js', 'jsx', 'mdx', 'ts', 'tsx'],
})
```

### 2. Middleware 中间件

```typescript
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  // 认证、重定向、A/B测试等
  if (!isAuthenticated(request)) {
    return NextResponse.redirect(new URL('/login', request.url))
  }
  return NextResponse.next()
}

export const config = {
  matcher: ['/dashboard/:path*'],
}
```

### 3. 自定义 Server

```javascript
// server.js
const { createServer } = require('http')
const { parse } = require('url')
const next = require('next')

const app = next({ dev: false })
const handle = app.getRequestHandler()

app.prepare().then(() => {
  createServer((req, res) => {
    const parsedUrl = parse(req.url, true)
    // 自定义路由逻辑
    handle(req, res, parsedUrl)
  }).listen(3000)
})
```

---

## 测试策略

### 测试类型分布

| 测试类型 | 工具 | 位置 | 目的 |
|----------|------|------|------|
| 单元测试 | Jest | `test/unit/` | 函数/组件测试 |
| 集成测试 | Playwright | `test/e2e/` | 端到端流程 |
| 基准测试 | custom | `bench/` | 性能回归 |

### 测试示例

```typescript
// 组件测试
import { render, screen } from '@testing-library/react'
import Home from '../pages/index'

describe('Home', () => {
  it('renders a heading', () => {
    render(<Home />)
    const heading = screen.getByRole('heading', { name: /welcome/i })
    expect(heading).toBeInTheDocument()
  })
})
```

---

## 文档组织

```
docs/
├── 01-getting-started/     # 快速入门
├── 02-app/                 # App Router 文档
│   ├── 01-building/
│   ├── 02-api-reference/
│   └── 03-architecture/
├── 03-pages/               # Pages Router 文档
├── 04-architecture/        # 架构设计
│   ├── fast-refresh.md
│   ├── turbopack.md
│   └── edge.md
└── 05-api-reference/       # API 参考
```

---

## 架构亮点

### 1. 渐进式采用
- 支持逐步从 Pages Router 迁移到 App Router
- 向后兼容，平滑升级路径

### 2. 多运行时支持
- Node.js Runtime (传统服务端)
- Edge Runtime (轻量级边缘计算)
- 浏览器 Runtime (客户端)

### 3. 构建系统演进
- Webpack → Turbopack (Rust重写)
- Babel → SWC (Rust重写)
- 编译速度提升 700x

### 4. React Server Components
- 服务端组件作为默认
- 客户端组件显式声明 ('use client')
- 流式传输优化首屏

---

## 最佳实践提取

1. **约定优于配置**: 文件系统路由减少配置负担
2. **渐进增强**: 支持从简单静态页面到复杂全栈应用
3. **性能优先**: 图片优化、代码分割、预取预加载内置
4. **开发体验**: 快速刷新、TypeScript支持、清晰错误提示
5. **部署灵活**: 支持多种部署目标 (Vercel、Docker、自托管)

---

## 参考链接

- [官方文档](https://nextjs.org/docs)
- [架构文档](https://nextjs.org/docs/architecture)
- [GitHub 仓库](https://github.com/vercel/next.js)
- [Turbopack 文档](https://turbo.build/pack)
