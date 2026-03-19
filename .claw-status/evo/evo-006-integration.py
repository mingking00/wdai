"""evo-006: ReAct Integration to WDai v3.7"""
import sys
import importlib.util

# Load ReActAgent from evo-006-react.py
spec = importlib.util.spec_from_file_location("react_agent", "/root/.openclaw/workspace/.claw-status/evo/evo-006-react.py")
react_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(react_module)
ReActAgent = react_module.ReActAgent

from typing import Dict, Callable, Any

class WDaiV37:
    """WDai v3.7 - With ReAct Planning"""
    
    def __init__(self, llm_fn: Callable[[str], str]):
        self.version = "3.7"
        self.llm = llm_fn
        
        # Register tools
        self.tools = {
            "read_file": self._tool_read_file,
            "write_file": self._tool_write_file,
            "search_memory": self._tool_search_memory,
            "calculator": self._tool_calculator,
        }
        
        # Initialize ReAct agent
        self.react = ReActAgent(llm_fn, self.tools)
    
    def process(self, task: str) -> str:
        """Process task with ReAct planning"""
        
        # Check if task needs multi-step planning
        if self._needs_planning(task):
            return self.react.run(task)
        else:
            # Simple tasks - direct LLM
            return self.llm(task)
    
    def _needs_planning(self, task: str) -> bool:
        """Determine if task needs ReAct planning"""
        
        planning_keywords = [
            "calculate", "compute", "and then", "search and", "find and",
            "multiple steps", "step by step", "plan", "decompose"
        ]
        
        task_lower = task.lower()
        return any(kw in task_lower for kw in planning_keywords)
    
    # ============ Tools ============
    
    def _tool_read_file(self, path: str) -> str:
        """Read file content | e.g. '/tmp/test.txt'"""
        try:
            with open(path.strip(), 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading {path}: {e}"
    
    def _tool_write_file(self, params: str) -> str:
        """Write to file | format: 'path|content'"""
        try:
            parts = params.split("|", 1)
            if len(parts) != 2:
                return "Error: format should be 'path|content'"
            path, content = parts
            with open(path.strip(), 'w') as f:
                f.write(content)
            return f"Written to {path}"
        except Exception as e:
            return f"Error writing {path}: {e}"
    
    def _tool_search_memory(self, query: str) -> str:
        """Search memory | e.g. 'what is ReAct'"""
        # Integrate with existing memory system
        from memory_search import memory_search
        try:
            results = memory_search(query, max_results=3)
            if results:
                return "\n".join([f"- {r.get('content', '')[:100]}..." for r in results])
            return "No memory found"
        except:
            return "Memory search unavailable"
    
    def _tool_calculator(self, expression: str) -> str:
        """Calculate math expression | e.g. '15 + 27'"""
        try:
            allowed = {"__builtins__": {}}
            result = eval(expression, allowed, {})
            return str(result)
        except Exception as e:
            return f"Error: {e}"


# Demo
def demo_llm(prompt: str) -> str:
    """Demo LLM for testing"""
    obs = prompt.count("Observation:")
    
    if "read" in prompt.lower() and obs == 0:
        return "Thought: I need to read the file\nAction: read_file\nAction Input: /tmp/test.txt"
    elif "write" in prompt.lower() and obs == 0:
        return "Thought: I need to write to the file\nAction: write_file\nAction Input: /tmp/output.txt|Hello World"
    elif obs > 0:
        return "Thought: Task completed\nAction: finish\nAction Input: Task done successfully"
    
    return "Thought: Simple task\nAction: finish\nAction Input: " + prompt[:50]


if __name__ == "__main__":
    print("WDai v3.7 - ReAct Integration Demo")
    print("=" * 50)
    
    wdai = WDaiV37(demo_llm)
    
    # Test 1: Simple task (no ReAct)
    print("\n1. Simple task:")
    result = wdai.process("Hello")
    print(f"   Result: {result[:50]}")
    
    # Test 2: Multi-step task (uses ReAct)
    print("\n2. Multi-step task (uses ReAct):")
    result = wdai.process("Read file and then write result")
    print(f"   Result: {result}")
    print(f"   ReAct steps: {len(wdai.react.history)}")
    
    # Test 3: Calculator
    print("\n3. Calculator tool:")
    result = wdai.tools["calculator"]("15 + 27")
    print(f"   15 + 27 = {result}")
    
    print("\n" + "=" * 50)
    print("WDai v3.7 initialized with ReAct planning ✅")
    print(f"Tools: {list(wdai.tools.keys())}")
