# Session 09: L2/L3 安全分析

## 目标
构建深度安全分析能力，从简单的正则匹配升级到 AI 辅助的复杂漏洞检测。

## 前置要求
- ✅ s06: 安全审查 Agent (L1 Fast Check 已就绪)
- ✅ s03: 多 Agent 协调 (Coder + Reviewer 模式)

## 预计时间
6-8 小时

---

## 学习目标

完成本 Session 后，你将：

1. **理解静态分析工具的工作原理** (Semgrep/CodeQL)
2. **掌握 AI 辅助安全审查的流程** (LLM + 上下文)
3. **学会构建多层防御体系** (L1+L2+L3 协同)

---

## 三层架构回顾

```
Coder Agent → Security Agent
                ├── L1: Fast Check (0.1ms) - 正则/AST
                ├── L2: Static Analysis (1-10s) - Semgrep/CodeQL
                └── L3: AI Review (5-30s) - LLM 深度分析
```

---

## 实现步骤

### Step 1: 集成 Semgrep (L2)

**目标**: 使用 Semgrep 做 deeper static analysis

**技术选型**:
- **Semgrep**: 轻量级，规则易写，适合 Agent 场景
- 备选: CodeQL (太重), Bandit (Python only)

**实现**:
```python
# wdai_v3/core/security/l2_semgrep.py
class SemgrepAnalyzer:
    def analyze(self, code: str) -> AnalysisResult:
        # 1. 写入临时文件
        # 2. 调用 semgrep --config=auto
        # 3. 解析 JSON 输出
        # 4. 映射到统一的风险分数
```

**规则来源**:
- Semgrep Registry (p/security-audit, p/owasp-top-ten)
- 自定义规则 (针对 Agent 特定模式)

**验证**:
```bash
python -m wdai_v3.security.l2_semgrep test_vulnerable.py
# 期望: 检测到比 L1 更复杂的漏洞
```

### Step 2: AI 安全审查 (L3)

**目标**: 使用 LLM 做上下文感知的深度分析

**实现**:
```python
# wdai_v3/core/security/l3_ai_review.py
class AISecurityReviewer:
    def review(self, code: str, context: dict) -> ReviewResult:
        prompt = f"""
        审查以下代码的安全性。
        
        上下文:
        - 文件路径: {context['file_path']}
        - 项目类型: {context['project_type']}
        - 已发现问题: {context['l1_findings']}
        
        代码:
        ```python
        {code}
        ```
        
        请分析:
        1. 是否有复杂的逻辑漏洞？
        2. 是否有业务逻辑安全问题？
        3. 是否有不符合最佳实践的代码？
        
        输出 JSON 格式:
        {{
            "vulnerabilities": [...],
            "risk_score": 0-1,
            "suggested_fixes": [...]
        }}
        """
        return self.llm.call(prompt)
```

**优化策略**:
- **缓存**: 相同代码片段不重复调用
- **分批**: 大文件分块审查
- **上下文**: 传入 L1/L2 结果，避免重复发现

**验证**:
```python
# 测试复杂漏洞
code = """
def transfer_money(user, amount, target):
    # 业务逻辑漏洞: 没有验证 target 是否属于 user
    if user.balance >= amount:
        user.balance -= amount
        target.balance += amount
"""
result = l3_review(code)
assert result.has_business_logic_vulnerability
```

### Step 3: 三层协同 Orchestrator

**目标**: 智能调度 L1/L2/L3，平衡速度和深度

**实现**:
```python
# wdai_v3/core/security/layered_orchestrator.py
class LayeredSecurityOrchestrator:
    def analyze(self, code: str, context: dict) -> SecurityReport:
        # 总是运行 L1
        l1_result = self.l1.check(code)
        
        # 根据 L1 风险分数决定是否运行 L2
        if l1_result.risk_score > 0.3:
            l2_result = self.l2.analyze(code)
            l1_result.merge(l2_result)
        
        # 根据综合风险决定是否运行 L3
        if l1_result.risk_score > 0.7:
            l3_result = self.l3.review(code, context)
            l1_result.merge(l3_result)
        
        return SecurityReport(
            layers_executed=["L1", "L2", "L3"],
            total_time=...,  # 动态，取决于运行了哪些层
            findings=...
        )
```

**触发策略**:
| 场景 | 执行层 | 预计时间 |
|:---|:---:|:---:|
| 简单脚本，无危险模式 | L1 | 0.1ms |
| 检测到可疑模式 | L1 + L2 | 1-10s |
| 高风险代码或复杂逻辑 | L1 + L2 + L3 | 5-30s |

### Step 4: Coder Agent 集成

**目标**: Security Agent 自动在代码生成后触发

**修改点**:
```python
# wdai_v3/agents/coder.py
class CoderAgent:
    def generate_code(self, task: Task) -> CodeResult:
        # 1. 生成代码 (现有逻辑)
        code = self.llm.generate(task.description)
        
        # 2. 自动安全审查 (新增)
        security_report = self.security_orchestrator.analyze(
            code=code,
            context={
                "file_path": task.target_file,
                "project_type": self.detect_project_type(),
                "task_description": task.description
            }
        )
        
        # 3. 根据风险决定是否阻止
        if security_report.risk_score > 0.8:
            return CodeResult(
                code=None,
                error="Security check failed",
                security_report=security_report
            )
        
        return CodeResult(
            code=code,
            security_report=security_report
        )
```

---

## 验收标准

- [ ] L2 (Semgrep) 能检测 L1 遗漏的复杂漏洞
- [ ] L3 (AI Review) 能发现业务逻辑漏洞
- [ ] 三层协同工作，自动根据风险调整深度
- [ ] Coder Agent 生成代码后自动触发安全审查
- [ ] 高风险代码 (score > 0.8) 自动阻止提交
- [ ] 安全审查报告包含修复建议

---

## 经验总结

### 学到的原则

1. **分层防御**: 快速层过滤明显问题，深度层处理复杂场景
2. **动态调度**: 不是所有代码都需要深度分析，根据风险调整
3. **上下文传递**: L1/L2 结果传给 L3，避免重复工作

### 常见陷阱

- **过度调用 L3**: LLM 成本高，需要有明确的触发条件
- **误报率**: L2/L3 可能产生误报，需要白名单机制
- **延迟**: L3 较慢，不能阻塞快速迭代流程

### 延伸阅读

- [Semgrep Documentation](https://semgrep.dev/docs/)
- [OWASP Code Review Guide](https://owasp.org/www-project-code-review-guide/)
- [AI for Security: Opportunities and Challenges](https://ai.stanford.edu/blog/ai-for-security/)

---

## 前后对比

### Before
- 只有 L1 (Fast Check)
- 能检测简单的 eval/exec
- 无法发现业务逻辑漏洞
- 检测能力: 12 → 53 条规则

### After
- L1 + L2 + L3 三层架构
- 能检测复杂漏洞和业务逻辑问题
- AI 提供修复建议
- 智能调度，平衡速度和深度

---

## 下一步

完成本 Session 后，可以：

- **s10**: 自动会话摘要 - 自动提取关键信息
- **扩展**: 添加更多 L2 工具 (CodeQL, Bandit)

---

*Session 设计完成时间: 2026-03-18*
