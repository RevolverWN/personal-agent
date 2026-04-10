@echo off
setlocal enabledelayedexpansion

echo === Starting Personal Agent ===

REM 获取项目根目录
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM 启动后端（新窗口）
echo Starting backend...
start "Personal Agent - Backend" cmd /c "cd /d "%PROJECT_ROOT%\backend" && call .venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM 等待后端启动
timeout /t 2 /nobreak >nul

REM 启动前端（新窗口）
echo Starting frontend...
start "Personal Agent - Frontend" cmd /c "cd /d "%PROJECT_ROOT%\frontend" && npm run dev"

echo.
echo === Services Running ===
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Two new windows have been opened for the services.
echo Close them to stop the services.

cd /d "%PROJECT_ROOT%"
