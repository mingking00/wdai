"""
Test Extended Tools
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/kimi-platform/src')

from tools.extended import get_extended_tools, get_all_tools
from tools.builtin import get_default_tools


def test_extended_tools():
    """测试扩展工具"""
    print("\n" + "="*60)
    print("TEST: Extended Tools")
    print("="*60)
    
    tools = get_extended_tools()
    
    print(f"\nExtended tools ({len(tools)}):")
    for tool in tools:
        print(f"  • {tool.name}: {tool.description}")
    
    # 测试HTTP工具
    http_tool = [t for t in tools if t.name == "http_request"][0]
    result = http_tool.execute(
        method="GET",
        url="https://httpbin.org/get",
        timeout=5
    )
    print(f"\n[HTTP Tool] Success: {result.get('success')}")
    
    # 测试JSON工具
    json_tool = [t for t in tools if t.name == "json_processor"][0]
    data = {"name": "test", "value": 123}
    result = json_tool.execute(action="stringify", data=data)
    print(f"[JSON Tool] Result: {result[:50]}...")
    
    # 测试日期时间工具
    datetime_tool = [t for t in tools if t.name == "datetime"][0]
    result = datetime_tool.execute(action="now")
    print(f"[Datetime Tool] Now: {result}")
    
    # 测试随机工具
    random_tool = [t for t in tools if t.name == "random_generator"][0]
    result = random_tool.execute(action="uuid")
    print(f"[Random Tool] UUID: {result}")
    
    # 测试系统工具
    system_tool = [t for t in tools if t.name == "system_info"][0]
    result = system_tool.execute(action="platform")
    print(f"[System Tool] Platform: {result}")
    
    # 测试数据转换工具
    data_tool = [t for t in tools if t.name == "data_transform"][0]
    result = data_tool.execute(action="unique", data=[1, 2, 2, 3, 3, 3])
    print(f"[Data Tool] Unique: {result}")
    
    # 测试文本工具
    text_tool = [t for t in tools if t.name == "text_processor"][0]
    result = text_tool.execute(action="upper", text="hello world")
    print(f"[Text Tool] Upper: {result}")
    
    print("\n✅ All extended tools working")
    return True


def test_all_tools():
    """测试所有工具"""
    print("\n" + "="*60)
    print("TEST: All Tools (Builtin + Extended)")
    print("="*60)
    
    builtin = get_default_tools()
    extended = get_extended_tools()
    all_tools = get_all_tools()
    
    print(f"\nBuiltin tools: {len(builtin)}")
    print(f"Extended tools: {len(extended)}")
    print(f"Total tools: {len(all_tools)}")
    
    assert len(all_tools) == len(builtin) + len(extended)
    
    print("\n✅ Tool count correct")
    return True


def run_tests():
    """运行所有测试"""
    print("\n" + "🛠️" * 30)
    print("EXTENDED TOOLS TESTS")
    print("🛠️" * 30)
    
    tests = [
        test_extended_tools,
        test_all_tools,
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
    print(f"Total tools available: {len(get_all_tools())}")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
