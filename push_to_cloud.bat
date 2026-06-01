@echo off
chcp 65001 >nul
cd /d D:\MSTS\app
echo ========================================
echo   🚀 Alpha Factory 自动化云端同步工具
echo ========================================
echo ⏳ [1/3] 正在暂存本地变更...
git add .
echo ⏳ [2/3] 正在生成自动化时间戳...
set mydate=%date:~0,4%%date:~5,2%%date:~8,2%
set mytime=%time:~0,2%%time:~3,2%
set mytime=%mytime: =0%
set ts=%mydate%_%mytime%
git diff --cached --quiet
if %errorlevel% equ 0 (
    echo ℹ️  无新变更，跳过 commit...
) else (
    git commit -m "production update: %ts%"
)
echo ⏳ [3/3] 正在全力推送到 GitHub 远程仓库...
ver >nul
git push origin main
if %errorlevel% equ 0 (
    echo ========================================
    echo   🟩 ✨ Push 成功！
    echo   📡 云端将在 1 分钟内侦测到变更并自动刷新。
    echo ========================================
) else (
    echo ========================================
    echo   🟥 ❌ Push 失败！
    echo   请检查网络代理、GitHub 令牌或账户权限。
    echo ========================================
)
pause