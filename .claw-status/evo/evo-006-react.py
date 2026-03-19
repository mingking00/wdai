"""ReAct Agent - MVP | evo-006 | <150 lines | 3 tests passing"""
import json
from typing import List, Dict, Callable

class ReActAgent:
    """ReAct: Reasoning + Acting | Loop: Thought->Action->Observation->...->Answer"""
    
    def __init__(self, llm_fn: Callable[[str], str], tools: Dict[str, Callable]):
        self.llm = llm_fn
        self.tools = tools
        self.history: List[Dict] = []
        
    def run(self, task: str, max_steps: int = 10) -> str:
        prompt = self._build_prompt(task)
        for step in range(max_steps):
            response = self.llm(prompt)
            parsed = self._parse_response(response)
            self.history.append({"step": step, **parsed})
            if parsed.get("action") == "finish":
                return parsed.get("action_input", "")
            observation = self._execute_action(parsed.get("action", ""), parsed.get("action_input", ""))
            self.history[-1]["observation"] = observation
            prompt += f"\nObservation: {observation}\n"
        return self._force_answer(task)
    
    def _build_prompt(self, task: str) -> str:
        tool_desc = "\n".join([f"- {n}: {f.__doc__}" for n, f in self.tools.items()])
        return f"""You solve tasks by thinking step by step.
Available tools:
{tool_desc}
Task: {task}
Respond format:
Thought: <reasoning>
Action: <tool or finish>
Action Input: <input or answer>
Begin:
Thought:"""
    
    def _parse_response(self, response: str) -> Dict[str, str]:
        result = {}
        for line in response.strip().split("\n"):
            if line.startswith("Thought:"): result["thought"] = line[8:].strip()
            elif line.startswith("Action:"): result["action"] = line[7:].strip()
            elif line.startswith("Action Input:"): result["action_input"] = line[13:].strip()
        return result
    
    def _execute_action(self, action: str, action_input: str) -> str:
        if action == "finish": return "Done"
        if action not in self.tools: return f"Error: Unknown '{action}'"
        try: return str(self.tools[action](action_input))
        except Exception as e: return f"Error: {e}"
    
    def _force_answer(self, task: str) -> str:
        return self.llm(f"History: {json.dumps(self.history)}\nFinal answer:")

# Test Tools
def calculator(expr: str) -> float:
    """Calculate math expression | e.g. '15 + 27'"""
    return eval(expr, {"__builtins__": {}}, {"__import__": __import__})

def search(query: str) -> str:
    """Search information | e.g. 'Python ReAct'"""
    return {"react": "ReAct=Reasoning+Acting", "planning": "Planning=task decomposition"}.get(query.lower().split()[0], "No result")

# Mock LLM
def mock_llm(prompt: str) -> str:
    obs = prompt.count("Observation:")
    if "15 + 27" in prompt:
        if obs == 0: return "Thought: First add 15+27\nAction: calculator\nAction Input: 15 + 27"
        if obs == 1: return "Thought: Now multiply by 3\nAction: calculator\nAction Input: 42 * 3"
        if obs == 2: return "Thought: Now subtract 8\nAction: calculator\nAction Input: 126 - 8"
        return "Thought: Done\nAction: finish\nAction Input: 118"
    if "search" in prompt.lower():
        if obs == 0: return "Thought: Search for ReAct\nAction: search\nAction Input: react"
        return "Thought: Found it\nAction: finish\nAction Input: ReAct pattern info"
    return "Thought: Done\nAction: finish\nAction Input: Completed"

# Tests
def test_math():
    print("\n=== Test 1: Math ===")
    agent = ReActAgent(mock_llm, {"calculator": calculator})
    result = agent.run("Calculate (15+27)*3-8")
    print(f"Result: {result} | Steps: {len(agent.history)}")
    assert "118" in result, f"Expected 118, got {result}"
    print("✅ Passed")

def test_search():
    print("\n=== Test 2: Search ===")
    agent = ReActAgent(mock_llm, {"search": search})
    result = agent.run("What is ReAct?")
    print(f"Result: {result[:50]}... | Steps: {len(agent.history)}")
    assert "ReAct" in result
    print("✅ Passed")

def test_multi_step():
    print("\n=== Test 3: Multi-step ===")
    def llm(p):
        obs = p.count("Observation:")
        if obs == 0: return "Thought: Search A\nAction: search\nAction Input: react"
        if obs == 1: return "Thought: Search B\nAction: search\nAction Input: planning"
        return "Thought: Combined\nAction: finish\nAction Input: Combined result"
    agent = ReActAgent(llm, {"search": search})
    result = agent.run("Compare ReAct and Planning")
    print(f"Result: {result[:50]}... | Steps: {len(agent.history)}")
    assert len(agent.history) >= 2
    print("✅ Passed")

if __name__ == "__main__":
    print("ReAct MVP Tests")
    print("=" * 40)
    test_math()
    test_search()
    test_multi_step()
    print("\n" + "=" * 40)
    print("All tests passed! ✅")
    
    # Count lines
    import inspect
    lines = len(inspect.getsource(ReActAgent).split("\n"))
    print(f"\nCode: {lines} lines | Target: <150 | Status: {'✅' if lines < 150 else '⚠️'}")
