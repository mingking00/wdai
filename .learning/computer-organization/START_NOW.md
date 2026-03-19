# 🚀 立即开始指南

## 明确分工

### 🤖 我能做的 (AI助手)
- ✅ 解释概念和原理
- ✅ 检查你的HDL代码
- ✅ 回答学习中的问题
- ✅ 生成学习资料
- ✅ 跟踪你的进度

### 👤 你需要做的 (学习者)
- 📖 阅读教材和视频
- ✍️ 动手写HDL代码
- 🧪 在HardwareSimulator中测试
- 🤔 思考"为什么"
- 📝 记录学习笔记

---

## 🎯 开始第1周学习

### 步骤1: 搭建环境 (5分钟)

```bash
# 运行环境搭建脚本
bash /root/.openclaw/workspace/.learning/computer-organization/setup-nand2tetris.sh
```

这会:
- 下载Nand2Tetris软件
- 安装Java
- 创建项目目录
- 生成启动指南

### 步骤2: 启动硬件仿真器

```bash
cd ~/nand2tetris/tools
./HardwareSimulator.sh
```

你会看到一个GUI界面，这是你的"实验台"。

### 步骤3: 实现第一个门 (Not)

1. 在仿真器中: File → Load Chip → 选择 `projects/01/Not.hdl`
2. 编辑 `Not.hdl` 文件，添加实现:

```hdl
CHIP Not {
    IN in;
    OUT out;

    PARTS:
    Nand(a=in, b=in, out=out);
}
```

3. 加载测试: File → Load Script → 选择 `projects/01/Not.tst`
4. 运行: Run → Run (或按 F5)
5. 看到绿色对勾 = 通过! ✅

### 步骤4: 使用学习助手

```bash
# 查看概念解释
python3 /root/.openclaw/workspace/.learning/computer-organization/n2t-helper.py concept nand
python3 /root/.openclaw/workspace/.learning/computer-organization/n2t-helper.py concept not

# 检查你的代码
python3 /root/.openclaw/workspace/.learning/computer-organization/n2t-helper.py check ~/nand2tetris/projects/01/Not.hdl
```

---

## 📚 本周任务清单

### 第1天: 理解Nand和Not
- [ ] 阅读《计算机系统要素》第1章前半部分
- [ ] 观看Nand2Tetris视频第1讲
- [ ] 实现Not门
- [ ] 理解: 为什么Nand(x,x)=Not(x)?

### 第2天: And和Or
- [ ] 实现And门 (提示: Not+Nand)
- [ ] 实现Or门 (提示: 德摩根定律)
- [ ] 验证真值表

### 第3天: Xor和Mux
- [ ] 实现Xor门
- [ ] 实现Mux (多路选择器)
- [ ] 理解Mux的实际用途

### 第4-7天: 完成所有15个门
- [ ] 16位版本 (Not16, And16, Or16, Mux16)
- [ ] 多路选择器 (Mux4Way16, Mux8Way16)
- [ ] 多路分配器 (DMux, DMux4Way, DMux8Way)

---

## 💡 如何向我求助

在学习过程中，你可以问我：

**概念问题**:
- "解释为什么Nand是万能门?"
- "德摩根定律是什么?"
- "Mux和DMux的区别?"

**代码问题**:
- "帮我检查这个Or.hdl"
- "Xor门为什么这样实现?"
- "这个错误是什么意思?"

**原理问题**:
- "为什么计算机用二进制?"
- "逻辑门怎么变成物理电路?"
- "这一步的目的是什么?"

---

## 🎓 学习原则 (基于之前的教训)

### 1. 理解先于记忆
❌ 不要: 背下HDL代码  
✅ 要做: 理解布尔代数原理

### 2. 每个门都要测试
❌ 不要: 写完了就认为对  
✅ 要做: 在仿真器中运行测试，看到绿色对勾

### 3. 不看答案先思考
❌ 不要: 直接看答案实现  
✅ 要做: 先自己推导，卡住了再看提示

### 4. 能解释才算懂
❌ 不要: "运行通过了就下一个"  
✅ 要做: 试着向我解释"为什么这样实现"

---

## 📖 关键资源

| 资源 | 链接/位置 | 用途 |
|------|-----------|------|
| 官网 | https://www.nand2tetris.org/ | 下载材料 |
| 书籍 | 《计算机系统要素》 | 系统学习 |
| 视频 | Coursera: Nand2Tetris Part I | 讲解 |
| 软件 | ~/nand2tetris/tools/ | 硬件仿真器 |
| 项目 | ~/nand2tetris/projects/01/ | 你的代码 |
| 助手 | n2t-helper.py | 查询概念 |

---

## ⚡ 现在就开始

```bash
# 1. 搭建环境
bash /root/.openclaw/workspace/.learning/computer-organization/setup-nand2tetris.sh

# 2. 查看Not门概念
python3 /root/.openclaw/workspace/.learning/computer-organization/n2t-helper.py concept not

# 3. 启动仿真器开始实践
cd ~/nand2tetris/tools && ./HardwareSimulator.sh
```

**有问题随时问我!** 🤖

---

*记住: 我不是在学习，我是在协助你学习。真正的理解来自你的动手实践。*
