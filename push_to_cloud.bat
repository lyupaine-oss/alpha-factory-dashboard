@echo off
chcp 65001
cd /d D:\MSTS\app
echo === 正在提交最新代码到 GitHub ===
git add .
git commit -m "update: %date% %time% auto push"
git push origin main
echo === Push 完成！云端将在 1 分钟内自动刷新 ===
pause