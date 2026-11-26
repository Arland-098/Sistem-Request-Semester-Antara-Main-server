@echo off
echo =========================================================================
echo   Sistem Pengajuan Semester Antara - UIN Syarif Hidayatullah Jakarta
echo   Berdasarkan SK Rektor Nomor 686 Tahun 2025
echo =========================================================================
echo.

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_BIN=.venv\Scripts\python.exe"
) else (
    set "PYTHON_BIN=python"
)

if not defined FLASK_DEBUG set "FLASK_DEBUG=1"

echo Mengaktifkan server Flask di http://127.0.0.1:5000 ...
"%PYTHON_BIN%" app.py
pause
