@echo off 
color 0a
tasklist | findstr /i "taskmgrblock.exe" > nul
if %errorlevel% == 1 (
    start taskmgrblock.exe
)
%0