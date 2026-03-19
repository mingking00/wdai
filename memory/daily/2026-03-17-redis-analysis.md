

---

## Redis 单线程Reactor模式分析 - 2026-03-17

**项目**: Redis (C语言实现)  
**分析方式**: 基于源码文档和架构文章  
**核心文件**: `src/ae.c`, `src/ae_epoll.c`, `src/networking.c`

### 核心发现

| 模式 | 实现 | 与wdai的关联 |
|:---|:---|:---|
| **单线程Reactor** | `aeMain()` + `aeProcessEvents()` | Agent系统是否应单线程？ |
| **事件分层** | 文件事件 + 时间事件 | 需要添加定时器支持 |
| **Pipeline批量** | 客户端批量提交命令 | 子任务批量提交优化 |
| **原子性保证** | 单线程命令执行 | 竞态条件防护 |

### 关键代码

```c
// 单线程事件循环
void aeMain(aeEventLoop *eventLoop) {
    while (!eventLoop->stop) {
        aeProcessEvents(eventLoop, AE_ALL_EVENTS);
    }
}

// 处理事件
int aeProcessEvents(...) {
    numevents = aeApiPoll(eventLoop, tvp);  // epoll_wait
    
    for (j = 0; j < numevents; j++) {
        // 读事件
        if (fe->mask & AE_READABLE) {
            fe->rfileProc(eventLoop, fd, ...);
        }
        // 写事件
        if (fe->mask & AE_WRITABLE) {
            fe->wfileProc(eventLoop, fd, ...);
        }
    }
    
    processTimeEvents(eventLoop);  // 定时器
}
```

### 为什么单线程？

**Redis作者的观点**:
1. 内存操作足够快 (μs级)
2. 网络延迟 (ms级) > 处理时间
3. 无锁开销，代码简单
4. 水平扩展 (多实例) 比垂直扩展 (多线程) 更容易

**不适用单线程的场景**:
- CPU密集型任务
- 长执行时间任务
- 需要利用多核

### 应用到wdai的评估

| 模式 | 适用性 | 理由 |
|:---|:---:|:---|
| 单线程Reactor | ⭐ | Agent任务非内存操作，有I/O阻塞 |
| 时间事件 | ⭐⭐⭐ | 需要：超时检查、心跳、定期清理 |
| Pipeline | ⭐⭐ | 可优化：批量提交子任务减少调度开销 |
| 原子性保证 | ⭐⭐ | asyncio已有，关键路径可加锁 |

### 建议

**暂不应用**:
- 单线程Reactor - 与当前多Agent架构冲突
- 全内存设计 - 不适合长任务处理

**可考虑**:
- 时间事件/定时器 - 添加超时和定期任务支持
- Pipeline批量 - 优化子任务提交效率

### 分析产出

- [x] 分析文档: `.learning/c-patterns/redis-analysis.md` (5.8KB)
- [x] 技能文档更新: v1.3 (添加Redis模式)

---
