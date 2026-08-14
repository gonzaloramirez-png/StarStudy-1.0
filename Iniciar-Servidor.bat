@echo off
chcp 65001 >nul
title StarStudy - Servidor
cd /d "D:\proyectos\proyecto GitHub\GitHub\StarStudy-1.0"

echo Verificando que MySQL (XAMPP) este activo...
netstat -an | findstr ":3306" | findstr "LISTENING" >nul
if %errorlevel%==0 (
  echo MySQL: OK
) else (
  echo MySQL no esta corriendo. Inicia MySQL desde el Panel de XAMPP.
  pause
  exit /b 1
)

echo Iniciando StarStudy en http://127.0.0.1:8000/
echo Para apagar: cierra esta ventana o presiona Ctrl+C
echo.
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload

pause
