@echo off
REM Launcher for parser-2gis (uses the isolated .venv).
REM   No args            -> launches GUI
REM   With args          -> runs CLI, e.g.:
REM   parser-2gis.bat -i "https://2gis.ru/..." -o out.csv -f csv
"%~dp0.venv\Scripts\parser-2gis-new.exe" %*
