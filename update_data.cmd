@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Lancement du script Python...
python script-BDD.py

echo.
echo Ajout des fichiers du dossier data...
git add data/

echo.
echo Commit...
git commit -m "données à jour"

echo.
echo Push...
git push -f origin main

echo.
echo Terminé!
pause
