#!/usr/bin/env python3
"""
B站收藏夹快速导出 - 使用OpenClaw Browser工具
通过JavaScript注入自动提取数据
"""

import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

BILIBILI_DIR = Path("/root/.openclaw/workspace/.knowledge/bilibili")
UID = "3461564002732313"

def export_via_javascript():
    """通过JavaScript注入提取收藏夹数据"""
    
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║     B站收藏夹快速导出工具                                  ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    # JavaScript代码 - 提取收藏夹列表
    js_favorites = '''
    (() => {
        const favorites = [];
        document.querySelectorAll('.fav-list-item').forEach(item => {
            const titleEl = item.querySelector('.text');
            const countEl = item.querySelector('.num');
            const linkEl = item.querySelector('a');
            
            if (titleEl && linkEl) {
                const href = linkEl.getAttribute('href');
                const match = href.match(/fid=(\\d+)/);
                favorites.push({
                    id: match ? match[1] : null,
                    title: titleEl.textContent.trim(),
                    count: countEl ? countEl.textContent.trim() : '0'
                });
            }
        });
        return JSON.stringify(favorites);
    })();
    '''
    
    # JavaScript代码 - 提取视频列表
    js_videos = '''
    (async () => {
        const videos = [];
        let hasNext = true;
        let page = 1;
        
        while (hasNext && page <= 10) {  // 最多10页
            console.log(`Extracting page ${page}...`);
            
            document.querySelectorAll('.fav-video-list .small-item').forEach(item => {
                const titleEl = item.querySelector('.title');
                const upEl = item.querySelector('.up-name');
                const linkEl = item.querySelector('a');
                
                if (linkEl) {
                    const href = linkEl.getAttribute('href');
                    const bvidMatch = href.match(/BV[\\w]+/);
                    videos.push({
                        bvid: bvidMatch ? bvidMatch[0] : '',
                        title: titleEl ? titleEl.textContent.trim() : '',
                        owner: upEl ? upEl.textContent.trim() : ''
                    });
                }
            });
            
            // 检查下一页
            const nextBtn = document.querySelector('.be-pager-next:not(.be-pager-disabled)');
            if (nextBtn && page < 10) {
                nextBtn.click();
                await new Promise(r => setTimeout(r, 2000));
                page++;
            } else {
                hasNext = false;
            }
        }
        
        return JSON.stringify({count: videos.length, videos: videos});
    })();
    '''
    
    print("📋 导出步骤:")
    print()
    print("1️⃣  在浏览器中打开以下链接:")
    print(f"   https://space.bilibili.com/{UID}/favlist")
    print()
    print("2️⃣  登录B站（如果未登录）")
    print()
    print("3️⃣  按F12打开开发者工具，切换到Console")
    print()
    print("4️⃣  粘贴以下代码获取收藏夹列表:")
    print("-" * 60)
    print(js_favorites.strip())
    print("-" * 60)
    print()
    print("5️⃣  切换到目标收藏夹，粘贴以下代码获取视频:")
    print("-" * 60)
    print(js_videos.strip())
    print("-" * 60)
    print()
    print("6️⃣  将输出的JSON保存到文件:")
    print(f"   {BILIBILI_DIR}/export_{UID}.json")
    print()
    print("7️⃣  运行溯源分析:")
    print("   python3 tracer_v2.py", UID)
    print()

def create_bookmarklet():
    """创建书签小工具(bookmarklet)"""
    
    bookmarklet_code = '''
javascript:(function(){
    const videos=[];
    document.querySelectorAll('.fav-video-list .small-item').forEach(item=>{
        const title=item.querySelector('.title')?.textContent?.trim();
        const up=item.querySelector('.up-name')?.textContent?.trim();
        const link=item.querySelector('a');
        const bvid=link?.getAttribute('href')?.match(/BV\w+/)?.[0];
        if(bvid)videos.push({bvid,title,owner:up});
    });
    const text=videos.map(v=>`${v.bvid} | ${v.title} | ${v.owner}`).join('\\n');
    navigator.clipboard.writeText(text);
    alert(`已复制 ${videos.length} 个视频到剪贴板！\\n\\n粘贴到export_3461564002732313.txt`);
})();
    '''.strip().replace('\n', '')
    
    print("🔖 书签小工具 (Bookmarklet):")
    print()
    print("创建方法:")
    print("  1. 在浏览器书签栏添加新书签")
    print("  2. 名称: B站导出")
    print("  3. URL: 粘贴以下代码")
    print()
    print(bookmarklet_code)
    print()
    print("使用方法:")
    print("  - 打开B站收藏夹")
    print("  - 点击书签")
    print("  - 自动复制视频列表")
    print()

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--bookmarklet', action='store_true', help='生成书签小工具')
    
    args = parser.parse_args()
    
    if args.bookmarklet:
        create_bookmarklet()
    else:
        export_via_javascript()
        print()
        create_bookmarklet()

if __name__ == '__main__':
    main()
