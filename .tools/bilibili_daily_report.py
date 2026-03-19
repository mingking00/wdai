#!/usr/bin/env python3
"""
Bilibili Daily Reporter - B站每日收藏夹报告
定时任务脚本
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from bilibili_collector import BilibiliCollector

async def main():
    """生成每日收藏夹报告"""
    collector = BilibiliCollector("3461564002732313")
    
    # 采集视频
    videos = await collector.collect_with_browser()
    
    if not videos:
        videos = collector.collect_with_api()
    
    # 检测新视频
    new_videos = collector.detect_new_videos(videos)
    
    # 生成报告
    report = collector.format_report(new_videos)
    
    # 输出报告（会被定时任务捕获）
    print(report)
    
    # 如果有新视频，尝试总结第一个
    if new_videos:
        print("\n📝 **视频简介**:\n")
        for video in new_videos[:1]:  # 只总结第一个
            print(f"**{video.title}**")
            print(f"UP主: {video.uploader}")
            print(f"时长: {video.duration}秒")
            if video.desc:
                print(f"简介: {video.desc[:200]}...")
            print(f"\n👉 链接: {video.link}")

if __name__ == "__main__":
    asyncio.run(main())
