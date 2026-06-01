@echo off
chcp 65001 >nul
cd /d D:\MSTS\app

echo ========================================
echo   Alpha Factory 自动化云端同步工具
echo ========================================

echo [1/3] 正在暂存本地变更...
git add .

echo [2/3] 正在生成自动化时间戳...
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set dt=%%I
set ts=%dt:~0,4%%dt:~4,2%%dt:~6,2%_%dt:~8,2%%dt:~10,2%

git diff --cached --quiet
if %errorlevel% equ 0 (
    echo [i] 无新变更，跳过 commit...
) else (
    git commit -m "production update: %ts%"
)

echo [3/3] 正在推送到 GitHub 远程仓库...
set retry=0
:PUSH_RETRY
ver >nul
git push origin main
if %errorlevel% equ 0 goto PUSH_OK
set /a retry+=1
if %retry% lss 3 (
    echo [!] Push 失败，第 %retry% 次重试，等待 5 秒...
    timeout /t 5 /nobreak >nul
    goto PUSH_RETRY
)
echo ========================================
echo   Push 失败^^!
echo   请检查以下几项：
echo   1. 网络是否能访问 GitHub
echo   2. 是否需要设置代理
echo   3. GitHub 令牌是否过期
echo ========================================
echo.
echo [提示] 设置代理（替换为你的实际端口）：
echo   git config --global http.proxy http://127.0.0.1:7890
echo   git config --global https.proxy http://127.0.0.1:7890
echo.
echo [提示] 取消代理：
echo   git config --global --unset http.proxy
echo   git config --global --unset https.proxy
goto END

:PUSH_OK
echo ========================================
echo   Push 成功^^!
echo   云端将在 1 分钟内自动刷新。
echo ========================================

:END
pause