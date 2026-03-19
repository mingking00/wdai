# 创新执行强制流程
# 解决"有原则但不执行"问题

## 自动触发机制

### 失败计数器（已部署）
```python
from .claw-status.innovation_trigger import record_failure, check_innovation_required

# 每次方法失败时记录
result = record_failure("方法名", "任务ID")
if result["trigger"]:
    print("⚠️ 强制创新触发！必须换完全不同的方法")
    # 原方法被锁定，必须创新
```

### 强制执行规则

**规则1: 3次失败锁定**
- 同一方法失败3次 → 自动锁定该方法
- 再次尝试该方法 → 系统阻断，提示"必须创新"

**规则2: 强制提问清单**
达到3次失败时，必须回答：
```
□ 还有什么完全不同的工具可以解决这个问题？
□ 能否绕过这个步骤？
□ 能否用本地工具替代远程API？
□ 能否换协议（HTTP→Git/SSH）？
□ 能否让用户手动操作？
```

**规则3: 成功验证**
- 报告"成功"前 → 必须验证结果
- 上传文件 → 必须下载验证内容一致
- 部署成功 → 必须访问URL确认

---

## 本次案例复盘

### 执行缺陷
| 次数 | 方法 | 结果 | 应该做什么 |
|------|------|------|-----------|
| 1 | GitHub API | 超时 | 记录失败 |
| 2 | GitHub API | 超时 | 记录失败 |
| 3 | GitHub API | 超时 | **触发强制创新** |
| 4 | GitHub API | 超时 | 系统应该阻断，提示换方法 |
| 5 | GitHub API | 超时 | ... |
| 6 | GitHub API | 超时 | ... |
| N | Git push | 成功 | 用户倒逼下才换路 |

### 改进后（理想流程）
```
API失败1次 → 记录
API失败2次 → 记录  
API失败3次 → 系统强制阻断："必须换方法"
           → 自动提问："还有什么完全不同的工具？"
           → 回答：Git协议、本地构建、用户手动...
           → 执行Git push → 成功
```

---

## 防止自欺欺人

**原错误模式：**
- 我："上传成功！"
- 实际：网络超时，文件未变
- 原因：没验证远程文件

**强制验证：**
```
上传后必须：
1. 下载远程文件
2. 对比本地内容
3. 一致 → 报告成功
4. 不一致 → 报告"上传失败，需重试"
```

---

## 执行检查点

在每个任务中插入检查点：

```python
# 检查点1: 方法是否被锁定？
if check_innovation_required("当前方法", "任务ID"):
    raise InnovationRequired("必须换方法！")

# 执行方法...

# 检查点2: 失败则记录
if failed:
    result = record_failure("当前方法", "任务ID")
    if result["trigger"]:
        print("强制创新触发！不能再使用此方法")
        # 必须换路

# 检查点3: 成功验证
if success:
    verify_result()  # 必须验证
    report_success() # 才能报告成功
```

---

## 集成到工作流程

**每次执行前自动运行：**
```bash
python3 .claw-status/innovation_trigger.py
```

**查看当前状态：**
```python
from innovation_trigger import get_status
print(get_status())  # 查看各方法失败次数
```

---

*Created: 2026-03-16*
*Purpose: 把创新能力从"原则"变成"强制执行的系统"*
