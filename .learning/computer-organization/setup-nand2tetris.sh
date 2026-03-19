#!/bin/bash
# Nand2Tetris 环境搭建脚本
# 为用户准备学习工具

set -e

echo "======================================"
echo "🖥️  Nand2Tetris 环境搭建"
echo "======================================"

N2T_DIR="$HOME/nand2tetris"

# 创建目录
mkdir -p "$N2T_DIR"
cd "$N2T_DIR"

echo ""
echo "📥 步骤1: 下载Nand2Tetris软件套件"
echo "--------------------------------------"

# 检查是否已下载
if [ -f "nand2tetris.zip" ]; then
    echo "✓ 软件包已存在"
else
    echo "正在从官方源下载..."
    # 官方下载链接
    wget -O nand2tetris.zip "https://drive.google.com/uc?export=download&id=1xZzcMIUETe3EYOhgyTpld4IrR9pAzRiM" 2>/dev/null || {
        echo "⚠️  Google Drive下载失败，使用备用方案"
        echo "请手动下载: https://www.nand2tetris.org/software"
        echo "下载后解压到: $N2T_DIR"
    }
fi

echo ""
echo "📦 步骤2: 解压软件"
echo "--------------------------------------"

if [ -d "nand2tetris" ]; then
    echo "✓ 已解压"
else
    unzip -q nand2tetris.zip 2>/dev/null || echo "请手动解压"
fi

echo ""
echo "☕ 步骤3: 安装Java (硬件仿真器需要)"
echo "--------------------------------------"

if command -v java &> /dev/null; then
    echo "✓ Java已安装: $(java -version 2>&1 | head -n 1)"
else
    echo "正在安装OpenJDK..."
    sudo apt-get update
    sudo apt-get install -y openjdk-11-jre
fi

echo ""
echo "📝 步骤4: 创建项目目录"
echo "--------------------------------------"

mkdir -p "$N2T_DIR/projects/01"
cd "$N2T_DIR/projects/01"

# 创建第一个项目文件
cat > Not.hdl << 'EOF'
// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/01/Not.hdl

/**
 * Not gate:
 * out = not in
 */

CHIP Not {
    IN in;
    OUT out;

    PARTS:
    // Put your code here:
    
}
EOF

cat > And.hdl << 'EOF'
// And gate: 
// out = 1 if (a == 1 and b == 1)
//       0 otherwise

CHIP And {
    IN a, b;
    OUT out;

    PARTS:
    // Put your code here:
    
}
EOF

echo "✓ 创建模板文件: Not.hdl, And.hdl"

echo ""
echo "🎯 步骤5: 启动说明"
echo "--------------------------------------"

cat > "$N2T_DIR/START_HERE.txt" << EOF
Nand2Tetris 学习启动指南
========================

1. 启动硬件仿真器:
   cd $N2T_DIR/nand2tetris/tools
   ./HardwareSimulator.sh

2. 打开项目文件:
   File -> Load Chip -> 选择 .hdl 文件

3. 运行测试:
   Run -> Run (或按 F5)

4. 项目目录:
   $N2T_DIR/projects/01/

学习资源:
- 官网: https://www.nand2tetris.org/
- 书籍: 《计算机系统要素》
- Coursera: Nand2Tetris Part I

开始你的第1个项目: 实现15个基本逻辑门!
EOF

cat "$N2T_DIR/START_HERE.txt"

echo ""
echo "======================================"
echo "✅ 环境搭建完成!"
echo "======================================"
echo ""
echo "下一步:"
echo "  1. 阅读 $N2T_DIR/START_HERE.txt"
echo "  2. 启动硬件仿真器"
echo "  3. 开始实现第一个门: Not.hdl"
echo ""
echo "提示: Not门的实现只有一行:"
echo "  Nand(a=in, b=in, out=out);"
echo ""
