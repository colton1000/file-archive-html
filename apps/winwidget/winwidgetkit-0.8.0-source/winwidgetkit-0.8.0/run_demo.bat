@echo off
cd /d "%~dp0"
py examples\all_widgets.py
if errorlevel 1 pause
