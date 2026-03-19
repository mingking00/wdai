# Week 1: 布尔逻辑与逻辑门
# 主题: 从Nand门构建所有基本逻辑门
# 学习时间: 2026-03-10
# 预计耗时: 3-5小时

## 🎯 学习目标

理解第一性原理:
- **Nand门是万能门** - 只用Nand门可以构建所有其他逻辑门
- **布尔代数** - 理解Not, And, Or, Xor的真值表和公式
- **硬件描述语言(HDL)** - 学会用代码描述硬件

## 📚 核心概念

### 1. Nand门 (与非门)
```
输入A | 输入B | 输出
  0   |   0   |   1
  0   |   1   |   1
  1   |   0   |   1
  1   |   1   |   0
```
公式: `Nand(a,b) = Not(And(a,b))`

### 2. 用Nand构建Not
```hdl
CHIP Not {
    IN in;
    OUT out;

    PARTS:
    Nand(a=in, b=in, out=out);
}
```
原理: `Nand(x,x) = Not(x)`

### 3. 用Nand构建And
```hdl
CHIP And {
    IN a, b;
    OUT out;

    PARTS:
    Nand(a=a, b=b, out=nandOut);
    Not(in=nandOut, out=out);
}
```
原理: `And(a,b) = Not(Nand(a,b))`

### 4. 用Nand构建Or (德摩根定律)
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
原理: `Or(a,b) = Not(And(Not(a), Not(b)))`

### 5. Xor (异或)
```
输入A | 输入B | 输出
  0   |   0   |   0
  0   |   1   |   1
  1   |   0   |   1
  1   |   1   |   0
```
公式: `Xor(a,b) = Or(And(a,Not(b)), And(Not(a),b))`

### 6. Mux (多路选择器)
```
选择位sel | 输入a | 输入b | 输出
    0     |   0   |   *   |   0
    0     |   1   |   *   |   1
    1     |   *   |   0   |   0
    1     |   *   |   1   |   1
```
公式: `Mux(a,b,sel) = Or(And(a,Not(sel)), And(b,sel))`

## 📝 项目任务

### Project 1: 实现基本逻辑门

需要实现的芯片 (按推荐顺序):
1. ✅ **Not** - 最简单，Nand(a,a)
2. ✅ **And** - Not + Nand
3. ✅ **Or** - 德摩根定律
4. ✅ **Xor** - 用And,Or,Not组合
5. ✅ **Mux** - 2选1多路选择器
6. ✅ **DMux** - 1分2多路分配器
7. ✅ **Not16** - 16位Not
8. ✅ **And16** - 16位And
9. ✅ **Or16** - 16位Or
10. ✅ **Mux16** - 16位Mux
11. ✅ **Or8Way** - 8输入Or
12. ✅ **Mux4Way16** - 4选1 16位Mux
13. ✅ **Mux8Way16** - 8选1 16位Mux
14. ✅ **DMux4Way** - 1分4 DMux
15. ✅ **DMux8Way** - 1分8 DMux

## 💡 关键洞察

**第一性原理应用**:

问题: "计算机需要什么基本组件？"

拆解:
1. 计算机需要处理信息
2. 信息用二进制表示 (0和1)
3. 需要操作二进制的电路
4. Nand门可以构建所有逻辑操作
5. 因此，Nand门是构建计算机的"原子"

**为什么从Nand开始？**
- Nand门是实际硅芯片中最容易实现的逻辑门
- 晶体管的天然特性就是Nand/Nor行为
- 只需要Nand就可以构建完整计算机

## 🛠️ 实践步骤

### 步骤1: 下载工具
```bash
# 下载Nand2Tetris软件套件
wget https://drive.google.com/file/d/1xZzcMIUETe3EYOhgyTpld4IrR9pAzRiM/view
# 或使用课程提供的工具
```

### 步骤2: 实现Not
```hdl
// projects/01/Not.hdl
CHIP Not {
    IN in;
    OUT out;

    PARTS:
    Nand(a=in, b=in, out=out);
}
```

### 步骤3: 测试
```bash
# 使用硬件仿真器
HardwareSimulator.sh
# 加载 Not.tst，运行测试
```

### 步骤4: 逐个实现其他门
按照推荐顺序，每个门:
1. 写出真值表
2. 推导出布尔表达式
3. 用HDL实现
4. 用测试文件验证

## ✅ 完成标准

- [ ] 所有15个基本门实现完成
- [ ] 所有测试通过 (绿色对勾)
- [ ] 理解每个门的布尔代数原理
- [ ] 能够不看答案独立完成Xor和Mux

## 📝 学习笔记模板

```markdown
## 日期: 
## 学习内容: 
## 遇到的困难: 
## 解决方法: 
## 关键收获: 
## 代码片段: 
```

## 📖 资源

- 网站: https://www.nand2tetris.org/
- 书籍: 《计算机系统要素》第1章
- Coursera: Nand2Tetris Part I, Week 1

---

*第一周学习目标: 理解Nand是万能门，学会用HDL描述硬件*
