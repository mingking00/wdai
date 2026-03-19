

---

## Gnet 代码分析 - 2026-03-17

**项目**: panjf2000/gnet  
**大小**: 1.3MB  
**定位**: 高性能事件驱动网络框架 (对标Netty)

### 核心架构

| 组件 | 实现 | 特点 |
|:---|:---|:---|
| **Reactor** | 多eventloop + epoll/kqueue | 边缘触发，无锁设计 |
| **负载均衡** | 轮询/最少连接/哈希 | 可插拔策略 |
| **Goroutine池** | ants库集成 | 256K容量，非阻塞提交 |
| **内存管理** | RingBuffer池化 | 延迟初始化，自动回收 |

### 关键模式 (可应用到wdai)

1. **负载均衡选择Agent**
   ```python
   # 当前：固定分配
   # 改进：最少连接 / 轮询 / 哈希
   ```

2. **任务队列池化**
   ```python
   # 当前：直接创建asyncio任务
   # 改进：限制并发池 (如Gnet的256K ants池)
   ```

3. **缓冲区池化**
   ```python
   # 当前：每次新建Context
   # 改进：池化复用，用完归还
   ```

### 与Rathole对比

| 特性 | Rathole (Rust) | Gnet (Go) |
|:---|:---|:---|
| 并发模型 | tokio async | Reactor + Goroutine池 |
| I/O模式 | 异步 | 事件驱动(epoll) |
| 负载均衡 | 无 | 3种策略 |
| 内存管理 | Bytes零拷贝 | 弹性缓冲区池 |
| 适用场景 | NAT代理 | 通用网络框架 |

### 分析产出

- [x] 代码分析文档: `.learning/go-patterns/gnet-analysis.md`
- [x] 技能文档更新: v1.2 (添加Gnet模式)
- [x] 可复用模式: Reactor、负载均衡、Goroutine池、内存池

### 下一步

- [ ] 实现简单的RoundRobin负载均衡器
- [ ] 添加Agent负载监控
- [ ] 评估是否需要goroutine池限制

---
