"""
Session Memory 自动提取系统
基于认知负荷触发，而非时间触发

提取时机：
- 上下文接近压缩阈值
- 任务完成边界
- 用户明确标记"记住"
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class SessionMemoryExtractor:
    """会话记忆提取器"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.memory_dir = Path(".claw-status/session-memory")
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # 触发阈值
        self.extraction_thresholds = {
            "context_size": 8000,      # 8K tokens 首次提取
            "incremental": 4000,       # 之后每4K增量
            "task_boundary": True,     # 任务边界提取
        }
        
        self.last_extraction_tokens = 0
    
    def should_extract(self, current_tokens: int) -> bool:
        """判断是否应该提取记忆"""
        tokens_since_last = current_tokens - self.last_extraction_tokens
        
        # 首次触发
        if self.last_extraction_tokens == 0 and current_tokens >= self.extraction_thresholds["context_size"]:
            return True
        
        # 增量触发
        if tokens_since_last >= self.extraction_thresholds["incremental"]:
            return True
        
        return False
    
    def extract_key_information(self, conversation_history: List[Dict]) -> Dict:
        """
        从对话历史中提取关键信息
        
        提取维度：
        1. 当前状态 - 正在进行的任务
        2. 关键决策 - 为什么选择某个方案
        3. 遇到的错误和解决
        4. 用户明确表达的偏好
        """
        extracted = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "current_state": [],
            "key_decisions": [],
            "errors_solved": [],
            "user_preferences": [],
            "tools_used": []
        }
        
        for msg in conversation_history[-20:]:  # 只看最近20条
            content = msg.get("content", "")
            
            # 提取用户明确偏好
            if msg.get("role") == "user":
                pref = self._extract_preference(content)
                if pref:
                    extracted["user_preferences"].append(pref)
            
            # 提取决策（我做出的选择）
            if msg.get("role") == "assistant":
                decision = self._extract_decision(content)
                if decision:
                    extracted["key_decisions"].append(decision)
                
                # 提取错误解决
                error_solved = self._extract_error_resolution(content)
                if error_solved:
                    extracted["errors_solved"].append(error_solved)
                
                # 记录工具使用
                tools = self._extract_tools_used(content)
                extracted["tools_used"].extend(tools)
        
        return extracted
    
    def _extract_preference(self, content: str) -> Optional[str]:
        """提取用户偏好"""
        # 匹配 "我喜欢...", "我更...", "不要..." 等模式
        patterns = [
            r"我喜欢(.{3,30})",
            r"我更(喜欢|倾向于)(.{3,30})",
            r"不要(.{3,30})",
            r"记得(.{3,30})",
            r"以后(.{3,30})",
        ]
        for p in patterns:
            match = re.search(p, content)
            if match:
                return match.group(0)
        return None
    
    def _extract_decision(self, content: str) -> Optional[str]:
        """提取关键决策"""
        # 匹配决策描述
        patterns = [
            r"我选择(.{3,40})",
            r"决定(使用|采用)(.{3,40})",
            r"基于此，(.{3,40})",
        ]
        for p in patterns:
            match = re.search(p, content)
            if match:
                return match.group(0)
        return None
    
    def _extract_error_resolution(self, content: str) -> Optional[str]:
        """提取错误解决"""
        if "错误" in content or "失败" in content or "修复" in content:
            # 提取错误和解决方案（简化版）
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if '错误' in line or '失败' in line:
                    # 取错误描述和后续2行（可能是解决方案）
                    context = ' | '.join(lines[i:i+3])
                    return context[:150]
        return None
    
    def _extract_tools_used(self, content: str) -> List[str]:
        """提取使用的工具"""
        tools = []
        tool_patterns = [
            (r"使用(`?\w+`?)工具", 1),
            (r"运行`?\w+`?命令", 0),
            (r"调用`?\w+`?函数", 0),
        ]
        for pattern, group in tool_patterns:
            matches = re.findall(pattern, content)
            tools.extend(matches)
        return list(set(tools))[:5]  # 去重，最多5个
    
    def save_memory(self, extracted: Dict):
        """保存提取的记忆"""
        memory_file = self.memory_dir / f"{self.session_id}.json"
        
        # 读取已有记忆（如果有）
        existing = []
        if memory_file.exists():
            try:
                with open(memory_file, 'r') as f:
                    existing = json.load(f)
            except:
                existing = []
        
        # 追加新记忆
        if isinstance(existing, list):
            existing.append(extracted)
        else:
            existing = [extracted]
        
        # 保存
        with open(memory_file, 'w') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    
    def generate_summary(self) -> str:
        """生成记忆摘要"""
        memory_file = self.memory_dir / f"{self.session_id}.json"
        
        if not memory_file.exists():
            return "暂无记忆"
        
        with open(memory_file, 'r') as f:
            memories = json.load(f)
        
        if not memories:
            return "暂无记忆"
        
        # 汇总
        all_prefs = []
        all_decisions = []
        all_errors = []
        
        for m in memories:
            all_prefs.extend(m.get("user_preferences", []))
            all_decisions.extend(m.get("key_decisions", []))
            all_errors.extend(m.get("errors_solved", []))
        
        lines = ["## Session Memory 摘要", ""]
        
        if all_prefs:
            lines.extend(["### 用户偏好", ""])
            for p in set(all_prefs):
                lines.append(f"- {p}")
            lines.append("")
        
        if all_decisions:
            lines.extend(["### 关键决策", ""])
            for d in set(all_decisions):
                lines.append(f"- {d}")
            lines.append("")
        
        if all_errors:
            lines.extend(["### 错误与解决", ""])
            for e in set(all_errors):
                lines.append(f"- {e}")
            lines.append("")
        
        return "\n".join(lines)


# 便捷函数
def extract_session_memory(session_id: str, conversation_history: List[Dict], 
                          current_tokens: int) -> bool:
    """
    便捷函数：检查并提取会话记忆
    
    Returns:
        是否进行了提取
    """
    extractor = SessionMemoryExtractor(session_id)
    
    if extractor.should_extract(current_tokens):
        extracted = extractor.extract_key_information(conversation_history)
        extractor.save_memory(extracted)
        return True
    
    return False


if __name__ == "__main__":
    # 测试
    extractor = SessionMemoryExtractor("test_session")
    
    # 模拟对话
    history = [
        {"role": "user", "content": "帮我写一个Python脚本"},
        {"role": "assistant", "content": "我选择使用requests库来实现HTTP请求"},
        {"role": "user", "content": "我喜欢用简洁的代码风格"},
        {"role": "assistant", "content": "修复了之前的错误，现在可以正常运行了"},
    ]
    
    extracted = extractor.extract_key_information(history)
    print(json.dumps(extracted, ensure_ascii=False, indent=2))
