@echo off
chcp 65001 >nul
cd /d D:\MSTS\app

echo ========================================
echo   Alpha Factory 自动化云端同步工具
echo ========================================

echo [1/3] 正在暂存本地变更...
git add .

echo [2/3] 正在生成自动化时间戳...
:: 用 wmic 直接读取系统时间，彻底绕开 %date% 的格式陷阱
:: 输出格式固定为 YYYYMMDD_HHMM，与地区/语言设置无关
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set dt=%%I
set ts=%dt:~0,4%%dt:~4,2%%dt:~6,2%_%dt:~8,2%%dt:~10,2%

git diff --cached --quiet
if %errorlevel% equ 0 (
    echo [i] 无新变更，跳过 commit...
) else (
    git commit -m "production update: %ts%"
)

echo [3/3] 正在推送到 GitHub 远程仓库...
ver >nul
git push origin main
if %errorlevel% equ 0 (
    echo ========================================
    echo   Push 成功^^!
    echo   云端将在 1 分钟内自动刷新。
    echo ========================================
) else (
    echo ========================================
    echo   Push 失败^^!
    echo   请检查以下几项：
    echo   1. 网络是否能访问 GitHub
    echo   2. 是否需要设置代理（见下方诊断）
    echo   3. GitHub 令牌是否过期
    echo ========================================
    echo.
    echo [诊断] 正在测试网络连通性...
    curl -v --max-time 10 https://github.com 2>&1 | findstr "Connected\|Failed\|SSL\|proxy"
    echo.
    echo [提示] 如使用代理，请运行以下命令后重试：
    echo   git config --global http.proxy http://127.0.0.1:你的代理端口
    echo   git config --global https.proxy http://127.0.0.1:你的代理端口
    echo.
    echo [提示] 取消代理设置请运行：
    echo   git config --global --unset http.proxy
    echo   git config --global --unset https.proxy
)
pause