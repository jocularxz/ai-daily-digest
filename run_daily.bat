@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo AI每日速递 - 定时任务
echo 时间: %date% %time%
echo ========================================
python main.py
echo.
echo 任务执行完毕
