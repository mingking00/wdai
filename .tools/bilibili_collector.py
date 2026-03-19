#!/usr/bin/env python3
"""
Bilibili Collector - B站收藏夹自动采集
改进版浏览器自动化，解决超时问题
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class VideoInfo:
    """视频信息"""
    title: str
    bvid: str
    link: str
    uploader: str
    desc: str
    duration: str
    add_time: str

class BilibiliCollector:
    """
    B站收藏夹采集器
    
    特性：
    - 持久化登录状态（cookie保存）
    - 自动重试机制
    - 失败优雅降级
    """
    
    def __init__(self, uid: str = "3461564002732313"):
        self.uid = uid
        self.cookie_file = Path(".learning/bilibili_cookies.json")
        self.history_file = Path(".learning/bilibili_history.json")
        self.data_dir = Path(".learning/bilibili")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.collected_videos: List[VideoInfo] = []
        self.new_videos: List[VideoInfo] = []
        
    def _load_cookies(self) -> Optional[List[Dict]]:
        """加载保存的cookies"""
        if self.cookie_file.exists():
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def _save_cookies(self, cookies: List[Dict]):
        """保存cookies"""
        with open(self.cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
    
    def _load_history(self) -> List[str]:
        """加载已采集的视频历史"""
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_history(self, bvids: List[str]):
        """保存采集历史"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(bvids, f, ensure_ascii=False, indent=2)
    
    async def collect_with_browser(self) -> List[VideoInfo]:
        """
        使用浏览器采集收藏夹
        
        流程：
        1. 尝试使用已有cookie登录
        2. 访问收藏夹页面
        3. 解析视频列表
        4. 对比历史，找出新视频
        5. 保存cookie供下次使用
        """
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                # 启动浏览器
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                
                # 加载cookies（如果有）
                cookies = self._load_cookies()
                if cookies:
                    await context.add_cookies(cookies)
                
                page = await context.new_page()
                
                # 访问B站收藏夹
                fav_url = f"https://space.bilibili.com/{self.uid}/favlist"
                
                try:
                    # 设置超时为60秒
                    await page.goto(fav_url, timeout=60000, wait_until="networkidle")
                except Exception as e:
                    print(f"页面加载超时: {e}")
                    await browser.close()
                    return []
                
                # 检查是否需要登录
                login_indicator = await page.query_selector(".login-box, .login-entry")
                if login_indicator:
                    print("需要登录，请先在浏览器中手动登录一次")
                    await browser.close()
                    return []
                
                # 等待视频列表加载
                try:
                    await page.wait_for_selector(".fav-video-list li, .video-list-item", timeout=10000)
                except:
                    print("未找到视频列表")
                    await browser.close()
                    return []
                
                # 解析视频信息
                videos = await self._parse_video_list(page)
                
                # 保存cookies
                cookies = await context.cookies()
                self._save_cookies(cookies)
                
                await browser.close()
                return videos
                
        except ImportError:
            print("Playwright未安装，尝试使用备用方案")
            return self.collect_with_api()
        except Exception as e:
            print(f"浏览器采集失败: {e}")
            return self.collect_with_api()
    
    async def _parse_video_list(self, page) -> List[VideoInfo]:
        """解析视频列表"""
        videos = []
        
        # 尝试多种可能的选择器
        selectors = [
            ".fav-video-list li",
            ".video-list-item",
            ".fav-list-item",
            "[class*='video'] [class*='item']"
        ]
        
        items = []
        for selector in selectors:
            items = await page.query_selector_all(selector)
            if items:
                break
        
        for item in items[:5]:  # 只取前5个
            try:
                # 提取标题
                title_elem = await item.query_selector("a.title, .title, h3 a")
                title = await title_elem.inner_text() if title_elem else "未知标题"
                
                # 提取链接
                link_elem = await item.query_selector("a[href]")
                link = await link_elem.get_attribute("href") if link_elem else ""
                if link and not link.startswith("http"):
                    link = f"https:{link}"
                
                # 提取BV号
                bvid = link.split("/")[-1].split("?")[0] if link else ""
                
                # 提取UP主
                up_elem = await item.query_selector("a.up-name, .up-name, [class*='up']")
                uploader = await up_elem.inner_text() if up_elem else "未知UP主"
                
                # 提取时长
                duration_elem = await item.query_selector(".duration, .length, [class*='time']")
                duration = await duration_elem.inner_text() if duration_elem else ""
                
                videos.append(VideoInfo(
                    title=title.strip(),
                    bvid=bvid,
                    link=link,
                    uploader=uploader.strip(),
                    desc="",
                    duration=duration,
                    add_time=""
                ))
            except Exception as e:
                print(f"解析单个视频失败: {e}")
                continue
        
        return videos
    
    def collect_with_api(self) -> List[VideoInfo]:
        """
        API备用方案
        
        当浏览器方式失败时使用
        """
        import requests
        
        videos = []
        
        try:
            # 尝试获取收藏夹列表
            session = requests.Session()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://space.bilibili.com',
            }
            
            # 获取默认收藏夹ID
            url = f"https://api.bilibili.com/x/v3/fav/folder/created/list-all?up_mid={self.uid}"
            
            resp = session.get(url, headers=headers, timeout=30)
            data = resp.json()
            
            if data.get('code') != 0:
                print(f"API返回错误: {data.get('message')}")
                return []
            
            folders = data.get('data', {}).get('list', [])
            if not folders:
                print("没有找到收藏夹")
                return []
            
            # 获取第一个收藏夹的内容
            default_folder = folders[0]
            media_id = default_folder['id']
            
            # 获取收藏夹内容
            content_url = f"https://api.bilibili.com/x/v3/fav/resource/list?media_id={media_id}&pn=1&ps=5"
            
            resp = session.get(content_url, headers=headers, timeout=30)
            content_data = resp.json()
            
            if content_data.get('code') != 0:
                print(f"获取内容失败: {content_data.get('message')}")
                return []
            
            medias = content_data.get('data', {}).get('medias', []) or []
            
            for media in medias[:5]:
                videos.append(VideoInfo(
                    title=media.get('title', ''),
                    bvid=media.get('bvid', ''),
                    link=f"https://www.bilibili.com/video/{media.get('bvid', '')}",
                    uploader=media.get('upper', {}).get('name', ''),
                    desc=media.get('intro', ''),
                    duration=media.get('duration', ''),
                    add_time=str(media.get('fav_time', ''))
                ))
        
        except Exception as e:
            print(f"API采集也失败了: {e}")
        
        return videos
    
    def detect_new_videos(self, videos: List[VideoInfo]) -> List[VideoInfo]:
        """检测新视频"""
        history = self._load_history()
        new_videos = []
        
        for video in videos:
            if video.bvid not in history:
                new_videos.append(video)
        
        # 更新历史
        all_bvids = [v.bvid for v in videos]
        self._save_history(all_bvids)
        
        return new_videos
    
    def format_report(self, new_videos: List[VideoInfo]) -> str:
        """格式化报告"""
        if not new_videos:
            return "📭 收藏夹暂无新视频"
        
        report = [f"📺 B站收藏夹更新 ({len(new_videos)} 个新视频)\n"]
        
        for i, video in enumerate(new_videos, 1):
            report.append(f"{i}. **{video.title}**")
            report.append(f"   UP主: {video.uploader}")
            report.append(f"   链接: {video.link}")
            if video.duration:
                report.append(f"   时长: {video.duration}")
            report.append("")
        
        return "\n".join(report)


async def main():
    """主函数"""
    print("🚀 B站收藏夹采集器启动")
    print("-" * 50)
    
    collector = BilibiliCollector("3461564002732313")
    
    # 采集视频
    print("正在采集收藏夹...")
    videos = await collector.collect_with_browser()
    
    if not videos:
        print("浏览器采集失败，尝试API方式...")
        videos = collector.collect_with_api()
    
    print(f"\n采集到 {len(videos)} 个视频")
    
    # 检测新视频
    new_videos = collector.detect_new_videos(videos)
    print(f"其中 {len(new_videos)} 个是新视频")
    
    # 生成报告
    report = collector.format_report(new_videos)
    print("\n" + report)
    
    return report


if __name__ == "__main__":
    result = asyncio.run(main())
