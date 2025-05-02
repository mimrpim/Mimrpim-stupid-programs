@echo off 
color 0a
tasklist | findstr /i "taskmgrblock.exe" > nul
if %errorlevel% == 1 (
    start taskmgrblock.exe
)
tasklist | findstr /i "msedgeblock.exe" > nul
if %errorlevel% == 1 (
    start msedgeblock.exe
)
%0
