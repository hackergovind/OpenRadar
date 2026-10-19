@echo off
title RadarOpus Medical Web UI
echo Starting RadarOpus Web UI with PostgreSQL...
start http://127.0.0.1:8080
python "%~dp0radaropus_app.py"
pause
