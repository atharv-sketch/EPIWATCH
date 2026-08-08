@echo off
setlocal enabledelayedexpansion

cd /d "C:\Users\silverfang\epiwatch"

echo.
echo === Creating directories ===
mkdir backend 2>nul
mkdir frontend 2>nul
mkdir data 2>nul
mkdir notebooks 2>nul
mkdir .github\workflows 2>nul
echo. Directories created

echo.
echo === Creating files ===
type nul > backend\__init__.py
type nul > backend\data_pipeline.py
type nul > backend\model.py
type nul > backend\api.py
type nul > backend\requirements.txt
type nul > data\.gitkeep
type nul > notebooks\.gitkeep
echo. Files created

echo.
echo === Git Operations ===

echo.
echo [1] git --no-pager status
git --no-pager status

echo.
echo [2] git add .
git add .
echo. Files staged

echo.
echo [3] git commit with scaffold message
git --no-pager commit -m "feat: initial project scaffold with CI pipeline" --author "Copilot <223556219+Copilot@users.noreply.github.com>"

echo.
echo [4] Creating and pushing data-pipeline branch
git --no-pager branch data-pipeline
git --no-pager push origin data-pipeline

echo.
echo [5] Creating and pushing modeling branch
git --no-pager branch modeling
git --no-pager push origin modeling

echo.
echo [6] Creating and pushing dashboard branch
git --no-pager branch dashboard
git --no-pager push origin dashboard

echo.
echo [7] Creating and pushing risk-map branch
git --no-pager branch risk-map
git --no-pager push origin risk-map

echo.
echo [8] Checkout main
git --no-pager checkout main

echo.
echo [9] Checkout data-pipeline
git --no-pager checkout data-pipeline

echo.
echo [10] Final status on data-pipeline
git --no-pager status

endlocal
