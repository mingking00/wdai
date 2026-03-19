#!/usr/bin/env python3
"""
B站收藏视频溯源系统 v1.0 - 演示模式
展示系统功能，使用示例数据
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.knowledge/bilibili')

from bilibili_tracer import BilibiliTracer, BilibiliVideo, BILIBILI_DIR
import json
from pathlib import Path

def demo_mode():
    """演示模式 - 使用示例数据展示功能"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║           B站收藏视频溯源系统 v1.0 - 演示模式               ║")
    print("║     根据收藏视频自动溯源高质量信息源                        ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    tracer = BilibiliTracer(uid="demo_mode")
    
    # 使用示例视频数据
    print("📺 模拟从收藏夹获取视频...")
    videos = tracer._get_sample_videos()
    print(f"✅ 获取到 {len(videos)} 个视频\n")
    
    print("="*65)
    print("🔍 开始视频溯源分析")
    print("="*65)
    
    # 分析每个视频
    results = []
    for i, video in enumerate(videos, 1):
        print(f"\n[{i}/{len(videos)}] {video.title}")
        print(f"    UP主: {video.owner}")
        print(f"    标签: {', '.join(video.tags)}")
        
        result = tracer.analyze_video(video)
        results.append(result)
        
        # 显示溯源结果
        print(f"    🔑 关键词: {', '.join(result.keywords[:5])}")
        print(f"    📄 论文: {len(result.papers)}篇")
        for p in result.papers[:2]:
            print(f"       - {p['title'][:40]}... ({p['year']})")
        print(f"    💻 项目: {len(result.repositories)}个")
        for r in result.repositories[:2]:
            print(f"       - {r['name']}: {r['desc']}")
    
    # 生成学习计划
    print("\n" + "="*65)
    print("📚 基于收藏夹的学习计划")
    print("="*65)
    
    plan = tracer.generate_study_plan()
    
    print(f"\n📊 主题兴趣分布:")
    sorted_topics = sorted(plan['topic_distribution'].items(), key=lambda x: -x[1])
    for topic, count in sorted_topics:
        bar = "█" * count
        print(f"  {topic:12s} {bar} ({count})")
    
    print(f"\n🎯 推荐学习路径:")
    for i, path in enumerate(plan['recommended_study_path'], 1):
        print(f"\n  路径 {i}: {path['video_title'][:45]}...")
        if path['papers']:
            print(f"    📖 必读论文: {path['papers'][0][:50]}...")
        if path['repos']:
            print(f"    💻 实践项目: {path['repos'][0]}")
        print(f"    ⏱️  预计时间: {path['estimated_time']}")
    
    print(f"\n💡 溯源洞察:")
    for result in results:
        for insight in result.insights[:2]:
            print(f"  • {insight}")
    
    # 保存分析结果
    output_file = BILIBILI_DIR / "demo_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "demo_mode": True,
            "videos_analyzed": len(videos),
            "topic_distribution": plan['topic_distribution'],
            "study_paths": plan['recommended_study_path']
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 演示完成！")
    print(f"📁 分析报告已保存: {output_file}")
    print()
    print("="*65)
    print("📝 使用真实数据:")
    print("   1. 获取你的B站UID (个人主页URL中的数字)")
    print("   2. 运行: python3 bilibili_tracer.py --set-uid YOUR_UID")
    print("   3. 运行: python3 bilibili_tracer.py 获取真实分析")
    print("="*65)

if __name__ == "__main__":
    demo_mode()
