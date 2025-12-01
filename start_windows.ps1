# StreamDiffusion Windows环境前后端启动脚本 (PowerShell版本)

# 获取脚本所在目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# 颜色输出函数
function Write-ColorOutput {
    param(
        [string]$Message,
        [ConsoleColor]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# 输出标题
Write-ColorOutput "========================================" "Green"
Write-ColorOutput "StreamDiffusion Windows环境启动脚本" "Green"
Write-ColorOutput "========================================" "Green"

# 检查Python是否安装
try {
    $PythonVersion = python --version 2>&1
    Write-ColorOutput "Python版本: $PythonVersion" "Green"
} catch {
    Write-ColorOutput "错误: 未检测到Python，请先安装Python 3.10或更高版本" "Red"
    Read-Host "按Enter键退出"
    exit 1
}

# 检查虚拟环境
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-ColorOutput "激活虚拟环境..." "Yellow"
    & .\venv\Scripts\Activate.ps1
} else {
    Write-ColorOutput "虚拟环境不存在，正在创建..." "Yellow"
    try {
        python -m venv venv
        & .\venv\Scripts\Activate.ps1
        Write-ColorOutput "✓ 虚拟环境创建成功" "Green"
    } catch {
        Write-ColorOutput "错误: 创建虚拟环境失败" "Red"
        Read-Host "按Enter键退出"
        exit 1
    }
}

# 升级pip
Write-ColorOutput "升级pip..." "Yellow"
try {
    python -m pip install --upgrade pip
} catch {
    Write-ColorOutput "警告: pip升级失败，继续使用当前版本" "Yellow"
}

# 检查配置文件
if (-not (Test-Path "app\config.yaml")) {
    Write-ColorOutput "错误: 配置文件不存在: app\config.yaml" "Red"
    Read-Host "按Enter键退出"
    exit 1
}
Write-ColorOutput "配置文件: app\config.yaml" "Green"

# 检查必要的目录
if (-not (Test-Path "engines")) { New-Item -ItemType Directory -Path "engines" | Out-Null }
if (-not (Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" | Out-Null }

# 设置环境变量
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONDONTWRITEBYTECODE = "1"

# 安装后端依赖
Write-ColorOutput "安装后端依赖..." "Yellow"
try {
    pip install -r requirements.txt
    Write-ColorOutput "✓ 后端依赖安装完成" "Green"
} catch {
    Write-ColorOutput "错误: 安装后端依赖失败" "Red"
    Read-Host "按Enter键退出"
    exit 1
}

# 检查Node.js是否安装
try {
    $NodeVersion = node --version 2>&1
    Write-ColorOutput "Node.js版本: $NodeVersion" "Green"
} catch {
    Write-ColorOutput "错误: 未检测到Node.js，请先安装Node.js" "Red"
    Read-Host "按Enter键退出"
    exit 1
}

# 检查前端目录
if (-not (Test-Path "frontend")) {
    Write-ColorOutput "警告: 前端目录不存在，仅启动后端服务" "Yellow"
    $FrontendAvailable = $false
} else {
    $FrontendAvailable = $true
    
    # 检查前端依赖
    if (-not (Test-Path "frontend\node_modules")) {
        Write-ColorOutput "前端依赖未安装，正在安装..." "Yellow"
        try {
            Set-Location frontend
            npm install
            Set-Location ..
            Write-ColorOutput "✓ 前端依赖安装完成" "Green"
        } catch {
            Write-ColorOutput "错误: 安装前端依赖失败" "Red"
            Read-Host "按Enter键退出"
            exit 1
        }
    }
}

# 启动后端服务
Write-ColorOutput "启动后端服务..." "Green"
$BackendProcess = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload" -PassThru -RedirectStandardOutput "logs\backend.log" -RedirectStandardError "logs\backend.log"

# 等待后端服务启动
Write-ColorOutput "等待后端服务启动..." "Yellow"
Start-Sleep -Seconds 5

# 检查后端是否启动成功
try {
    $Response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health" -TimeoutSec 2 -ErrorAction Stop
    Write-ColorOutput "✓ 后端服务已启动" "Green"
} catch {
    Write-ColorOutput "警告: 后端服务可能未完全启动，请检查日志" "Yellow"
    Write-ColorOutput "后端日志: logs\backend.log" "Blue"
}

# 如果前端目录存在，启动前端服务
if ($FrontendAvailable) {
    # 启动前端服务
    Write-ColorOutput "启动前端服务..." "Green"
    Set-Location frontend
    $FrontendProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -PassThru -RedirectStandardOutput "..\logs\frontend.log" -RedirectStandardError "..\logs\frontend.log"
    Set-Location ..
    
    # 等待前端服务启动
    Start-Sleep -Seconds 3
    
    Write-ColorOutput "✓ 前端服务已启动" "Green"
    Write-ColorOutput "前端日志: logs\frontend.log" "Blue"
}

Write-Host ""
Write-ColorOutput "========================================" "Green"
Write-ColorOutput "所有服务已启动" "Green"
Write-ColorOutput "========================================" "Green"
Write-ColorOutput "后端服务: http://0.0.0.0:8000" "Blue"
Write-ColorOutput "前端服务: http://127.0.0.1:6006" "Blue"
Write-ColorOutput "按任意键停止所有服务..." "Yellow"
Write-Host ""

# 等待用户按键
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# 停止服务
Write-ColorOutput "正在停止服务..." "Yellow"

# 停止后端服务
if ($BackendProcess -and !$BackendProcess.HasExited) {
    try {
        $BackendProcess.Kill()
        Write-ColorOutput "✓ 后端服务已停止" "Green"
    } catch {
        Write-ColorOutput "警告: 无法正常停止后端服务" "Yellow"
    }
}

# 停止前端服务
if ($FrontendAvailable -and $FrontendProcess -and !$FrontendProcess.HasExited) {
    try {
        $FrontendProcess.Kill()
        Write-ColorOutput "✓ 前端服务已停止" "Green"
    } catch {
        Write-ColorOutput "警告: 无法正常停止前端服务" "Yellow"
    }
}

# 清理可能残留的进程
try {
    Get-Process | Where-Object {$_.ProcessName -eq "python" -and $_.CommandLine -like "*uvicorn*"} | Stop-Process -Force
    Get-Process | Where-Object {$_.ProcessName -eq "node" -and $_.CommandLine -like "*vite*"} | Stop-Process -Force
} catch {
    Write-ColorOutput "警告: 清理残留进程时出错" "Yellow"
}

Write-ColorOutput "✓ 所有服务已停止" "Green"
Read-Host "按Enter键退出"
