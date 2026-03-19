#!/usr/bin/env python3
"""
B站收藏夹自动爬虫 v3.0
自动获取收藏夹视频列表
"""

import json
import time
import random
import urllib.request
import urllib.parse
import ssl
from pathlib import Path
from typing import List, Dict
from datetime import datetime

BILIBILI_DIR = Path("/root/.openclaw/workspace/.knowledge/bilibili")
UID = "3461564002732313"
FAV_ID = "17414708"  # 'q'收藏夹

def create_ssl_context():
    """创建SSL上下文"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def get_headers():
    """获取请求头 - 模拟真实浏览器"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': f'https://space.bilibili.com/{UID}/favlist',
        'Origin': 'https://space.bilibili.com',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
    }

def fetch_favorite_videos(fid: str, pn: int = 1, ps: int = 20) -> Dict:
    """获取收藏夹视频列表"""
    
    try:
        import requests
        
        # 构建URL - 注意media_id需要加'13'后缀
        media_id = f"{fid}13"
        url = f'https://api.bilibili.com/x/v3/fav/resource/list?media_id={media_id}&pn={pn}&ps={ps}&keyword=&order=mtime&type=0&tid=0&platform=web'
        
        response = requests.get(url, headers=get_headers(), timeout=15)
        return response.json()
        
    except Exception as e:
        print(f"请求失败: {e}")
        return {'code': -1, 'message': str(e)}

def extract_all_videos(fid: str, fav_title: str = "q") -> List[Dict]:
    """提取所有视频"""
    all_videos = []
    pn = 1
    max_pages = 10  # 最多10页
    
    print(f"🎬 正在获取收藏夹 '{fav_title}' 的视频...")
    print(f"   FID: {fid}")
    print()
    
    while pn <= max_pages:
        print(f"📄 获取第 {pn} 页...", end=" ")
        
        result = fetch_favorite_videos(fid, pn)
        
        if result.get('code') != 0:
            print(f"❌ 错误: {result.get('message')}")
            break
        
        data = result.get('data', {})
        medias = data.get('medias') or []
        info = data.get('info', {})
        
        if pn == 1:
            total = info.get('media_count', 0)
            print(f"(共 {total} 个视频)")
        
        if not medias:
            print("没有更多视频")
            break
        
        for media in medias:
            video = {
                'bvid': media.get('bvid', ''),
                'title': media.get('title', ''),
                'owner': media.get('upper', {}).get('name', ''),
                'intro': media.get('intro', '')[:100],
                'ctime': media.get('ctime', 0),
                'pubtime': media.get('pubtime', 0),
                'fav_time': media.get('fav_time', 0),
                'duration': media.get('duration', 0),
            }
            all_videos.append(video)
        
        print(f"✓ 获取 {len(medias)} 个")
        
        # 随机延迟，避免风控
        time.sleep(random.uniform(0.5, 1.5))
        
        # 检查是否还有下一页
        if len(medias) < 20:
            break
        
        pn += 1
    
    return all_videos

def save_videos(videos: List[Dict], uid: str, fav_title: str):
    """保存视频列表"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存JSON
    json_file = BILIBILI_DIR / f"videos_{uid}_{fav_title}_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'uid': uid,
            'favorite': fav_title,
            'count': len(videos),
            'export_time': datetime.now().isoformat(),
            'videos': videos
        }, f, indent=2, ensure_ascii=False)
    
    # 保存标准格式文本（供溯源器使用）
    txt_file = BILIBILI_DIR / f"export_{uid}.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        for v in videos:
            f.write(f"{v['bvid']} | {v['title']} | {v['owner']}\n")
    
    # 同时保存到最新文件
    latest_file = BILIBILI_DIR / f"export_{uid}_latest.txt"
    with open(latest_file, 'w', encoding='utf-8') as f:
        for v in videos:
            f.write(f"{v['bvid']} | {v['title']} | {v['owner']}\n")
    
    print(f"\n💾 已保存:")
    print(f"  - JSON: {json_file.name} ({len(videos)} 个视频)")
    print(f"  - TXT: {txt_file.name}")
    
    return json_file, txt_file

def main():
    """主函数"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║     B站收藏夹自动爬虫 v3.0                                 ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    # 获取收藏夹 'q' 的视频
    videos = extract_all_videos(FAV_ID, "q")
    
    if videos:
        print(f"\n✅ 成功获取 {len(videos)} 个视频")
        
        # 保存
        json_file, txt_file = save_videos(videos, UID, "q")
        
        # 显示前10个
        print(f"\n📺 前10个视频:")
        for i, v in enumerate(videos[:10], 1):
            print(f"  {i}. {v['title'][:45]}...")
            print(f"     UP: {v['owner']}")
        
        print(f"\n🔄 自动启动溯源分析...")
        
        # 导入并运行溯源器
        import sys
        sys.path.insert(0, str(BILIBILI_DIR))
        from tracer_v2 import BilibiliTracerV2, analyze_uid
        
        analyze_uid(UID)
        
        print(f"\n✅ 全部完成！")
        
    else:
        print("\n❌ 未能获取视频，可能原因:")
        print("  1. API风控限制")
        print("  2. 收藏夹为空或私有")
        print("  3. 网络连接问题")
        print()
        print("替代方案:")
        print("  请使用浏览器手动导出，然后运行:")
        print("  python3 tracer_v2.py", UID)

if __name__ == '__main__':
    main()
