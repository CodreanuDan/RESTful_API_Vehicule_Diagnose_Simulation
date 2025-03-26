REM:: Imported from: https://github.com/CodreanuDan/Linked_API_RequestsApp/blob/master/api/init.bat

@echo off
echo ==============================
echo INFO: Running init.bat...
echo ==============================

REM:: Clean pip cache
echo INFO: Cleaning pip cache...
pip cache purge

REM:: Get current dir path
set current_dir=%~dp0

REM:: Display dir path
echo Directory path: %current_dir%

REM:: Go to the directory where env_data.env is located
cd /d "%current_dir%"

REM:: Check if env_data.env file exists
if not exist "env_data.env" (
    echo ERROR: No env_data.env file in the specified directory!
    pause
    exit /b
)

REM:: Load environment variables
for /f "tokens=*" %%i in (env_data.env) do (
    set %%i
    echo Loaded: %%i
)

echo INFO: Environment variables loaded.

echo ==============================
echo INFO: Finished...
@REM pause
@REM exit /b
exit /b 0