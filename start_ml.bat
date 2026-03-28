@echo off
echo =====================================
echo   Russian Yatzy - ML Quick Start
echo =====================================
echo.
echo Choose an option:
echo   1. Train ML Agent (Quick - 5K episodes)
echo   2. Train ML Agent (Full - 50K episodes)
echo   3. Benchmark ML vs Probability (1000 games)
echo   4. Start Main Game (with ML options)
echo   5. Exit
echo.
set /p choice="Enter choice (1-5): "

if "%choice%"=="1" (
    echo.
    echo Training quick model...
    python train_ml.py --mode quick
    pause
    goto :start
)
if "%choice%"=="2" (
    echo.
    echo Training full model...
    python train_ml.py --mode full
    pause
    goto :start
)
if "%choice%"=="3" (
    echo.
    echo Running benchmarks...
    python benchmark_strategies.py --games 1000
    pause
    goto :start
)
if "%choice%"=="4" (
    echo.
    echo Starting game...
    python src/main.py
    pause
    goto :start
)
if "%choice%"=="5" (
    echo Goodbye!
    exit /b
)

echo Invalid choice!
pause
:start
cls
goto :EOF
