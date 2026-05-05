@echo off
:: DayZ Geometry Maker - Windows Developer Setup
:: Creates a symlink from Blender's extensions folder to this repo.
:: Must be run as Administrator.
::
:: Usage: Right-click install_dev.bat -> "Run as administrator"
::        OR open an elevated Command Prompt and run it from the repo root.

setlocal EnableDelayedExpansion

echo ============================================================
echo  DayZ Geometry Maker - Developer Symlink Setup (Windows)
echo ============================================================
echo.

:: --- Check for Administrator privileges ---
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator.
    echo Right-click the script and choose "Run as administrator".
    echo.
    pause
    exit /b 1
)

:: --- Locate the repo's addon subfolder ---
:: This script lives in <repo_root>\scripts\, so the addon folder is one level up.
set "SCRIPT_DIR=%~dp0"
set "REPO_ROOT=%SCRIPT_DIR%.."
pushd "%REPO_ROOT%"
set "REPO_ROOT=%CD%"
popd

set "ADDON_SRC=%REPO_ROOT%\dayz_geometry_maker"

if not exist "%ADDON_SRC%\__init__.py" (
    echo ERROR: Could not find the addon folder at:
    echo   %ADDON_SRC%
    echo Make sure you are running this script from inside the cloned repository.
    echo.
    pause
    exit /b 1
)

echo Addon source folder:
echo   %ADDON_SRC%
echo.

:: --- Find Blender extensions path ---
:: Try common Blender versions in descending order.
set "BLENDER_BASE=%APPDATA%\Blender Foundation\Blender"
set "BLENDER_EXT="

for %%V in (5.1 5.0 4.4 4.3 4.2) do (
    if exist "%BLENDER_BASE%\%%V\extensions\user_default" (
        if "!BLENDER_EXT!"=="" (
            set "BLENDER_EXT=%BLENDER_BASE%\%%V\extensions\user_default"
            set "BLENDER_VER=%%V"
        )
    )
)

if "!BLENDER_EXT!"=="" (
    echo ERROR: Could not auto-detect your Blender extensions folder.
    echo Please enter the full path to your Blender extensions\user_default folder.
    echo Example: C:\Users\You\AppData\Roaming\Blender Foundation\Blender\5.1\extensions\user_default
    echo.
    set /p "BLENDER_EXT=Path: "
    if not exist "!BLENDER_EXT!" (
        echo ERROR: Path does not exist. Aborting.
        pause
        exit /b 1
    )
)

echo Detected Blender %BLENDER_VER% extensions folder:
echo   !BLENDER_EXT!
echo.

set "LINK_TARGET=!BLENDER_EXT!\dayz_geometry_maker"

:: --- Check if something already exists at the link target ---
if exist "!LINK_TARGET!" (
    echo WARNING: Something already exists at:
    echo   !LINK_TARGET!
    echo.
    set /p "OVERWRITE=Remove it and create a fresh symlink? [y/N]: "
    if /i "!OVERWRITE!"=="y" (
        rmdir "!LINK_TARGET!" >nul 2>&1
        if exist "!LINK_TARGET!" (
            echo ERROR: Could not remove existing folder/link. Try deleting it manually.
            pause
            exit /b 1
        )
    ) else (
        echo Aborted. No changes made.
        pause
        exit /b 0
    )
)

:: --- Create the symlink ---
mklink /D "!LINK_TARGET!" "%ADDON_SRC%"

if %errorLevel% equ 0 (
    echo.
    echo SUCCESS! Symlink created:
    echo   !LINK_TARGET!
    echo   ^-^> %ADDON_SRC%
    echo.
    echo Next steps:
    echo   1. Open Blender
    echo   2. Go to Edit ^> Preferences ^> Extensions
    echo   3. Enable "DayZ Geometry Maker" if not already enabled
    echo   4. The DayZ tab will appear in the 3D Viewport N-Panel
    echo.
    echo Any file you save in your repo is instantly live in Blender.
    echo Use F3 ^> "Reload Scripts" to pick up changes without restarting.
) else (
    echo.
    echo ERROR: mklink failed. Make sure you are running as Administrator.
)

echo.
pause
endlocal
