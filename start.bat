@echo off
chcp 65001 >nul
setlocal

:: ============================================================
::  App Store Ikon Méretező  –  Indítószkript (Windows 11/10)
::  start.bat
:: ============================================================
::
::  MIT CSINÁL EZ A FÁJL?
::  ─────────────────────
::  1) Ellenőrzi, hogy telepített-e Python 3 a gépen.
::     Ha nem: linket mutat a letöltéshez és kilép.
::
::  2) ELSŐ INDÍTÁSKOR automatikusan létrehozza a .venv
::     nevű virtuális Python-környezetet a projekt mappájában.
::       -> Ez elkülöníti a projekt csomagjait a rendszer-
::          Python-tól, nem "szennyezi be" a globális telepítést.
::       -> Windows 11-en ez SZÜKSÉGES, mert az újabb Python
::          alapértelmezetten megtagadja a rendszerszintű
::          pip install-t engedély nélkül (PEP 668 / externally
::          managed environment hiba elkerülése).
::
::  3) Aktiválja a virtuális környezetet (.venv\Scripts\activate).
::
::  4) Telepíti / frissíti a szükséges csomagokat a
::     requirements.txt alapján (Pillow, svglib, PyMuPDF stb.).
::     Ha már telepítve vannak és nincs újabb verzió, ez
::     néhány másodperc alatt lefut.
::
::  5) Elindítja az icon_resizer.py grafikus alkalmazást.
::
::  ÚJRAINDÍTÁSNÁL (2. alkalom+):
::  ─────────────────────────────
::  A .venv már létezik, a csomagok már telepítve vannak,
::  ezért a 4. lépés szinte azonnal lefut, és a program
::  gyorsan elindul.
::
::  MAPPA-STRUKTÚRA (amit ez a szkript hoz létre / kezel):
::  ───────────────────────────────────────────────────────
::  projekt_mappa\
::    start.bat          <- ez a fájl
::    icon_resizer.py    <- a fő program
::    requirements.txt   <- szükséges Python csomagok listája
::    .venv\             <- virtuális környezet (AUTO LÉTREHOZVA)
::      Scripts\
::        python.exe     <- a projekt saját Python-ja
::        activate.bat   <- aktiváló szkript
::      Lib\site-packages\ <- telepített csomagok
:: ============================================================

echo.
echo  ============================================================
echo   App Store Ikon Meretező – Indítás
echo  ============================================================
echo.

:: ── 1) Python ellenőrzés ─────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [HIBA] Python 3 nem talalhato a PATH-ban!
    echo.
    echo  Kerjuk telepitse a Python 3.9 vagy ujabb verziot:
    echo    https://www.python.org/downloads/
    echo.
    echo  FONTOS: Telepíteskor pipálja be:
    echo    [x] Add Python to PATH
    echo.
    pause
    exit /b 1
)

echo  [OK] Python talalhato:
python --version
echo.

:: ── 2) Virtuális környezet létrehozása (csak egyszer) ────────
if not exist ".venv\Scripts\activate.bat" (
    echo  [ELSO INDITAS] Virtualis kornyezet (.venv) letrehozasa...
    echo  Ez csak egyszer fut le, kb. 5-15 masodpercet vesz igenybe.
    echo.
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo  [HIBA] A virtualis kornyezet letrehozasa nem sikerult!
        pause
        exit /b 1
    )
    echo  [OK] .venv letrehozva.
    echo.
)

:: ── 3) Virtuális környezet aktiválása ────────────────────────
call ".venv\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo  [HIBA] A virtualis kornyezet aktiválása sikertelen!
    pause
    exit /b 1
)

:: ── 4) Függőségek telepítése / ellenőrzése ───────────────────
echo  Fuggosegek ellenorzese es telepitese (requirements.txt)...
pip install -r requirements.txt --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo.
    echo  [HIBA] A csomagok telepitese nem sikerult!
    echo  Ellenorizze az internetkapcsolatot, majd probálja ujra.
    pause
    exit /b 1
)
echo  [OK] Minden fuggoseg elerheto.
echo.

:: ── 5) Program indítása ───────────────────────────────────────
echo  Program inditasa...
echo  ============================================================
echo.
python icon_resizer.py

endlocal
