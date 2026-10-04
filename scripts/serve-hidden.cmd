@echo off
REM ============================================================
REM  本地博客服务器（静默后台启动）
REM  由启动器以 CREATE_NO_WINDOW 方式调用，自身不再产生新窗口
REM ============================================================
setlocal

set "DIST=%~1"
set "PORT=%~2"
if "%DIST%"=="" set "DIST=C:\Code\VibeCoding\blog\dist"
if "%PORT%"=="" set "PORT=4321"

cd /d "%DIST%"
"C:\Tools\miniconda3\pythonw.exe" -m http.server %PORT% --bind 127.0.0.1
