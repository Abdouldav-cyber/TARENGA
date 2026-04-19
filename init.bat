@echo off
echo ========================================================
echo INITIALISATION DU PROJET TERANGA 2027 (DJANGO PUR)
echo ========================================================

echo.
echo 1. Creation de l'environnement virtuel Python...
python -m venv venv
call venv\Scripts\activate.bat

echo.
echo 2. Installation de Django et des dependances...
pip install -r requirements.txt

echo.
echo 3. Generation des fichiers Django de base...
django-admin startproject teranga .
python manage.py startapp core

echo.
echo ========================================================
echo INITIALISATION TERMINEE !
echo Vous pouvez maintenant lancer Docker :
echo docker-compose up -d --build
echo ========================================================
pause
