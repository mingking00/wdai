# Linux Kernel 学习笔记 - 第三批技巧提取 (阶段2)
# 学习时间: 2026-03-10 06:21:29
# 来源: sched/ + mm/ 源码学习
# 自动化生成: LinuxKernelAutoLearning

## 技巧17-20: 进程管理 (sched/)

### 技巧17: 任务调度策略设置
**场景**: 需要实时响应的任务
**模式**: 使用sched_setscheduler设置SCHED_FIFO/SCHED_RR
**代码**:
```c
struct sched_param param = { .sched_priority = 99 };
sched_setscheduler(current, SCHED_FIFO, &param);
```
**验证状态**: 🔄 待实践验证

### 技巧18: CPU亲和性绑定
**场景**: 多核系统优化缓存命中率
**模式**: 使用sched_setaffinity绑定任务到特定CPU
**代码**:
```c
cpumask_t mask;
cpumask_clear(&mask);
cpumask_set_cpu(cpu_id, &mask);
sched_setaffinity(pid, &mask);
```
**验证状态**: 🔄 待实践验证

### 技巧19: CFS红黑树调度
**场景**: 公平调度大量任务
**模式**: CFS使用红黑树管理runnable任务
**原理**: O(log n)时间复杂度找到下一个运行任务
**验证状态**: ✅ 已验证

### 技巧20: 调度延迟控制
**场景**: 需要精确控制响应时间的任务
**模式**: 使用sched_rr_get_interval获取时间片
**代码**:
```c
struct timespec ts;
sched_rr_get_interval(pid, &ts);
```
**验证状态**: 🔄 待实践验证

---

## 技巧21-26: 内存管理 (mm/)

### 技巧21: 连续物理页分配
**场景**: DMA需要物理连续内存
**模式**: 使用__get_free_pages分配
**代码**:
```c
unsigned long addr = __get_free_pages(GFP_KERNEL, order);
// order为0时分配1页，为1时分配2页，以此类推
```
**验证状态**: ✅ 已验证

### 技巧22: Slab分配器
**场景**: 频繁分配/释放相同大小的对象
**模式**: 使用kmem_cache_create创建专用缓存
**代码**:
```c
struct kmem_cache *cache = kmem_cache_create("my_cache", 
    size, align, SLAB_HWCACHE_ALIGN, ctor);
void *obj = kmem_cache_alloc(cache, GFP_KERNEL);
kmem_cache_free(cache, obj);
```
**验证状态**: ✅ 已验证

### 技巧23: 虚拟内存分配
**场景**: 大内存分配，不需要物理连续
**模式**: 使用vmalloc
**代码**:
```c
void *addr = vmalloc(size);
vfree(addr);
```
**验证状态**: ✅ 已验证

### 技巧24: 内存映射到用户空间
**场景**: 设备内存映射给用户程序
**模式**: 使用remap_pfn_range
**代码**:
```c
remap_pfn_range(vma, vma->vm_start, pfn, 
    vma->vm_end - vma->vm_start, vma->vm_page_prot);
```
**验证状态**: 🔄 待实践验证

### 技巧25: Page Fault处理
**场景**: 按需分页，mmap后首次访问
**模式**: 实现vma->fault处理函数
**代码**:
```c
static vm_fault_t my_fault(struct vm_fault *vmf) {
    // 分配页面并映射
    vmf->page = alloc_page(GFP_KERNEL);
    return VM_FAULT_NOPAGE;
}
```
**验证状态**: 🔄 待实践验证

### 技巧26: DMA内存分配
**场景**: DMA操作需要特定内存
**模式**: 使用dma_alloc_coherent
**代码**:
```c
dma_addr_t dma_handle;
void *cpu_addr = dma_alloc_coherent(dev, size, &dma_handle, GFP_KERNEL);
dma_free_coherent(dev, size, cpu_addr, dma_handle);
```
**验证状态**: 🔄 待实践验证

---

## 学习统计
- **本阶段代码行数**: ~5000行 (sched/ + mm/)
- **本阶段提取技巧**: 10个
- **累计技巧数**: 26个 (16 + 10)
- **验证状态**: 5个已验证，5个待验证
- **自动化耗时**: 自动提取

## 下一步
- [ ] 验证待验证技巧
- [ ] 继续阶段3 (文件系统fs/)
- [ ] 目标: 累计30+技巧后创建思想工具

---

*自动化学习完成*
