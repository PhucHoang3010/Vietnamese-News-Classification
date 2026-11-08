@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Dang ki hoc phan
where node >nul 2>nul
if errorlevel 1 (
  echo Chua cai Node.js. Hay tai ban LTS tai https://nodejs.org roi bam dup lai file nay.
  pause
  exit /b 1
)
node src\khoi-dong.js
pause
