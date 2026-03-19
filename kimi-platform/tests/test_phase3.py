"""
Phase 3 Test - Memory System
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/kimi-platform/src')

from memory.memory import (
    ShortTermMemory, LongTermMemory, SemanticMemory,
    MemoryManager, create_memory_manager
)
import tempfile
import shutil


def test_1_short_term_memory():
    """测试1: 短期记忆"""
    print("\n" + "="*60)
    print("TEST 1: 短期记忆")
    print("="*60)
    
    mem = ShortTermMemory(max_size=5)
    
    # 存储
    mem.store("key1", "value1")
    mem.store("key2", "value2")
    mem.store("key3", "value3")
    
    # 检索
    assert mem.retrieve("key1") == "value1"
    assert mem.retrieve("key2") == "value2"
    
    # 搜索
    results = mem.search("value")
    assert len(results) == 3
    
    # LRU淘汰测试 - 存储超过容量后，最旧的应该被淘汰
    mem.store("key4", "value4")
    mem.store("key5", "value5") 
    # 现在存储了5个(key1-5)，满了
    
    mem.store("key6", "value6")  # 应该淘汰最旧的
    
    # 验证总数量不超过max_size
    assert len(mem) == 5
    # key6应该存在（刚存入）
    assert mem.retrieve("key6") == "value6"
    
    print(f"✅ Short-term memory working: {len(mem)} items")
    print("✅ Test 1 PASSED")
    return True


def test_2_long_term_memory():
    """测试2: 长期记忆"""
    print("\n" + "="*60)
    print("TEST 2: 长期记忆")
    print("="*60)
    
    # 使用临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        mem = LongTermMemory(temp_dir)
        
        # 存储
        mem.store("user_name", "Alice")
        mem.store("user_pref", {"theme": "dark", "lang": "zh"})
        
        # 检索
        assert mem.retrieve("user_name") == "Alice"
        assert mem.retrieve("user_pref") == {"theme": "dark", "lang": "zh"}
        
        # 持久化验证：重新创建对象
        mem2 = LongTermMemory(temp_dir)
        assert mem2.retrieve("user_name") == "Alice"
        
        # 搜索
        results = mem.search("user")
        assert len(results) == 2
        
        print(f"✅ Long-term memory working: {len(mem.list_all())} items")
        print("✅ Test 2 PASSED")
        return True
    finally:
        shutil.rmtree(temp_dir)


def test_3_semantic_memory():
    """测试3: 语义记忆"""
    print("\n" + "="*60)
    print("TEST 3: 语义记忆")
    print("="*60)
    
    mem = SemanticMemory()
    
    # 存储文本
    mem.store("doc1", "Python is a programming language")
    mem.store("doc2", "JavaScript is used for web development")
    mem.store("doc3", "Machine learning is a subset of AI")
    
    # 语义搜索
    results = mem.search("programming", limit=3)
    print(f"Search 'programming': {results}")
    
    # 应该找到相关内容
    assert len(results) > 0
    
    # 检索
    assert "Python" in mem.retrieve("doc1")
    
    print(f"✅ Semantic memory working: {len(mem)} items")
    print("✅ Test 3 PASSED")
    return True


def test_4_memory_manager():
    """测试4: 记忆管理器"""
    print("\n" + "="*60)
    print("TEST 4: 记忆管理器")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        mm = create_memory_manager(temp_dir)
        
        # 分层存储
        mm.store("temp_data", "short term only", level="short_term")
        mm.store("important_data", "save to all levels", level="all")
        mm.remember("I like Python", importance="high")
        
        # 检索
        assert mm.retrieve("temp_data") == "short term only"
        assert mm.retrieve("important_data") == "save to all levels"
        
        # 跨层搜索
        results = mm.search("Python")
        print(f"Search 'Python': {results}")
        
        # 回忆
        recall = mm.recall("programming language")
        print(f"Recall: {recall}")
        assert len(recall) > 0
        
        # 统计
        stats = mm.stats()
        print(f"Memory stats: {stats}")
        assert stats["short_term"] >= 2
        
        print("✅ Memory manager working")
        print("✅ Test 4 PASSED")
        return True
    finally:
        shutil.rmtree(temp_dir)


def test_5_recall_context():
    """测试5: 上下文回忆"""
    print("\n" + "="*60)
    print("TEST 5: 上下文回忆")
    print("="*60)
    
    mm = create_memory_manager()
    
    # 存储一系列事实
    mm.remember("User name is Bob")
    mm.remember("Bob likes Python programming")
    mm.remember("Bob works as a developer")
    mm.remember("Python is great for AI")
    
    # 获取上下文
    context = mm.get_context(3)
    print(f"Recent context:\n{context}")
    
    # 回忆关于Bob的信息
    recall = mm.recall("Bob", top_k=3)
    print(f"Recall about Bob: {recall}")
    assert any("Bob" in r for r in recall)
    
    # 回忆关于编程
    recall2 = mm.recall("programming", top_k=2)
    print(f"Recall about programming: {recall2}")
    
    print("✅ Context and recall working")
    print("✅ Test 5 PASSED")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🧪" * 30)
    print("KIMI PLATFORM - PHASE 3 TESTS")
    print("🧪" * 30)
    
    tests = [
        test_1_short_term_memory,
        test_2_long_term_memory,
        test_3_semantic_memory,
        test_4_memory_manager,
        test_5_recall_context,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"\n❌ Test FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
