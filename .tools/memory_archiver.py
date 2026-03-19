#!/usr/bin/env python3
"""
记忆自动归档系统
基于Mem0自适应记忆机制实现

功能：
1. 自动归档30天前的daily记录到core
2. 按使用频率自动调整记忆保留策略
3. 低频经验标记为"归档"状态
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ArchiveConfig:
    """归档配置"""
    daily_retention_days: int = 30  # daily记录保留天数
    archive_threshold_days: int = 90  # 归档阈值天数
    low_frequency_threshold: int = 3  # 低频使用阈值（使用次数）


class MemoryArchiver:
    """
    记忆归档器
    
    实现多层级记忆管理：
    - Working Memory (daily): 短期活跃记忆
    - Long-term Memory (core): 长期归档记忆
    """
    
    def __init__(self, workspace_path: str = "/root/.openclaw/workspace"):
        self.workspace = Path(workspace_path)
        self.memory_dir = self.workspace / "memory"
        self.config = ArchiveConfig()
        
        # 统计信息
        self.stats = {
            "daily_files": 0,
            "archived_records": 0,
            "low_frequency_marked": 0,
            "errors": []
        }
    
    def scan_daily_files(self) -> List[Path]:
        """扫描所有daily记录文件"""
        daily_files = []
        
        if not self.memory_dir.exists():
            return daily_files
        
        for file in self.memory_dir.glob("2026-*.md"):
            if file.name != "index.md":
                daily_files.append(file)
        
        # 按日期排序
        daily_files.sort()
        return daily_files
    
    def parse_file_date(self, filepath: Path) -> Optional[datetime]:
        """从文件名解析日期"""
        try:
            # 格式: 2026-03-15.md
            date_str = filepath.stem
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            return None
    
    def should_archive(self, file_date: datetime) -> bool:
        """判断是否应该归档"""
        cutoff_date = datetime.now() - timedelta(days=self.config.daily_retention_days)
        return file_date < cutoff_date
    
    def extract_content(self, filepath: Path) -> str:
        """提取文件内容"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.stats["errors"].append(f"读取失败 {filepath}: {e}")
            return ""
    
    def archive_to_core(self, content: str, source_file: str) -> bool:
        """
        将内容归档到core
        
        策略：
        - 提取重要事件/决策/学习
        - 追加到core/principles.md或core/skills.md
        """
        try:
            # 解析内容，提取关键信息
            key_sections = self._extract_key_sections(content)
            
            if not key_sections:
                return False
            
            # 归档到core/archive.md
            archive_file = self.memory_dir / "core" / "archive.md"
            archive_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(archive_file, 'a', encoding='utf-8') as f:
                f.write(f"\n\n## 归档自 {source_file}\n\n")
                f.write(f"归档时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
                for section in key_sections:
                    f.write(f"{section}\n")
            
            return True
            
        except Exception as e:
            self.stats["errors"].append(f"归档失败: {e}")
            return False
    
    def _extract_key_sections(self, content: str) -> List[str]:
        """提取内容中的关键章节"""
        sections = []
        
        # 查找重要标记
        important_markers = [
            "###",
            "**重要**",
            "**决策**",
            "**学习**",
            "**错误**",
            "**TODO**"
        ]
        
        lines = content.split('\n')
        current_section = []
        in_important_section = False
        
        for line in lines:
            # 检查是否是重要章节开始
            if any(marker in line for marker in important_markers):
                if current_section:
                    sections.append('\n'.join(current_section))
                current_section = [line]
                in_important_section = True
            elif in_important_section:
                # 空行或新章节标记结束当前章节
                if line.strip() == '' or line.startswith('#'):
                    if len(current_section) > 1:  # 至少有一行内容
                        sections.append('\n'.join(current_section))
                    current_section = []
                    in_important_section = False
                else:
                    current_section.append(line)
        
        # 处理最后一个章节
        if current_section and len(current_section) > 1:
            sections.append('\n'.join(current_section))
        
        return sections
    
    def mark_low_frequency_experiences(self) -> int:
        """
        标记低频经验
        
        基于IER-KG经验图谱，标记使用频率低的经验
        """
        try:
            # 读取IER-KG经验图谱
            graph_file = self.workspace / "skills" / "code-dev-agent" / "ier_kg" / "graph_data.json"
            
            if not graph_file.exists():
                return 0
            
            with open(graph_file, 'r') as f:
                graph_data = json.load(f)
            
            marked_count = 0
            
            for exp_id, exp in graph_data.get('experiences', {}).items():
                # 获取使用次数 (metadata中)
                access_count = exp.get('metadata', {}).get('access_count', 0)
                last_accessed = exp.get('metadata', {}).get('last_accessed')
                
                # 判断是否低频
                is_low_freq = access_count < self.config.low_frequency_threshold
                
                if is_low_freq and not exp.get('archived', False):
                    # 标记为低频
                    exp['archived'] = True
                    exp['archive_reason'] = 'low_frequency'
                    marked_count += 1
            
            # 保存更新
            with open(graph_file, 'w') as f:
                json.dump(graph_data, f, indent=2)
            
            return marked_count
            
        except Exception as e:
            self.stats["errors"].append(f"标记低频经验失败: {e}")
            return 0
    
    def run_archival_job(self) -> Dict:
        """
        运行归档任务
        
        返回归档统计
        """
        print("=" * 60)
        print("🗄️  记忆自动归档系统")
        print("=" * 60)
        
        # 1. 扫描daily文件
        daily_files = self.scan_daily_files()
        self.stats["daily_files"] = len(daily_files)
        
        print(f"\n📁 发现 {len(daily_files)} 个daily记录文件")
        
        # 2. 归档过期文件
        archived = 0
        for filepath in daily_files:
            file_date = self.parse_file_date(filepath)
            if file_date and self.should_archive(file_date):
                print(f"  📦 归档: {filepath.name}")
                content = self.extract_content(filepath)
                if content and self.archive_to_core(content, filepath.name):
                    archived += 1
        
        self.stats["archived_records"] = archived
        
        # 3. 标记低频经验
        print("\n🏷️  标记低频经验...")
        low_freq_count = self.mark_low_frequency_experiences()
        self.stats["low_frequency_marked"] = low_freq_count
        
        # 4. 生成报告
        print("\n" + "=" * 60)
        print("📊 归档统计")
        print("=" * 60)
        print(f"  Daily文件总数: {self.stats['daily_files']}")
        print(f"  归档记录数: {self.stats['archived_records']}")
        print(f"  低频经验标记: {self.stats['low_frequency_marked']}")
        
        if self.stats["errors"]:
            print(f"\n⚠️  错误 ({len(self.stats['errors'])}):")
            for error in self.stats["errors"][:5]:
                print(f"    - {error}")
        
        print("\n✅ 归档任务完成")
        
        return self.stats


def main():
    """主函数"""
    archiver = MemoryArchiver()
    stats = archiver.run_archival_job()
    return stats


if __name__ == "__main__":
    main()
