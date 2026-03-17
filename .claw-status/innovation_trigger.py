# 创新触发器系统
# Innovation Trigger System
# 强制执行：同一方法失败3次后必须换路

import os
import json
from datetime import datetime

STATE_FILE = "/root/.openclaw/workspace/.claw-status/innovation_state.json"

def load_state():
    """加载失败计数状态"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    """保存失败计数状态"""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def record_failure(method_name, task_id):
    """
    记录方法失败，自动检测是否需要触发创新
    
    使用方式：
        from innovation_trigger import record_failure, MUST_INNOVATE
        
        if attempt_failed:
            result = record_failure("github_api_upload", "blog_deploy")
            if result["trigger"]:
                print(f"⚠️ 强制创新触发！已失败{result['count']}次")
                # 必须换方法，不能再用原方法
    """
    state = load_state()
    key = f"{task_id}:{method_name}"
    
    if key not in state:
        state[key] = {"count": 0, "first_fail": datetime.now().isoformat()}
    
    state[key]["count"] += 1
    state[key]["last_fail"] = datetime.now().isoformat()
    
    save_state(state)
    
    count = state[key]["count"]
    return {
        "count": count,
        "trigger": count >= 3,  # 3次失败强制触发创新
        "method": method_name,
        "task": task_id
    }

def reset_counter(method_name, task_id):
    """成功后重置计数器"""
    state = load_state()
    key = f"{task_id}:{method_name}"
    if key in state:
        del state[key]
        save_state(state)

def get_status(task_id=None):
    """查看当前失败状态"""
    state = load_state()
    if task_id:
        return {k: v for k, v in state.items() if k.startswith(f"{task_id}:")}
    return state

# 强制创新标记
MUST_INNOVATE = "MUST_SWITCH_METHOD"

def check_innovation_required(method_name, task_id):
    """
    检查是否必须创新（换方法）
    
    在尝试方法前调用：
        if check_innovation_required("github_api", "upload"):
            raise Exception("该方法已失败3次，必须换路！")
    """
    state = load_state()
    key = f"{task_id}:{method_name}"
    
    if key in state and state[key]["count"] >= 3:
        return True
    return False

if __name__ == "__main__":
    # 测试
    print("创新触发器系统状态：")
    print(json.dumps(get_status(), indent=2))
