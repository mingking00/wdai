#!/usr/bin/env python3
"""
B站视频 → 关键帧提取 → RAG-Anything 知识库
自动化流程脚本 (支持B站Cookie登录)

用法:
    # 基础用法
    python3 video_to_kg.py <bilibili_url>
    
    # 使用Cookie登录（解决412错误）
    python3 video_to_kg.py <bilibili_url> --cookies cookies.txt
    
    # 使用本地视频文件
    python3 video_to_kg.py --local-video </path/to/video.mp4>
    
示例:
    python3 video_to_kg.py "https://www.bilibili.com/video/BV1nvcuz5Ewj" --cookies ~/.bilibili_cookies.txt
"""

import os
import sys
import json
import re
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional


class VideoToKG:
    """视频到知识图谱转换器"""
    
    def __init__(self, output_dir: str = "./output", cookies_file: Optional[str] = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cookies_file = cookies_file
        
        # 子目录
        self.video_dir = self.output_dir / "videos"
        self.subtitle_dir = self.output_dir / "subtitles"
        self.keyframe_dir = self.output_dir / "keyframes"
        self.kg_dir = self.output_dir / "knowledge_graph"
        
        for d in [self.video_dir, self.subtitle_dir, self.keyframe_dir, self.kg_dir]:
            d.mkdir(exist_ok=True)
    
    def download_video(self, url: str) -> Path:
        """
        下载B站视频（支持短链接和Cookie）
        """
        print(f"📥 正在下载视频: {url}")
        
        # 处理b23.tv短链接 - 解析重定向
        if "b23.tv" in url:
            print("🔗 检测到短链接，解析中...")
            url = self._resolve_short_url(url)
            print(f"   解析结果: {url}")
        
        # 提取BV号
        bv_match = re.search(r'BV[a-zA-Z0-9]+', url)
        if not bv_match:
            raise ValueError("无法提取BV号，请检查URL")
        
        bv_id = bv_match.group()
        output_path = self.video_dir / f"{bv_id}.mp4"
        
        # 检查是否已存在
        if output_path.exists():
            print(f"✅ 视频已存在: {output_path}")
            return output_path
        
        # 构建yt-dlp命令
        cmd = [
            "yt-dlp",
            "--merge-output-format", "mp4",
            "--output", str(output_path),
            "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--add-header", "User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "--add-header", "Referer:https://www.bilibili.com",
        ]
        
        # 添加Cookie支持
        if self.cookies_file and Path(self.cookies_file).exists():
            print(f"🍪 使用Cookie文件: {self.cookies_file}")
            cmd.extend(["--cookies", self.cookies_file])
        else:
            print("⚠️  未使用Cookie，可能遇到412错误")
            print("💡 提示: 使用 --cookies 参数添加Cookie文件以解决下载限制")
        
        cmd.append(url)
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
            
            if output_path.exists():
                file_size = output_path.stat().st_size / (1024 * 1024)  # MB
                print(f"✅ 下载完成: {output_path} ({file_size:.1f} MB)")
                return output_path
            else:
                raise FileNotFoundError(f"预期文件未生成: {output_path}")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ 下载失败")
            print(f"错误信息: {e.stderr[:500] if e.stderr else '无详细错误'}")
            
            if "412" in (e.stderr or ""):
                print("\n⚠️  HTTP 412错误 - B站反爬限制")
                print("\n💡 解决方案:")
                print("   1. 使用 --cookies 参数提供登录Cookie")
                print("   2. 或者手动下载视频后使用 --local-video 参数")
                print("\n📖 Cookie获取方法:")
                print("   浏览器安装 Cookie-Editor 扩展")
                print("   导出B站Cookie为Netscape格式")
                print("   保存到文件如 ~/.bilibili_cookies.txt")
            
            raise
    
    def _resolve_short_url(self, short_url: str) -> str:
        """解析b23.tv短链接到完整URL"""
        import urllib.request
        
        try:
            req = urllib.request.Request(
                short_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.geturl()
        except Exception as e:
            print(f"⚠️  短链接解析失败: {e}")
            print("   请直接使用B站视频完整URL")
            raise
    
    def process_local_video(self, video_path: str) -> Path:
        """
        处理本地视频文件（复制到工作目录）
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        print(f"📁 使用本地视频: {video_path}")
        
        # 复制到工作目录
        dest_path = self.video_dir / video_path.name
        if dest_path.exists():
            print(f"✅ 视频已在工作目录: {dest_path}")
            return dest_path
        
        import shutil
        shutil.copy2(video_path, dest_path)
        print(f"✅ 已复制到: {dest_path}")
        return dest_path
    
    def extract_subtitle(self, video_path: Path) -> Path:
        """
        提取字幕（优先使用B站原生字幕，否则用Whisper）
        """
        print(f"📝 正在提取字幕: {video_path.name}")
        
        bv_id = video_path.stem
        subtitle_path = self.subtitle_dir / f"{bv_id}.srt"
        json_path = self.subtitle_dir / f"{bv_id}.json"
        
        # 先尝试下载B站原生字幕
        if self.cookies_file and self._try_download_bilibili_subtitle(bv_id, subtitle_path):
            print(f"✅ 使用B站原生字幕")
        else:
            # 使用Whisper转录
            print(f"🔄 使用Whisper转录音频...")
            self._whisper_transcribe(video_path, subtitle_path)
        
        # 转换为JSON格式（方便处理）
        self._srt_to_json(subtitle_path, json_path)
        
        return json_path
    
    def _try_download_bilibili_subtitle(self, bv_id: str, output_path: Path) -> bool:
        """尝试下载B站原生字幕"""
        try:
            url = f"https://www.bilibili.com/video/{bv_id}"
            
            cmd = [
                "yt-dlp",
                "--skip-download",
                "--write-subs",
                "--sub-langs", "zh-CN,zh-TW,zh-Hans,zh",
                "--convert-subs", "srt",
                "--output", str(self.subtitle_dir / bv_id),
            ]
            
            if self.cookies_file and Path(self.cookies_file).exists():
                cmd.extend(["--cookies", self.cookies_file])
            
            cmd.append(url)
            
            subprocess.run(cmd, check=True, capture_output=True, timeout=30)
            
            # 查找下载的字幕文件
            for sub_file in self.subtitle_dir.glob(f"{bv_id}*.srt"):
                if sub_file.exists():
                    sub_file.rename(output_path)
                    return True
            return False
        except:
            return False
    
    def _whisper_transcribe(self, video_path: Path, output_path: Path):
        """使用Whisper转录音频"""
        cmd = [
            "whisper",
            str(video_path),
            "--model", "small",
            "--language", "zh",
            "--output_format", "srt",
            "--output_dir", str(self.subtitle_dir),
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            whisper_output = self.subtitle_dir / f"{video_path.stem}.srt"
            if whisper_output.exists():
                whisper_output.rename(output_path)
            print(f"✅ Whisper转录完成")
        except subprocess.CalledProcessError as e:
            print(f"❌ Whisper转录失败: {e}")
            raise
    
    def _srt_to_json(self, srt_path: Path, json_path: Path):
        """将SRT转换为JSON格式"""
        import re
        
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.+?)(?=\n\d+\n|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        subtitles = []
        for idx, start, end, text in matches:
            subtitles.append({
                'index': int(idx),
                'start': start,
                'end': end,
                'start_seconds': self._time_to_seconds(start),
                'end_seconds': self._time_to_seconds(end),
                'text': text.strip().replace('\n', ' ')
            })
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(subtitles, f, ensure_ascii=False, indent=2)
    
    def _time_to_seconds(self, time_str: str) -> float:
        """时间字符串转秒数"""
        parts = time_str.replace(',', '.').split(':')
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    
    def analyze_key_moments(self, subtitle_json: Path) -> List[Dict]:
        """
        分析关键时间点
        """
        print(f"🔍 分析关键时间点: {subtitle_json.name}")
        
        with open(subtitle_json, 'r', encoding='utf-8') as f:
            subtitles = json.load(f)
        
        # 生成分析提示词
        analysis_prompt = self._generate_analysis_prompt(subtitles)
        prompt_path = self.subtitle_dir / f"{subtitle_json.stem}_analysis_prompt.txt"
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(analysis_prompt)
        
        print(f"📝 分析提示词已保存: {prompt_path}")
        
        # 启发式关键帧提取
        key_moments = self._heuristic_key_moments(subtitles)
        
        return key_moments
    
    def _generate_analysis_prompt(self, subtitles: List[Dict]) -> str:
        """生成分析提示词"""
        sample = subtitles[:30]
        
        subtitle_text = "\n".join([
            f"[{s['start']}] {s['text']}" 
            for s in sample
        ])
        
        prompt = f"""请分析以下视频字幕，提取关键内容的时间点。

## 任务
从字幕中识别"关键时刻"——即包含重要信息、核心概念、关键结论的时间点。

## 判断标准
1. **概念首次出现**：新术语、新概念的首次解释
2. **重要结论**：总结性陈述、关键发现
3. **操作步骤**：教程类视频的关键步骤开始
4. **对比分析**：不同方案的对比、优缺点分析

## 字幕内容
{subtitle_text}

...(共{len(subtitles)}条字幕)

## 输出格式
请返回JSON数组：
```json
[
  {{
    "timestamp": "00:02:15",
    "reason": "注意力机制核心原理首次详细解释",
    "keywords": ["注意力", "机制", "原理"],
    "importance": 9
  }},
  ...
]
```
"""
        return prompt
    
    def _heuristic_key_moments(self, subtitles: List[Dict]) -> List[Dict]:
        """启发式关键帧提取"""
        keywords = [
            "关键是", "核心", "重点", "注意", "总结", "结论",
            "首先", "第一步", "接下来", "然后",
            "对比", "区别", "不同", "优势", "劣势",
            "例如", "实例", "案例", "演示",
            "问题", "解决", "方案", "方法",
            "定义", "概念", "原理", "机制"
        ]
        
        key_moments = []
        
        for sub in subtitles:
            text = sub['text']
            score = 0
            matched_keywords = []
            
            for kw in keywords:
                if kw in text:
                    score += 2
                    matched_keywords.append(kw)
            
            if len(text) > 30:
                score += 1
            
            tech_terms = ["API", "函数", "算法", "模型", "数据", "代码", "系统"]
            for term in tech_terms:
                if term in text:
                    score += 1
            
            if score >= 4:
                key_moments.append({
                    'timestamp': sub['start'],
                    'timestamp_seconds': sub['start_seconds'],
                    'text': text,
                    'keywords': matched_keywords,
                    'score': score
                })
        
        # 按时间排序，合并相邻的
        key_moments.sort(key=lambda x: x['timestamp_seconds'])
        
        filtered = []
        last_time = -60
        for moment in key_moments:
            if moment['timestamp_seconds'] - last_time > 30:
                filtered.append(moment)
                last_time = moment['timestamp_seconds']
        
        print(f"✅ 识别到 {len(filtered)} 个关键时间点")
        return filtered[:15]
    
    def extract_keyframes(self, video_path: Path, key_moments: List[Dict]) -> List[Path]:
        """提取关键帧"""
        print(f"🖼️  正在提取关键帧: {len(key_moments)} 个")
        
        keyframe_paths = []
        bv_id = video_path.stem
        
        for i, moment in enumerate(key_moments, 1):
            timestamp = moment['timestamp']
            output_path = self.keyframe_dir / f"{bv_id}_keyframe_{i:02d}_{timestamp.replace(':', '')}.jpg"
            
            cmd = [
                "ffmpeg",
                "-ss", timestamp,
                "-i", str(video_path),
                "-vframes", "1",
                "-q:v", "2",
                str(output_path)
            ]
            
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=10)
                keyframe_paths.append(output_path)
                print(f"  ✓ {timestamp} - {moment['text'][:30]}...")
            except Exception as e:
                print(f"  ✗ {timestamp} 提取失败: {e}")
        
        print(f"✅ 成功提取 {len(keyframe_paths)} 个关键帧")
        return keyframe_paths
    
    def generate_kg_input(self, bv_id: str, key_moments: List[Dict], keyframe_paths: List[Path]):
        """生成知识图谱输入"""
        print(f"📦 正在生成知识图谱输入...")
        
        kg_documents = []
        
        for i, (moment, frame_path) in enumerate(zip(key_moments, keyframe_paths), 1):
            doc = {
                "id": f"{bv_id}_moment_{i:02d}",
                "type": "video_keyframe",
                "source": {
                    "video_id": bv_id,
                    "platform": "bilibili",
                    "timestamp": moment['timestamp'],
                    "timestamp_seconds": moment['timestamp_seconds']
                },
                "content": {
                    "text": moment['text'],
                    "image_path": str(frame_path.relative_to(self.output_dir)),
                    "keywords": moment.get('keywords', []),
                    "description": f"视频关键时刻，时间戳{moment['timestamp']}"
                },
                "metadata": {
                    "extracted_at": datetime.now().isoformat(),
                    "importance": moment.get('score', 5),
                    "extraction_method": "subtitle_analysis"
                }
            }
            kg_documents.append(doc)
        
        # 保存为JSON
        kg_path = self.kg_dir / f"{bv_id}_kg_input.json"
        with open(kg_path, 'w', encoding='utf-8') as f:
            json.dump(kg_documents, f, ensure_ascii=False, indent=2)
        
        # 同时生成Markdown
        md_path = self.kg_dir / f"{bv_id}_summary.md"
        self._generate_summary_md(bv_id, key_moments, keyframe_paths, md_path)
        
        print(f"✅ 知识图谱输入已生成: {kg_path}")
        return kg_path
    
    def _generate_summary_md(self, bv_id: str, key_moments: List[Dict], keyframe_paths: List[Path], output_path: Path):
        """生成Markdown摘要"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# B站视频关键内容摘要\n\n")
            f.write(f"**视频ID**: {bv_id}\n\n")
            f.write(f"**提取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write(f"**关键帧数量**: {len(key_moments)}\n\n")
            f.write("---\n\n")
            
            for i, (moment, frame_path) in enumerate(zip(key_moments, keyframe_paths), 1):
                f.write(f"## 关键时刻 {i:02d} - {moment['timestamp']}\n\n")
                f.write(f"**内容**: {moment['text']}\n\n")
                f.write(f"**关键词**: {', '.join(moment.get('keywords', []))}\n\n")
                f.write(f"**图片**: `{frame_path.name}`\n\n")
                f.write("---\n\n")
    
    def run(self, url: str = None, local_video: str = None):
        """执行完整流程"""
        print("=" * 60)
        print("🎬 B站视频 → 关键帧 → 知识图谱")
        print("=" * 60)
        
        try:
            # 1. 获取视频
            if local_video:
                video_path = self.process_local_video(local_video)
            elif url:
                video_path = self.download_video(url)
            else:
                raise ValueError("请提供视频URL或本地视频路径")
            
            # 2. 提取字幕
            subtitle_json = self.extract_subtitle(video_path)
            
            # 3. 分析关键时间点
            key_moments = self.analyze_key_moments(subtitle_json)
            
            if not key_moments:
                print("⚠️  未识别到关键时间点")
                return
            
            # 4. 提取关键帧
            keyframe_paths = self.extract_keyframes(video_path, key_moments)
            
            # 5. 生成知识图谱输入
            bv_id = video_path.stem
            kg_path = self.generate_kg_input(bv_id, key_moments, keyframe_paths)
            
            # 完成
            print("\n" + "=" * 60)
            print("✅ 处理完成!")
            print("=" * 60)
            print(f"\n📁 输出目录: {self.output_dir.absolute()}")
            print(f"   ├─ 视频: {self.video_dir}")
            print(f"   ├─ 字幕: {subtitle_json}")
            print(f"   ├─ 关键帧: {self.keyframe_dir}")
            print(f"   └─ 知识图谱: {kg_path}")
            
        except Exception as e:
            print(f"\n❌ 处理失败: {e}")
            raise


def show_cookie_guide():
    """显示Cookie获取指南"""
    guide = """
╔══════════════════════════════════════════════════════════════╗
║              B站Cookie获取指南                               ║
╚══════════════════════════════════════════════════════════════╝

方法1: Cookie-Editor 扩展（推荐）
─────────────────────────────────
1. 浏览器安装 Cookie-Editor 扩展
   Chrome: https://chrome.google.com/webstore/detail/cookie-editor/...
   
2. 登录B站 (www.bilibili.com)

3. 点击扩展图标 → 选择bilibili.com

4. 点击 "Export" → 选择 "Netscape"

5. 保存到文件，例如: ~/.bilibili_cookies.txt

方法2: 开发者工具
─────────────────
1. 登录B站
2. F12打开开发者工具 → Application/应用 → Cookies
3. 复制SESSDATA值
4. 格式化为Netscape格式保存

使用方法:
────────
python3 video_to_kg.py "BV链接" --cookies ~/.bilibili_cookies.txt
"""
    print(guide)


def main():
    parser = argparse.ArgumentParser(description='B站视频 → 关键帧 → 知识图谱')
    parser.add_argument('url', nargs='?', help='B站视频URL (支持b23.tv短链接)')
    parser.add_argument('--local-video', '-l', help='本地视频文件路径')
    parser.add_argument('--output-dir', '-o', default='./output', help='输出目录')
    parser.add_argument('--cookies', '-c', help='B站Cookie文件路径 (Netscape格式)')
    parser.add_argument('--cookie-guide', action='store_true', help='显示Cookie获取指南')
    
    args = parser.parse_args()
    
    if args.cookie_guide:
        show_cookie_guide()
        return
    
    if not args.url and not args.local_video:
        parser.print_help()
        print("\n💡 提示: 使用 --cookie-guide 查看B站Cookie获取方法")
        return
    
    converter = VideoToKG(output_dir=args.output_dir, cookies_file=args.cookies)
    converter.run(url=args.url, local_video=args.local_video)


if __name__ == "__main__":
    main()
