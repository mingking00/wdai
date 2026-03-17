#!/usr/bin/env python3
"""
Document RAG Skill 使用示例
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace')

from skills.document_rag import DocumentRAGSkill

def main():
    # 初始化 Skill（可以传入 KIMI_API_KEY）
    skill = DocumentRAGSkill()
    
    # 示例 1: 快速问答（一次性处理）
    print("=" * 50)
    print("示例 1: 快速问答")
    print("=" * 50)
    
    result = skill.quick_answer(
        question="违约金条款是什么？",
        file_path="/tmp/test_contract.txt"
    )
    
    print(result.to_markdown())
    
    # 示例 2: 批量处理并建立知识库
    print("\n" + "=" * 50)
    print("示例 2: 建立知识库")
    print("=" * 50)
    
    # 处理文档
    info = skill.process_document(
        file_path="/tmp/test_contract.txt",
        kb_name="test_kb"
    )
    
    print(f"\n已处理: {info.filename}")
    print(f"分块数: {info.chunks_count}")
    print(f"使用模板: {info.template}")
    
    # 基于知识库问答
    print("\n" + "=" * 50)
    print("示例 3: 知识库问答")
    print("=" * 50)
    
    result = skill.query(
        question="付款方式有哪些？",
        kb_name="test_kb"
    )
    
    print(result.to_markdown())
    
    # 示例 4: 查看知识库信息
    print("\n" + "=" * 50)
    print("示例 4: 知识库信息")
    print("=" * 50)
    
    info = skill.get_kb_info("test_kb")
    print(f"知识库名称: {info['name']}")
    print(f"文本块数量: {info['chunks_count']}")
    print(f"来源文档: {info['sources']}")
    
    # 示例 5: 列出所有知识库
    print("\n" + "=" * 50)
    print("示例 5: 知识库列表")
    print("=" * 50)
    
    kbs = skill.list_knowledge_bases()
    print(f"共有 {len(kbs)} 个知识库:")
    for kb in kbs:
        print(f"  - {kb}")
    
    # 清理
    print("\n" + "=" * 50)
    print("清理测试知识库...")
    print("=" * 50)
    skill.delete_knowledge_base("test_kb")
    print("✅ 已删除")


if __name__ == "__main__":
    main()
