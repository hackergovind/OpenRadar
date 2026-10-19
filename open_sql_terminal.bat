@echo off
set PGPASSWORD=admin123
"%~dp0bin\psql.exe" -h 127.0.0.1 -p 5432 -U postgres -d "RadarOpus-WinCHIP"
pause
