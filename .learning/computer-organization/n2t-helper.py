#!/usr/bin/env python3
"""
Nand2Tetris 学习助手
为用户学习过程提供辅助
"""

import os
import sys

def show_concept(concept):
    """解释核心概念"""
    concepts = {
        "nand": """
🧱 Nand门 (与非门) - 计算机的原子

真值表:
┌─────┬─────┬────────┐
│  a  │  b  │ Nand   │
├─────┼─────┼────────┤
│  0  │  0  │   1    │
│  0  │  1  │   1    │
│  1  │  0  │   1    │
│  1  │  1  │   0    │
└─────┴─────┴────────┘

布尔表达式: Nand(a,b) = NOT(AND(a,b))

关键洞察:
- Nand是"万能门" - 只用Nand可以构建任何逻辑门
- 现代计算机芯片由数十亿个Nand门组成
- 这是理解计算机的第一性原理起点
""",
        "not": """
🔲 Not门 - 用Nand实现

原理: Nand(x, x) = Not(x)

HDL实现:
```hdl
CHIP Not {
    IN in;
    OUT out;
    PARTS:
    Nand(a=in, b=in, out=out);
}
```

验证:
- in=0: Nand(0,0)=1 → out=1 ✓
- in=1: Nand(1,1)=0 → out=0 ✓
""",
        "and": """
🔳 And门 - 用Nand+Not实现

原理: And(a,b) = Not(Nand(a,b))

HDL实现:
```hdl
CHIP And {
    IN a, b;
    OUT out;
    PARTS:
    Nand(a=a, b=b, out=nandOut);
    Not(in=nandOut, out=out);
}
```

注意:
- 先调用Nand，输出命名为nandOut
- 再用Not取反，得到最终out
""",
        "or": """
🔲 Or门 - 德摩根定律

原理: Or(a,b) = Not(And(Not(a), Not(b)))
     即: Or(a,b) = Nand(Not(a), Not(b))

HDL实现:
```hdl
CHIP Or {
    IN a, b;
    OUT out;
    PARTS:
    Not(in=a, out=notA);
    Not(in=b, out=notB);
    Nand(a=notA, b=notB, out=out);
}
```

这是德摩根定律的应用:
- NOT(A AND B) = (NOT A) OR (NOT B)
- 因此: A OR B = NOT((NOT A) AND (NOT B))
""",
        "xor": """
❌ Xor门 (异或)

定义: Xor(a,b) = 1 当且仅当 a≠b

布尔表达式:
Xor(a,b) = Or(And(a, Not(b)), And(Not(a), b))
         = (a AND NOT b) OR (NOT a AND b)

HDL实现思路:
1. 计算 Not(a) 和 Not(b)
2. 计算 a AND Not(b)
3. 计算 Not(a) AND b
4. 用 Or 合并结果

验证真值表:
┌─────┬─────┬────────┐
│  a  │  b  │  Xor   │
├─────┼─────┼────────┤
│  0  │  0  │   0    │
│  0  │  1  │   1    │
│  1  │  0  │   1    │
│  1  │  1  │   0    │
└─────┴─────┴────────┘
""",
        "mux": """
🔀 Mux (多路选择器)

定义: 2选1选择器
- sel=0: 选择a
- sel=1: 选择b

布尔表达式:
Mux(a,b,sel) = Or(And(a, Not(sel)), And(b, sel))

HDL实现思路:
1. Not(sel)
2. And(a, Not(sel)) → 当sel=0时输出a
3. And(b, sel)     → 当sel=1时输出b
4. Or(上述两个结果)

应用场景:
- CPU中的数据选择
- 条件执行
- 内存寻址
"""
    }
    
    if concept in concepts:
        print(concepts[concept])
    else:
        print(f"可用概念: {', '.join(concepts.keys())}")

def check_hdl(file_path):
    """检查HDL代码并提供反馈"""
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    print(f"📄 检查文件: {file_path}")
    print("-" * 40)
    
    # 基础检查
    checks = []
    
    if 'CHIP' in content:
        checks.append(("✅", "找到CHIP定义"))
    else:
        checks.append(("❌", "缺少CHIP定义"))
    
    if 'IN' in content and 'OUT' in content:
        checks.append(("✅", "有输入/输出定义"))
    else:
        checks.append(("❌", "缺少IN/OUT定义"))
    
    if 'PARTS:' in content:
        checks.append(("✅", "找到PARTS部分"))
    else:
        checks.append(("❌", "缺少PARTS部分"))
    
    if 'Nand' in content or 'Not' in content or 'And' in content:
        checks.append(("✅", "使用了基本门"))
    else:
        checks.append(("⚠️", "尚未实现逻辑 (可能只是模板)"))
    
    for status, msg in checks:
        print(f"{status} {msg}")
    
    print("-" * 40)
    print("💡 提示: 在HardwareSimulator中加载对应的.tst文件运行测试")

def show_progress():
    """显示学习进度"""
    progress_file = "/root/.openclaw/workspace/.learning/computer-organization/progress.json"
    
    if os.path.exists(progress_file):
        import json
        with open(progress_file, 'r') as f:
            data = json.load(f)
        
        print("📊 当前学习进度")
        print("=" * 40)
        print(f"阶段: {data.get('stage', 0)}")
        print(f"已完成: {len(data.get('completed_topics', []))} 个主题")
        print(f"当前主题: {data.get('current_topic', '无')}")
        print(f"总学习时间: {data.get('total_hours', 0)} 小时")
    else:
        print("📊 尚未开始学习")
        print("运行 ./setup-nand2tetris.sh 开始")

def main():
    if len(sys.argv) < 2:
        print("Nand2Tetris 学习助手")
        print("=" * 40)
        print()
        print("用法:")
        print(f"  python3 {sys.argv[0]} concept [nand|not|and|or|xor|mux]")
        print(f"  python3 {sys.argv[0]} check [hdl文件路径]")
        print(f"  python3 {sys.argv[0]} progress")
        print()
        print("示例:")
        print(f"  python3 {sys.argv[0]} concept nand")
        print(f"  python3 {sys.argv[0]} check ~/nand2tetris/projects/01/Not.hdl")
        return
    
    command = sys.argv[1]
    
    if command == "concept" and len(sys.argv) > 2:
        show_concept(sys.argv[2])
    elif command == "check" and len(sys.argv) > 2:
        check_hdl(sys.argv[2])
    elif command == "progress":
        show_progress()
    else:
        print(f"未知命令: {command}")

if __name__ == "__main__":
    main()
