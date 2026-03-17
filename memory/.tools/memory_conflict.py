#!/usr/bin/env python3
"""
记忆冲突检测系统
- 识别矛盾信息
- 检测过期内容
- 标记待验证记忆
"""

import chromadb
import re
from datetime import datetime, timedelta
from pathlib import Path
from difflib import SequenceMatcher

MEMORY_DIR = Path("/root/.openclaw/workspace/memory")
DB_PATH = MEMORY_DIR / ".vectordb"

def load_all_memories():
    """加载所有记忆"""
    client = chromadb.PersistentClient(path=str(DB_PATH))
    collection = client.get_collection("memories")
    return collection.get()

def detect_contradictions(threshold=0.7):
    """检测矛盾信息"""
    memories = load_all_memories()
    
    contradictions = []
    
    # 提取陈述句
    statements = []
    for doc, meta, id_ in zip(
        memories['documents'],
        memories['metadatas'],
        memories['ids']
    ):
        # 提取关键陈述
        sentences = re.split(r'[。！？\.\n]', doc)
        for sent in sentences:
            sent = sent.strip()
            # 匹配 "X 是 Y" 或 "X 应该 Y" 格式的陈述
            if re.search(r'(是|应该|必须|始终|从不|不要)', sent) and len(sent) > 10:
                statements.append({
                    "text": sent,
                    "id": id_,
                    "path": meta.get('path', 'unknown'),
                    "type": meta.get('type', 'unknown')
                })
    
    # 检测相似但可能矛盾的陈述
    for i, stmt1 in enumerate(statements):
        for stmt2 in statements[i+1:]:
            similarity = SequenceMatcher(None, stmt1['text'], stmt2['text']).ratio()
            
            # 相似度高但有关键词相反
            if similarity > threshold:
                # 检查是否有相反关键词
                opposite_pairs = [
                    ("应该", "不应该"),
                    ("必须", "不必"),
                    ("始终", "有时"),
                    ("是", "不是"),
                    ("要", "不要"),
                    ("可以", "不可以")
                ]
                
                has_opposite = False
                for pos, neg in opposite_pairs:
                    if (pos in stmt1['text'] and neg in stmt2['text']) or \
                       (neg in stmt1['text'] and pos in stmt2['text']):
                        has_opposite = True
                        break
                
                if has_opposite or similarity > 0.9:
                    contradictions.append({
                        "statement1": stmt1,
                        "statement2": stmt2,
                        "similarity": similarity,
                        "type": "possible_contradiction" if has_opposite else "high_similarity"
                    })
    
    return contradictions

def detect_outdated_memories(days=90):
    """检测过期记忆"""
    memories = load_all_memories()
    
    outdated = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    for doc, meta, id_ in zip(
        memories['documents'],
        memories['metadatas'],
        memories['ids']
    ):
        created = meta.get('created', '')
        if created:
            try:
                mem_date = datetime.strptime(created, "%Y-%m-%d")
                if mem_date < cutoff_date:
                    # 检查是否是原则类（不过期）
                    if meta.get('type') not in ['principle']:
                        outdated.append({
                            "id": id_,
                            "path": meta.get('path', 'unknown'),
                            "type": meta.get('type', 'unknown'),
                            "created": created,
                            "age_days": (datetime.now() - mem_date).days
                        })
            except:
                pass
    
    return outdated

def detect_duplicate_tags():
    """检测重复标签"""
    memories = load_all_memories()
    
    tag_sources = {}
    
    for meta in memories['metadatas']:
        tags = meta.get('tags', '').split(',') if meta.get('tags') else []
        for tag in tags:
            tag = tag.strip()
            if tag:
                if tag not in tag_sources:
                    tag_sources[tag] = []
                tag_sources[tag].append(meta.get('path', 'unknown'))
    
    # 找出重复的标签
    duplicates = {tag: paths for tag, paths in tag_sources.items() if len(paths) > 1}
    
    return duplicates

def generate_conflict_report(contradictions, outdated, duplicates):
    """生成冲突报告"""
    report = f"""# 记忆冲突检测报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## ⚠️ 潜在矛盾 ({len(contradictions)} 项)

"""
    
    if contradictions:
        for i, conflict in enumerate(contradictions[:10], 1):  # 最多显示10个
            report += f"""### {i}. {conflict['type']}

**记忆 1** ({conflict['statement1']['path']}):
> {conflict['statement1']['text']}

**记忆 2** ({conflict['statement2']['path']}):
> {conflict['statement2']['text']}

相似度: {conflict['similarity']:.1%}

---

"""
    else:
        report += "✅ 未发现明显矛盾\n\n"
    
    report += f"""## 🕐 过期记忆 ({len(outdated)} 项)

"""
    
    if outdated:
        report += "| 路径 | 类型 | 创建时间 | 天数 |\n"
        report += "|------|------|----------|------|\n"
        for item in outdated[:20]:  # 最多显示20个
            report += f"| {item['path']} | {item['type']} | {item['created']} | {item['age_days']} |\n"
        
        if len(outdated) > 20:
            report += f"\n... 还有 {len(outdated) - 20} 项\n"
    else:
        report += "✅ 未发现过期记忆\n\n"
    
    report += f"""
## 🏷️ 重复标签 ({len(duplicates)} 项)

"""
    
    if duplicates:
        for tag, paths in list(duplicates.items())[:10]:
            report += f"**{tag}**: 出现在 {len(paths)} 个记忆中\n"
            for path in paths[:3]:
                report += f"  - {path}\n"
            if len(paths) > 3:
                report += f"  ... 还有 {len(paths) - 3} 个\n"
            report += "\n"
    else:
        report += "✅ 未发现重复标签问题\n\n"
    
    report += """## 💡 建议操作

1. **解决矛盾**: 检查标记的潜在矛盾，更新或删除过时的记忆
2. **清理过期**: 归档超过90天的短期记忆
3. **标准化标签**: 统一标签命名规范
4. **定期检测**: 建议每月运行一次冲突检测

"""
    
    # 保存报告
    report_path = MEMORY_DIR / ".reports" / f"conflict_report_{datetime.now().strftime('%Y%m%d')}.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    return report_path

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 记忆冲突检测")
    print("=" * 60)
    
    # 1. 检测矛盾
    print("\n⚠️  检测潜在矛盾...")
    contradictions = detect_contradictions()
    print(f"  发现 {len(contradictions)} 个潜在矛盾")
    
    # 2. 检测过期记忆
    print("\n🕐 检测过期记忆...")
    outdated = detect_outdated_memories(days=90)
    print(f"  发现 {len(outdated)} 个过期记忆")
    
    # 3. 检测重复标签
    print("\n🏷️  检测重复标签...")
    duplicates = detect_duplicate_tags()
    print(f"  发现 {len(duplicates)} 个重复标签")
    
    # 4. 生成报告
    print("\n📝 生成冲突报告...")
    report_path = generate_conflict_report(contradictions, outdated, duplicates)
    print(f"  报告已保存: {report_path}")
    
    # 5. 显示摘要
    print("\n" + "=" * 60)
    print("📊 检测摘要")
    print("=" * 60)
    print(f"  潜在矛盾: {len(contradictions)}")
    print(f"  过期记忆: {len(outdated)}")
    print(f"  重复标签: {len(duplicates)}")
    
    if contradictions or outdated:
        print("\n⚠️  发现需要处理的问题，请查看详细报告")
    else:
        print("\n✅ 记忆系统状态良好")
    
    print("\n" + "=" * 60)
    print("✅ 冲突检测完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()
