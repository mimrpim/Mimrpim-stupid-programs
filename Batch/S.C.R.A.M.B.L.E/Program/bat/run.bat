@echo off
color 0a
title S.C.R.A.M.B.L.E DO NOT CLOSE
if exist "C:\Users\%username%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\scramble_run.bat" (
echo ok
cd control_running
start control1.exe
) else (
color c
echo error install
echo now i start instalation program
pause
install.bat
)
