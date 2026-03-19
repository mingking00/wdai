#!/usr/bin/env python3
"""
B站收藏夹获取工具 - 使用B站公开API
无需登录即可获取公开收藏夹
"""

import requests
import json
import time

# ============ 配置区域 ============
UID = 3461564002732313  # 你的B站UID
# ==================================

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://space.bilibili.com',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',  # 禁用br编码
}

def get_favorite_list(uid):
    """获取用户收藏夹列表"""
    url = "https://api.bilibili.com/x/v3/fav/folder/created/list-all"
    params = {
        'up_mid': uid,
        'jsonp': 'jsonp'
    }
    
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get('code') != 0:
            print(f"API错误: {data.get('message', '未知错误')}")
            return None
        
        return data.get('data', {}).get('list', [])
    
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def get_favorite_videos(media_id, page=1, page_size=20):
    """获取收藏夹视频列表"""
    url = "https://api.bilibili.com/x/v3/fav/resource/list"
    params = {
        'media_id': media_id,
        'pn': page,
        'ps': page_size,
        'keyword': '',
        'order': 'mtime',  # 按收藏时间排序
        'type': 0,
        'tid': 0,
        'platform': 'web',
        'jsonp': 'jsonp'
    }
    
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get('code') != 0:
            print(f"API错误: {data.get('message', '未知错误')}")
            return None
        
        return data.get('data', {})
    
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def format_video_info(video):
    """格式化视频信息"""
    upper = video.get('upper', {})
    
    # 处理时长（秒转时分秒）
    duration_sec = video.get('duration', 0)
    if duration_sec >= 3600:
        duration_str = f"{duration_sec//3600}:{(duration_sec%3600)//60:02d}:{duration_sec%60:02d}"
    else:
        duration_str = f"{duration_sec//60}:{duration_sec%60:02d}"
    
    # 处理播放量
    play_count = video.get('cnt_info', {}).get('play', 0)
    if play_count >= 10000:
        play_str = f"{play_count/10000:.1f}万"
    else:
        play_str = str(play_count)
    
    return {
        "标题": video.get('title', 'N/A'),
        "Bvid": video.get('bvid', 'N/A'),
        "链接": f"https://www.bilibili.com/video/{video.get('bvid', '')}",
        "UP主": upper.get('name', 'N/A') if isinstance(upper, dict) else 'N/A',
        "UP主ID": upper.get('mid', 'N/A') if isinstance(upper, dict) else 'N/A',
        "时长": duration_str,
        "播放量": play_str,
        "收藏时间": video.get('fav_time', 'N/A'),
        "简介": (video.get('intro', '')[:100] + '...') if len(video.get('intro', '')) > 100 else video.get('intro', 'N/A')
    }

def main():
    """主函数"""
    print("=" * 70)
    print("B站收藏夹视频获取工具 (API版本)")
    print("=" * 70)
    
    # 1. 获取收藏夹列表
    print(f"\n正在获取用户 {UID} 的收藏夹列表...")
    fav_list = get_favorite_list(UID)
    
    if not fav_list:
        print("获取收藏夹列表失败，可能是：")
        print("  1. UID错误")
        print("  2. 收藏夹设置为私密（需要登录）")
        print("  3. 请求被风控（稍后再试）")
        return
    
    print(f"找到 {len(fav_list)} 个收藏夹:")
    for fav in fav_list:
        print(f"  - {fav['title']}: {fav.get('media_count', 0)} 个视频")
    
    # 2. 找默认收藏夹
    default_fav = None
    for fav in fav_list:
        if fav.get('title') == '默认收藏夹':
            default_fav = fav
            break
    
    if not default_fav and fav_list:
        default_fav = fav_list[0]
    
    if not default_fav:
        print("未找到可用收藏夹")
        return
    
    media_id = default_fav['id']
    print(f"\n使用收藏夹: {default_fav['title']} (ID: {media_id})")
    
    # 3. 获取视频列表
    print(f"\n正在获取视频列表...")
    time.sleep(0.5)  # 避免请求过快
    
    videos_data = get_favorite_videos(media_id, page=1, page_size=20)
    
    if not videos_data:
        print("获取视频列表失败")
        return
    
    video_list = videos_data.get('medias', [])
    info = videos_data.get('info', {})
    total_count = info.get('media_count', len(video_list))
    
    print(f"\n获取到 {len(video_list)} 个视频 (收藏夹共 {total_count} 个视频):\n")
    
    # 4. 显示结果
    results = []
    for i, video in enumerate(video_list, 1):
        info = format_video_info(video)
        results.append(info)
        
        print(f"[{i}] {info['标题']}")
        print(f"    UP主: {info['UP主']} | 时长: {info['时长']} | 播放: {info['播放量']}")
        print(f"    链接: {info['链接']}")
        intro = info['简介'][:50] + '...' if len(info['简介']) > 50 else info['简介']
        if intro and intro != 'N/A':
            print(f"    简介: {intro}")
        print()
    
    # 5. 保存到文件
    output_file = "bilibili_favorites.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✅ 结果已保存到: {output_file}")
    print(f"   共获取 {len(results)} 个视频")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
