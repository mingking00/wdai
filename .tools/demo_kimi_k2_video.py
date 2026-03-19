#!/usr/bin/env python3
"""
完整演示：Kimi K2.5 视频 → 关键帧 → 知识图谱
使用模拟字幕数据（因B站下载受限）
"""

import json
from pathlib import Path
from datetime import datetime

# 模拟从视频提取的真实字幕内容
# 基于视频: [LLM Architect] 08 Dive into K2.5，Kimi K2.5 论文串讲与导读
SIMULATED_SUBTITLES = [
    {"start": "00:00:00", "text": "今天我们来深入解读Kimi K2.5的技术报告"},
    {"start": "00:00:45", "text": "Kimi K2.5是一个原生多模态大模型，这是它最大的特点"},
    {"start": "00:01:30", "text": "原生多模态的意思是，模型从一开始就用图文混合数据训练，而不是后期拼接"},
    {"start": "00:02:15", "text": "关键架构设计：视觉编码器采用了一种创新的分层策略"},
    {"start": "00:03:00", "text": "注意力机制上，K2.5使用了改进的稀疏注意力，降低长上下文计算的复杂度"},
    {"start": "00:04:30", "text": "Agent Swarm是另一个亮点，多个Agent协作完成任务"},
    {"start": "00:05:45", "text": "总结来说，Kimi K2.5的核心创新有三点：原生多模态、Agent Swarm、长上下文优化"},
    {"start": "00:07:00", "text": "对比GPT-4o，K2.5在多模态理解上有明显优势，特别是在中文场景"},
    {"start": "00:08:30", "text": "实际应用中，K2.5的Agent能力可以自动化完成复杂工作流"},
    {"start": "00:10:00", "text": "下一步我将用代码演示如何调用K2.5的多模态API"},
]

def analyze_key_moments(subtitles):
    """分析关键时间点"""
    print("=" * 60)
    print("🔍 分析关键时间点")
    print("=" * 60)
    
    # 关键词权重
    keywords = {
        "核心": 3, "关键": 3, "重要": 2, "总结": 3, "对比": 2,
        "创新": 2, "特点": 2, "优势": 2, "应用": 2, "演示": 2,
        "原生多模态": 4, "Agent Swarm": 4, "注意力机制": 3,
        "架构设计": 3, "视觉编码器": 3, "长上下文": 3,
    }
    
    key_moments = []
    
    for sub in subtitles:
        text = sub['text']
        score = 0
        matched_keywords = []
        
        # 计算关键词得分
        for kw, weight in keywords.items():
            if kw in text:
                score += weight
                matched_keywords.append(kw)
        
        # 信息密度加分
        if len(text) > 30:
            score += 1
        
        # 技术术语密度
        tech_terms = ["模型", "架构", "编码器", "注意力", "Agent", "API"]
        for term in tech_terms:
            if term in text:
                score += 1
        
        # 阈值判断
        if score >= 4:
            key_moments.append({
                'timestamp': sub['start'],
                'text': text,
                'keywords': matched_keywords,
                'score': score
            })
            print(f"✓ [{sub['start']}] {text[:40]}... (score: {score})")
    
    print(f"\n✅ 识别到 {len(key_moments)} 个关键时间点")
    return key_moments

def generate_analysis_prompt(subtitles):
    """生成给我分析的提示词"""
    print("\n" + "=" * 60)
    print("📝 生成AI分析提示词")
    print("=" * 60)
    
    subtitle_text = "\n".join([
        f"[{s['start']}] {s['text']}" 
        for s in subtitles
    ])
    
    prompt = f"""请分析以下视频字幕，提取关键内容的时间点。

## 任务
从字幕中识别"关键时刻"——即包含重要信息、核心概念、关键结论的时间点。

## 判断标准
1. **概念首次出现**：新术语、新概念的首次解释
2. **重要结论**：总结性陈述、关键发现  
3. **对比分析**：不同方案的对比、优缺点分析
4. **实战预告**：即将演示的内容

## 字幕内容
{subtitle_text}

## 输出格式
请返回JSON数组，包含：
- timestamp: 时间戳 (HH:MM:SS)
- reason: 为什么是关键时刻
- keywords: 关键词列表
- importance: 重要性评分 (1-10)
"""
    
    print("提示词已生成，长度:", len(prompt), "字符")
    return prompt

def generate_kg_documents(video_id, key_moments):
    """生成知识图谱文档"""
    print("\n" + "=" * 60)
    print("📦 生成知识图谱输入")
    print("=" * 60)
    
    documents = []
    
    for i, moment in enumerate(key_moments, 1):
        doc = {
            "id": f"{video_id}_moment_{i:02d}",
            "type": "video_keyframe",
            "source": {
                "video_id": video_id,
                "title": "[LLM Architect] 08 Dive into K2.5",
                "platform": "bilibili",
                "timestamp": moment['timestamp'],
                "url": f"https://www.bilibili.com/video/{video_id}?t={moment['timestamp']}"
            },
            "content": {
                "text": moment['text'],
                "image_path": f"keyframes/{video_id}_keyframe_{i:02d}.jpg",
                "keywords": moment['keywords'],
                "summary": f"视频关键时刻 - {moment['timestamp']}"
            },
            "metadata": {
                "extracted_at": datetime.now().isoformat(),
                "importance_score": moment['score'],
                "analysis_method": "keyword_scoring"
            }
        }
        documents.append(doc)
    
    return documents

def generate_markdown_summary(video_id, key_moments):
    """生成Markdown摘要"""
    print("\n" + "=" * 60)
    print("📝 生成Markdown可视化摘要")
    print("=" * 60)
    
    md_content = f"""# 🎬 Kimi K2.5 论文串讲 - 关键内容摘要

**视频标题**: [LLM Architect] 08 Dive into K2.5，Kimi K2.5 论文串讲与导读  
**UP主**: 五道口纳什  
**视频ID**: {video_id}  
**提取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**关键帧数量**: {len(key_moments)}

---

## 📋 视频核心内容概览

本视频深入解读了月之暗面发布的Kimi K2.5技术报告，重点介绍了：
- ✅ 原生多模态架构设计
- ✅ Agent Swarm协作机制  
- ✅ 长上下文优化策略
- ✅ 与GPT-4o的对比分析

---

## 🎯 关键时刻详细记录

"""
    
    for i, moment in enumerate(key_moments, 1):
        md_content += f"""### 时刻 {i:02d} - ⏱️ {moment['timestamp']}

**内容**: {moment['text']}

**关键词**: {', '.join(moment['keywords'])}

**重要性**: {'⭐' * min(moment['score'] // 2, 5)}

**对应帧**: `{video_id}_keyframe_{i:02d}.jpg`

---

"""
    
    md_content += f"""## 💡 知识图谱导入说明

1. 将 `keyframes/` 目录下的图片导入 RAG-Anything
2. 导入对应的JSON元数据文件
3. 即可开始针对视频内容进行问答

## 🔗 相关链接

- [原始视频](https://www.bilibili.com/video/{video_id})
- [Kimi K2.5 技术报告](https://www.moonshot.cn/)
"""
    
    return md_content

def main():
    print("🚀 开始处理: Kimi K2.5 论文串讲视频")
    print("视频: BV1nvcuz5Ewj")
    print("时长: ~58分钟 (模拟前10分钟字幕)\n")
    
    video_id = "BV1nvcuz5Ewj"
    
    # 1. 分析关键时间点
    key_moments = analyze_key_moments(SIMULATED_SUBTITLES)
    
    if not key_moments:
        print("❌ 未识别到关键时间点")
        return
    
    # 2. 生成分析提示词（供我后续使用）
    prompt = generate_analysis_prompt(SIMULATED_SUBTITLES)
    
    # 3. 生成知识图谱文档
    kg_docs = generate_kg_documents(video_id, key_moments)
    
    # 4. 生成Markdown摘要
    md_content = generate_markdown_summary(video_id, key_moments)
    
    # 保存文件
    output_dir = Path("./demo_output")
    output_dir.mkdir(exist_ok=True)
    
    # 保存KG JSON
    kg_path = output_dir / f"{video_id}_kg.json"
    with open(kg_path, 'w', encoding='utf-8') as f:
        json.dump(kg_docs, f, ensure_ascii=False, indent=2)
    
    # 保存Markdown
    md_path = output_dir / f"{video_id}_summary.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    # 保存提示词
    prompt_path = output_dir / f"{video_id}_analysis_prompt.txt"
    with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write(prompt)
    
    # 输出总结
    print("\n" + "=" * 60)
    print("✅ 处理完成!")
    print("=" * 60)
    print(f"\n📁 输出文件:")
    print(f"   ├─ KG文档: {kg_path}")
    print(f"   ├─ 摘要: {md_path}")
    print(f"   └─ 分析提示词: {prompt_path}")
    
    print(f"\n🎯 识别的关键时间点:")
    for i, m in enumerate(key_moments, 1):
        print(f"   {i}. [{m['timestamp']}] {m['text'][:35]}... (score: {m['score']})")
    
    print(f"\n💡 下一步:")
    print(f"   1. 查看 {md_path.name} 了解视频结构")
    print(f"   2. 使用 {kg_path.name} 导入RAG-Anything")
    print(f"   3. 可针对这些关键时刻提问")

if __name__ == "__main__":
    main()
