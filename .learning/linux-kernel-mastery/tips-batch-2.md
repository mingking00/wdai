# Linux Kernel 学习笔记 - 第二批技巧提取
# 学习时间: 2026-03-10
# 来源: Linux Kernel API Documentation

## 技巧9: 错误指针模式 (ERR_PTR/PTR_ERR/IS_ERR)
**场景**: 内核函数需要返回指针或错误码
**模式**: 使用 ERR_PTR 将错误码编码为指针，用 IS_ERR 检查
**代码**:
```c
void *ptr = ERR_PTR(-ENOMEM);  // 返回错误
if (IS_ERR(ptr))               // 检查错误
    return PTR_ERR(ptr);       // 解码错误码
```
**优势**: 统一返回类型，避免使用输出参数
**效率提升**: 代码更简洁，接口更统一
**验证状态**: ✅ 已验证 (内核标准做法)

---

## 技巧10: 容器结构体宏 (container_of)
**场景**: 从成员指针获取父结构体指针
**模式**: 使用 container_of 宏
**代码**:
```c
struct my_struct *parent = container_of(child_ptr, struct my_struct, child_member);
```
**原理**: 通过偏移量计算父结构体地址
**效率提升**: 避免存储反向指针，节省内存
**验证状态**: ✅ 已验证

---

## 技巧11: 位操作原子化
**场景**: 多线程安全的位操作
**模式**: 使用原子位操作而非普通位运算
**代码**:
```c
set_bit(0, &bitmap);           // 原子设置位
clear_bit(1, &bitmap);         // 原子清除位
test_and_set_bit(2, &bitmap);  // 原子测试并设置
```
**优势**: 无需额外锁，硬件级原子操作
**效率提升**: 高性能并发位操作
**验证状态**: ✅ 已验证

---

## 技巧12: RCU 读侧保护
**场景**: 读多写少的共享数据访问
**模式**: 使用 RCU (Read-Copy-Update) 机制
**代码**:
```c
rcu_read_lock();
p = rcu_dereference(ptr);
// 读取数据...
rcu_read_unlock();

// 更新侧
new_ptr = kmalloc(...);
*new_ptr = new_data;
rcu_assign_pointer(ptr, new_ptr);
synchronize_rcu();  // 等待所有读者完成
kfree(old_ptr);
```
**优势**: 读者无锁，可扩展性极好
**效率提升**: 读操作性能接近本地访问
**验证状态**: ✅ 已验证

---

## 技巧13: 内存屏障显式控制
**场景**: 多核/多线程内存序控制
**模式**: 显式使用内存屏障
**代码**:
```c
smp_mb();   // 全内存屏障
smp_rmb();  // 读内存屏障
smp_wmb();  // 写内存屏障
```
**原理**: 防止编译器和CPU乱序优化
**效率提升**: 在正确的地方用最弱的屏障
**验证状态**: 🔄 需深入理解后使用

---

## 技巧14: 链表操作标准宏
**场景**: 内核链表操作
**模式**: 使用标准链表宏
**代码**:
```c
list_add(&new->list, &head);      // 添加到头部
list_add_tail(&new->list, &head); // 添加到尾部
list_del(&entry->list);           // 删除
list_for_each_entry(pos, &head, member) // 遍历
```
**优势**: 统一接口，内联优化
**效率提升**: 避免手写链表逻辑错误
**验证状态**: ✅ 已验证

---

## 技巧15: 工作队列异步处理
**场景**: 需要异步执行的工作
**模式**: 使用工作队列
**代码**:
```c
struct work_struct my_work;
INIT_WORK(&my_work, work_handler);
schedule_work(&my_work);  // 提交到工作队列
```
**优势**: 不阻塞当前上下文，可延迟执行
**效率提升**: 系统统一管理工作线程
**验证状态**: ✅ 已验证

---

## 技巧16: 定时器处理
**场景**: 延迟或周期性任务
**模式**: 使用内核定时器
**代码**:
```c
struct timer_list my_timer;
timer_setup(&my_timer, timer_callback, 0);
my_timer.expires = jiffies + HZ;  // 1秒后
add_timer(&my_timer);
```
**优势**: 基于jiffies，精度足够
**效率提升**: 避免忙等待
**验证状态**: ✅ 已验证

---

## 学习统计
- **阅读代码行数**: ~2000行 (内核API文档)
- **累计提取技巧**: 16个
- **验证状态**: 14个已验证，2个待验证
- **累计耗时**: 约45分钟

## 技巧分类

### 内存管理 (技巧2, 6, 9, 12, 13)
- __init/__exit 优化
- copy_to/from_user 安全拷贝
- ERR_PTR 错误处理
- RCU 无锁读取
- 内存屏障

### 并发控制 (技巧5, 11, 12)
- atomic_cmpxchg
- 原子位操作
- RCU

### 数据结构 (技巧10, 14)
- container_of
- 标准链表宏

### 异步处理 (技巧15, 16)
- 工作队列
- 定时器

## 下一步
1. 阅读进程管理 (sched/) 源码
2. 阅读内存管理 (mm/) 源码
3. 提取更多核心技巧
4. 创建第一个思想工具

---

*持续进化中...*
