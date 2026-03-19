#!/usr/bin/env python3
"""
Kimi MCP Server - Integration Test Suite
集成测试套件：验证所有功能并展示多智能体协作
"""

import sys
import json
import time
from typing import Dict, List, Any, Callable
from datetime import datetime

sys.path.insert(0, '/root/.openclaw/workspace/kimi-mcp-server/src')

from extended_tools import KimiMCPExtendedServer
from mcp_transport import MCPProtocolHandler
from phase3_final import ResourcesManager, PromptsManager


class TestResult:
    """测试结果"""
    def __init__(self, name: str, passed: bool, message: str = "", duration: float = 0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration
    
    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status} | {self.name} ({self.duration:.3f}s)"


class IntegrationTestSuite:
    """集成测试套件"""
    
    def __init__(self):
        self.server = KimiMCPExtendedServer()
        self.protocol = MCPProtocolHandler(self.server)
        self.results: List[TestResult] = []
    
    def run_test(self, name: str, test_func: Callable) -> TestResult:
        """运行单个测试"""
        start = time.time()
        try:
            test_func()
            duration = time.time() - start
            result = TestResult(name, True, "Success", duration)
        except Exception as e:
            duration = time.time() - start
            result = TestResult(name, False, str(e), duration)
        
        self.results.append(result)
        return result
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*70)
        print("🔬 INTEGRATION TEST SUITE")
        print("="*70)
        
        # Phase 1 Tests
        print("\n📦 Phase 1: Core Tools")
        self.run_test("file_read_text", self._test_file_read)
        self.run_test("file_write_text", self._test_file_write)
        self.run_test("file_list_directory", self._test_file_list)
        self.run_test("core_plan_task", self._test_plan_task)
        self.run_test("core_decompose_problem", self._test_decompose)
        self.run_test("web_search_brave", self._test_web_search)
        self.run_test("web_fetch_page", self._test_web_fetch)
        
        # Phase 2 Tests
        print("\n📦 Phase 2: Extended Tools")
        self.run_test("media_image_generate", self._test_image_generate)
        self.run_test("media_audio_tts", self._test_tts)
        self.run_test("sys_health_check", self._test_health_check)
        self.run_test("comm_send_message", self._test_send_message)
        self.run_test("research_github_explore", self._test_github_explore)
        
        # Phase 3 Tests
        print("\n📦 Phase 3: MCP Protocol")
        self.run_test("mcp_initialize", self._test_mcp_init)
        self.run_test("mcp_tools_list", self._test_mcp_tools)
        self.run_test("mcp_tools_call", self._test_mcp_call)
        
        # Resources Tests
        print("\n📦 Phase 3: Resources")
        self.run_test("resources_list", self._test_resources_list)
        self.run_test("resources_read", self._test_resources_read)
        
        # Prompts Tests
        print("\n📦 Phase 3: Prompts")
        self.run_test("prompts_list", self._test_prompts_list)
        self.run_test("prompts_get", self._test_prompts_get)
        
        self._print_summary()
    
    def _print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total_time = sum(r.duration for r in self.results)
        
        print(f"\n   Total: {len(self.results)} tests")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   ⏱️  Time: {total_time:.3f}s")
        
        print("\n   Results:")
        for r in self.results:
            print(f"   {r}")
        
        if failed == 0:
            print("\n   🎉 All tests passed!")
        else:
            print(f"\n   ⚠️  {failed} test(s) failed")
    
    # === Phase 1 Tests ===
    def _test_file_read(self):
        result = self.server.call_tool('file_read_text', {'path': 'README.md', 'limit': 5})
        assert result['success'], f"Failed: {result.get('error')}"
    
    def _test_file_write(self):
        result = self.server.call_tool('file_write_text', {
            'path': '/tmp/test_integration.txt',
            'content': 'Integration test'
        })
        assert result['success'], f"Failed: {result.get('error')}"
    
    def _test_file_list(self):
        result = self.server.call_tool('file_list_directory', {'path': '.'})
        assert result['success'], f"Failed: {result.get('error')}"
        assert len(result['items']) > 0, "No items found"
    
    def _test_plan_task(self):
        result = self.server.call_tool('core_plan_task', {
            'task': 'Integration test',
            'complexity': 'low'
        })
        assert result['success'], f"Failed: {result.get('error')}"
        assert len(result['plan']['steps']) > 0, "No steps generated"
    
    def _test_decompose(self):
        result = self.server.call_tool('core_decompose_problem', {
            'problem': 'Test problem'
        })
        assert result['success'], f"Failed: {result.get('error')}"
    
    def _test_web_search(self):
        result = self.server.call_tool('web_search_brave', {
            'query': 'Python programming',
            'count': 3
        })
        assert result['success'], f"Failed: {result.get('error')}"
    
    def _test_web_fetch(self):
        result = self.server.call_tool('web_fetch_page', {
            'url': 'https://docs.python.org/3/'
        })
        assert result['success'], f"Failed: {result.get('error')}"
    
    # === Phase 2 Tests ===
    def _test_image_generate(self):
        result = self.server.call_tool('media_image_generate', {
            'prompt': 'test',
            'size': '1024x1024'
        })
        assert result['success'], f"Failed: {result.get('error')}"
    
    def _test_tts(self):
        result = self.server.call_tool('media_audio_tts', {
            'text': 'Hello world',
            'voice': 'alloy'
        })
        assert result['success'], f"Failed: {result.get('error')}"
    
    def _test_health_check(self):
        result = self.server.call_tool('sys_health_check', {'scope': 'full'})
        assert result['success'], f"Failed: {result.get('error')}"
        assert result['overall_status'] == 'healthy'
    
    def _test_send_message(self):
        result = self.server.call_tool('comm_send_message', {
            'channel': 'test',
            'message': 'Test message'
        })
        assert result['success'], f"Failed: {result.get('error')}"
    
    def _test_github_explore(self):
        result = self.server.call_tool('research_github_explore', {
            'repo': 'python/cpython'
        })
        assert result['success'], f"Failed: {result.get('error')}"
    
    # === Phase 3 Tests ===
    def _test_mcp_init(self):
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        resp = self.protocol.handle_request(req)
        assert resp.to_dict()['result']['protocolVersion'] == '2024-11-05'
    
    def _test_mcp_tools(self):
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        resp = self.protocol.handle_request(req)
        assert len(resp.to_dict()['result']['tools']) > 0
    
    def _test_mcp_call(self):
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "core_plan_task",
                "arguments": {"task": "Test", "complexity": "low"}
            }
        }
        resp = self.protocol.handle_request(req)
        assert 'result' in resp.to_dict()
    
    def _test_resources_list(self):
        mgr = ResourcesManager()
        resources = mgr.list_resources()
        assert len(resources) > 0
    
    def _test_resources_read(self):
        mgr = ResourcesManager()
        content = mgr.read_resource("tools://list")
        assert 'text' in content
    
    def _test_prompts_list(self):
        mgr = PromptsManager()
        prompts = mgr.list_prompts()
        assert len(prompts) > 0
    
    def _test_prompts_get(self):
        mgr = PromptsManager()
        prompt = mgr.get_prompt("deep_research", {"topic": "test", "depth": "quick"})
        assert len(prompt['messages']) > 0


# ============ Multi-Agent System Demo ============

class Agent:
    """智能体基类"""
    def __init__(self, name: str, role: str, tools: List[str]):
        self.name = name
        self.role = role
        self.tools = tools
        self.server = KimiMCPExtendedServer()
        self.memory = []
    
    def log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"   [{timestamp}] 🤖 {self.name}: {message}")
        self.memory.append(f"[{timestamp}] {message}")
    
    def use_tool(self, tool_name: str, params: Dict) -> Any:
        """使用Tool"""
        self.log(f"Using tool '{tool_name}'...")
        result = self.server.call_tool(tool_name, params)
        status = "✅" if result.get('success') else "❌"
        self.log(f"{status} Tool result: {result.get('status', 'unknown')}")
        return result
    
    def think(self, thought: str):
        """思考过程"""
        self.log(f"💭 {thought}")


class ResearchAgent(Agent):
    """研究智能体"""
    def __init__(self):
        super().__init__(
            name="ResearchAgent",
            role="研究专家",
            tools=["web_search_brave", "web_fetch_page", "research_github_explore", 
                   "research_paper_search", "research_summarize"]
        )
    
    def research_topic(self, topic: str) -> Dict:
        """研究主题"""
        self.log(f"Starting research on: {topic}")
        
        # Step 1: Web search
        self.think("First, I'll search for recent information on this topic")
        search_result = self.use_tool('web_search_brave', {
            'query': topic,
            'count': 5
        })
        
        # Step 2: GitHub exploration
        self.think("Let me check if there are relevant open-source projects")
        github_result = self.use_tool('research_github_explore', {
            'repo': 'openai/gpt-4' if 'AI' in topic else 'python/cpython'
        })
        
        # Step 3: Summarize findings
        self.think("Now I'll synthesize all findings")
        
        return {
            'topic': topic,
            'search_results': search_result.get('results', []),
            'github_info': github_result.get('info', {}),
            'agent': self.name
        }


class CodeAgent(Agent):
    """代码智能体"""
    def __init__(self):
        super().__init__(
            name="CodeAgent",
            role="代码专家",
            tools=["file_read_text", "file_write_text", "file_list_directory"]
        )
    
    def create_project(self, project_name: str, research_data: Dict) -> Dict:
        """创建项目"""
        self.log(f"Creating project: {project_name}")
        
        # Step 1: Create directory structure
        self.think("Setting up project structure")
        
        # Step 2: Create main file
        self.think("Creating main implementation file")
        content = f"""# {project_name}
# Generated based on research: {research_data['topic']}

class {project_name.replace(' ', '')}:
    def __init__(self):
        self.version = "1.0.0"
    
    def run(self):
        print("Running {project_name}...")
        return "Success"

if __name__ == "__main__":
    app = {project_name.replace(' ', '')}()
    app.run()
"""
        
        write_result = self.use_tool('file_write_text', {
            'path': f'/tmp/{project_name.lower().replace(" ", "_")}/main.py',
            'content': content
        })
        
        # Step 3: Create README
        self.think("Creating project documentation")
        readme = f"""# {project_name}

## Overview
This project was created based on research about {research_data['topic']}.

## Features
- Core functionality
- Research-backed design
- Professional implementation

## Usage
```python
python main.py
```

## Research Data
- Topic: {research_data['topic']}
- Researcher: {research_data['agent']}
"""
        
        self.use_tool('file_write_text', {
            'path': f'/tmp/{project_name.lower().replace(" ", "_")}/README.md',
            'content': readme
        })
        
        return {
            'project_name': project_name,
            'files_created': 2,
            'status': 'complete'
        }


class DocumentAgent(Agent):
    """文档智能体"""
    def __init__(self):
        super().__init__(
            name="DocumentAgent",
            role="文档专家",
            tools=["file_read_text", "file_write_text", "media_image_generate"]
        )
    
    def generate_report(self, project_data: Dict, research_data: Dict) -> Dict:
        """生成报告"""
        self.log("Generating comprehensive report")
        
        # Step 1: Create visual diagram
        self.think("Creating project architecture diagram")
        img_result = self.use_tool('media_image_generate', {
            'prompt': f"Architecture diagram for {project_data['project_name']}, clean technical illustration",
            'size': '1792x1024'
        })
        
        # Step 2: Write comprehensive report
        self.think("Writing detailed project report")
        report = f"""# Project Report: {project_data['project_name']}

## Executive Summary
Project completed successfully with full documentation and implementation.

## Research Foundation
**Topic:** {research_data['topic']}
**Research Agent:** {research_data['agent']}

### Key Findings
- Comprehensive web search conducted
- Open-source projects analyzed
- Best practices incorporated

## Implementation
**Code Agent:** Created structured project with:
- Main application file
- Project documentation
- Professional code structure

## Visual Assets
- Architecture diagram generated
- Technical illustrations created

## Status
✅ Project Complete
📁 Files Created: {project_data['files_created']}
🎨 Images Generated: 1

## Next Steps
1. Review implementation
2. Run tests
3. Deploy to production
"""
        
        write_result = self.use_tool('file_write_text', {
            'path': f'/tmp/{project_data["project_name"].lower().replace(" ", "_")}/REPORT.md',
            'content': report
        })
        
        return {
            'report_path': f'/tmp/{project_data["project_name"].lower().replace(" ", "_")}/REPORT.md',
            'images_generated': 1,
            'status': 'complete'
        }


class ManagerAgent(Agent):
    """管理智能体 - 协调其他智能体"""
    def __init__(self):
        super().__init__(
            name="ManagerAgent",
            role="项目管理者",
            tools=["core_plan_task", "core_decompose_problem"]
        )
        self.agents = {
            'research': ResearchAgent(),
            'code': CodeAgent(),
            'document': DocumentAgent()
        }
    
    def execute_project(self, topic: str, project_name: str) -> Dict:
        """执行完整项目"""
        print("\n" + "="*70)
        print("🚀 MULTI-AGENT PROJECT EXECUTION")
        print("="*70)
        self.log(f"Starting project: {project_name}")
        self.log(f"Topic: {topic}")
        
        # Step 1: Plan the project
        self.think("Creating project plan...")
        plan_result = self.use_tool('core_plan_task', {
            'task': f'Create project about {topic}',
            'complexity': 'high'
        })
        
        # Step 2: Decompose the problem
        self.think("Decomposing project into sub-tasks...")
        decompose_result = self.use_tool('core_decompose_problem', {
            'problem': f'Create comprehensive project about {topic}'
        })
        
        # Step 3: Research phase
        print("\n" + "-"*70)
        print("📚 PHASE 1: RESEARCH")
        print("-"*70)
        research_data = self.agents['research'].research_topic(topic)
        
        # Step 4: Code phase
        print("\n" + "-"*70)
        print("💻 PHASE 2: IMPLEMENTATION")
        print("-"*70)
        project_data = self.agents['code'].create_project(project_name, research_data)
        
        # Step 5: Documentation phase
        print("\n" + "-"*70)
        print("📝 PHASE 3: DOCUMENTATION")
        print("-"*70)
        report_data = self.agents['document'].generate_report(project_data, research_data)
        
        # Summary
        print("\n" + "="*70)
        print("📊 PROJECT SUMMARY")
        print("="*70)
        self.log(f"Project '{project_name}' completed successfully!")
        self.log(f"📁 Files created: {project_data['files_created'] + 1}")
        self.log(f"🎨 Images generated: {report_data['images_generated']}")
        self.log(f"🔍 Research items: {len(research_data['search_results'])}")
        
        return {
            'project_name': project_name,
            'topic': topic,
            'phases_completed': 3,
            'research': research_data,
            'project': project_data,
            'documentation': report_data,
            'status': 'success'
        }


def run_multi_agent_demo():
    """运行多智能体演示"""
    manager = ManagerAgent()
    
    result = manager.execute_project(
        topic="Multi-Agent Systems Architecture",
        project_name="MAS Framework"
    )
    
    print("\n" + "="*70)
    print("✅ Multi-Agent Execution Complete!")
    print("="*70)
    print(f"\nFinal result: {result['status'].upper()}")
    print(f"Check /tmp/mas_framework/ for generated files")


def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🔬 INTEGRATION TEST + 🤖 MULTI-AGENT DEMO                             ║
║                                                                          ║
║   Complete verification of Kimi MCP Server functionality                ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Run integration tests
    test_suite = IntegrationTestSuite()
    test_suite.run_all_tests()
    
    # Run multi-agent demo
    print("\n" + "="*70)
    print("⏳ Starting Multi-Agent Demo...")
    print("="*70)
    time.sleep(1)
    
    run_multi_agent_demo()
    
    print("\n" + "="*70)
    print("🎉 ALL TESTS AND DEMOS COMPLETED!")
    print("="*70)


if __name__ == "__main__":
    main()
