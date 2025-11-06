@echo off
REM Startup script for AI Tutoring Assistant Web Frontend (Windows)

echo 🤖 Starting AI Tutoring Assistant Web Server...
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo 📦 Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Check if API key is set
if "%GOOGLE_API_KEY%"=="" (
    echo ⚠️  Warning: GOOGLE_API_KEY not set!
    echo    Set it with: set GOOGLE_API_KEY=your-key-here
    echo    Or create a .env file with: GOOGLE_API_KEY=your-key-here
    echo.
)

REM Check if dependencies are installed
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo 📥 Installing dependencies...
    pip install -r requirements.txt
    echo.
)

REM Start the server
echo 🚀 Starting server on http://localhost:8000
echo    Press Ctrl+C to stop
echo.
python api.py

