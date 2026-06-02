@echo off
chcp 65001 >nul

:: 💡 绝对锁定：确保脚本不论在哪里被调用，都强行物理切换到本地仓库根目录
cd /d D:\MSTS\app

echo ========================================
echo     Alpha Factory 自动化云端同步工具
echo ========================================

echo [0/3] 🔄 正在自动物理搬运今日最新分析状态小文件...

:: 1. 搬运特征工厂的 CSV 小文件
xcopy "D:\MSTS\outputs\final_tables\*.csv" "D:\MSTS\app\data\" /Y /Q >nul 2>&1

:: 2. 精准指名道姓搬运 final_tables 的特定 json，绝不盲目全拷（防止覆盖）
if exist "D:\MSTS\outputs\final_tables\valid_features.json" (
    xcopy "D:\MSTS\outputs\final_tables\valid_features.json" "D:\MSTS\app\data\" /Y /Q >nul 2>&1
)

:: 3. 🎯 精准搬运今日刚出炉的信号核心报告（指名道姓，物理防踩踏）
xcopy "D:\MSTS\outputs\signals\pnl_report_v3.json" "D:\MSTS\app\data\" /Y /Q
xcopy "D:\MSTS\outputs\signals\short_governance_report.json" "D:\MSTS\app\data\" /Y /Q

:: 4. 🚀 选填：如果网页端确实需要读取这个 parquet 信号文件，解除下面这行的注释
:: xcopy "D:\MSTS\outputs\signals\alpha_selection.parquet" "D:\MSTS\app\data\" /Y /Q

echo [1/3] 正在暂存本地变更...
:: 强制再次通知 Git 忽略那些被套上隐身衣的本地密钥文件
git update-index --assume-unchanged .env >nul 2>&1
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
:: 自动根据网络直连测试，保持最纯净的无代理推流状态
git push origin main
if %errorlevel% equ 0 goto PUSH_OK
set /a retry+=1
if %retry% lss 3 (
    echo [!] Push 失败，第 %retry% 次重试，等待 5 秒...
    timeout /t 5 /nobreak >nul
    goto PUSH_RETRY
)
echo ========================================
echo    Push 失败!
echo    请检查以下几项：
echo    1. 网络是否能访问 GitHub
echo    2. 是否需要设置代理
echo    3. GitHub 令牌是否过期
echo ========================================
echo.
echo [提示] 设置代理（替换为你的实际端口）：
echo    git config --global http.proxy http://127.0.0.1:7890
echo    git config --global https.proxy http://127.0.0.1:7890
echo.
echo [提示] 取消代理：
echo    git config --global --unset http.proxy
echo    git config --global --unset https.proxy
goto END

:PUSH_OK
echo ========================================
echo    🎉 Push 成功!
echo    今日小文件已全部自动归档，云端即将刷新。
echo ========================================

:END
pause