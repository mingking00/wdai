#!/usr/bin/env python3
"""
B站智能监控 - 基于品味模型的实时推送
结合方案1的优质来源 + 方案2的品味模型
"""

import json
import sqlite3
import requests
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict

# 路径配置
BASE_DIR = Path("/root/.openclaw/workspace")
TOOLS_DIR = BASE_DIR / ".tools"
MEMORY_DIR = BASE_DIR / "memory/core"
DATA_DIR = BASE_DIR / ".claw-status/data"

class TasteScorer:
    """基于品味模型的内容评分器"""
    
    def __init__(self):
        self.keywords = {
            # 强信号词 (1.0)
            "agent": 1.0, "claude": 1.0, "llm": 1.0, "multi-agent": 1.0,
            "autonomous": 1.0, "reflection": 1.0, "openclaw": 1.0,
            # 高信号词 (0.8)
            "架构": 0.8, "系统": 0.8, "框架": 0.8, "设计模式": 0.8,
            "效率": 0.8, "自动化": 0.8, "工具链": 0.8,
            "实践": 0.8, "案例": 0.8, "实战": 0.8,
            # 中信号词 (0.5)
            "编程": 0.5, "代码": 0.5, "github": 0.5, "开源": 0.5,
            "游戏": 0.5, "引擎": 0.5, "开发": 0.5,
        }
        self.preferred_ups = ["慢学AI", "易-ZX", "GitHub很棒", "keysking", "龙哥ai炼丹"]
    
    def score(self, video: Dict) -> float:
        """给视频打分"""
        score = 0.0
        text = (video.get("标题", "") + " " + video.get("简介", "")).lower()
        
        # 关键词匹配
        for kw, weight in self.keywords.items():
            if kw in text:
                score += weight
        
        # UP主加分
        if video.get("UP主") in self.preferred_ups:
            score += 0.5
        
        # 时长偏好 (14分钟左右最佳)
        duration = self._parse_duration(video.get("时长", "0:0"))
        if 300 <= duration <= 900:  # 5-15分钟
            score += 0.3
        
        # 质量信号
        try:
            views = int(video.get("播放量", "0").replace("万", "0000"))
            if views > 1000:
                score += min(views / 10000, 0.3)  # 最高加0.3
        except:
            pass
        
        return min(score, 2.0)  # 封顶2.0
    
    def _parse_duration(self, d: str) -> int:
        parts = d.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return 0
    
    def should_notify(self, score: float) -> str:
        """根据分数决定推送策略"""
        if score >= 1.2:
            return "immediate"  # 立即推送
        elif score >= 0.7:
            return "daily"      # 每日汇总
        else:
            return "weekly"     # 周报


class BilibiliSmartMonitor:
    """智能监控系统"""
    
    def __init__(self):
        self.scorer = TasteScorer()
        self.history_file = TOOLS_DIR / "bilibili_favorites.json"
        self.queue_file = DATA_DIR / "notify_queue.json"
        self.quality_sources = self._load_quality_sources()
    
    def _load_quality_sources(self) -> Dict:
        """加载优质来源配置"""
        sources_file = MEMORY_DIR / "quality_sources.md"
        # 解析markdown获取UP主列表
        preferred_ups = ["慢学AI", "易-ZX", "GitHub很棒", "keysking", "龙哥ai炼丹", 
                        "Vibero", "秦无邪OvO", "AI-seeker"]
        return {"ups": preferred_ups}
    
    def check_new_videos(self) -> List[Dict]:
        """检查新视频并评分"""
        if not self.history_file.exists():
            return []
        
        with open(self.history_file, 'r', encoding='utf-8') as f:
            videos = json.load(f)
        
        # 只检查最近24小时的
        cutoff = time.time() - 86400
        new_videos = []
        
        for v in videos:
            fav_time = v.get("收藏时间", 0)
            if fav_time > cutoff:
                score = self.scorer.score(v)
                v["score"] = score
                v["notify_strategy"] = self.scorer.should_notify(score)
                new_videos.append(v)
        
        # 按分数排序
        new_videos.sort(key=lambda x: x["score"], reverse=True)
        return new_videos
    
    def process_notifications(self):
        """处理推送队列"""
        videos = self.check_new_videos()
        
        immediate = [v for v in videos if v["notify_strategy"] == "immediate"]
        daily = [v for v in videos if v["notify_strategy"] == "daily"]
        
        # 立即推送高价值内容
        for v in immediate:
            self._send_immediate(v)
        
        # 存入队列等待每日汇总
        if daily:
            self._queue_daily(daily)
        
        return {
            "immediate": len(immediate),
            "daily": len(daily),
            "total": len(videos)
        }
    
    def _send_immediate(self, video: Dict):
        """发送即时通知"""
        print(f"🔔 高价值内容检测到!")
        print(f"   标题: {video['标题'][:40]}...")
        print(f"   UP主: {video['UP主']}")
        print(f"   评分: {video['score']:.2f}")
        print(f"   链接: {video['链接']}")
        print()
        
        # 这里可以集成飞书/Discord通知
        # 暂时只打印，后续可以调用 message.send
    
    def _queue_daily(self, videos: List[Dict]):
        """加入每日队列"""
        queue = []
        if self.queue_file.exists():
            with open(self.queue_file, 'r') as f:
                queue = json.load(f)
        
        for v in videos:
            queue.append({
                "title": v["标题"],
                "owner": v["UP主"],
                "score": v["score"],
                "link": v["链接"],
                "added_at": datetime.now().isoformat()
            })
        
        with open(self.queue_file, 'w') as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)
    
    def generate_daily_report(self) -> str:
        """生成每日汇总报告"""
        if not self.queue_file.exists():
            return "暂无新内容"
        
        with open(self.queue_file, 'r') as f:
            queue = json.load(f)
        
        if not queue:
            return "暂无新内容"
        
        # 清空队列
        self.queue_file.unlink()
        
        # 生成报告
        report = ["## 📺 B站收藏更新报告", ""]
        
        for i, v in enumerate(queue[:10], 1):  # 最多10条
            report.append(f"### {i}. {v['title'][:50]}")
            report.append(f"**UP主**: {v['owner']}")
            report.append(f"**评分**: {v['score']:.2f}/2.0")
            report.append(f"**链接**: {v['link']}")
            report.append("")
        
        return "\n".join(report)


def main():
    """主函数"""
    monitor = BilibiliSmartMonitor()
    
    # 检查新内容
    result = monitor.process_notifications()
    print(f"\n📊 检查结果:")
    print(f"  立即推送: {result['immediate']} 个")
    print(f"  每日汇总: {result['daily']} 个")
    print(f"  总计: {result['total']} 个新视频")
    
    # 如果有立即推送的内容，显示出来
    if result['immediate'] > 0:
        print("\n✨ 高价值内容已识别，建议立即查看!")


if __name__ == "__main__":
    main()
