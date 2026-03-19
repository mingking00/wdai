#!/usr/bin/env python3
"""
Simple Video Learning - 简化版

合并: video_parser + knowledge_extractor + learning_integrator
核心功能: 从视频提取关键概念，保存到记忆
"""

import json
from pathlib import Path
from datetime import datetime

class VideoLearner:
    """简单的视频学习器"""
    
    def __init__(self, memory_file: str = "MEMORY.md"):
        self.memory_file = Path(memory_file)
        self.learned_videos = []
    
    def learn(self, video_info: dict) -> dict:
        """
        学习视频内容
        
        Args:
            video_info: {title, url, key_concepts}
        
        Returns:
            学习结果摘要
        """
        title = video_info.get("title", "")
        concepts = video_info.get("key_concepts", [])
        
        # 生成学习笔记
        learning_note = f"""
## 学习: {title}

**时间**: {datetime.now().strftime('%Y-%m-%d')}
**来源**: {video_info.get('url', '')}

### 核心概念
{chr(10).join(f'- {c}' for c in concepts)}

### 关键理解
{video_info.get('summary', '从视频提取的核心知识')}
"""
        
        # 保存到记忆
        self._append_to_memory(learning_note)
        
        # 记录已学习
        self.learned_videos.append(title)
        
        return {
            "video": title,
            "concepts_learned": len(concepts),
            "concepts": concepts,
            "saved": True
        }
    
    def _append_to_memory(self, note: str):
        """追加到记忆文件"""
        with open(self.memory_file, 'a', encoding='utf-8') as f:
            f.write(note)
            f.write("\n---\n")


# 使用示例
if __name__ == "__main__":
    learner = VideoLearner()
    
    # 学习C-JEPA
    result = learner.learn({
        "title": "C-JEPA: 告别99%Token冗余",
        "url": "https://bilibili.com/video/BV1e4cyziEqH",
        "key_concepts": ["C-JEPA", "对象级干预", "世界模型", "算力优化"],
        "summary": "C-JEPA通过选择性处理变化的对象，实现99%Token冗余消除。"
    })
    
    print(f"✅ 学习完成: {result['video']}")
    print(f"📚 掌握概念: {result['concepts_learned']}个")
