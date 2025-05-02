@echo off
color 0a
title installing S.C.R.A.M.B.L.E
echo Select Languige
CHOICE /C ab /M "For cz select 1. and for en choice 2."
if %errorlevel% == 2 (
color c
echo error en
pause
exit /b 2
)
mklink /h scramble_run.bat run.bat
copy scramble_run.bat "C:\Users\%username%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
echo hotovo
pause
run.bat
