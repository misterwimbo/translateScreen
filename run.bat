@echo off
cd /d "%~dp0"
set PYC=py
where py >nul 2>&1
if not %errorlevel%==0 set PYC=python
%PYC% -c "import traducteur.ui" 2>nul
if %errorlevel%==0 (
  %PYC% -m traducteur.ui
) else (
  echo [UI pas encore livree - etape 3 - lancement du diagnostic]
  %PYC% -m traducteur.selftest
)
pause
