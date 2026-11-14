# Traducteur d'écran (prototype)

Traduit à la volée le texte d'un jeu : presse-papiers auto + capture/OCR,
affiché dans un overlay. Voir `SPEC.md` (cahier des charges).

## Installation (une fois)

1. Python 3.10+ : https://www.python.org/downloads/
   (cocher « Add python.exe to PATH »).
2. Tesseract OCR (seulement pour la capture d'écran) :
   https://github.com/UB-Mannheim/tesseract/wiki
   Noter le dossier d'install, ex : `C:\Program Files\Tesseract-OCR`.
3. Dépendances :
```
cd traducteur
pip install -r requirements.txt
```

## Lancer

Double-clic sur `run.bat`, ou :
```
python -m traducteur.ui
```

## Vérifier l'install
```
python -m traducteur.selftest
```
Tout doit être vert, sauf Tesseract si non installé (consigne affichée).
Le test de traduction utilise le moteur avec réessais + repli : en cas de
quota Google temporaire (`TooManyRequests`), il patiente et réessaie.

## Glossaire

`traducteur/glossaire.json` : remplacements appliqués après traduction
(noms propres, termes de jeu). Format : `{"Ancien": "Nouveau"}`.
"# translateScreen" 
