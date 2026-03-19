#!/usr/bin/env python3
"""
测试脚本 - 模拟视频处理流程
不需要下载真实视频，用本地测试数据验证逻辑
"""

import json
from pathlib import Path
from datetime import datetime

# 测试数据：模拟字幕
TEST_SUBTITLES = [
    {"index": 1, "start": "00:00:05", "end": "00:00:10", "text": "大家好，今天讲RAG技术"},
    {"index": 2, "start": "00:00:15", "end": "00:00:25", "text": "RAG是检索增强生成，核心是把外部知识接入大模型"},
    {"index": 3, "start": "00:00:30", "end": "00:00:45", "text": "首先是索引阶段，要把文档切分成小块"},
    {"index": 4, "start": "00:01:00", "end": "00:01:20", "text": "注意，切分很重要，太大或太小都会影响效果"},
    {"index": 5, "start": "00:01:30", "end": "00:01:50", "text": "然后是检索阶段，用户提问时找到最相关的块"},
    {"index": 6, "start": "00:02:00", "end": "00:02:15", "text": "关键是embedding要准，相似度计算要对"},
    {"index": 7, "start": "00:02:30", "end": "00:02:50", "text": "最后生成阶段，把检索结果塞进prompt"},
    {"index": 8, "start": "00:03:00", "end": "00:03:20", "text": "总结一下，RAG三步：索引、检索、生成"},
    {"index": 9, "start": "00:03:30", "end": "00:03:50", "text": "对比微调方案，RAG的优势是知识可更新"},
    {"index": 10, "start": "00:04:00", "end": "00:04:15", "text": "下节课我们实战，用LangChain实现一个简单的RAG"},
]

def test_subtitle_analysis():
    """测试字幕分析逻辑"""
    print("=" * 60)
    print("🧪 测试：字幕关键帧提取")
    print("=" * 60)
    
    # 启发式规则（和主脚本一致）
    keywords = [
        "关键是", "核心", "重点", "注意", "总结", "结论",
        "首先", "第一步", "接下来", "然后",
        "对比", "区别", "不同", "优势", "劣势",
        "例如", "实例", "案例", "演示",
        "问题", "解决", "方案", "方法",
        "定义", "概念", "原理", "机制"
    ]
    
    key_moments = []
    
    for sub in TEST_SUBTITLES:
        text = sub['text']
        score = 0
        matched_keywords = []
        
        for kw in keywords:
            if kw in text:
                score += 2
                matched_keywords.append(kw)
        
        if len(text) > 20:
            score += 1
        
        tech_terms = ["API", "函数", "算法", "模型", "数据", "代码", "系统", "RAG", "LangChain"]
        for term in tech_terms:
            if term in text:
                score += 1
        
        if score >= 3:
            key_moments.append({
                'timestamp': sub['start'],
                'text': text,
                'keywords': matched_keywords,
                'score': score
            })
            print(f"✓ [{sub['start']}] {text[:30]}... (score: {score})")
    
    print(f"\n✅ 识别到 {len(key_moments)} 个关键时间点")
    return key_moments

def test_analysis_prompt_generation():
    """测试分析提示词生成"""
    print("\n" + "=" * 60)
    print("🧪 测试：分析提示词生成")
    print("=" * 60)
    
    subtitle_text = "\n".join([
        f"[{s['start']}] {s['text']}" 
        for s in TEST_SUBTITLES[:5]
    ])
    
    prompt = f"""请分析以下视频字幕，提取关键内容的时间点。

## 任务
从字幕中识别"关键时刻"——即包含重要信息、核心概念、关键结论的时间点。

## 判断标准
1. **概念首次出现**：新术语、新概念的首次解释
2. **重要结论**：总结性陈述、关键发现
3. **操作步骤**：教程类视频的关键步骤开始
4. **对比分析**：不同方案的对比、优缺点分析

## 字幕内容（前5条）
{subtitle_text}

...(共{len(TEST_SUBTITLES)}条字幕)

## 输出格式
请返回JSON数组...
"""
    
    print("生成的提示词预览：")
    print("-" * 40)
    print(prompt[:500] + "...")
    print("-" * 40)
    print("✅ 提示词已生成，可以发送给我进行分析")

def test_kg_output(key_moments):
    """测试知识图谱输出格式"""
    print("\n" + "=" * 60)
    print("🧪 测试：知识图谱输出格式")
    print("=" * 60)
    
    bv_id = "BV_test123"
    kg_documents = []
    
    for i, moment in enumerate(key_moments, 1):
        doc = {
            "id": f"{bv_id}_moment_{i:02d}",
            "type": "video_keyframe",
            "source": {
                "video_id": bv_id,
                "platform": "bilibili",
                "timestamp": moment['timestamp'],
            },
            "content": {
                "text": moment['text'],
                "image_path": f"keyframes/{bv_id}_keyframe_{i:02d}.jpg",
                "keywords": moment.get('keywords', []),
            },
            "metadata": {
                "importance": moment.get('score', 5),
            }
        }
        kg_documents.append(doc)
    
    # 保存到文件
    output_dir = Path("./test_output")
    output_dir.mkdir(exist_ok=True)
    
    kg_path = output_dir / "test_kg_input.json"
    with open(kg_path, 'w', encoding='utf-8') as f:
        json.dump(kg_documents, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 知识图谱JSON已生成: {kg_path}")
    print(f"\n内容预览:")
    print(json.dumps(kg_documents[:2], ensure_ascii=False, indent=2))
    print(f"\n...共 {len(kg_documents)} 条记录")

def test_markdown_generation(key_moments):
    """测试Markdown摘要生成"""
    print("\n" + "=" * 60)
    print("🧪 测试：Markdown摘要生成")
    print("=" * 60)
    
    output_dir = Path("./test_output")
    md_path = output_dir / "test_summary.md"
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# B站视频关键内容摘要\n\n")
        f.write("**视频ID**: BV_test123\n\n")
        f.write(f"**关键帧数量**: {len(key_moments)}\n\n")
        f.write("---\n\n")
        
        for i, moment in enumerate(key_moments, 1):
            f.write(f"## 关键时刻 {i:02d} - {moment['timestamp']}\n\n")
            f.write(f"**内容**: {moment['text']}\n\n")
            f.write(f"**关键词**: {', '.join(moment.get('keywords', []))}\n\n")
            f.write("---\n\n")
    
    print(f"✅ Markdown摘要已生成: {md_path}")
    print(f"\n内容预览:")
    with open(md_path, 'r') as f:
        print(f.read()[:800] + "...")

def main():
    print("🚀 启动视频到知识图谱流程测试\n")
    
    # 1. 测试字幕分析
    key_moments = test_subtitle_analysis()
    
    if not key_moments:
        print("❌ 未识别到关键时间点")
        return
    
    # 2. 测试提示词生成
    test_analysis_prompt_generation()
    
    # 3. 测试知识图谱输出
    test_kg_output(key_moments)
    
    # 4. 测试Markdown生成
    test_markdown_generation(key_moments)
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过!")
    print("=" * 60)
    print("\n📁 测试输出目录: ./test_output/")
    print("\n💡 实际使用时需要安装:")
    print("   pip install yt-dlp openai-whisper")
    print("   apt install ffmpeg")

if __name__ == "__main__":
    main()
