@echo off
chcp 65001 >nul
cd /d "%~dp0\tools\futu-opend-rs-1.4.114"

if "%FUTU_ACCOUNT%"=="" (
    echo [错误] 未设置登录账号。
    echo.
    echo 请在当前终端设置环境变量后重新运行：
    echo   set FUTU_ACCOUNT=你的富途账号
    echo   set FUTU_PWD=你的登录密码
    echo.
    echo 注意：密码不会保存到任何文件中，仅在当前进程使用。
    pause
    exit /b 1
)

echo 正在启动 FUTU-OpenD-rs 网关（127.0.0.1:11111）...
futu-opend.exe -i 127.0.0.1 -p 11111 --login-account %FUTU_ACCOUNT% --login-pwd "%FUTU_PWD%"

pause
