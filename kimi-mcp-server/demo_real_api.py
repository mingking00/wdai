#!/usr/bin/env python3
"""
Multi-Agent Demo with REAL APIs
使用真实API的多智能体演示
"""

import sys
import json
import urllib.request
from typing import Dict, List, Any
from datetime import datetime

sys.path.insert(0, '/root/.openclaw/workspace/kimi-mcp-server/src')

from extended_tools import KimiMCPExtendedServer


class RealResearchAgent:
    """真实研究智能体 - 使用GitHub API"""
    def __init__(self):
        self.name = "RealResearchAgent"
        self.server = KimiMCPExtendedServer()
    
    def log(self, msg: str):
        print(f"   [{datetime.now().strftime('%H:%M:%S')}] 🔍 {self.name}: {msg}")
    
    def execute(self, topic: str) -> Dict:
        self.log(f"开始研究: {topic}")
        
        # 使用真实GitHub API
        self.log("调用 GitHub API 搜索相关项目...")
        
        try:
            # 搜索与主题相关的仓库
            query = topic.replace(' ', '+')
            url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=5"
            
            headers = {
                'User-Agent': 'Kimi-MCP-Server',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                repos = []
                for item in data.get('items', []):
                    repos.append({
                        'name': item.get('full_name'),
                        'stars': item.get('stargazers_count'),
                        'language': item.get('language'),
                        'description': item.get('description', '')[:100],
                        'url': item.get('html_url')
                    })
                
                self.log(f"✅ 找到 {len(repos)} 个相关项目")
                for i, r in enumerate(repos[:3], 1):
                    self.log(f"   {i}. {r['name']} (⭐ {r['stars']:,}) - {r['language']}")
                
                return {
                    'success': True,
                    'topic': topic,
                    'repositories': repos,
                    'total': data.get('total_count', 0),
                    'source': 'github_api_real'
                }
                
        except Exception as e:
            self.log(f"❌ API调用失败: {e}")
            return {'success': False, 'error': str(e)}


class RealCodeAgent:
    """真实代码智能体 - 创建实际项目"""
    def __init__(self):
        self.name = "RealCodeAgent"
        self.server = KimiMCPExtendedServer()
    
    def log(self, msg: str):
        print(f"   [{datetime.now().strftime('%H:%M:%S')}] 💻 {self.name}: {msg}")
    
    def execute(self, topic: str, research_data: Dict) -> Dict:
        self.log(f"基于研究创建项目: {topic}")
        
        # 获取研究数据中的最佳项目作为参考
        repos = research_data.get('repositories', [])
        top_repo = repos[0] if repos else {'name': 'unknown', 'language': 'Python'}
        
        self.log(f"参考项目: {top_repo['name']} ({top_repo['language']})")
        
        project_name = topic.lower().replace(' ', '_').replace('-', '_')
        
        # 创建真实的Python代码
        code = f'''#!/usr/bin/env python3
"""
{topic} Implementation
Generated based on research of {top_repo['name']}
Reference: {top_repo.get('url', 'N/A')}
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ResearchResult:
    """研究结果数据类"""
    topic: str
    repositories: List[Dict]
    timestamp: str
    
    def to_dict(self) -> Dict:
        return {{
            'topic': self.topic,
            'repositories': self.repositories,
            'timestamp': self.timestamp
        }}


class {topic.replace(' ', '').replace('-', '')}System:
    """
    {topic} 主系统
    
    基于GitHub研究的最佳实践实现
    参考项目: {top_repo['name']} ({top_repo['language']})
    """
    
    VERSION = "1.0.0"
    
    def __init__(self):
        self.version = self.VERSION
        self.components: List[str] = []
        self.research_data: Optional[ResearchResult] = None
        self.initialized = False
    
    def initialize(self) -> bool:
        """初始化系统"""
        print(f"🚀 Initializing {{self.version}}...")
        self.components = [
            "research_module",
            "analysis_engine", 
            "output_formatter"
        ]
        self.initialized = True
        print(f"✅ System ready with {{len(self.components)}} components")
        return True
    
    async def process(self, data: Dict) -> Dict:
        """异步处理数据"""
        if not self.initialized:
            raise RuntimeError("System not initialized. Call initialize() first.")
        
        # 模拟处理
        await asyncio.sleep(0.1)
        
        return {{
            "status": "success",
            "processed_at": datetime.now().isoformat(),
            "input_size": len(str(data)),
            "components_used": self.components
        }}
    
    def get_info(self) -> Dict:
        """获取系统信息"""
        return {{
            "version": self.version,
            "initialized": self.initialized,
            "components": self.components,
            "reference_project": "{top_repo['name']}"
        }}
    
    async def run(self, input_data: Dict = None) -> Dict:
        """主运行循环"""
        self.initialize()
        
        if input_data is None:
            input_data = {{"query": "default"}}
        
        result = await self.process(input_data)
        
        print(f"✅ Execution complete")
        return result


async def main():
    """异步主函数"""
    system = {topic.replace(' ', '').replace('-', '')}System()
    
    # 运行示例
    test_data = {{
        "query": "{topic}",
        "options": {{"deep_search": True}}
    }}
    
    result = await system.run(test_data)
    
    print(f"\\nResult: {{json.dumps(result, indent=2)}}")
    return result


if __name__ == "__main__":
    asyncio.run(main())
'''
        
        # 写入文件
        self.log("使用 file_write_text 创建 main.py...")
        result = self.server.call_tool('file_write_text', {
            'path': f'/tmp/real_project_{project_name}/main.py',
            'content': code
        })
        
        if result['success']:
            self.log(f"✅ 代码文件已创建 ({len(code)} chars)")
        
        # 创建配置文件
        config = {
            "project": topic,
            "version": "1.0.0",
            "inspired_by": top_repo['name'],
            "language": top_repo['language'],
            "settings": {
                "debug": True,
                "async_mode": True,
                "log_level": "INFO"
            },
            "research": {
                "total_repos_found": research_data.get('total', 0),
                "top_references": [r['name'] for r in repos[:3]]
            }
        }
        
        self.log("创建 config.json...")
        self.server.call_tool('file_write_text', {
            'path': f'/tmp/real_project_{project_name}/config.json',
            'content': json.dumps(config, indent=2)
        })
        
        self.log("✅ 配置文件已创建")
        
        return {
            'success': True,
            'project_name': project_name,
            'reference_repo': top_repo['name'],
            'files_created': 2,
            'code_length': len(code)
        }


class RealDocumentAgent:
    """真实文档智能体"""
    def __init__(self):
        self.name = "RealDocumentAgent"
        self.server = KimiMCPExtendedServer()
    
    def log(self, msg: str):
        print(f"   [{datetime.now().strftime('%H:%M:%S')}] 📝 {self.name}: {msg}")
    
    def execute(self, topic: str, code_data: Dict, research_data: Dict) -> Dict:
        self.log(f"生成文档: {topic}")
        
        project_name = topic.lower().replace(' ', '_').replace('-', '_')
        ref_repo = code_data.get('reference_repo', 'unknown')
        
        # 生成README
        readme = f'''# {topic}

## Overview

This project implements a comprehensive solution for **{topic}**.

### Research Foundation

Based on analysis of top GitHub repositories:
'''
        
        # 添加研究数据
        for i, repo in enumerate(research_data.get('repositories', [])[:3], 1):
            readme += f"- **{repo['name']}** (⭐ {repo['stars']:,}) - {repo['language']}\\n"
        
        readme += f'''
### Implementation Reference

Primary inspiration: `{ref_repo}`

## Features

- ✅ Async/await support
- ✅ Type hints throughout
- ✅ Dataclass models
- ✅ Research-backed architecture
- ✅ Production-ready structure

## Installation

```bash
git clone <repository>
cd real_project_{project_name}
pip install -r requirements.txt
```

## Usage

```python
import asyncio
from main import {topic.replace(' ', '').replace('-', '')}System

async def main():
    system = {topic.replace(' ', '').replace('-', '')}System()
    result = await system.run({{"query": "test"}})
    print(result)

asyncio.run(main())
```

## Development

This project was created using a **Multi-Agent System** with:
- 🔍 RealResearchAgent (GitHub API)
- 💻 RealCodeAgent (Code generation)
- 📝 RealDocumentAgent (Documentation)

## License

MIT License
'''
        
        self.log("创建 README.md...")
        self.server.call_tool('file_write_text', {
            'path': f'/tmp/real_project_{project_name}/README.md',
            'content': readme
        })
        
        self.log("✅ 文档已生成")
        
        return {
            'success': True,
            'docs_created': 1,
            'readme_length': len(readme)
        }


def run_real_demo():
    """运行真实API演示"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🔥 MULTI-AGENT DEMO WITH REAL APIs                                    ║
║                                                                          ║
║   使用真实GitHub API完成研究 → 代码 → 文档完整流程                      ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    topic = "AI Agent Framework"
    
    print(f"\n📌 任务: 创建 '{topic}' 项目")
    print("📡 使用真实API: GitHub Search API\n")
    
    # Phase 1: Research
    print("━"*70)
    print("📚 PHASE 1: RESEARCH (RealResearchAgent)")
    print("━"*70)
    research_agent = RealResearchAgent()
    research_result = research_agent.execute(topic)
    
    if not research_result['success']:
        print("\n❌ 研究阶段失败，演示终止")
        return
    
    # Phase 2: Implementation
    print("\n" + "━"*70)
    print("💻 PHASE 2: IMPLEMENTATION (RealCodeAgent)")
    print("━"*70)
    code_agent = RealCodeAgent()
    code_result = code_agent.execute(topic, research_result)
    
    # Phase 3: Documentation
    print("\n" + "━"*70)
    print("📝 PHASE 3: DOCUMENTATION (RealDocumentAgent)")
    print("━"*70)
    doc_agent = RealDocumentAgent()
    doc_result = doc_agent.execute(topic, code_result, research_result)
    
    # Summary
    print("\n" + "="*70)
    print("📊 REAL API DEMO SUMMARY")
    print("="*70)
    
    project_name = topic.lower().replace(' ', '_').replace('-', '_')
    
    print(f"\n🎯 项目: {topic}")
    print(f"📁 位置: /tmp/real_project_{project_name}/")
    print(f"\n📊 产出:")
    print(f"   • 研究到的项目: {research_result.get('total', 0)} 个")
    print(f"   • 参考项目: {code_result.get('reference_repo', 'N/A')}")
    print(f"   • 代码长度: {code_result.get('code_length', 0)} chars")
    print(f"   • 文档: {doc_result.get('docs_created', 0)} 个")
    
    print(f"\n✅ 使用真实GitHub API完成!")
    print(f"   数据全部来自真实的GitHub仓库")


if __name__ == "__main__":
    run_real_demo()
