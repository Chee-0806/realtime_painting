# StreamDiffusion Windows环境使用指南

本文档提供了在Windows环境下配置和运行StreamDiffusion项目的详细指南。

## 系统要求

- Windows 10/11 (64位)
- Python 3.10 或更高版本
- Node.js 16.0 或更高版本
- Git (可选，用于克隆项目)

## 安装步骤

### 1. 安装Python

1. 访问 [Python官网](https://www.python.org/downloads/)
2. 下载Python 3.10或更高版本
3. 运行安装程序，**务必勾选"Add Python to PATH"选项**

### 2. 安装Node.js

1. 访问 [Node.js官网](https://nodejs.org/)
2. 下载LTS版本
3. 运行安装程序，按照默认设置完成安装

### 3. 克隆项目

```bash
git clone <项目地址>
cd realtime_painting
```

## 使用脚本

我们提供了三个Windows脚本，根据您的需求选择使用：

### 1. setup_and_start_windows.bat (推荐)

**一键配置和启动脚本**，包含完整的环境检测和配置功能。

**功能特点：**
- 自动检测Python和Node.js环境
- 自动创建和配置虚拟环境
- 自动检测CUDA并安装相应版本的PyTorch
- 自动安装所有依赖
- 可选择是否立即启动服务

**使用方法：**
```bash
setup_and_start_windows.bat
```

### 2. start_windows.bat

**快速启动脚本**，适用于已配置好环境的情况。

**功能特点：**
- 快速启动前后端服务
- 基本的环境检查
- 适合日常使用

**使用方法：**
```bash
start_windows.bat
```

### 3. start_windows.ps1

**PowerShell版本启动脚本**，提供更好的进程管理和错误处理。

**功能特点：**
- 更精确的进程控制
- 更好的错误处理
- 彩色输出
- 适合需要更精细控制的用户

**使用方法：**
```powershell
powershell -ExecutionPolicy Bypass -File start_windows.ps1
```

## 常见问题解决

### 1. Python相关问题

**问题：** `python不是内部或外部命令`
**解决：** 确保安装Python时勾选了"Add Python to PATH"，或者手动将Python添加到系统PATH环境变量

**问题：** 虚拟环境创建失败
**解决：** 尝试以管理员身份运行脚本

### 2. Node.js相关问题

**问题：** `node不是内部或外部命令`
**解决：** 重新安装Node.js，确保勾选"Add to PATH"选项

**问题：** npm安装依赖失败
**解决：** 尝试清除npm缓存：`npm cache clean --force`

### 3. CUDA相关问题

**问题：** CUDA不可用
**解决：** 
1. 确保安装了NVIDIA显卡驱动
2. 安装与显卡驱动兼容的CUDA Toolkit
3. 安装与CUDA版本匹配的PyTorch

### 4. 端口占用问题

**问题：** 端口8000或6006被占用
**解决：** 
1. 关闭占用端口的程序
2. 或者修改脚本中的端口号

### 5. PowerShell执行策略问题

**问题：** 无法运行PowerShell脚本
**解决：** 以管理员身份运行PowerShell，执行：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 手动配置步骤

如果自动脚本无法正常工作，可以尝试手动配置：

### 1. 创建虚拟环境

```bash
python -m venv venv
venv\Scripts\activate.bat
```

### 2. 安装PyTorch

**CUDA版本：**
```bash
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu118
```

**CPU版本：**
```bash
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cpu
```

### 3. 安装其他依赖

```bash
pip install -r requirements.txt
```

### 4. 安装前端依赖

```bash
cd frontend
npm install
cd ..
```

### 5. 启动服务

**启动后端：**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**启动前端（新终端）：**
```bash
cd frontend
npm run dev
```

## 访问应用

服务启动后，可以通过以下地址访问：

- 前端应用：http://127.0.0.1:6006
- 后端API：http://0.0.0.0:8000
- API文档：http://0.0.0.0:8000/docs

## 日志文件

日志文件位于`logs`目录：
- `backend.log` - 后端服务日志
- `frontend.log` - 前端服务日志

## 技术支持

如果遇到问题，请检查：

1. Python和Node.js版本是否符合要求
2. 是否有足够的磁盘空间
3. 网络连接是否正常（用于下载依赖）
4. 防火墙是否阻止了相关端口

如需更多帮助，请查看项目的GitHub Issues或联系开发团队。
