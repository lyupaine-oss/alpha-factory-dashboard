@echo off
chcp 65001 >nul

:: 💡 绝对锁定：确保脚本不论在哪里被调用，都强行物理切换到本地 App 仓库根目录
cd /d D:\MSTS\app

echo ========================================
echo      Alpha Factory 自动化云端同步工具
echo ========================================

echo [0/4] 🔄 正在自动物理搬运今日最新分析状态小文件...

:: 1. 搬运特征工厂的 CSV 小文件到 app/data 下
xcopy "D:\MSTS\outputs\final_tables\*.csv" "D:\MSTS\app\data\" /Y /Q >nul 2>&1

:: 2. 精准搬运 final_tables 的特定 json
if exist "D:\MSTS\outputs\final_tables\valid_features.json" (
    xcopy "D:\MSTS\outputs\final_tables\valid_features.json" "D:\MSTS\app\data\" /Y /Q >nul 2>&1
)

:: 3. 🎯 精准搬运今日刚出炉的信号核心报告
xcopy "D:\MSTS\outputs\signals\pnl_report_v3.json" "D:\MSTS\app\data\" /Y /Q
xcopy "D:\MSTS\outputs\signals\short_governance_report.json" "D:\MSTS\app\data\" /Y /Q

:: 4. 🚨【新增核心搬运】把 pnl_tracker.py 生成在 backtest_outputs 里的最新成果，同步准备好
if exist "D:\MSTS\app\backtest_outputs\pnl_report.txt" (
    echo [i] 发现最新复盘文案，正在就地整备...
)

echo.
echo [1/4] 🚀 正在调度 hf_daily_push.py 生成今日量化日报推文...
:: 💡 此时工作目录在 D:\MSTS\app，hf_daily_push.py 会直接读取同目录或 backtest_outputs 下的文件
python hf_daily_push.py
if %errorlevel% neq 0 (
    echo [⚠️] hf_daily_push.py 运行似乎遇到了点问题，请检查上方报错！
    echo [i] 程序将继续尝试同步现有数据...
) else (
    echo [🎉] 今日推文及传播数据生成完毕。
)
echo.

echo [2/4] 正在暂存本地变更...
:: 强制再次通知 Git 忽略那些被套上隐身衣的本地密钥文件
git update-index --assume-unchanged .env >nul 2>&1
:: 将 app 目录下的所有变化（包含新生成的 data 和最新的代码修改）一网打尽
git add .

echo [3/4] 正在生成自动化时间戳...
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set dt=%%I
set ts=%dt:~0,4%%dt:~4,2%%dt:~6,2%_%dt:~8,2%%dt:~10,2%

git diff --cached --quiet
if %errorlevel% equ 0 (
    echo [i] 无新变更，跳过 commit...
) else (
    git commit -m "production update: %ts%"
)

echo [4/4] 正在推送到 GitHub 远程仓库...
set retry=0
:PUSH_RETRY
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
echo    请检查网络或代理设置。
echo ========================================
goto END

:PUSH_OK
echo ========================================
echo    🎉 Push 成功!
echo    今日小文件及传播内容已全部自动归档，云端即将刷新。
echo ========================================

:END
pause