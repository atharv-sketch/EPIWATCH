@echo off
setlocal enabledelayedexpansion

cd /d "C:\Users\silverfang\epiwatch"

REM Create directories if they don't exist
if not exist backend mkdir backend
if not exist frontend mkdir frontend
if not exist data mkdir data
if not exist notebooks mkdir notebooks
if not exist .github\workflows mkdir .github\workflows

REM Create empty files if they don't exist
type nul > backend\__init__.py 2>nul
type nul > backend\data_pipeline.py 2>nul
type nul > backend\model.py 2>nul
type nul > backend\api.py 2>nul
type nul > backend\requirements.txt 2>nul
type nul > data\.gitkeep 2>nul
type nul > notebooks\.gitkeep 2>nul

REM Create output file
set OUTPUT=git_commands_output.txt
if exist %OUTPUT% del %OUTPUT%

REM Command a: git status
echo [COMMAND_a_START] >> %OUTPUT%
git --no-pager status >> %OUTPUT% 2>&1
echo [COMMAND_a_END] >> %OUTPUT%
echo. >> %OUTPUT%

REM Command b: git add
echo [COMMAND_b_START] >> %OUTPUT%
git add . >> %OUTPUT% 2>&1
echo [COMMAND_b_END] >> %OUTPUT%
echo. >> %OUTPUT%

REM Command c: git commit
echo [COMMAND_c_START] >> %OUTPUT%
git --no-pager commit -m "feat: initial project scaffold with CI pipeline" --author "Copilot <223556219+Copilot@users.noreply.github.com>" >> %OUTPUT% 2>&1
echo [COMMAND_c_END] >> %OUTPUT%
echo. >> %OUTPUT%

REM Command d: git branch data-pipeline
echo [COMMAND_d_START] >> %OUTPUT%
git --no-pager branch data-pipeline >> %OUTPUT% 2>&1
echo [COMMAND_d_END] >> %OUTPUT%
echo. >> %OUTPUT%

REM Command e: git branch modeling
echo [COMMAND_e_START] >> %OUTPUT%
git --no-pager branch modeling >> %OUTPUT% 2>&1
echo [COMMAND_e_END] >> %OUTPUT%
echo. >> %OUTPUT%

REM Command f: git branch dashboard
echo [COMMAND_f_START] >> %OUTPUT%
git --no-pager branch dashboard >> %OUTPUT% 2>&1
echo [COMMAND_f_END] >> %OUTPUT%
echo. >> %OUTPUT%

REM Command g: git branch risk-map
echo [COMMAND_g_START] >> %OUTPUT%
git --no-pager branch risk-map >> %OUTPUT% 2>&1
echo [COMMAND_g_END] >> %OUTPUT%
echo. >> %OUTPUT%

REM Command h: git push origin data-pipeline
echo [COMMAND_h_START] >> %OUTPUT%
git --no-pager push origin data-pipeline >> %OUTPUT% 2>&1
echo [COMMAND_h_END] >> %OUTPUT%
echo. >> %OUTPUT%

REM Command i: git push origin modeling
echo [COMMAND_i_START] >> %OUTPUT%
git --no-pager push origin modeling >> %OUTPUT% 2>&1
echo [COMMAND_i_END] >> %OUTPUT%
echo. >> %OUTPUT%

REM Command j: git push origin dashboard
echo [COMMAND_j_START] >> %OUTPUT%
git --no-pager push origin dashboard >> %OUTPUT% 2>&1
echo [COMMAND_j_END] >> %OUTPUT%
echo. >> %OUTPUT%

REM Command k: git push origin risk-map
echo [COMMAND_k_START] >> %OUTPUT%
git --no-pager push origin risk-map >> %OUTPUT% 2>&1
echo [COMMAND_k_END] >> %OUTPUT%
echo. >> %OUTPUT%

REM Command l: git checkout main
echo [COMMAND_l_START] >> %OUTPUT%
git --no-pager checkout main >> %OUTPUT% 2>&1
echo [COMMAND_l_END] >> %OUTPUT%
echo. >> %OUTPUT%

REM Command m: git checkout data-pipeline
echo [COMMAND_m_START] >> %OUTPUT%
git --no-pager checkout data-pipeline >> %OUTPUT% 2>&1
echo [COMMAND_m_END] >> %OUTPUT%
echo. >> %OUTPUT%

REM Command n: git status --short
echo [COMMAND_n_START] >> %OUTPUT%
git --no-pager status --short >> %OUTPUT% 2>&1
echo [COMMAND_n_END] >> %OUTPUT%
echo. >> %OUTPUT%

REM Command o: git rev-parse --abbrev-ref HEAD
echo [COMMAND_o_START] >> %OUTPUT%
git --no-pager rev-parse --abbrev-ref HEAD >> %OUTPUT% 2>&1
echo [COMMAND_o_END] >> %OUTPUT%
echo. >> %OUTPUT%

REM Display the output
type %OUTPUT%

endlocal
