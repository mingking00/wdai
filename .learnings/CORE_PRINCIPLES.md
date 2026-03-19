# Core Operating Principles

## 1. Progressive Disclosure Architecture
从元数据 → 主体 → 参考资源的渐进式加载，最小化上下文消耗。
- 仅加载当前任务必需的信息
- Skill 触发后才加载完整指令
- 参考资源按需读取

## 2. Reusable Asset Pattern
识别重复任务 → 提取脚本/模板/参考 → 资产化沉淀。
- 重复写的代码 → scripts/
- 重复查的文档 → references/
- 重复用的模板 → assets/

## 3. Feedback Loop Integration
错误/修正 → 记录 → 分析模式 → 提升为规则 → 注入系统提示。
- 即时记录到 .learnings/
- 周期性复盘提炼
- 高频模式升级至 SKILL/AGENTS.md

## 4. Tool Composition Strategy
单一工具做一件事，组合工具完成复杂任务。
- browser + summarize = 网页情报提取
- github + coding-agent = 代码审查工作流
- cron + message = 自动化推送

## 5. Context Efficiency First
Token 是有限资源，每个字必须服务于交付。
- SKILL.md < 500 行
- 使用 refs 而非完整内容
- 避免冗余说明
