@echo off
REM Chay 24 ca kiem thu + tu xuat bao cao (Windows) bang MOT lan nhap dup.
REM   chay_kiem_thu.bat              mac dinh lap 20 lan/ca, xong tu mo bao cao HTML
REM   chay_kiem_thu.bat --lap 50     do ky hon
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo ^>^> Tao moi truong ao .venv
  py -3 -m venv .venv 2>nul || python -m venv .venv
  if errorlevel 1 (
    echo !! Can Python 3.10 tro len: https://www.python.org/downloads/  ^(tick "Add python.exe to PATH"^)
    pause & exit /b 2
  )
  ".venv\Scripts\python.exe" -m pip install -q --upgrade pip
)

echo ^>^> Kiem tra thu vien
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt -r requirements-bao-cao.txt
if errorlevel 1 ( echo !! Cai thu vien that bai - kiem tra Internet & pause & exit /b 2 )

".venv\Scripts\python.exe" xuat_bao_cao.py --chay --mo %*
set KQ=%errorlevel%
echo.
if %KQ%==0 (echo KET QUA: B dat moi muc tieu.) else (echo KET QUA: xem bao cao - ma thoat %KQ%)
pause
exit /b %KQ%
