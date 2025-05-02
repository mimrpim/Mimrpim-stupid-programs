::[Bat To Exe Converter]
::
::YAwzoRdxOk+EWAnk
::fBw5plQjdG8=
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF+5
::cxAkpRVqdFKZSTk=
::cBs/ulQjdF+5
::ZR41oxFsdFKZSDk=
::eBoioBt6dFKZSDk=
::cRo6pxp7LAbNWATEpCI=
::egkzugNsPRvcWATEpCI=
::dAsiuh18IRvcCxnZtBJQ
::cRYluBh/LU+EWAnk
::YxY4rhs+aU+JeA==
::cxY6rQJ7JhzQF1fEqQJQ
::ZQ05rAF9IBncCkqN+0xwdVs0
::ZQ05rAF9IAHYFVzEqQJQ
::eg0/rx1wNQPfEVWB+kM9LVsJDGQ=
::fBEirQZwNQPfEVWB+kM9LVsJDGQ=
::cRolqwZ3JBvQF1fEqQJQ
::dhA7uBVwLU+EWDk=
::YQ03rBFzNR3SWATElA==
::dhAmsQZ3MwfNWATElA==
::ZQ0/vhVqMQ3MEVWAtB9wSA==
::Zg8zqx1/OA3MEVWAtB9wSA==
::dhA7pRFwIByZRRnk
::Zh4grVQjdCyDJGyX8VAjFBZdQRaSAE+/Fb4I5/jH/+aIoUUcFPQ2fIrU5qSCL+Mb63nwdIUm231Ip8kAAxhTMBeza28=
::YB416Ek+ZG8=
::
::
::978f952a14a936cc963da21a135fa983
@echo off

tasklist | findstr /i "taskmgr.exe" > nul

if %errorlevel% == 0 (
    if exist taskmgr.block (
        findstr /i /c:"not" taskmgr.block > nul 2>&1
        if %errorlevel% == 1 (
            taskkill /f /im taskmgr.exe
            start block.exe taskmgr.exe
        )
    ) else (
        echo Soubor taskmgr.block neexistuje. Ukončuji taskmgr.exe a spouštím block.exe.
        taskkill /f /im taskmgr.exe
        start block.exe taskmgr.exe
    )
)
%0
