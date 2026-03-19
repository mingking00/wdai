# Vue.js 架构分析

## 基本信息

| 属性 | 值 |
|------|-----|
| 项目名称 | Vue.js Core |
| GitHub | https://github.com/vuejs/core |
| 语言 | TypeScript (96.6%), JavaScript (1.7%) |
| Stars | 53.2k+ (core) / 209k+ (legacy) |
| Forks | 9.1k+ |
| 维护方 | Vue.js Team (Evan You) |
| 许可证 | MIT |

---

## 项目结构

```
core/
├── .github/              # GitHub配置
├── .vscode/              # VSCode配置
├── changelogs/           # 变更日志
├── packages/             # 核心包 (Monorepo)
│   ├── reactivity/       # 响应式系统
│   ├── runtime-core/     # 运行时核心
│   ├── runtime-dom/      # DOM运行时
│   ├── runtime-vue/      # Vue运行时
│   ├── compiler-core/    # 编译器核心
│   ├── compiler-dom/     # DOM编译器
│   ├── compiler-sfc/     # 单文件组件编译器
│   ├── server-renderer/  # 服务端渲染
│   ├── vue/              # 完整构建
│   └── shared/           # 共享工具
├── packages-private/     # 私有包
├── scripts/              # 构建脚本
├── package.json          # pnpm工作区配置
├── pnpm-workspace.yaml   # pnpm配置
├── rollup.config.js      # 打包配置
└── vitest.config.ts      # 测试配置
```

---

## 模块划分策略

### 核心包职责

| 包名 | 职责 | 依赖 |
|------|------|------|
| `@vue/reactivity` | 响应式系统 | 无 |
| `@vue/runtime-core` | 虚拟DOM和组件系统 | reactivity |
| `@vue/runtime-dom` | DOM操作和属性处理 | runtime-core |
| `@vue/compiler-core` | 模板解析和代码生成 | 无 |
| `@vue/compiler-dom` | DOM特定编译优化 | compiler-core |
| `@vue/compiler-sfc` | `.vue`文件编译 | compiler-core, compiler-dom |
| `vue` | 完整功能构建 | 以上所有 |

### 架构层次

```
┌─────────────────────────────────────────┐
│           Application Layer             │
│  Components + Templates + Composables   │
├─────────────────────────────────────────┤
│           Compiler Layer                │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │Parse    │ │Transform│ │Generate │   │
│  │Template │ │AST      │ │Code     │   │
│  └─────────┘ └─────────┘ └─────────┘   │
├─────────────────────────────────────────┤
│           Runtime Layer                 │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │VNode    │ │Diff     │ │Patch    │   │
│  │Renderer │ │Algorithm│ │DOM      │   │
│  └─────────┘ └─────────┘ └─────────┘   │
├─────────────────────────────────────────┤
│           Reactivity Layer              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │Ref      │ │Reactive │ │Computed │   │
│  │Effect   │ │Proxy    │ │Watch    │   │
│  └─────────┘ └─────────┘ └─────────┘   │
└─────────────────────────────────────────┘
```

---

## 响应式系统架构

### 核心实现

```typescript
// reactivity/src/reactive.ts
export function reactive(target: object) {
  return createReactiveObject(
    target,
    mutableHandlers,
    mutableCollectionHandlers
  )
}

// 基于Proxy的响应式
const mutableHandlers: ProxyHandler<object> = {
  get(target, key, receiver) {
    track(target, key) // 依赖收集
    return Reflect.get(target, key, receiver)
  },
  set(target, key, value, receiver) {
    const result = Reflect.set(target, key, value, receiver)
    trigger(target, key) // 触发更新
    return result
  }
}
```

### 依赖收集流程

```
┌─────────────────────────────────────────┐
│ 1. Component Render                     │
│    ↓                                    │
│ 2. Access Reactive Property             │
│    ↓                                    │
│ 3. track() - 收集当前组件effect         │
│    ↓                                    │
│ 4. Property Changed                     │
│    ↓                                    │
│ 5. trigger() - 通知所有依赖组件         │
│    ↓                                    │
│ 6. Re-render Affected Components        │
└─────────────────────────────────────────┘
```

---

## 编译器架构

### 编译流程

```
Template String
       ↓
   Parse (解析器)
       ↓
   AST (抽象语法树)
       ↓
   Transform (转换器)
   - v-bind, v-on 转换
   - v-if, v-for 转换
       ↓
   Codegen (代码生成器)
       ↓
   Render Function (JS Code)
```

### 编译优化

| 优化类型 | 说明 | 示例 |
|----------|------|------|
| 静态提升 | 静态节点只创建一次 | `const _hoisted_1 = _createVNode(...)` |
| PatchFlag | 标记动态属性类型 | `/* TEXT, CLASS */` |
| Block Tree | 减少对比范围 | `openBlock(), createBlock()` |

---

## 组合式 API (Composition API)

### 设计理念

```typescript
// 逻辑复用 vs 选项式API
import { ref, computed, watch, onMounted } from 'vue'

// useCounter.ts - 可复用逻辑
export function useCounter() {
  const count = ref(0)
  const double = computed(() => count.value * 2)
  
  function increment() {
    count.value++
  }
  
  watch(count, (newVal) => {
    console.log('Count changed:', newVal)
  })
  
  return { count, double, increment }
}

// 组件中使用
export default {
  setup() {
    const { count, double, increment } = useCounter()
    return { count, double, increment }
  }
}
```

### 生命周期映射

| Options API | Composition API |
|-------------|-----------------|
| beforeCreate | setup() |
| created | setup() |
| beforeMount | onBeforeMount |
| mounted | onMounted |
| beforeUpdate | onBeforeUpdate |
| updated | onUpdated |
| beforeUnmount | onBeforeUnmount |
| unmounted | onUnmounted |

---

## 依赖管理

### 构建配置

```javascript
// package.json
{
  "packageManager": "pnpm@8.0.0",
  "scripts": {
    "build": "node scripts/build.js",
    "test": "vitest",
    "test:e2e": "node scripts/e2e.js"
  }
}
```

### 关键依赖

| 依赖 | 用途 |
|------|------|
| `@rollup/plugin-typescript` | TypeScript打包 |
| `esbuild` | 快速编译 |
| `vitest` | 单元测试 |
| `@vue/repl` | SFC REPL演示 |

---

## 扩展性机制

### 1. 插件系统

```typescript
// 插件定义
const MyPlugin = {
  install(app, options) {
    // 全局属性
    app.config.globalProperties.$http = () => {}
    
    // 全局指令
    app.directive('focus', {
      mounted(el) { el.focus() }
    })
    
    // 全局组件
    app.component('MyComponent', MyComponent)
    
    // 全局混入
    app.mixin({
      mounted() {
        console.log('Global mixin')
      }
    })
  }
}

// 使用插件
app.use(MyPlugin, { option: 'value' })
```

### 2. 自定义渲染器

```typescript
// 非DOM平台 (如Canvas、Native)
import { createRenderer } from '@vue/runtime-core'

const { render, createApp } = createRenderer({
  createElement(type) {
    // 创建元素
  },
  insert(child, parent, anchor) {
    // 插入节点
  },
  patchProp(el, key, prevValue, nextValue) {
    // 更新属性
  },
  // ...更多节点操作
})
```

### 3. 编译器扩展

```typescript
// 自定义块处理 (SFC)
const i18nPlugin = {
  transformInclude(id) {
    return id.endsWith('.i18n')
  },
  transform(code, id) {
    // 自定义块转换
    return { code: `export default ${JSON.stringify(code)}` }
  }
}
```

---

## 测试策略

### 测试金字塔

```
        /\
       /  \
      /E2E \        (Playwright)
     /------\
    /Integration\   (组件测试)
   /--------------\
  /    Unit Tests   \  (Vitest)
 /--------------------\
```

### 测试示例

```typescript
// 响应式系统测试
import { ref, computed } from '@vue/reactivity'
import { describe, it, expect } from 'vitest'

describe('reactivity', () => {
  it('should track ref changes', () => {
    const count = ref(0)
    expect(count.value).toBe(0)
    
    count.value = 1
    expect(count.value).toBe(1)
  })
  
  it('should compute derived values', () => {
    const count = ref(2)
    const double = computed(() => count.value * 2)
    expect(double.value).toBe(4)
  })
})
```

---

## 文档组织

```
docs/
├── src/
│   ├── guide/            # 指南
│   │   ├── essentials/   # 基础
│   │   ├── components/   # 组件
│   │   ├── reuse/        # 复用
│   │   └── scaling-up/   # 规模化
│   ├── api/              # API参考
│   ├── examples/         # 示例
│   └── ecosystem/        # 生态系统
├── public/               # 静态资源
└── .vitepress/           # VitePress配置
```

---

## 架构亮点

### 1. 渐进式框架
```
┌─────────────────────────────────────┐
│  声明式渲染 + 组件系统              │
│  ├─ CDN引入即可使用                  │
│  └─ 无构建步骤                      │
├─────────────────────────────────────┤
│  + 客户端路由 (Vue Router)          │
│  + 状态管理 (Pinia/Vuex)            │
│  + 构建工具 (Vite)                  │
├─────────────────────────────────────┤
│  + 服务端渲染 (Nuxt.js)             │
│  + 跨平台 (Weex/UniApp)             │
└─────────────────────────────────────┘
```

### 2. 性能优化策略
- **编译时优化**: 静态提升、PatchFlag标记
- **运行时优化**: 异步组件、树摇(tree-shaking)
- **响应式优化**: 精准依赖追踪、按需更新

### 3. 开发体验
- **SFC**: 单文件组件，结构清晰
- **DevTools**: 完善的浏览器调试工具
- **TypeScript**: 一流的TS支持

---

## 最佳实践提取

1. **按功能组织**: 组合式API支持逻辑复用
2. **单向数据流**: props down, events up
3. **最小化渲染**: 虚拟DOM + Diff算法
4. **按需加载**: 异步组件 + 代码分割
5. **类型安全**: 全面的TypeScript集成

---

## 参考链接

- [官方文档](https://vuejs.org/)
- [GitHub 仓库](https://github.com/vuejs/core)
- [RFC 文档](https://github.com/vuejs/rfcs)
- [设计模式](https://patterns.dev.vuejs.org/)
