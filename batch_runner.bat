@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM Navigate to repository
cd /d "C:\Users\silverfang\epiwatch"

REM Initialize output variable to capture all results
set "OUTPUT_FILE=%TEMP%\git_commands_output.txt"
del /f /q "%OUTPUT_FILE%" 2>nul

REM Function to run command and log output
goto START

:RUN_CMD
setlocal
set CMD=%~1
set NUM=%~2
set OUTPUT_FILE=%~3

echo. >> "%OUTPUT_FILE%"
echo ======== COMMAND %NUM%/15 ======== >> "%OUTPUT_FILE%"
echo Command: %CMD% >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

%CMD% >> "%OUTPUT_FILE%" 2>&1
set "EXIT_CODE=!ERRORLEVEL!"

echo. >> "%OUTPUT_FILE%"
echo Exit Code: !EXIT_CODE! >> "%OUTPUT_FILE%"

endlocal
exit /b

:START

REM Run all 15 commands
call :RUN_CMD "git --no-pager status" 1 "%OUTPUT_FILE%"
call :RUN_CMD "git add ." 2 "%OUTPUT_FILE%"
call :RUN_CMD "git --no-pager commit -m "feat: initial project scaffold with CI pipeline" --author "Copilot <223556219+Copilot@users.noreply.github.com>"" 3 "%OUTPUT_FILE%"
call :RUN_CMD "git --no-pager branch data-pipeline" 4 "%OUTPUT_FILE%"
call :RUN_CMD "git --no-pager branch modeling" 5 "%OUTPUT_FILE%"
call :RUN_CMD "git --no-pager branch dashboard" 6 "%OUTPUT_FILE%"
call :RUN_CMD "git --no-pager branch risk-map" 7 "%OUTPUT_FILE%"
call :RUN_CMD "git --no-pager push origin data-pipeline" 8 "%OUTPUT_FILE%"
call :RUN_CMD "git --no-pager push origin modeling" 9 "%OUTPUT_FILE%"
call :RUN_CMD "git --no-pager push origin dashboard" 10 "%OUTPUT_FILE%"
call :RUN_CMD "git --no-pager push origin risk-map" 11 "%OUTPUT_FILE%"
call :RUN_CMD "git --no-pager checkout main" 12 "%OUTPUT_FILE%"
call :RUN_CMD "git --no-pager checkout data-pipeline" 13 "%OUTPUT_FILE%"
call :RUN_CMD "git --no-pager status --short" 14 "%OUTPUT_FILE%"
call :RUN_CMD "git --no-pager rev-parse --abbrev-ref HEAD" 15 "%OUTPUT_FILE%"

echo. >> "%OUTPUT_FILE%"
echo ======== FINAL SUMMARY ======== >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo Current Branch: >> "%OUTPUT_FILE%"
git --no-pager rev-parse --abbrev-ref HEAD >> "%OUTPUT_FILE%" 2>&1
echo. >> "%OUTPUT_FILE%"
echo Status Output: >> "%OUTPUT_FILE%"
git --no-pager status --short >> "%OUTPUT_FILE%" 2>&1

type "%OUTPUT_FILE%"
