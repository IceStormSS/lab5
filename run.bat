@echo off
cd /d "%~dp0"
echo ========================================================
echo  Zapusk saytu:       http://127.0.0.1:5000/
echo  Swagger UI (Lab 5): http://127.0.0.1:5000/apidocs/
echo ========================================================
start "" cmd /c "timeout /t 2 >nul & start http://127.0.0.1:5000/"
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe app.py
) else (
    python app.py
)
pause