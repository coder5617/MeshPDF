@echo off
echo Building MeshPDF executable...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Clean previous builds
echo Cleaning previous builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM Build executable
echo Building executable with PyInstaller...
pyinstaller MeshPDF.spec

echo.
if exist "dist\MeshPDF.exe" (
    echo ✅ Build successful! 
    echo Executable created: dist\MeshPDF.exe
    echo.
    echo You can now run: dist\MeshPDF.exe
) else (
    echo ❌ Build failed! Check the output above for errors.
)

pause