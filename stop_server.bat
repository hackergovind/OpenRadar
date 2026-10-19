@echo off
echo Stopping PostgreSQL...
"%~dp0bin\pg_ctl.exe" stop -D "%~dp0data" -m fast
pause
