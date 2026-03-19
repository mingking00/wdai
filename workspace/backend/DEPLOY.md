# 在新电脑上部署 Vibero Reader

## 📦 需要复制的文件

只复制这个文件夹到新电脑：

```
backend/                    ← 整个文件夹
├── app.py
├── requirements.txt
├── start.sh / start.bat
├── README.md
└── templates/
    └── index.html
```

## 🖥️ 新电脑环境要求

- **Python 3.8+** (必须)
- **pip** (Python包管理器)
- **浏览器** (Chrome/Firefox/Safari)

### 检查Python
```bash
python3 --version    # Mac/Linux
python --version     # Windows
```

如果没有Python，从 https://python.org 下载安装。

---

## 🚀 启动步骤

### 1. 复制文件
把 `backend` 文件夹复制到新电脑任意位置，例如桌面。

### 2. 打开终端

**Mac/Linux:** 打开 Terminal  
**Windows:** 打开 CMD 或 PowerShell

### 3. 进入目录
```bash
cd ~/Desktop/backend        # Mac/Linux
cd C:\Users\用户名\Desktop\backend   # Windows
```

### 4. 安装依赖（首次）
```bash
pip3 install -r requirements.txt    # Mac/Linux
pip install -r requirements.txt     # Windows
```

或者一键启动脚本会自动安装：
```bash
./start.sh              # Mac/Linux
start.bat               # Windows
```

### 5. 启动服务
```bash
./start.sh              # Mac/Linux
start.bat               # Windows
```

### 6. 浏览器访问
打开 http://localhost:5000

---

## ⚠️ 常见问题

### 端口被占用
如果提示 "Address already in use"，修改 `app.py` 最后一行：
```python
app.run(host='0.0.0.0', port=5001, debug=True)  # 改成5001或其他
```

### 防火墙/网络
- 本机使用：没问题
- 局域网其他设备访问：需要关闭防火墙或开放5000端口

### 依赖安装失败
```bash
# 尝试升级pip
python -m pip install --upgrade pip

# 然后重新安装
pip install flask flask-cors requests
```

---

## 📋 快速检查清单

在新电脑上：

- [ ] 安装 Python 3.8+
- [ ] 复制 backend 文件夹
- [ ] 安装依赖 `pip install -r requirements.txt`
- [ ] 运行 `./start.sh` 或 `start.bat`
- [ ] 浏览器打开 http://localhost:5000
- [ ] 配置 API Key（点击⚙️）
- [ ] 上传小说开始阅读

---

## 💾 打包给别人的方法

如果想把整个应用打包发给别人：

```bash
# 1. 创建压缩包
cd workspace
zip -r ViberoReader.zip backend/

# 2. 发给对方，对方解压后按上面步骤启动
```

---

**简单说：只要有Python，复制backend文件夹就能运行。**
