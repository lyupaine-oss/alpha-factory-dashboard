@echo off
chcp 65001 >nul
cd /d D:\MSTS\app

echo ========================================
echo    Alpha Factory 自动化云端同步工具
echo ========================================

echo [0/3] 🔄 正在自动物理搬运今日最新分析状态小文件...
:: 自动将今天盘后新生成的分析结果小文件（如 all_interaction_icir.csv）强行覆盖搬运至 app\data 目录
xcopy "D:\MSTS\outputs\final_tables\*.csv" "D:\MSTS\app\data\" /Y /Q >nul 2>&1
xcopy "D:\MSTS\outputs\final_tables\*.json" "D:\MSTS\app\data\" /Y /Q >nul 2>&1

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
:: 如果之前设置过 socks5 强推，这里会自动沿用，保持历史干净即可
git push origin main
if %errorlevel% equ 0 goto PUSH_OK
set /a retry+=1
if %retry% lss 3 (
    echo [!] Push 失败，第 %retry% 次重试，等待 5 秒...
    timeout /t 5 /nobreak >nul
    goto PUSH_RETRY
)
echo ========================================
echo    Push 失败^^!
echo    请检查以下几项：
echo    1. 网络是否能访问 GitHub
echo    2. 是否需要设置代理
echo    3. GitHub 令牌是否过期
echo ========================================
echo.
echo [提示] 设置代理（替换为你的实际端口）：
echo    git config --global http.proxy socks5://127.0.0.1:7890
echo    git config --global https.proxy socks5://127.0.0.1:7890
echo.
echo [提示] 取消代理：
echo    git config --global --unset http.proxy
echo    git config --global --unset https.proxy
goto END

:PUSH_OK
echo ========================================
echo    Push 成功^^!
echo    今日小文件已全部自动归档，云端即将刷新。
echo ========================================

:END
pause