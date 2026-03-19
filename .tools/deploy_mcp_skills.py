#!/usr/bin/env python3
"""
MCP Skills 批量部署工具

自动部署十大AI Agent Skills:
1. MCP Filesystem Server
2. Playwright MCP Server
3. GitHub MCP Server
4. ChromaDB MCP Server
5. Docker MCP Server
6. SQLite MCP Server
7. Obsidian MCP Server
8. pymupdf4llm MCP
9. Notion MCP Server
10. CSV/Excel MCP Server

用法:
    python3 deploy_mcp_skills.py [--check] [--install] [--configure]
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# 部署配置
DEPLOY_DIR = Path("/root/.openclaw/workspace/.mcp-servers")
CONFIG_FILE = DEPLOY_DIR / "mcp-config.json"
LOG_FILE = DEPLOY_DIR / "deploy.log"

class DeployStatus(Enum):
    PENDING = "pending"
    CHECKING = "checking"
    INSTALLING = "installing"
    CONFIGURING = "configuring"
    READY = "ready"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class MCPServer:
    """MCP服务器定义"""
    name: str
    description: str
    github: str
    install_cmd: str
    config_template: Dict
    dependencies: List[str]
    priority: int  # 1-10, 越小越优先
    requires_token: bool
    token_env_var: Optional[str]
    
    def __post_init__(self):
        self.status = DeployStatus.PENDING
        self.error_msg = ""

# 定义10个MCP服务器
MCP_SERVERS = [
    MCPServer(
        name="filesystem",
        description="安全的文件系统访问",
        github="modelcontextprotocol/servers",
        install_cmd="npm install -g @anthropic/mcp-server-filesystem",
        config_template={
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-server-filesystem", "/root/.openclaw/workspace"]
        },
        dependencies=["nodejs", "npm"],
        priority=1,
        requires_token=False,
        token_env_var=None
    ),
    MCPServer(
        name="sqlite",
        description="SQLite数据库操作(73+工具)",
        github="adamic/ai-agent-mcp",
        install_cmd="pip install sqlite-mcp",
        config_template={
            "command": "python3",
            "args": ["-m", "sqlite_mcp", "--db-path", "/root/.openclaw/workspace/.mcp-servers/data.db"]
        },
        dependencies=["python3", "pip"],
        priority=2,
        requires_token=False,
        token_env_var=None
    ),
    MCPServer(
        name="github",
        description="GitHub平台完整交互",
        github="github/github-mcp-server",
        install_cmd="docker pull ghcr.io/github/github-mcp-server:latest",
        config_template={
            "command": "docker",
            "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", 
                     "ghcr.io/github/github-mcp-server"],
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"}
        },
        dependencies=["docker"],
        priority=3,
        requires_token=True,
        token_env_var="GITHUB_TOKEN"
    ),
    MCPServer(
        name="playwright",
        description="浏览器自动化测试",
        github="microsoft/playwright-mcp",
        install_cmd="npm install -g @playwright/mcp",
        config_template={
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest"]
        },
        dependencies=["nodejs", "npm"],
        priority=4,
        requires_token=False,
        token_env_var=None
    ),
    MCPServer(
        name="docker",
        description="Docker容器管理",
        github="QuantGeekDev/docker-mcp",
        install_cmd="npm install -g @quantgeek/docker-mcp",
        config_template={
            "command": "npx",
            "args": ["-y", "@quantgeek/docker-mcp"]
        },
        dependencies=["nodejs", "npm", "docker"],
        priority=5,
        requires_token=False,
        token_env_var=None
    ),
    MCPServer(
        name="chroma",
        description="向量数据库/RAG",
        github="chroma-core/chroma-mcp",
        install_cmd="pip install chroma-mcp",
        config_template={
            "command": "python3",
            "args": ["-m", "chroma_mcp.server", "--data-dir", "/root/.openclaw/workspace/.chroma"]
        },
        dependencies=["python3", "pip"],
        priority=6,
        requires_token=False,
        token_env_var=None
    ),
    MCPServer(
        name="obsidian",
        description="Obsidian知识库集成",
        github="MarkusPfundstein/mcp-obsidian",
        install_cmd="npm install -g mcp-obsidian",
        config_template={
            "command": "npx",
            "args": ["-y", "mcp-obsidian", "--vault-path", "/root/.openclaw/workspace/notes"],
            "env": {"OBSIDIAN_API_KEY": "${OBSIDIAN_API_KEY}"}
        },
        dependencies=["nodejs", "npm"],
        priority=7,
        requires_token=True,
        token_env_var="OBSIDIAN_API_KEY"
    ),
    MCPServer(
        name="pymupdf",
        description="PDF转Markdown",
        github="ArtifexSoftware/pymupdf4llm-mcp",
        install_cmd="pip install pymupdf4llm-mcp",
        config_template={
            "command": "python3",
            "args": ["-m", "pymupdf4llm_mcp"]
        },
        dependencies=["python3", "pip"],
        priority=8,
        requires_token=False,
        token_env_var=None
    ),
    MCPServer(
        name="notion",
        description="Notion工作空间管理",
        github="makenotion/notion-mcp-server",
        install_cmd="npm install -g @notionhq/notion-mcp-server",
        config_template={
            "command": "npx",
            "args": ["-y", "@notionhq/notion-mcp-server"],
            "env": {"NOTION_API_TOKEN": "${NOTION_TOKEN}"}
        },
        dependencies=["nodejs", "npm"],
        priority=9,
        requires_token=True,
        token_env_var="NOTION_TOKEN"
    ),
    MCPServer(
        name="csv-excel",
        description="CSV/Excel数据处理",
        github="shadowk1337/mcp-csv-excel-processor",
        install_cmd="echo 'Java项目，需手动构建'",
        config_template={
            "command": "java",
            "args": ["-jar", "/root/.openclaw/workspace/.mcp-servers/csv-excel-processor.jar"]
        },
        dependencies=["java", "maven"],
        priority=10,
        requires_token=False,
        token_env_var=None
    )
]

class MCPDeployer:
    """MCP服务器部署器"""
    
    def __init__(self):
        self.servers = sorted(MCP_SERVERS, key=lambda s: s.priority)
        self.deploy_dir = DEPLOY_DIR
        self.deploy_dir.mkdir(parents=True, exist_ok=True)
        (self.deploy_dir / "data").mkdir(exist_ok=True)
        
    def check_dependencies(self, server: MCPServer) -> Tuple[bool, str]:
        """检查依赖是否满足"""
        missing = []
        for dep in server.dependencies:
            if not self._check_command(dep):
                missing.append(dep)
        
        if missing:
            return False, f"缺少依赖: {', '.join(missing)}"
        return True, "所有依赖已满足"
    
    def _check_command(self, cmd: str) -> bool:
        """检查命令是否可用"""
        try:
            result = subprocess.run(
                ["which", cmd], 
                capture_output=True, 
                check=False
            )
            return result.returncode == 0
        except:
            return False
    
    def install_server(self, server: MCPServer) -> bool:
        """安装服务器"""
        try:
            result = subprocess.run(
                server.install_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0
        except Exception as e:
            server.error_msg = str(e)
            return False
    
    def generate_config(self) -> Dict:
        """生成统一配置文件"""
        config = {"mcpServers": {}}
        
        for server in self.servers:
            if server.status == DeployStatus.READY:
                config["mcpServers"][server.name] = server.config_template
        
        return config
    
    def save_config(self):
        """保存配置文件"""
        config = self.generate_config()
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"💾 配置已保存: {CONFIG_FILE}")
    
    def deploy_all(self):
        """部署所有服务器"""
        print("=" * 60)
        print("🚀 MCP Skills 批量部署")
        print("=" * 60)
        
        for server in self.servers:
            print(f"\n📦 [{server.priority}] {server.name}")
            print(f"   {server.description}")
            
            # 检查依赖
            server.status = DeployStatus.CHECKING
            ok, msg = self.check_dependencies(server)
            if not ok:
                print(f"   ⚠️  {msg}")
                if server.name == "csv-excel":
                    print(f"   ⏭️  跳过 (Java项目需手动构建)")
                    server.status = DeployStatus.SKIPPED
                else:
                    print(f"   🔧 尝试安装依赖...")
                continue
            print(f"   ✅ 依赖检查通过")
            
            # 安装
            server.status = DeployStatus.INSTALLING
            print(f"   📥 安装中...")
            if server.name == "csv-excel":
                print(f"   ⏭️  跳过 (需手动构建)")
                server.status = DeployStatus.SKIPPED
                continue
                
            if self.install_server(server):
                print(f"   ✅ 安装成功")
                server.status = DeployStatus.READY
            else:
                print(f"   ❌ 安装失败: {server.error_msg}")
                server.status = DeployStatus.FAILED
        
        # 保存配置
        self.save_config()
        
        # 打印汇总
        self.print_summary()
    
    def print_summary(self):
        """打印部署汇总"""
        print("\n" + "=" * 60)
        print("📊 部署汇总")
        print("=" * 60)
        
        ready = sum(1 for s in self.servers if s.status == DeployStatus.READY)
        failed = sum(1 for s in self.servers if s.status == DeployStatus.FAILED)
        skipped = sum(1 for s in self.servers if s.status == DeployStatus.SKIPPED)
        
        print(f"✅ 成功: {ready} | ❌ 失败: {failed} | ⏭️ 跳过: {skipped}")
        print("\n已部署的服务器:")
        for server in self.servers:
            icon = {
                DeployStatus.READY: "✅",
                DeployStatus.FAILED: "❌",
                DeployStatus.SKIPPED: "⏭️"
            }.get(server.status, "⏳")
            print(f"  {icon} {server.name:15} - {server.status.value}")
        
        print(f"\n📁 配置文件: {CONFIG_FILE}")
        print("\n⚠️  需要配置Token的服务器:")
        for server in self.servers:
            if server.requires_token and server.status == DeployStatus.READY:
                print(f"   • {server.name}: 设置环境变量 {server.token_env_var}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="MCP Skills 批量部署工具")
    parser.add_argument("--check", action="store_true", help="仅检查依赖")
    parser.add_argument("--install", action="store_true", help="执行安装")
    parser.add_argument("--configure", action="store_true", help="生成配置")
    
    args = parser.parse_args()
    
    deployer = MCPDeployer()
    
    if args.check:
        print("🔍 依赖检查模式")
        for server in deployer.servers:
            ok, msg = deployer.check_dependencies(server)
            icon = "✅" if ok else "❌"
            print(f"{icon} {server.name}: {msg}")
    elif args.install or args.configure or not any([args.check, args.install, args.configure]):
        deployer.deploy_all()

if __name__ == "__main__":
    main()
