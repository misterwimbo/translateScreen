# Cahier des charges — Traducteur d'écran (prototype Python)

Inspiré de GameTranslate (traduction de jeux en temps réel : capture → OCR → traduction → overlay).
Règle d'or : **simple et intuitif, qui marche dès le premier lancement.**

## 1. Objectif

Utilitaire Windows qui traduit à la volée le texte affiché dans un jeu
(dialogues, menus) et montre la traduction dans une fenêtre toujours visible.
Public : joueur non technicien. Installation : Python + 1 Tesseract + `pip install`.

## 2. Périmètre du prototype (ce qui est dedans)

1. **Source presse-papiers (garantie)** : tout texte copié (Ctrl+C dans le jeu /
   navigateur) est traduit automatiquement. Fonctionne sans rien d'autre.
2. **Source capture + OCR (optionnelle)** : bouton « Capturer » → sélection d'une
   zone d'écran → OCR via Tesseract (si installé) → traduction. Si Tesseract
   absent : message clair + bascule auto sur presse-papiers.
3. **Moteur de traduction** : `deep-translator` (Google, gratuit, sans clé) +
   cache mémoire + historique SQLite. En cas d'échec réseau : message explicite,
   l'historique reste consultable.
4. **Paires de langues** : source auto ou choisie, cible choisie (FR par défaut ;
   EN, JA, ZH, KO, ES, DE… codes ISO affichés en clair).
5. **Fenêtre principale (unique)** : source, langues, dernier résultat, historique
   récent, 3 actions visibles max (Capturer / Traduire / Paramètres).
6. **Overlay** : petite fenêtre toujours-au-dessus, déplaçable, opacité réglable,
   qui affiche la dernière traduction.
7. **Mini-glossaire** : remplacements mot-à-mot appliqués après traduction
   (ex : noms propres). Fichier `glossaire.json` éditable.
8. **Paramètres persistés** (`config.json`) : langues, dernière zone, opacité.

## 3. Hors périmètre (pas dans le prototype)

Injection/overlay dans le moteur du jeu, hooks DirectX, raccourcis globaux
système, pack en `.exe`, comptes/API payantes, traduction d'images en masse.

## 4. Exigences non fonctionnelles

- Windows 10+, Python 3.10+, interface **tkinter** (stdlib, rien à installer).
- Dépendances pip : `mss`, `Pillow`, `pytesseract`, `deep-translator`.
- Tesseract externe **optionnel** (requis seulement pour la capture).
- Aucune clé API, aucun compte. Internet requis uniquement pour l'appel MT.
- Tous les textes FR, messages d'erreur qui disent quoi faire.
- `python -m traducteur.selftest` doit valider l'install sur la machine.

## 5. Architecture (dossier `traducteur/`)

- `run.bat` — double-clic pour lancer.
- `requirements.txt`, `README.md` (install + Tesseract), `SPEC.md` (ce fichier).
- `traducteur/__init__.py` — version.
- `traducteur/moteur.py` — MT + cache + historique SQLite.
- `traducteur/sources.py` — presse-papiers + capture (mss) + OCR (pytesseract).
- `traducteur/ui.py` — fenêtre principale + overlay (tkinter).
- `traducteur/selftest.py` — auto-diagnostic.

## 6. Risques et parades (cohérence)

| Risque | Parade |
|---|---|
| Tesseract non installé | Détection au lancement, mode presse-papiers par défaut, lien d'install dans README |
| Google bloque / hors-ligne | Erreur claire, historique + cache toujours lisibles |
| OCR approximatif (pixels de jeu) | Zone réglable, upscale x2 avant OCR, texte source affiché et éditable avant traduction |
| `deep-translator` change d'API | Moteur isolé dans `moteur.py`, 1 seul point de changement |

## 7. Critères d'acceptation

1. `run.bat` ouvre la fenêtre sans erreur sur machine Windows + Python 3.10.
2. Copier un texte EN → traduction FR affichée < 5 s (connexion normale).
3. Capture d'une zone lisible → texte OCR affiché et traduisible.
4. Redémarrage : langues, glossaire et historique conservés.
5. `selftest` : tout vert sauf Tesseract si absent (avec consigne).

## 8. Découpage (on avance par étape)

- **Étape 1** : squelette (présent) — arborescence, requirements, run.bat, selftest.
- **Étape 2** : moteur (MT + cache + historique + glossaire).
- **Étape 3** : UI principale + presse-papiers auto.
- **Étape 4** : capture + OCR + tolerances.
- **Étape 5** : overlay + paramètres + polish.
- **Étape 6** : recette (checklist d'acceptation sur ta machine).
