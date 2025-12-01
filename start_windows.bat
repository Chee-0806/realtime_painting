@echo off
REM StreamDiffusion Windows环境前后端启动脚本

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
echo %GREEN%StreamDiffusion Windows环境启动脚本%NC%
echo %GREEN%========================================%NC%

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%错误: 未检测到Python，请先安装Python 3.10或更高版本%NC%
    pause
    exit /b 1
)

REM 检查Python版本
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo %GREEN%Python版本: %PYTHON_VERSION%%NC%

REM 检查虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo %YELLOW%激活虚拟环境...%NC%
    call venv\Scripts\activate.bat
) else (
    echo %YELLOW%虚拟环境不存在，正在创建...%NC%
    python -m venv venv
    if %errorlevel% neq 0 (
        echo %RED%错误: 创建虚拟环境失败%NC%
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
    echo %GREEN%✓ 虚拟环境创建成功%NC%
)

REM 升级pip
echo %YELLOW%升级pip...%NC%
python -m pip install --upgrade pip

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

REM 安装后端依赖
echo %YELLOW%安装后端依赖...%NC%
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo %RED%错误: 安装后端依赖失败%NC%
    pause
    exit /b 1
)
echo %GREEN%✓ 后端依赖安装完成%NC%

REM 检查Node.js是否安装
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%错误: 未检测到Node.js，请先安装Node.js%NC%
    pause
    exit /b 1
)

REM 检查前端目录
if not exist "frontend" (
    echo %YELLOW%警告: 前端目录不存在，仅启动后端服务%NC%
    goto :start_backend_only
)

REM 检查前端依赖
if not exist "frontend\node_modules" (
    echo %YELLOW%前端依赖未安装，正在安装...%NC%
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
)

:start_backend_only
REM 启动后端服务
echo %GREEN%启动后端服务...%NC%
start /b python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > logs\backend.log 2>&1
set BACKEND_PID=%errorlevel%

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
    start /b npm run dev > ..\logs\frontend.log 2>&1
    set FRONTEND_PID=%errorlevel%
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
echo %YELLOW%按任意键停止所有服务...%NC%
echo.

REM 等待用户按键
pause >nul

REM 停止服务
echo %YELLOW%正在停止服务...%NC%

REM 停止后端服务
taskkill /f /im python.exe /fi "windowtitle eq uvicorn*" >nul 2>&1
taskkill /f /im python.exe /fi "cmd /c python -m uvicorn*" >nul 2>&1

REM 停止前端服务
taskkill /f /im node.exe /fi "windowtitle eq *vite*" >nul 2>&1

echo %GREEN%✓ 所有服务已停止%NC%
pause
