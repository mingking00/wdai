#!/usr/bin/env python3
"""
Computer Organization Auto-Learning System
计算机组成原理自动化学习系统

遵循第一性原理：
从逻辑门 → 芯片 → CPU → 汇编 → C语言 → 操作系统理论 → Linux内核
"""

import os
import json
from datetime import datetime

class ComputerOrganizationLearning:
    """计算机组成原理自动化学习系统"""
    
    def __init__(self):
        self.workspace = "/root/.openclaw/workspace/.learning/computer-organization"
        os.makedirs(self.workspace, exist_ok=True)
        os.makedirs(f"{self.workspace}/projects", exist_ok=True)
        
        self.progress_file = f"{self.workspace}/progress.json"
        self.current_stage = self._load_progress()
        
    def _load_progress(self):
        """加载学习进度"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            "stage": 0,
            "completed_topics": [],
            "current_topic": None,
            "total_hours": 0
        }
    
    def _save_progress(self):
        """保存学习进度"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.current_stage, f, indent=2)
    
    def run(self):
        """运行自动化学习"""
        print("="*70)
        print("🖥️  Computer Organization Auto-Learning System")
        print("   计算机组成原理自动化学习系统")
        print("="*70)
        print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 显示学习路线图
        self._show_roadmap()
        
        # 开始第一阶段
        print("\n" + "="*70)
        print("🚀 开始第一阶段: Nand2Tetris (硬件基础)")
        print("="*70)
        self._stage1_nand2tetris()
        
    def _show_roadmap(self):
        """显示学习路线图"""
        print("📚 第一性原理学习路径:")
        print()
        print("┌─────────────────────────────────────────────────────────────────┐")
        print("│ Stage 0: Nand2Tetris (4-6周)                                     │")
        print("│   ├─ 从逻辑门(Nand)开始                                          │")
        print("│   ├─ 构建加法器、ALU                                            │")
        print("│   ├─ 构建寄存器、内存                                            │")
        print("│   ├─ 构建CPU (Hack计算机)                                        │")
        print("│   └─ 汇编语言基础                                                │")
        print("├─────────────────────────────────────────────────────────────────┤")
        print("│ Stage 1: CS61C / CSAPP (理论深化)                                │")
        print("│   ├─ C语言系统编程                                               │")
        print("│   ├─ x86/RISC-V汇编                                              │")
        print("│   ├─ 内存层次结构                                                │")
        print("│   ├─ 缓存、流水线                                               │")
        print("│   └─ 链接与加载                                                  │")
        print("├─────────────────────────────────────────────────────────────────┤")
        print("│ Stage 2: 操作系统原理                                            │")
        print("│   ├─ 进程/线程概念                                               │")
        print("│   ├─ 虚拟内存理论                                                │")
        print("│   ├─ 文件系统理论                                                │")
        print("│   └─ 设备管理                                                    │")
        print("├─────────────────────────────────────────────────────────────────┤")
        print("│ Stage 3: Linux内核源码 (现在才到这里)                            │")
        print("│   ├─ 进程调度实现                                                │")
        print("│   ├─ 内存管理实现                                                │")
        print("│   ├─ 设备驱动实现                                                │")
        print("│   └─ 高级主题 (eBPF等)                                           │")
        print("└─────────────────────────────────────────────────────────────────┘")
        print()
        print("当前进度: Stage 0 (刚开始)")
        print()
    
    def _stage1_nand2tetris(self):
        """阶段1: Nand2Tetris学习"""
        
        topics = [
            {
                "id": 1,
                "name": "布尔逻辑与逻辑门",
                "duration": "3-5小时",
                "key_concepts": ["Nand门", "Not", "And", "Or", "Xor", "Mux", "DMux"],
                "project": "Project 1: 用HDL实现基本逻辑门",
                "output": "BasicGates.hdl"
            },
            {
                "id": 2,
                "name": "布尔算术",
                "duration": "4-6小时",
                "key_concepts": ["二进制", "补码", "加法器", "ALU"],
                "project": "Project 2: 实现加法器和ALU",
                "output": "ALU.hdl"
            },
            {
                "id": 3,
                "name": "时序逻辑",
                "duration": "5-7小时",
                "key_concepts": ["D触发器", "寄存器", "RAM", "程序计数器PC"],
                "project": "Project 3: 实现内存组件",
                "output": "RAM8/64/512/4K/16K.hdl"
            },
            {
                "id": 4,
                "name": "机器语言",
                "duration": "4-6小时",
                "key_concepts": ["指令集", "A指令", "C指令", "汇编语法"],
                "project": "练习: 写汇编程序",
                "output": "*.asm files"
            },
            {
                "id": 5,
                "name": "计算机架构",
                "duration": "6-8小时",
                "key_concepts": ["数据通路", "控制逻辑", "Fetch-Decode-Execute"],
                "project": "Project 5: 构建完整CPU",
                "output": "CPU.hdl + Computer.hdl"
            },
            {
                "id": 6,
                "name": "汇编器",
                "duration": "6-8小时",
                "key_concepts": ["汇编过程", "符号解析", "代码生成"],
                "project": "Project 6: 实现汇编器",
                "output": "Assembler.py (or C/Java)"
            }
        ]
        
        print("📖 Nand2Tetris Part I: Hardware (前6章)")
        print(f"预计总时间: 28-40小时 (4-6周)")
        print()
        
        for i, topic in enumerate(topics, 1):
            print(f"\n{'='*70}")
            print(f"主题 {i}: {topic['name']}")
            print(f"{'='*70}")
            print(f"⏱️  预计时间: {topic['duration']}")
            print(f"🔑 核心概念: {', '.join(topic['key_concepts'])}")
            print(f"📝 项目练习: {topic['project']}")
            print(f"📤 产出: {topic['output']}")
            print()
            
            # 模拟学习过程 (实际应该真正学习)
            print(f"[学习任务 {i}]:")
            print(f"  1. 阅读教材: {topic['name']}")
            print(f"  2. 观看视频讲解")
            print(f"  3. 完成项目: {topic['project']}")
            print(f"  4. 测试验证")
            print(f"  5. 记录学习笔记")
            
        # 生成学习计划
        self._generate_study_plan(topics)
        
    def _generate_study_plan(self, topics):
        """生成详细学习计划"""
        plan_file = f"{self.workspace}/STUDY_PLAN.md"
        
        content = f"""# 计算机组成原理学习计划
# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 学习资源: Nand2Tetris + CS61C + CSAPP

## 学习路线图

```
逻辑门 → 算术单元 → 时序逻辑 → 汇编 → CPU → 汇编器
  │         │          │         │      │       │
  └─────────┴──────────┴─────────┴──────┴───────┘
                    │
                    ↓
          C语言系统编程
                    │
                    ↓
          操作系统原理
                    │
                    ↓
          Linux内核源码
```

## Stage 0: Nand2Tetris (当前)

**资源**:
- 网站: https://www.nand2tetris.org/
- 书籍: 《计算机系统要素》(The Elements of Computing Systems)
- Coursera课程: Nand2Tetris Part I

**学习目标**:
- 理解从Nand门到完整计算机的构建过程
- 掌握硬件描述语言(HDL)
- 理解CPU工作原理
- 理解汇编语言基础

**学习进度**:

"""
        
        for i, topic in enumerate(topics, 1):
            content += f"""### 第{i}周: {topic['name']}
- [ ] 阅读教材
- [ ] 观看视频
- [ ] 完成项目: {topic['project']}
- [ ] 测试通过
- [ ] 记录笔记

**核心概念**: {', '.join(topic['key_concepts'])}

**产出**: {topic['output']}

---

"""
        
        content += """## Stage 1: CS61C / CSAPP

**资源**:
- 课程: UC Berkeley CS61C
- 书籍: 《深入理解计算机系统》(CSAPP)

**学习目标**:
- C语言系统编程
- x86/RISC-V汇编
- 内存层次结构
- 缓存与流水线

## Stage 2: 操作系统原理

**资源**:
- 课程: MIT 6.S081 / Berkeley CS162
- 书籍: 《操作系统导论》(OSTEP)

**学习目标**:
- 进程/线程
- 虚拟内存
- 文件系统
- 设备管理

## Stage 3: Linux内核

**资源**:
- Linux内核源码
- LKD (Linux Kernel Development)

**学习目标**:
- 内核源码阅读
- 技巧提取与验证
- 思想工具构建

---

*计划生成完成*
*开始执行...*
"""
        
        with open(plan_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"\n📄 学习计划已生成: {plan_file}")
        print("\n" + "="*70)
        print("✅ 自动化学习系统初始化完成")
        print("="*70)
        print()
        print("🎯 立即开始:")
        print("  1. 访问 https://www.nand2tetris.org/")
        print("  2. 下载课程材料")
        print("  3. 开始第1章: 布尔逻辑")
        print()
        print("⚠️  重要提醒:")
        print("  - 每个项目必须真正动手完成")
        print("  - 不要跳过任何步骤")
        print("  - 确保理解后再进入下一章")
        print()


if __name__ == "__main__":
    learner = ComputerOrganizationLearning()
    learner.run()
