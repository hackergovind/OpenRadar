@echo off
title OpenRadar Medical Repertory & Practice Management
echo =========================================================
echo  OpenRadar Synthesis Repertory & Practice Management
echo  SQLite High-Speed Medical Engine (No Postgres Required!)
echo =========================================================
start http://127.0.0.1:8080
python "%~dp0radaropus_app.py"
pause
