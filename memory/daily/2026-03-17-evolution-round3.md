

---

## 进化内循环第3轮 - 代码依赖图模块解析修复

**时间**: 2026-03-17 19:35  
**问题**: build_dependency_graph 生成0条边

### 根因分析
两轮构建流程错误：
```python
# 错误：第二轮逐个添加时，解析导入时其他节点还未加入
for file_path, analysis in analyses.items():
    graph.add_file(analysis, resolve_imports=True)  # 解析时图不完整
```

### 修复方案
改为三轮构建：
```python
# 第一轮：分析所有文件
analyses = {file: analyze(content) for file, content in files.items()}

# 第二轮：添加所有节点（不解析）
for file_path, analysis in analyses.items():
    graph.add_file(analysis, resolve_imports=False)

# 第三轮：解析所有导入（图已完整）
for file_path, analysis in analyses.items():
    graph._resolve_imports(analysis)
```

### 同时改进的模块解析
- 支持目录匹配：`auth` 匹配 `src/auth/*.py`
- 支持模糊匹配：`service` 匹配任意位置的 `service.py`
- 支持精确匹配：`auth.service` 匹配 `auth/service.py`

### 测试结果
```
边数: 3
src/main.py -> {'src/db/repository.py', 'src/auth/service.py'}
src/auth/service.py -> {'src/db/repository.py'}
```

### 10项测试全部通过 ✅

---
