#!/usr/bin/env python3
"""
B站视频字幕提取工具（使用原生字幕API）
"""

import json
import re
import subprocess
from pathlib import Path

def extract_bilibili_subtitle(bv_id: str, cookies_file: str = None) -> Path:
    """
    提取B站原生字幕
    """
    output_dir = Path("./output/subtitles")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    json_path = output_dir / f"{bv_id}.json"
    
    # 使用yt-dlp下载字幕
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-subs",
        "--sub-langs", "zh-CN,zh-TW,zh-Hans,zh,en",
        "--convert-subs", "srt",
        "--output", str(output_dir / bv_id),
    ]
    
    if cookies_file and Path(cookies_file).exists():
        cmd.extend(["--cookies", cookies_file])
    
    cmd.append(f"https://www.bilibili.com/video/{bv_id}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        print(result.stdout)
        if result.stderr:
            print(f"stderr: {result.stderr[:500]}")
        
        # 查找下载的字幕文件
        for sub_file in output_dir.glob(f"{bv_id}*.srt"):
            if sub_file.exists():
                print(f"✅ 找到字幕: {sub_file}")
                return sub_file
        
        print("⚠️ 未找到字幕文件")
        return None
        
    except Exception as e:
        print(f"❌ 提取失败: {e}")
        return None

if __name__ == "__main__":
    import sys
    bv_id = sys.argv[1] if len(sys.argv) > 1 else "BV1nvcuz5Ewj"
    cookies = sys.argv[2] if len(sys.argv) > 2 else ".tools/bilibili_cookies.txt"
    
    result = extract_bilibili_subtitle(bv_id, cookies)
    if result:
        print(f"字幕已保存到: {result}")
    else:
        print("提取失败")
