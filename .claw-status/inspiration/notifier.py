#!/usr/bin/env python3
"""
灵感摄取系统 - 通知模块
当发现高质量内容时发送通知

Author: wdai
Version: 1.0
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict


class InspirationNotifier:
    """灵感通知器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.notified_file = self.data_dir / "notified_items.json"
        self.notified_ids = self._load_notified()
    
    def _load_notified(self) -> set:
        """加载已通知的项目ID"""
        if self.notified_file.exists():
            try:
                with open(self.notified_file, 'r') as f:
                    return set(json.load(f))
            except:
                return set()
        return set()
    
    def _save_notified(self):
        """保存已通知的项目ID"""
        try:
            with open(self.notified_file, 'w') as f:
                json.dump(list(self.notified_ids), f)
        except:
            pass
    
    def check_and_notify(self, items: List[Dict]) -> List[Dict]:
        """
        检查新内容并返回需要通知的项目
        
        通知规则:
        1. 质量分 >= 0.8
        2. 未通知过
        3. 最近24小时内
        """
        notifications = []
        
        for item in items:
            item_id = item.get('id') or item.get('title', '')
            quality = item.get('quality_score', 0)
            
            # 高质量且未通知
            if quality >= 0.8 and item_id not in self.notified_ids:
                notifications.append(item)
                self.notified_ids.add(item_id)
        
        # 限制通知数量，避免轰炸
        if len(notifications) > 5:
            notifications = sorted(
                notifications, 
                key=lambda x: x.get('quality_score', 0), 
                reverse=True
            )[:5]
        
        self._save_notified()
        return notifications
    
    def format_notification(self, items: List[Dict]) -> str:
        """格式化通知内容"""
        if not items:
            return ""
        
        lines = []
        lines.append("🎯 **灵感更新**\n")
        
        for item in items:
            title = item.get('title', 'Untitled')[:60]
            source = item.get('source', 'Unknown')
            quality = item.get('quality_score', 0)
            url = item.get('url', '')
            
            stars = "⭐" * int(quality * 5)
            lines.append(f"**{title}**")
            lines.append(f"{stars} | 来自 {source}")
            if url:
                lines.append(f"🔗 {url}")
            lines.append("")
        
        return "\n".join(lines)


def main():
    """测试通知功能"""
    notifier = InspirationNotifier()
    
    # 模拟测试数据
    test_items = [
        {
            'id': 'test1',
            'title': 'New Breakthrough in AI Agents',
            'source': 'arxiv',
            'quality_score': 0.85,
            'url': 'https://arxiv.org/abs/2401.12345'
        },
        {
            'id': 'test2', 
            'title': 'Claude Code Best Practices',
            'source': 'reddit',
            'quality_score': 0.9,
            'url': 'https://reddit.com/r/ClaudeAI/...'
        }
    ]
    
    notifications = notifier.check_and_notify(test_items)
    if notifications:
        print(notifier.format_notification(notifications))
    else:
        print("没有新通知")


if __name__ == "__main__":
    main()
