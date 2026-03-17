# HEARTBEAT.md - 定期自检和检查清单

## 每日自检任务

### 自动运行
- **时间**: 每天上午9:00 (Asia/Shanghai)
- **任务**: daily-self-check
- **脚本**: `.tools/daily_self_check.py`
- **报告**: `.learning/daily-checks/daily-check-YYYYMMDD.json`

### 自检内容
1. 回顾过去24小时的工作记录
2. 检查物理现实约束
3. 验证是否需要额外验证
4. 警告过度推断
5. 生成改进建议

## 每周学习任务

### 自动运行
- **时间**: 每周一晚上21:00 (Asia/Shanghai)
- **任务**: self-driven-learning
- **脚本**: `.tools/self_driven_learning.py`
- **功能**: 识别知识缺口，制定学习计划，启动学习流程

### 学习内容
1. 分析MEMORY.md识别知识缺口
2. 根据缺口制定学习目标
3. 分解学习任务(理论→案例→实践→验证)
4. 创建学习计划和任务文件
5. 开始执行第一个任务

## 技能进化检查（每个项目后）

### 检查清单
- [ ] 提取了3+小技巧？
- [ ] 记录了效率和成功率？
- [ ] 有新技巧达到验证阈值(3次)？
- [ ] 可以组合成新工具？
- [ ] 需要更新教学指南？

### 使用工具
```python
from skill_evolution_framework import SkillEvolutionEngine

engine = SkillEvolutionEngine("skill-name")

# 1. 提取技巧
tip = engine.extract_tip(task, solution, result)

# 2. 验证技巧
engine.verify_tip(tip.id, new_task, success)

# 3. 创造工具
tool = engine.create_mental_tool("ToolName", [tip1.id, tip2.id])

# 4. 验证工具
engine.verify_tool(tool.id, success, feedback)

# 5. 生成教学
engine.teach_skill()

# 6. 生成报告
engine.generate_evolution_report()
```

## 手动触发
```bash
# 每日自检
python3 .tools/daily_self_check.py

# 启动学习
python3 .tools/self_driven_learning.py

# 技能进化
python3 .tools/skill_evolution_framework.py
```

## 检查清单（每次重要任务前）

### 物理现实检查
- [ ] 涉及真实世界实体？→ 查询物理约束
- [ ] 时间尺度合理？→ 人类响应分钟级，不是秒级
- [ ] 资源限制考虑？→ CPU/内存/网络都是有限的

### 验证流程检查
- [ ] 新设计方案？→ 需要小规模测试
- [ ] 从单一案例推断？→ 寻找更多证据
- [ ] 假设未经证实？→ 查阅文献

### 过度推断检查
- [ ] 使用绝对化词语？→ "总是"、"从不"、"一定"
- [ ] 从个人经验推广？→ 可能只是特例
- [ ] 忽略边界条件？→ 极端情况会怎样

## 查看历史报告
```bash
ls -la .learning/daily-checks/
cat .learning/daily-checks/daily-check-20260310.json
```

## 技能库
```bash
ls -la .learning/skills/
cat .learning/skills/{skill-name}/evolution_report.md
```

## 如有问题
如果自检发现警告：
1. 查看详细报告
2. 根据建议采取行动
3. 更新设计或文档
4. 记录学习到MEMORY.md
