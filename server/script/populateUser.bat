echo off

if "%~1"=="" (
    echo Number of users to create is required. Defaulting to 10.
    set "numUsers=10"
) else (
    set "username=%~1"
)

echo Creating %numUsers% users...

for /L %%i in (1, 1, 10) do (
    call "%~dp0userCreate"
)

echo Users created successfully.

