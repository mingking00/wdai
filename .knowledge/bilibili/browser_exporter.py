#!/usr/bin/env python3
"""
B站收藏夹浏览器自动化导出工具 v1.0
使用Playwright自动化浏览器获取收藏夹数据
"""

import json
import asyncio
import argparse
from pathlib import Path
from typing import List, Dict
from datetime import datetime

BILIBILI_DIR = Path("/root/.openclaw/workspace/.knowledge/bilibili")
BILIBILI_DIR.mkdir(parents=True, exist_ok=True)

class BilibiliBrowserExporter:
    """
    B站收藏夹浏览器自动化导出器
    通过浏览器自动化获取收藏夹视频列表
    """
    
    def __init__(self, uid: str, headless: bool = True):
        self.uid = uid
        self.headless = headless
        self.export_dir = BILIBILI_DIR / "exports"
        self.export_dir.mkdir(exist_ok=True)
        
    async def init_browser(self):
        """初始化浏览器"""
        try:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            
            # 启动浏览器
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            # 创建新页面
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            self.page = await self.context.new_page()
            print("✅ 浏览器已启动")
            
        except ImportError:
            print("❌ 请先安装Playwright: pip install playwright")
            print("   然后运行: playwright install chromium")
            raise
            
    async def close_browser(self):
        """关闭浏览器"""
        if hasattr(self, 'browser'):
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        print("✅ 浏览器已关闭")
        
    async def login_if_needed(self):
        """检查是否需要登录"""
        print("\n🔐 检查登录状态...")
        
        # 访问B站首页
        await self.page.goto('https://www.bilibili.com', wait_until='networkidle')
        
        # 检查是否有登录按钮
        try:
            login_btn = await self.page.query_selector('.header-login-entry')
            if login_btn:
                print("⚠️  未检测到登录状态")
                print("\n请选择登录方式:")
                print("  1. 扫描二维码登录 (推荐)")
                print("  2. 使用已登录的Chrome Profile")
                print("  3. 手动登录后按回车继续")
                
                # 这里需要用户交互
                # 简化处理：提示用户手动登录
                print("\n📝 请手动登录B站后，按回车继续...")
                input()
                
                # 刷新页面检查登录状态
                await self.page.reload(wait_until='networkidle')
                
        except Exception as e:
            print(f"检查登录状态时出错: {e}")
            
    async def get_favorites_list(self) -> List[Dict]:
        """获取收藏夹列表"""
        print(f"\n📁 获取用户 {self.uid} 的收藏夹列表...")
        
        url = f'https://space.bilibili.com/{self.uid}/favlist'
        await self.page.goto(url, wait_until='networkidle')
        
        # 等待收藏夹列表加载
        await self.page.wait_for_selector('.fav-list-item', timeout=10000)
        
        # 提取收藏夹信息
        favorites = await self.page.evaluate('''() => {
            const items = document.querySelectorAll('.fav-list-item');
            const favs = [];
            items.forEach(item => {
                const titleEl = item.querySelector('.text');
                const countEl = item.querySelector('.num');
                const linkEl = item.querySelector('a');
                
                if (titleEl && linkEl) {
                    const href = linkEl.getAttribute('href');
                    const match = href.match(/fid=(\\d+)/);
                    favs.push({
                        id: match ? match[1] : null,
                        title: titleEl.textContent.trim(),
                        count: countEl ? countEl.textContent.trim() : '0'
                    });
                }
            });
            return favs;
        }''')
        
        print(f"✅ 找到 {len(favorites)} 个收藏夹")
        for i, fav in enumerate(favorites, 1):
            print(f"  {i}. {fav['title']} ({fav['count']}个视频)")
        
        return favorites
        
    async def export_favorite_videos(self, fav_id: str, fav_title: str) -> List[Dict]:
        """导出指定收藏夹的视频列表"""
        print(f"\n📺 正在导出收藏夹: {fav_title}")
        
        url = f'https://space.bilibili.com/{self.uid}/favlist?fid={fav_id}'
        await self.page.goto(url, wait_until='networkidle')
        
        # 等待视频列表加载
        await self.page.wait_for_selector('.fav-video-list', timeout=10000)
        
        videos = []
        page_num = 1
        
        while True:
            print(f"  正在获取第 {page_num} 页...")
            
            # 提取当前页的视频
            page_videos = await self.page.evaluate('''() => {
                const items = document.querySelectorAll('.fav-video-list .small-item');
                const vids = [];
                items.forEach(item => {
                    const titleEl = item.querySelector('.title');
                    const upEl = item.querySelector('.up-name');
                    const linkEl = item.querySelector('a');
                    const bvidMatch = linkEl ? linkEl.getAttribute('href').match(/BV[\\w]+/) : null;
                    
                    vids.push({
                        bvid: bvidMatch ? bvidMatch[0] : '',
                        title: titleEl ? titleEl.textContent.trim() : '',
                        owner: upEl ? upEl.textContent.trim() : '',
                        url: linkEl ? 'https:' + linkEl.getAttribute('href') : ''
                    });
                });
                return vids;
            }''')
            
            videos.extend(page_videos)
            print(f"    获取到 {len(page_videos)} 个视频")
            
            # 检查是否有下一页
            next_btn = await self.page.query_selector('.be-pager-next:not(.be-pager-disabled)')
            if not next_btn:
                break
                
            # 点击下一页
            await next_btn.click()
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(1)  # 等待加载
            page_num += 1
        
        print(f"✅ 共导出 {len(videos)} 个视频")
        return videos
        
    def save_export(self, fav_title: str, videos: List[Dict]):
        """保存导出结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.uid}_{fav_title}_{timestamp}"
        
        # 保存JSON
        json_file = self.export_dir / f"{filename}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'uid': self.uid,
                'favorite_title': fav_title,
                'export_time': datetime.now().isoformat(),
                'video_count': len(videos),
                'videos': videos
            }, f, indent=2, ensure_ascii=False)
        
        # 保存文本格式（便于溯源分析）
        txt_file = self.export_dir / f"{filename}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"# B站收藏夹导出\n")
            f.write(f"# UID: {self.uid}\n")
            f.write(f"# 收藏夹: {fav_title}\n")
            f.write(f"# 导出时间: {datetime.now().isoformat()}\n")
            f.write(f"# 视频数量: {len(videos)}\n\n")
            
            for v in videos:
                f.write(f"{v['bvid']} | {v['title']} | {v['owner']}\n")
        
        # 同时保存到标准位置供溯源器使用
        standard_file = BILIBILI_DIR / f"export_{self.uid}.txt"
        with open(standard_file, 'w', encoding='utf-8') as f:
            for v in videos:
                f.write(f"{v['bvid']} | {v['title']} | {v['owner']}\n")
        
        print(f"\n💾 导出文件已保存:")
        print(f"  - JSON: {json_file}")
        print(f"  - TXT: {txt_file}")
        print(f"  - 标准格式: {standard_file}")
        
        return json_file, txt_file
        
    async def run(self, specific_fav: str = None):
        """运行导出流程"""
        try:
            await self.init_browser()
            await self.login_if_needed()
            
            # 获取收藏夹列表
            favorites = await self.get_favorites_list()
            
            if not favorites:
                print("❌ 没有找到收藏夹")
                return
            
            # 选择要导出的收藏夹
            if specific_fav:
                target = next((f for f in favorites if f['title'] == specific_fav or f['id'] == specific_fav), None)
                if not target:
                    print(f"❌ 找不到收藏夹: {specific_fav}")
                    return
                targets = [target]
            else:
                print("\n📝 请输入要导出的收藏夹编号 (用逗号分隔多个，或输入 'all' 导出全部):")
                user_input = input("> ").strip()
                
                if user_input.lower() == 'all':
                    targets = favorites
                else:
                    try:
                        indices = [int(i.strip()) - 1 for i in user_input.split(',')]
                        targets = [favorites[i] for i in indices if 0 <= i < len(favorites)]
                    except (ValueError, IndexError):
                        print("❌ 输入无效")
                        return
            
            # 导出选中的收藏夹
            for fav in targets:
                videos = await self.export_favorite_videos(fav['id'], fav['title'])
                self.save_export(fav['title'], videos)
                
                # 自动触发溯源分析
                print(f"\n🔄 是否立即对此收藏夹进行溯源分析? (y/n)")
                if input("> ").strip().lower() == 'y':
                    await self.trigger_tracing(fav['title'], videos)
                    
        finally:
            await self.close_browser()
            
    async def trigger_tracing(self, fav_title: str, videos: List[Dict]):
        """触发溯源分析"""
        print(f"\n🔍 启动溯源分析...")
        
        # 保存为标准格式
        standard_file = BILIBILI_DIR / f"export_{self.uid}.txt"
        with open(standard_file, 'w', encoding='utf-8') as f:
            for v in videos:
                f.write(f"{v['bvid']} | {v['title']} | {v['owner']}\n")
        
        # 调用溯源器
        import subprocess
        result = subprocess.run(
            ['python3', 'tracer_v2.py', self.uid],
            cwd=str(BILIBILI_DIR),
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='B站收藏夹浏览器自动化导出')
    parser.add_argument('--uid', default='3461564002732313', help='B站UID')
    parser.add_argument('--fav', help='指定收藏夹名称或ID')
    parser.add_argument('--headless', action='store_true', help='无头模式（不显示浏览器）')
    parser.add_argument('--visible', action='store_true', help='显示浏览器窗口')
    
    args = parser.parse_args()
    
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║     B站收藏夹浏览器自动化导出工具 v1.0                      ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    
    exporter = BilibiliBrowserExporter(
        uid=args.uid,
        headless=not args.visible
    )
    
    await exporter.run(specific_fav=args.fav)

if __name__ == '__main__':
    asyncio.run(main())
