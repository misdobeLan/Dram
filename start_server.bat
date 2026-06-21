@echo off
chcp 65001 >nul
cd /d "%~dp0"

set VENV=.venv\Scripts
set PYTHON=%VENV%\python.exe
set UVICORN=%VENV%\uvicorn.exe

echo [1/3] 检查 OpenD...
%PYTHON% backend\opend_helper.py
if errorlevel 1 (
    echo.
    echo [提示] 未检测到可用的 OpenD。将尝试启动项目内置网关（离线模式）。
    echo        如需获取真实行情，请先登录 OpenD。
)

echo.
echo [2/3] 启动行情代理后端...
start "DRAM Quote Backend" %UVICORN% main:app --host 0.0.0.0 --port 8080 --app-dir backend

echo 等待后端启动...
timeout /t 3 /nobreak >nul

echo.
echo [3/3] 打开浏览器...
start http://127.0.0.1:8080

echo.
echo 后端已启动：http://127.0.0.1:8080
echo 按任意键关闭本窗口（后端仍会在后台运行）...
pause >nul
