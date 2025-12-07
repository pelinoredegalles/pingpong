echo Lancement du script Python...
python script-BDD.py

echo.
echo Ajout des fichiers du dossier data...
git add .

echo.
echo Commit...
git commit -m "données à jour"

echo.
echo Push...
git push -f origin main

echo.
echo Terminé!
pause