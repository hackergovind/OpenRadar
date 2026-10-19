@echo off
echo Starting PostgreSQL from %~dp0...
"%~dp0bin\pg_ctl.exe" start -D "%~dp0data" -l "%~dp0logs\server.log"
pause
