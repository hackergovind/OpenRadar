@echo off
title Build OpenRadar Android APK
echo ========================================================
echo  Building OpenRadar Android APK (Native Offline Engine)
echo ========================================================

set "JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot"
cd /d "%~dp0android"

call gradlew.bat assembleDebug

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================================
    echo  APK BUILD SUCCESSFUL!
    echo ========================================================
    copy /y "app\build\outputs\apk\debug\app-debug.apk" "..\OpenRadar-v1.0.apk"
    echo Saved to: %~dp0OpenRadar-v1.0.apk
) else (
    echo.
    echo [ERROR] Build failed! Check log above.
)
pause
