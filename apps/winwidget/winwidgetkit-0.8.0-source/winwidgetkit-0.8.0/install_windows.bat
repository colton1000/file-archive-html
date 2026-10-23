@echo off
setlocal
cd /d "%~dp0"
echo Installing WinWidgetKit 0.8.0...
py -m pip install -e .
if errorlevel 1 goto error
py -c "import winwidgetkit; print('Installed version:', winwidgetkit.__version__)"
if errorlevel 1 goto error
py examples\orb_demo.py
if errorlevel 1 pause
exit /b 0
:error
echo Installation failed. Make sure Python and the py launcher are installed.
pause
exit /b 1
