@echo off
setlocal enabledelayedexpansion

if "%~1"=="" (
    echo Usage: vibe_compile.bat [source_file.c]
    exit /b 1
)

set SOURCE_FILE=%~1
set OUTPUT_FILE=%~dpn1.exe
set OBJ_FILE=%~dpn1.obj

:: Search for vcvarsall.bat
set VCVARS=""
set VSWHERE_PATH="C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
for /f "usebackq tokens=*" %%i in (`!VSWHERE_PATH! -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do (
    set VS_PATH=%%i
    set VCVARS="!VS_PATH!\VC\Auxiliary\Build\vcvarsall.bat"
)

if not exist %VCVARS% (
    echo Error: MSVC vcvarsall.bat not found. Please install Visual Studio with C++ tools.
    exit /b 1
)

echo Initializing MSVC environment...
call %VCVARS% x64 > nul

echo Compiling %SOURCE_FILE%...
cl %SOURCE_FILE% /Fe:"%OUTPUT_FILE%" /Fo:"%OBJ_FILE%" /D_CRT_SECURE_NO_WARNINGS /W3 /O2

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Compilation successful: %OUTPUT_FILE%
) else (
    echo.
    echo Compilation failed.
    exit /b %ERRORLEVEL%
)
