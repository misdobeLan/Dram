@echo off
chcp 65001 >nul
cd /d "%~dp0"

set PYTHON=.venv\Scripts\python.exe

echo 运行 DRAM Tracker 数据一致性测试...
echo 注意：测试需要 OpenD 运行并登录，否则与真实行情相关的用例会被跳过。
echo.

%PYTHON% -m pytest tests -v

pause
