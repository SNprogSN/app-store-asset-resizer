@echo off
chcp 65001 >nul
echo ============================================
echo  App Store Ikon Méretezo - Indítás
echo ============================================
echo.

:: Ellenőrizzük, hogy a Python elérhető-e
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [HIBA] Python nem talalhato! Kerjuk telepitse: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Pillow telepítése ha szükséges
echo Függosegek ellenorzese...
python -m pip install -r requirements.txt --quiet

echo.
echo Program inditasa...
python icon_resizer.py
