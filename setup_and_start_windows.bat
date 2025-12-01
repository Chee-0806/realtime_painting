@echo off
setlocal enabledelayedexpansion

REM StreamDiffusion Windows环境一键配置和启动脚本

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM 设置颜色代码
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

echo %GREEN%========================================%NC%
echo %GREEN%StreamDiffusion Windows环境一键配置脚本%NC%
echo %GREEN%========================================%NC%

REM 检查Python是否安装
echo %BLUE%检查Python环境...%NC%
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%错误: 未检测到Python，请先安装Python 3.10或更高版本%NC%
    echo %YELLOW%下载地址: https://www.python.org/downloads/%NC%
    pause
    exit /b 1
)

REM 检查Python版本
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo %GREEN%Python版本: %PYTHON_VERSION%%NC%

REM 检查pip是否可用
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%错误: pip不可用，请检查Python安装%NC%
    pause
    exit /b 1
)

REM 检查虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo %GREEN%检测到现有虚拟环境%NC%
    choice /c YN /m "是否要重新创建虚拟环境? (Y/N)"
    if !errorlevel! equ 1 (
        echo %YELLOW%删除现有虚拟环境...%NC%
        rmdir /s /q venv
        if exist "venv" (
            echo %RED%错误: 无法删除现有虚拟环境，请手动删除%NC%
            pause
            exit /b 1
        )
        set CREATE_VENV=1
    ) else (
        set CREATE_VENV=0
    )
) else (
    set CREATE_VENV=1
)

REM 创建虚拟环境
if %CREATE_VENV% equ 1 (
    echo %YELLOW%创建虚拟环境...%NC%
    python -m venv venv
    if %errorlevel% neq 0 (
        echo %RED%错误: 创建虚拟环境失败%NC%
        pause
        exit /b 1
    )
    echo %GREEN%✓ 虚拟环境创建成功%NC%
)

REM 激活虚拟环境
echo %YELLOW%激活虚拟环境...%NC%
call venv\Scripts\activate.bat

REM 升级pip
echo %YELLOW%升级pip...%NC%
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo %YELLOW%警告: pip升级失败，继续使用当前版本%NC%
)

REM 检查CUDA是否可用
echo %BLUE%检查CUDA环境...%NC%
python -c "import torch; print('CUDA可用' if torch.cuda.is_available() else 'CUDA不可用')" 2>nul
if %errorlevel% neq 0 (
    echo %YELLOW%警告: 无法检查CUDA状态，可能需要安装PyTorch%NC%
    set CUDA_AVAILABLE=0
) else (
    for /f "delims=" %%i in ('python -c "import torch; print('1' if torch.cuda.is_available() else '0')" 2^>nul') do set CUDA_AVAILABLE=%%i
    if !CUDA_AVAILABLE! equ 1 (
        for /f "delims=" %%i in ('python -c "import torch; print(torch.version.cuda)" 2^>nul') do set CUDA_VERSION=%%i
        echo %GREEN%CUDA版本: !CUDA_VERSION!%NC%
    ) else (
        echo %YELLOW%CUDA不可用，将使用CPU模式%NC%
    )
)

REM 检查配置文件
if not exist "app\config.yaml" (
    echo %RED%错误: 配置文件不存在: app\config.yaml%NC%
    pause
    exit /b 1
)
echo %GREEN%配置文件: app\config.yaml%NC%

REM 检查必要的目录
if not exist "engines" mkdir engines
if not exist "logs" mkdir logs

REM 设置环境变量
set PYTHONUNBUFFERED=1
set PYTHONDONTWRITEBYTECODE=1

REM 安装PyTorch（根据CUDA状态）
if %CUDA_AVAILABLE% equ 1 (
    echo %YELLOW%安装PyTorch (CUDA支持)...%NC%
    pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu118
) else (
    echo %YELLOW%安装PyTorch (CPU版本)...%NC%
    pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cpu
)

if %errorlevel% neq 0 (
    echo %RED%错误: PyTorch安装失败%NC%
    pause
    exit /b 1
)

REM 安装其他后端依赖
echo %YELLOW%安装其他后端依赖...%NC%
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo %RED%错误: 安装后端依赖失败%NC%
    pause
    exit /b 1
)
echo %GREEN%✓ 后端依赖安装完成%NC%

REM 检查Node.js是否安装
echo %BLUE%检查Node.js环境...%NC%
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%错误: 未检测到Node.js，请先安装Node.js%NC%
    echo %YELLOW%下载地址: https://nodejs.org/%NC%
    pause
    exit /b 1
)

REM 检查Node.js版本
for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo %GREEN%Node.js版本: !NODE_VERSION!%NC%

REM 检查npm版本
for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
echo %GREEN%npm版本: !NPM_VERSION!%NC%

REM 检查前端目录
if not exist "frontend" (
    echo %YELLOW%警告: 前端目录不存在，仅启动后端服务%NC%
    goto :start_backend_only
)

REM 检查前端依赖
if not exist "frontend\node_modules" (
    echo %YELLOW%安装前端依赖...%NC%
    cd frontend
    npm install
    if %errorlevel% neq 0 (
        echo %RED%错误: 安装前端依赖失败%NC%
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo %GREEN%✓ 前端依赖安装完成%NC%
) else (
    echo %GREEN%前端依赖已安装%NC%
)

:start_backend_only
REM 询问是否立即启动服务
echo.
echo %GREEN%========================================%NC%
echo %GREEN%环境配置完成%NC%
echo %GREEN%========================================%NC%
choice /c YN /m "是否立即启动前后端服务? (Y/N)"
if !errorlevel! equ 2 (
    echo %GREEN%环境配置完成，可以手动运行 start_windows.bat 启动服务%NC%
    pause
    exit /b 0
)

REM 启动后端服务
echo %GREEN%启动后端服务...%NC%
start /b cmd /c "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > logs\backend.log 2>&1"

REM 等待后端服务启动
echo %YELLOW%等待后端服务启动...%NC%
timeout /t 5 /nobreak >nul

REM 检查后端是否启动成功
curl -s -f --max-time 2 http://127.0.0.1:8000/api/health >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%警告: 后端服务可能未完全启动，请检查日志%NC%
    echo %BLUE%后端日志: logs\backend.log%NC%
) else (
    echo %GREEN%✓ 后端服务已启动%NC%
)

REM 如果前端目录存在，启动前端服务
if exist "frontend" (
    REM 启动前端服务
    echo %GREEN%启动前端服务...%NC%
    cd frontend
    start /b cmd /c "npm run dev > ..\logs\frontend.log 2>&1"
    cd ..
    
    REM 等待前端服务启动
    timeout /t 3 /nobreak >nul
    
    echo %GREEN%✓ 前端服务已启动%NC%
    echo %BLUE%前端日志: logs\frontend.log%NC%
)

echo.
echo %GREEN%========================================%NC%
echo %GREEN%所有服务已启动%NC%
echo %GREEN%========================================%NC%
echo %BLUE%后端服务: http://0.0.0.0:8000%NC%
echo %BLUE%前端服务: http://127.0.0.1:6006%NC%
echo %BLUE%API文档: http://0.0.0.0:8000/docs%NC%
echo %YELLOW%按任意键停止所有服务...%NC%
echo.

REM 等待用户按键
pause >nul

REM 停止服务
echo %YELLOW%正在停止服务...%NC%

REM 停止后端服务
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| find "python.exe"') do (
    taskkill /f /pid %%i >nul 2>&1
)

REM 停止前端服务
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq node.exe" /fo csv ^| find "node.exe"') do (
    taskkill /f /pid %%i >nul 2>&1
)

echo %GREEN%✓ 所有服务已停止%NC%
pause
