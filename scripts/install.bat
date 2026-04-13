@echo off
setlocal enabledelayedexpansion

echo === Personal Agent Setup ===
echo.

REM 检查 Python
echo Checking Python 3.11+...
where python >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed. Please install Python 3.11 or higher.
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python %PYTHON_VERSION% found.

REM 检查 Node.js
echo Checking Node.js 20+...
where node >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed. Please install Node.js 20 or higher.
    exit /b 1
)

for /f "tokens=1" %%i in ('node -v') do set NODE_VERSION=%%i
echo Node.js %NODE_VERSION% found.

REM 获取项目根目录
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM 安装后端
echo.
echo === Setting up Backend ===
cd /d "%PROJECT_ROOT%\backend"
if not exist .venv (
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -e .

REM 安装前端
echo.
echo === Setting up Frontend ===
cd /d "%PROJECT_ROOT%\frontend"
call npm install
call npm run build

echo.
echo === Setup Complete ===
echo.
echo To start the application:
echo   scripts\start.bat
echo.
echo Or run manually:
echo   Backend: cd backend ^&^& .venv\Scripts\activate ^&^& uvicorn app.main:app --reload
echo   Frontend: cd frontend ^&^& npm run dev
echo.
echo Then visit: http://localhost:5173

cd /d "%PROJECT_ROOT%"
