# progress_reporter.py - 进度报告装饰器
# 自动为所有任务添加进度追踪

import functools
import time
from pathlib import Path
import sys

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))
from work_monitor import WorkMonitor, WorkStatus

class ProgressReporter:
    """
    进度报告装饰器
    
    用法:
    @ProgressReporter.track("正在分析代码")
    def analyze_code(file_path):
        # 工作代码
        pass
    """
    
    monitor = WorkMonitor()
    
    @classmethod
    def track(cls, task_name: str, steps: int = 0):
        """装饰器：追踪函数执行"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 开始会话
                session_id = cls.monitor.start_session(task_name, steps)
                
                try:
                    # 执行函数
                    result = func(*args, **kwargs)
                    
                    # 完成
                    cls.monitor.complete(f"完成: {task_name}")
                    return result
                    
                except Exception as e:
                    cls.monitor.error(str(e), recoverable=False)
                    raise
                    
            return wrapper
        return decorator
    
    @classmethod
    def step(cls, step_name: str, increment: bool = True):
        """报告当前步骤"""
        session = cls.monitor.current_session
        if session:
            current = session.completed_steps + 1 if increment else session.completed_steps
            cls.monitor.update_progress(step_name, current, session.total_steps)

# ============ 实时状态文件 ============

def write_status_file(status: str, detail: str = ""):
    """
    写入状态到根目录的 STATUS.md
    用户可以随时 cat STATUS.md 查看
    """
    status_path = Path(__file__).parent.parent / "STATUS.md"
    
    content = f"""# 🤖 OpenClaw 工作状态

**更新时间**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 当前状态

- 🟢 **运行中** / 🟡 等待中 / 🔴 错误 / ⚪ 空闲

**当前任务**: {status}

{detail}

---

## 快速查看

```bash
# 查看详细状态
python3 .claw-status/work_monitor.py

# 查看历史
python3 .claw-status/work_monitor.py history

# 查看当前JSON
cat .claw-status/current.json
```

---

*此文件自动更新*
"""
    
    with open(status_path, 'w', encoding='utf-8') as f:
        f.write(content)

# 测试
if __name__ == "__main__":
    write_status_file("测试状态", "正在运行测试...")
    print("状态文件已写入 STATUS.md")
