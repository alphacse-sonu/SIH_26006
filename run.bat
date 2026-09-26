@echo off
REM Maritime Chartering Decision Platform - Start Script (Windows)

echo.
echo  Maritime Chartering Decision Platform
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is required. Install from https://python.org
    pause
    exit /b 1
)

REM Check Node
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is required. Install from https://nodejs.org
    pause
    exit /b 1
)

REM Backend setup
echo Setting up backend...
cd backend

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet

REM Generate data if not exists
if not exist "data\freight_rates.csv" (
    echo Generating synthetic training data...
    python data\generate_synthetic_data.py
)

REM Start backend
echo Starting backend server on port 8000...
start "Backend" cmd /c "uvicorn main:app --reload --port 8000"
cd ..

REM Frontend setup
echo.
echo Setting up frontend...
cd frontend

if not exist "node_modules" (
    echo Installing npm dependencies...
    call npm install
)

REM Start frontend
echo Starting frontend on port 5173...
start "Frontend" cmd /c "npm run dev"
cd ..

echo.
echo Platform is starting!
echo Open http://localhost:5173 in your browser
echo.
pause
