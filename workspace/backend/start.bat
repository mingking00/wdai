@echo off
chcp 65001 > nul
echo ==================================
echo   Vibero Reader - Startup Script  
echo ==================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

echo Working directory: %cd%
echo.

REM 检查Python
set PYTHON_CMD=
for %%P in (python python3 py) do (
    %%P --version > nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=%%P
        echo ✅ Found Python:
        %%P --version
        goto :found_python
    )
)

echo.
echo ❌ Python not found!
echo Please install Python 3.8+ from https://python.org
echo Make sure to check "Add Python to PATH"
echo.
pause
exit /b 1

:found_python
echo.

REM 检查 app.py
if not exist "app.py" (
    echo ❌ app.py not found in: %cd%
    echo Please run this script from the backend folder.
    pause
    exit /b 1
)

echo ✅ Found app.py
echo ✅ Found templates\index.html

REM 安装依赖
echo.
echo 📦 Checking dependencies...
%PYTHON_CMD% -m pip install -q flask flask-cors requests

if errorlevel 1 (
    echo ❌ Failed to install dependencies
    echo Please run: %PYTHON_CMD% -m pip install flask flask-cors requests
    pause
    exit /b 1
)

echo ✅ Dependencies ready
echo.

REM 启动服务器
echo ==================================
echo   🚀 Starting server...
echo   http://localhost:5000
echo ==================================
echo.
echo Press Ctrl+C to stop
echo.

%PYTHON_CMD% app.py

pause
