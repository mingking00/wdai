# ClawFlow Enhancement Plan

## 当前状态
- 8个基础节点
- 单线程执行
- 内存运行
- 基础表达式

## 增强方向

### Phase 1: 核心节点扩展 (高优先级)
- [ ] FileNode - 文件读写、移动、复制
- [ ] DatabaseNode - SQLite 支持
- [ ] EmailNode - 邮件发送
- [ ] CronNode - 定时触发
- [ ] LLMNode - 调用大模型

### Phase 2: 执行增强
- [ ] 并行执行 (asyncio)
- [ ] 错误重试机制
- [ ] 工作流持久化 (保存/加载 JSON)
- [ ] 执行日志详细记录

### Phase 3: 开发体验
- [ ] 工作流验证器
- [ ] 节点模板系统
- [ ] 更强大的表达式
- [ ] 可视化调试输出

### Phase 4: 系统集成
- [ ] OpenClaw cron 集成
- [ ] 消息系统集成
- [ ] 外部工具调用

## 下一步
开始 Phase 1：添加最实用的节点
