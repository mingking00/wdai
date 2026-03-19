#!/usr/bin/env python3
"""
WDai 多尺度记忆分层系统 - 自动迁移引擎
Multi-Scale Memory Migration Engine
"""

import os
import json
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import re


@dataclass
class MemoryEntry:
    """记忆条目"""
    content: str
    timestamp: str
    layer: str
    tags: List[str]
    importance: float  # 0-1
    access_count: int = 0
    last_accessed: str = ""


class MultiScaleMemorySystem:
    """多尺度记忆分层系统"""
    
    def __init__(self, workspace: str = "/root/.openclaw/workspace"):
        self.workspace = Path(workspace)
        self.memory_dir = self.workspace / "memory"
        
        # 各层目录
        self.layers = {
            'immediate': self.memory_dir / "immediate",
            'session': self.memory_dir / "session", 
            'project': self.memory_dir / "project",
            'domain': self.memory_dir / "domain",
            'universal': self.memory_dir / "universal",
            'archive': self.memory_dir / "archive"
        }
        
        # 确保目录存在
        for layer_path in self.layers.values():
            layer_path.mkdir(parents=True, exist_ok=True)
        
        # 迁移配置
        self.migration_rules = {
            'immediate': {'to': 'session', 'max_age_hours': 4},
            'session': {'to': 'project', 'max_age_days': 7},
            'project': {'to': 'domain', 'max_age_days': 30},
            'domain': {'to': 'universal', 'max_age_days': 90}
        }
        
        self.stats = {
            'migrated': 0,
            'archived': 0,
            'compressed': 0
        }
    
    # ========== 写入接口 ==========
    
    def write_immediate(self, content: str, tags: List[str] = None):
        """写入即时记忆 (当前会话)"""
        entry = MemoryEntry(
            content=content,
            timestamp=datetime.now().isoformat(),
            layer='immediate',
            tags=tags or [],
            importance=0.5
        )
        
        # 按会话ID存储
        session_id = self._get_current_session_id()
        file_path = self.layers['immediate'] / f"session_{session_id}.jsonl"
        
        with open(file_path, 'a') as f:
            f.write(json.dumps(asdict(entry)) + "\n")
        
        return entry
    
    def write_session(self, content: str, tags: List[str] = None, importance: float = 0.6):
        """写入会话记忆 (今日)"""
        entry = MemoryEntry(
            content=content,
            timestamp=datetime.now().isoformat(),
            layer='session',
            tags=tags or [],
            importance=importance
        )
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        file_path = self.layers['session'] / f"{date_str}.md"
        
        with open(file_path, 'a') as f:
            f.write(f"\n## {datetime.now().strftime('%H:%M:%S')}\n")
            f.write(f"**Tags**: {', '.join(tags or [])}\n\n")
            f.write(content + "\n")
        
        return entry
    
    def write_project(self, project_name: str, content: str, tags: List[str] = None):
        """写入项目记忆"""
        entry = MemoryEntry(
            content=content,
            timestamp=datetime.now().isoformat(),
            layer='project',
            tags=tags or [project_name],
            importance=0.7
        )
        
        file_path = self.layers['project'] / f"{project_name}.md"
        
        with open(file_path, 'a') as f:
            f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(content + "\n")
        
        return entry
    
    def write_domain(self, domain: str, content: str, pattern_type: str = ""):
        """写入领域记忆 (可复用知识)"""
        entry = MemoryEntry(
            content=content,
            timestamp=datetime.now().isoformat(),
            layer='domain',
            tags=[domain, pattern_type],
            importance=0.8
        )
        
        file_path = self.layers['domain'] / f"{domain}.md"
        
        with open(file_path, 'a') as f:
            f.write(f"\n### {pattern_type} - {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(content + "\n")
        
        return entry
    
    def write_universal(self, principle: str, content: str):
        """写入通用原则"""
        entry = MemoryEntry(
            content=content,
            timestamp=datetime.now().isoformat(),
            layer='universal',
            tags=['principle', principle],
            importance=0.95
        )
        
        file_path = self.layers['universal'] / "principles.md"
        
        with open(file_path, 'a') as f:
            f.write(f"\n## {principle}\n**Added**: {datetime.now().strftime('%Y-%m-%d')}\n\n")
            f.write(content + "\n")
        
        return entry
    
    # ========== 自动迁移 ==========
    
    def migrate_all(self):
        """执行所有层级的迁移"""
        print("🔄 开始多尺度记忆迁移...\n")
        
        # 1. immediate → session (会话结束)
        self._migrate_immediate_to_session()
        
        # 2. session → project (7天)
        self._migrate_session_to_project()
        
        # 3. project → domain (30天)
        self._migrate_project_to_domain()
        
        # 4. domain → universal (90天 + 高频访问)
        self._promote_domain_to_universal()
        
        # 5. 压缩旧档案
        self._archive_old_memories()
        
        print(f"\n📊 迁移完成:")
        print(f"   迁移: {self.stats['migrated']} 条")
        print(f"   归档: {self.stats['archived']} 条")
        print(f"   压缩: {self.stats['compressed']} 条")
    
    def _migrate_immediate_to_session(self):
        """即时记忆 → 会话记忆"""
        immediate_dir = self.layers['immediate']
        
        for file in immediate_dir.glob("session_*.jsonl"):
            # 检查文件修改时间
            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            if datetime.now() - mtime > timedelta(hours=4):
                # 读取内容
                entries = []
                with open(file) as f:
                    for line in f:
                        entries.append(json.loads(line))
                
                # 聚合到会话记忆
                if entries:
                    content = self._aggregate_entries(entries)
                    self.write_session(
                        content=content,
                        tags=['auto_migrated', 'immediate'],
                        importance=0.6
                    )
                    
                    # 删除原文件
                    file.unlink()
                    self.stats['migrated'] += len(entries)
                    print(f"   📤 immediate → session: {file.name}")
    
    def _migrate_session_to_project(self):
        """会话记忆 → 项目记忆"""
        session_dir = self.layers['session']
        cutoff = datetime.now() - timedelta(days=7)
        
        for file in session_dir.glob("*.md"):
            # 解析日期
            try:
                date_str = file.stem
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if file_date < cutoff:
                    # 按项目标签聚合
                    content = file.read_text()
                    projects = self._extract_projects(content)
                    
                    for project in projects:
                        project_content = self._extract_project_content(content, project)
                        self.write_project(project, project_content, ['auto_migrated'])
                    
                    # 归档原文件
                    self._archive_file(file)
                    self.stats['migrated'] += 1
                    print(f"   📤 session → project: {file.name}")
                    
            except ValueError:
                continue
    
    def _migrate_project_to_domain(self):
        """项目记忆 → 领域记忆"""
        project_dir = self.layers['project']
        cutoff = datetime.now() - timedelta(days=30)
        
        for file in project_dir.glob("*.md"):
            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            if mtime < cutoff:
                content = file.read_text()
                
                # 提取领域知识
                domain = self._classify_domain(file.stem)
                pattern = self._extract_pattern(content)
                
                if pattern:
                    self.write_domain(domain, pattern, file.stem)
                    self.stats['migrated'] += 1
                    print(f"   📤 project → domain: {file.name}")
    
    def _promote_domain_to_universal(self):
        """领域记忆 → 通用原则 (基于访问频率)"""
        domain_dir = self.layers['domain']
        
        for file in domain_dir.glob("*.md"):
            # 检查访问频率和重要性
            access_count = self._get_access_count(file)
            
            if access_count > 10:  # 高频访问
                content = file.read_text()
                principle = self._extract_universal_principle(content)
                
                if principle:
                    self.write_universal(
                        principle=f"auto_promoted_{file.stem}",
                        content=principle
                    )
                    self.stats['migrated'] += 1
                    print(f"   📤 domain → universal: {file.name}")
    
    def _archive_old_memories(self):
        """归档旧记忆"""
        archive_dir = self.layers['archive']
        cutoff = datetime.now() - timedelta(days=180)
        
        for layer in ['session', 'project', 'domain']:
            layer_dir = self.layers[layer]
            for file in layer_dir.glob("*.md"):
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if mtime < cutoff:
                    # 压缩归档
                    archive_path = archive_dir / f"{file.stem}.md.gz"
                    with open(file, 'rb') as f_in:
                        with gzip.open(archive_path, 'wb') as f_out:
                            f_out.write(f_in.read())
                    
                    file.unlink()
                    self.stats['archived'] += 1
                    self.stats['compressed'] += 1
                    print(f"   📦 archived: {file.name}")
    
    # ========== 辅助方法 ==========
    
    def _get_current_session_id(self) -> str:
        """获取当前会话ID"""
        # 简化实现 - 使用日期+随机
        return datetime.now().strftime("%Y%m%d_%H%M")
    
    def _aggregate_entries(self, entries: List[dict]) -> str:
        """聚合多个条目"""
        contents = [e['content'] for e in entries]
        return "\n\n".join(contents)
    
    def _extract_projects(self, content: str) -> List[str]:
        """从内容中提取项目标签"""
        # 匹配 evo-XXX 或项目名
        projects = re.findall(r'evo-\d+', content)
        return list(set(projects))
    
    def _extract_project_content(self, content: str, project: str) -> str:
        """提取特定项目的内容"""
        lines = content.split('\n')
        project_lines = []
        
        for line in lines:
            if project in line or any(tag in line for tag in ['##', '###']):
                project_lines.append(line)
        
        return '\n'.join(project_lines)
    
    def _classify_domain(self, project_name: str) -> str:
        """分类项目到领域"""
        domain_map = {
            'evo-006': 'planning',
            'evo-001': 'rag',
            'react': 'planning',
            'rag': 'retrieval',
            'agent': 'multi_agent',
        }
        
        for key, domain in domain_map.items():
            if key in project_name.lower():
                return domain
        
        return 'general'
    
    def _extract_pattern(self, content: str) -> str:
        """提取可复用模式"""
        # 简化：提取"##"开头的章节
        lines = content.split('\n')
        patterns = []
        
        for line in lines:
            if line.startswith('##') or line.startswith('###'):
                patterns.append(line)
        
        return '\n'.join(patterns[:3]) if patterns else ""
    
    def _extract_universal_principle(self, content: str) -> str:
        """提取通用原则"""
        # 提取总结性内容
        lines = content.split('\n')
        principles = []
        
        capture = False
        for line in lines:
            if '总结' in line or '原则' in line or 'pattern' in line.lower():
                capture = True
            if capture:
                principles.append(line)
                if len(principles) > 5:
                    break
        
        return '\n'.join(principles)
    
    def _get_access_count(self, file: Path) -> int:
        """获取文件访问次数 (从元数据)"""
        meta_file = file.parent / f"{file.stem}.meta.json"
        if meta_file.exists():
            with open(meta_file) as f:
                meta = json.load(f)
                return meta.get('access_count', 0)
        return 0
    
    def _archive_file(self, file: Path):
        """归档文件"""
        archive_dir = self.layers['archive']
        archive_dir.mkdir(exist_ok=True)
        
        archive_path = archive_dir / file.name
        shutil.move(str(file), str(archive_path))


def main():
    """主入口"""
    mms = MultiScaleMemorySystem()
    
    # 演示写入
    print("📝 写入演示数据...\n")
    
    # 写入即时记忆
    mms.write_immediate("用户要求优化代码", ["task", "code"])
    mms.write_immediate("检测到性能瓶颈", ["observation"])
    
    # 写入会话记忆
    mms.write_session("今天完成了evo-006实现", ["evo-006", "planning"], 0.8)
    
    # 写入项目记忆
    mms.write_project("evo-006", "ReAct核心实现完成，51行代码", ["react", "milestone"])
    
    # 写入领域记忆
    mms.write_domain("planning", "复杂任务应拆分为3个测试用例", "best_practice")
    
    # 写入通用原则
    mms.write_universal("MVP优先", "优先实现最小可用版本，再迭代优化")
    
    print("\n✅ 演示数据写入完成\n")
    
    # 执行迁移
    mms.migrate_all()
    
    print("\n" + "=" * 60)
    print("多尺度记忆分层系统运行正常")
    print("=" * 60)


if __name__ == "__main__":
    main()
