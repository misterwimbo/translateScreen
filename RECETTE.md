# Recette — prototype traducteur d'écran (étape 6)

Cocher dans l'ordre. Tout doit être vert pour figer le prototype.
En cas de KO : copier le message d'erreur exact + ce qui a été fait.

## 0. Install (rappel)
```
cd traducteur
pip install -r requirements.txt
python -m traducteur.selftest   → tout vert (Tesseract OK ici)
```

## 1. Lancement
- [ ] `run.bat` (double-clic) ouvre la fenêtre, sans erreur console.

## 2. Presse-papiers auto (critère spec : < 5 s)
- [ ] Copier un texte anglais (Ctrl+C) → traduction FR affichée < 5 s.
- [ ] Statut affiche `Traduit : X → Y car.` avec des nombres cohérents.
- [ ] Recopier la traduction ne re-traduit pas (pas de boucle).

## 3. Manuel + historique
- [ ] Coller un texte + **Traduire** → résultat complet (phrases non coupées).
- [ ] L'entrée apparaît dans l'historique ; double-clic la recharge.
- [ ] **Effacer l'historique** vide la liste.

## 4. Capture + OCR
- [ ] **Capturer** → voile noir → rectangle sur un texte → texte reconnu
      affiché (éditable) puis traduit.
- [ ] Échap annule proprement. Sans Tesseract : message + lien (non testable ici, il est installé).

## 5. Overlay + réglages
- [ ] L'overlay suit chaque traduction ; déplaçable ; × le masque.
- [ ] Case Overlay + curseur opacité fonctionnent.
- [ ] Fermer/rouvrir : langues, options, historique, glossaire conservés.

## 6. Glossaire
- [ ] Ajouter `Nuage → Cloud`, traduire "The Cloud is coming" → contient "Cloud".
- [ ] Supprimer la règle (liste à jour).

## Verdict
- [ ] Tout coché → prototype figé ✔
- [ ] Sinon, me renvoyer : n° du test + message exact.
