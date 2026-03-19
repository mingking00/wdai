#!/usr/bin/env python3
"""Bilibili Analyzer - 高层视频分析 Skill

封装 bilibili-cli，提供一键式视频内容分析工作流：
字幕 → AI总结 → 评论分析 → 相关视频

使用 Skill 进化框架设计，支持 YAML/JSON 输出
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


# ============================================================================
# 配置
# ============================================================================

SCHEMA_VERSION = "1.0.0"
DEFAULT_MAX_COMMENTS = 20
DEFAULT_MAX_RELATED = 10


# ============================================================================
# 数据模型
# ============================================================================

@dataclass
class VideoAnalysis:
    """视频分析结果"""
    bv_id: str
    title: str = ""
    subtitle: str = ""           # 字幕内容
    ai_summary: str = ""         # AI 总结
    comments: list = field(default_factory=list)
    related_videos: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "bv_id": self.bv_id,
            "title": self.title,
            "subtitle": self.subtitle[:500] + "..." if len(self.subtitle) > 500 else self.subtitle,
            "subtitle_length": len(self.subtitle),
            "ai_summary": self.ai_summary,
            "comments_count": len(self.comments),
            "comments_sample": self.comments[:5],
            "related_count": len(self.related_videos),
            "metadata": self.metadata,
            "warnings": self.warnings
        }


@dataclass
class AnalysisResult:
    """统一输出格式 (受 bilibili-cli SCHEMA.md 启发)"""
    ok: bool
    schema_version: str
    data: Optional[dict] = None
    error: Optional[dict] = None

    def to_yaml(self) -> str:
        return yaml.dump(self.__dict__, allow_unicode=True, sort_keys=False)

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False, indent=2)

    @classmethod
    def success(cls, data: dict) -> "AnalysisResult":
        return cls(ok=True, schema_version=SCHEMA_VERSION, data=data)

    @classmethod
    def error(cls, code: str, message: str) -> "AnalysisResult":
        return cls(
            ok=False,
            schema_version=SCHEMA_VERSION,
            error={"code": code, "message": message}
        )


# ============================================================================
# Bilibili CLI 调用
# ============================================================================

def run_bili_command(args: list[str]) -> tuple[bool, dict]:
    """运行 bilibili-cli 命令，返回 (成功, 结果)"""
    cmd = ["bili"] + args + ["--yaml"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            output = yaml.safe_load(result.stdout)
            return True, output
        else:
            # 尝试解析错误
            try:
                error_output = yaml.safe_load(result.stdout)
                return False, error_output
            except:
                return False, {"error": result.stderr or result.stdout}
    except subprocess.TimeoutExpired:
        return False, {"error": "Command timeout"}
    except FileNotFoundError:
        return False, {"error": "bilibili-cli not found. Install: pip install bilibili-cli"}
    except Exception as e:
        return False, {"error": str(e)}


# ============================================================================
# 分析工作流
# ============================================================================

def extract_bv_id(input_str: str) -> str:
    """从 URL 或 BV 号提取 BV ID"""
    if input_str.startswith("BV"):
        return input_str
    if "bilibili.com/video/" in input_str:
        # 提取 BV 号
        parts = input_str.split("/")
        for part in parts:
            if part.startswith("BV"):
                return part.split("?")[0]
    raise ValueError(f"无法提取 BV 号: {input_str}")


def analyze_video(
    bv_input: str,
    include_subtitle: bool = True,
    include_ai: bool = True,
    include_comments: bool = True,
    include_related: bool = False,
    max_comments: int = DEFAULT_MAX_COMMENTS,
    max_related: int = DEFAULT_MAX_RELATED
) -> AnalysisResult:
    """
    分析视频内容

    工作流：
    1. 获取基础信息和字幕（优先）
    2. 获取 AI 总结（补充）
    3. 获取评论（情感/互动分析）
    4. 获取相关视频（扩展）
    """
    try:
        bv_id = extract_bv_id(bv_input)
    except ValueError as e:
        return AnalysisResult.error("invalid_input", str(e))

    analysis = VideoAnalysis(bv_id=bv_id)

    # Step 1: 基础视频信息 + 字幕
    print(f"📹 获取视频信息: {bv_id}", file=sys.stderr)
    success, video_data = run_bili_command(["video", bv_id])

    if not success:
        error_msg = video_data.get("error", {}).get("message", "Unknown error")
        return AnalysisResult.error("fetch_failed", f"获取视频信息失败: {error_msg}")

    # 提取元数据
    video_info = video_data.get("data", {}).get("video", {})
    analysis.title = video_info.get("title", "")
    analysis.metadata = {
        "duration": video_info.get("duration"),
        "view_count": video_info.get("stat", {}).get("view"),
        "like_count": video_info.get("stat", {}).get("like"),
        "coin_count": video_info.get("stat", {}).get("coin"),
        "favorite_count": video_info.get("stat", {}).get("favorite"),
        "share_count": video_info.get("stat", {}).get("share"),
        "owner": video_info.get("owner", {}).get("name"),
    }

    # 提取字幕
    if include_subtitle:
        subtitle_data = video_data.get("data", {}).get("subtitle")
        if subtitle_data:
            analysis.subtitle = subtitle_data if isinstance(subtitle_data, str) else str(subtitle_data)
            print(f"✅ 获取到字幕 (长度: {len(analysis.subtitle)} 字符)", file=sys.stderr)
        else:
            analysis.warnings.append("视频无字幕")
            print("⚠️ 视频无字幕", file=sys.stderr)

    # Step 2: AI 总结
    if include_ai and (not analysis.subtitle or len(analysis.subtitle) < 100):
        print("🤖 获取 AI 总结...", file=sys.stderr)
        success, ai_data = run_bili_command(["video", bv_id, "--ai"])
        if success:
            ai_summary = ai_data.get("data", {}).get("ai_summary")
            if ai_summary:
                analysis.ai_summary = ai_summary if isinstance(ai_summary, str) else str(ai_summary)
                print(f"✅ 获取到 AI 总结", file=sys.stderr)

    # Step 3: 评论
    if include_comments:
        print(f"💬 获取评论...", file=sys.stderr)
        success, comments_data = run_bili_command(["video", bv_id, "--comments"])
        if success:
            comments = comments_data.get("data", {}).get("comments", [])
            analysis.comments = comments[:max_comments]
            print(f"✅ 获取到 {len(analysis.comments)} 条评论", file=sys.stderr)

    # Step 4: 相关视频
    if include_related:
        print(f"🔗 获取相关视频...", file=sys.stderr)
        success, related_data = run_bili_command(["video", bv_id, "--related"])
        if success:
            related = related_data.get("data", {}).get("related", [])
            analysis.related_videos = related[:max_related]
            print(f"✅ 获取到 {len(analysis.related_videos)} 个相关视频", file=sys.stderr)

    return AnalysisResult.success(analysis.to_dict())


def analyze_user(uid: str, max_videos: int = 10) -> AnalysisResult:
    """分析 UP 主"""
    print(f"👤 分析 UP 主: {uid}", file=sys.stderr)

    # 获取用户信息
    success, user_data = run_bili_command(["user", uid])
    if not success:
        error_msg = user_data.get("error", {}).get("message", "Unknown error")
        return AnalysisResult.error("fetch_failed", f"获取用户信息失败: {error_msg}")

    user_info = user_data.get("data", {}).get("user", {})

    # 获取视频列表
    print(f"🎬 获取视频列表 (max: {max_videos})...", file=sys.stderr)
    success, videos_data = run_bili_command(["user-videos", uid, "--max", str(max_videos)])

    videos = []
    if success:
        videos = videos_data.get("data", {}).get("items", [])

    result = {
        "uid": uid,
        "name": user_info.get("name"),
        "description": user_info.get("sign"),
        "followers": user_info.get("followers"),
        "following": user_info.get("following"),
        "video_count": user_info.get("video_count"),
        "videos": [
            {
                "bvid": v.get("bvid"),
                "title": v.get("title"),
                "duration": v.get("duration"),
                "view_count": v.get("stat", {}).get("view"),
                "like_count": v.get("stat", {}).get("like"),
            }
            for v in videos[:max_videos]
        ]
    }

    return AnalysisResult.success(result)


def analyze_trending(max_items: int = 20) -> AnalysisResult:
    """分析热门趋势"""
    print(f"🔥 获取热门视频 (max: {max_items})...", file=sys.stderr)

    success, hot_data = run_bili_command(["hot", "--max", str(max_items)])
    if not success:
        error_msg = hot_data.get("error", {}).get("message", "Unknown error")
        return AnalysisResult.error("fetch_failed", f"获取热门失败: {error_msg}")

    items = hot_data.get("data", {}).get("items", [])

    result = {
        "count": len(items),
        "items": [
            {
                "rank": i + 1,
                "bvid": item.get("bvid"),
                "title": item.get("title"),
                "owner": item.get("owner", {}).get("name"),
                "view_count": item.get("stat", {}).get("view"),
                "like_count": item.get("stat", {}).get("like"),
            }
            for i, item in enumerate(items[:max_items])
        ]
    }

    return AnalysisResult.success(result)


# ============================================================================
# CLI 接口
# ============================================================================

def print_help():
    help_text = """
Bilibili Analyzer - 视频内容分析工具

用法:
  python bilibili_analyzer.py video <BV号或URL> [选项]
  python bilibili_analyzer.py user <UID或用户名> [选项]
  python bilibili_analyzer.py trending [选项]

命令:
  video <BV>      分析单个视频
  user <UID>      分析 UP 主
  trending        分析热门趋势

选项:
  --no-subtitle       跳过字幕获取
  --no-ai             跳过 AI 总结
  --no-comments       跳过评论获取
  --related           获取相关视频
  --max-comments N    最大评论数 (默认: 20)
  --max-videos N      最大视频数 (默认: 10)
  --max-items N       最大条目数 (默认: 20)
  --json              输出 JSON (默认: YAML)

示例:
  python bilibili_analyzer.py video BV1ABcsztEcY
  python bilibili_analyzer.py user 946974 --max-videos 5
  python bilibili_analyzer.py trending --max-items 10
"""
    print(help_text)


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print_help()
        sys.exit(0)

    command = args[0]
    output_format = "yaml"

    # 解析选项
    if "--json" in args:
        output_format = "json"
        args.remove("--json")

    try:
        if command == "video":
            if len(args) < 2:
                print("错误: 需要提供 BV 号或 URL", file=sys.stderr)
                print_help()
                sys.exit(1)

            bv_input = args[1]
            include_subtitle = "--no-subtitle" not in args
            include_ai = "--no-ai" not in args
            include_comments = "--no-comments" not in args
            include_related = "--related" in args

            max_comments = DEFAULT_MAX_COMMENTS
            if "--max-comments" in args:
                idx = args.index("--max-comments")
                if idx + 1 < len(args):
                    max_comments = int(args[idx + 1])

            result = analyze_video(
                bv_input=bv_input,
                include_subtitle=include_subtitle,
                include_ai=include_ai,
                include_comments=include_comments,
                include_related=include_related,
                max_comments=max_comments
            )

        elif command == "user":
            if len(args) < 2:
                print("错误: 需要提供 UID 或用户名", file=sys.stderr)
                print_help()
                sys.exit(1)

            uid = args[1]
            max_videos = 10
            if "--max-videos" in args:
                idx = args.index("--max-videos")
                if idx + 1 < len(args):
                    max_videos = int(args[idx + 1])

            result = analyze_user(uid, max_videos)

        elif command == "trending":
            max_items = 20
            if "--max-items" in args:
                idx = args.index("--max-items")
                if idx + 1 < len(args):
                    max_items = int(args[idx + 1])

            result = analyze_trending(max_items)

        else:
            print(f"未知命令: {command}", file=sys.stderr)
            print_help()
            sys.exit(1)

        # 输出结果
        if output_format == "json":
            print(result.to_json())
        else:
            print(result.to_yaml())

        sys.exit(0 if result.ok else 1)

    except KeyboardInterrupt:
        print("\n⏹️ 已取消", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        result = AnalysisResult.error("internal_error", str(e))
        print(result.to_yaml() if output_format == "yaml" else result.to_json())
        sys.exit(1)


if __name__ == "__main__":
    main()
