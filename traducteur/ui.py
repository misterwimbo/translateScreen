"""Étape 3-5 — fenêtre principale + presse-papiers + capture + overlay (SPEC.md)."""
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from traducteur import moteur
from traducteur.overlay import Overlay
from traducteur.sources import (EcouteurTouche, PressePapiers, capturer_zone,
                                ocr, photographier, trouver_tesseract)

LANGUES = [
    ("auto", "Automatique"), ("fr", "Français"), ("en", "Anglais"),
    ("de", "Allemand"), ("es", "Espagnol"), ("it", "Italien"),
    ("pt", "Portugais"), ("nl", "Néerlandais"), ("pl", "Polonais"),
    ("ru", "Russe"), ("ja", "Japonais"), ("zh", "Chinois (simplifié)"),
    ("ko", "Coréen"),
]
NOM_VERS_CODE = {nom: code for code, nom in LANGUES}
SRC_NOMS = [nom for _c, nom in LANGUES]
DST_NOMS = [nom for c, nom in LANGUES if c != "auto"]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Traducteur d'écran")
        self.minsize(640, 620)
        cfg = moteur.charger_config()
        self.en_cours = False

        haut = ttk.Frame(self, padding=10)
        haut.pack(fill="x")
        ttk.Label(haut, text="De :").pack(side="left")
        self.src_nom = tk.StringVar(value=self._nom(cfg.get("source", "auto"), SRC_NOMS))
        ttk.Combobox(haut, textvariable=self.src_nom, values=SRC_NOMS,
                     state="readonly", width=18).pack(side="left", padx=(4, 10))
        ttk.Label(haut, text="Vers :").pack(side="left")
        self.dst_nom = tk.StringVar(value=self._nom(cfg.get("cible", "fr"), DST_NOMS))
        ttk.Combobox(haut, textvariable=self.dst_nom, values=DST_NOMS,
                     state="readonly", width=18).pack(side="left", padx=(4, 10))
        ttk.Button(haut, text="Traduire", command=self.traduire_manuel).pack(side="left")
        ttk.Button(haut, text="Capturer", command=self.capturer).pack(side="left", padx=(6, 0))

        opts = ttk.Frame(self, padding=(10, 0))
        opts.pack(fill="x")
        self.auto_var = tk.BooleanVar(value=bool(cfg.get("presse_papiers_auto", True)))
        ttk.Checkbutton(opts, text="Presse-papiers auto",
                        variable=self.auto_var).pack(side="left")
        self.ov_var = tk.BooleanVar(value=bool(cfg.get("overlay_visible", True)))
        ttk.Checkbutton(opts, text="Overlay", variable=self.ov_var,
                        command=self._bascule_overlay).pack(side="left", padx=(12, 0))
        ttk.Label(opts, text="Opacité :").pack(side="left", padx=(12, 4))
        self.opa_var = tk.DoubleVar(value=float(cfg.get("opacite", 0.92)))
        ttk.Scale(opts, from_=0.5, to=1.0, variable=self.opa_var,
                  command=lambda _v: self.overlay.set_opacite(self.opa_var.get()),
                  length=100).pack(side="left")
        ttk.Label(opts, text="Touche :").pack(side="left", padx=(12, 4))
        self.touche_var = tk.StringVar(value=str(cfg.get("touche_capture", "F8")))
        ttk.Entry(opts, textvariable=self.touche_var, width=12).pack(side="left")
        self.touche_var.trace_add("write", self._bascule_touche)

        corps = ttk.Frame(self, padding=10)
        corps.pack(fill="both", expand=True)
        ttk.Label(corps, text="Texte à traduire :").pack(anchor="w")
        self.src_txt = tk.Text(corps, height=6, wrap="word")
        self.src_txt.pack(fill="both", expand=True)
        ttk.Label(corps, text="Traduction :").pack(anchor="w", pady=(6, 0))
        self.dst_txt = tk.Text(corps, height=6, wrap="word", state="disabled",
                               bg="#f1f5f9")
        self.dst_txt.pack(fill="both", expand=True)

        bas = ttk.Frame(self, padding=(10, 0))
        bas.pack(fill="both", expand=True)
        ttk.Label(bas, text="Historique (double-clic pour recharger) :").pack(anchor="w")
        cadre = ttk.Frame(bas)
        cadre.pack(fill="both", expand=True)
        self.histo = tk.Listbox(cadre, height=5, font=("Consolas", 10))
        defil = ttk.Scrollbar(cadre, orient="vertical", command=self.histo.yview)
        self.histo.configure(yscrollcommand=defil.set)
        self.histo.pack(side="left", fill="both", expand=True)
        defil.pack(side="left", fill="y")
        self.histo.bind("<Double-Button-1>", self.recharger_histo)
        ttk.Button(bas, text="Effacer l'historique",
                   command=self.effacer_histo).pack(anchor="e", pady=(6, 0))

        glos = ttk.LabelFrame(self, text="Glossaire (remplacements après traduction)",
                              padding=10)
        glos.pack(fill="x", padx=10, pady=(0, 6))
        self.glos_liste = tk.Listbox(glos, height=3, font=("Consolas", 10))
        self.glos_liste.pack(side="left", fill="both", expand=True)
        gform = ttk.Frame(glos)
        gform.pack(side="left", padx=(8, 0))
        self.g_ancien = tk.StringVar()
        self.g_nouveau = tk.StringVar()
        ttk.Entry(gform, textvariable=self.g_ancien, width=16).pack(pady=2)
        ttk.Entry(gform, textvariable=self.g_nouveau, width=16).pack(pady=2)
        ttk.Button(gform, text="Ajouter", command=self.ajouter_glossaire).pack(fill="x", pady=2)
        ttk.Button(gform, text="Supprimer", command=self.supprimer_glossaire).pack(fill="x")
        self.charger_glossaire()

        self.statut = tk.StringVar(value="Prêt.")
        ttk.Label(self, textvariable=self.statut,
                  padding=(10, 0, 10, 10)).pack(anchor="w")

        self.overlay = Overlay(self, geo=cfg.get("overlay_geo"))
        self.overlay.set_opacite(self.opa_var.get())
        if self.ov_var.get():
            self.overlay.deiconify()

        self.clip = PressePapiers(self, callback=self.texte_copie)
        if self.auto_var.get():
            self.clip.demarrer()
        self.auto_var.trace_add("write", self._bascule_auto)
        self.ecoute = EcouteurTouche(self.touche_var.get(),
                                     lambda: self.after(0, self.capturer))
        self._bascule_touche()
        self.charger_histo()
        self.protocol("WM_DELETE_WINDOW", self.fermer)

    @staticmethod
    def _nom(code, choix):
        nom = dict(LANGUES).get(code, "")
        return nom if nom in choix else choix[0]

    def _codes(self):
        return NOM_VERS_CODE[self.src_nom.get()], NOM_VERS_CODE[self.dst_nom.get()]

    # --- actions
    def traduire_manuel(self):
        self._lancer(self.src_txt.get("1.0", "end-1c"))

    def texte_copie(self, texte):
        if not self.auto_var.get():
            return
        if texte == self._resultat():
            return  # on vient de copier la traduction : ignorer
        self.src_txt.delete("1.0", "end")
        self.src_txt.insert("1.0", texte)
        self._lancer(texte)

    def _lancer(self, texte):
        texte = (texte or "").strip()
        if not texte or self.en_cours:
            return
        src, dst = self._codes()
        self.en_cours = True
        self._src_len = len(texte)
        self.statut.set("Traduction…")
        threading.Thread(target=self._fond, args=(texte, src, dst),
                         daemon=True).start()

    def _fond(self, texte, src, dst):
        try:
            trad = moteur.traduire(texte, source=src, cible=dst)
            self.after(0, lambda: self._fini(trad))
        except Exception as e:
            msg = str(e)[:160]
            self.after(0, lambda: self._fini(None, msg))

    def _fini(self, trad, erreur=""):
        self.en_cours = False
        if trad is None:
            self.statut.set("Échec : " + erreur)
            return
        self.dst_txt.configure(state="normal")
        self.dst_txt.delete("1.0", "end")
        self.dst_txt.insert("1.0", trad)
        self.dst_txt.configure(state="disabled")
        self.statut.set(f"Traduit : {getattr(self, '_src_len', '?')} → {len(trad)} car.")
        if self.ov_var.get():
            self.overlay.afficher(trad)
        self.charger_histo()

    def _resultat(self):
        return self.dst_txt.get("1.0", "end-1c").strip()

    # --- capture + OCR (étape 4)
    def capturer(self):
        cancel = getattr(self, "_sel_cancel", None)
        if cancel:  # capture déjà ouverte : 2e appui = annuler
            self._sel_cancel = None
            try:
                cancel()
            except tk.TclError:
                pass
            self.statut.set("Capture annulée.")
            return
        if self.en_cours:
            return
        tess = trouver_tesseract()
        if not tess:
            messagebox.showinfo(
                "Tesseract manquant",
                "Tesseract n'est pas installé : capture/OCR indisponible.\n\n"
                "Installe-le : https://github.com/UB-Mannheim/tesseract/wiki\n"
                "En attendant, le presse-papiers auto fonctionne.")
            return
        box = capturer_zone(self)
        if not box:
            self.statut.set("Capture annulée.")
            return
        self.statut.set("Capture… OCR…")
        threading.Thread(target=self._fond_capture, args=(box, tess),
                         daemon=True).start()

    def _fond_capture(self, box, tess):
        try:
            img = photographier(box)
            src, _dst = self._codes()
            texte = ocr(img, src, tess)
            if not texte:
                self.after(0, lambda: self.statut.set("OCR : aucun texte détecté."))
                return
            self.after(0, lambda: self._capture_ok(texte))
        except Exception as e:
            msg = "OCR : " + str(e)[:160]
            self.after(0, lambda: self.statut.set(msg))

    def _capture_ok(self, texte):
        self.src_txt.delete("1.0", "end")
        self.src_txt.insert("1.0", texte)  # éditable avant traduction
        self._lancer(texte)

    # --- historique
    def charger_histo(self):
        self.histo.delete(0, "end")
        for ts, texte, trad in moteur.historique_recent(50):
            court = texte.replace("\n", " ")[:60]
            self.histo.insert("end", f"{ts[11:16] if len(ts) > 16 else ts}  {court}  →  {trad.replace(chr(10), ' ')[:60]}")

    def recharger_histo(self, _evt=None):
        sel = self.histo.curselection()
        if not sel:
            return
        rows = moteur.historique_recent(50)
        if sel[0] < len(rows):
            _ts, texte, trad = rows[sel[0]]
            self.src_txt.delete("1.0", "end")
            self.src_txt.insert("1.0", texte)
            self.dst_txt.configure(state="normal")
            self.dst_txt.delete("1.0", "end")
            self.dst_txt.insert("1.0", trad)
            self.dst_txt.configure(state="disabled")

    def effacer_histo(self):
        if messagebox.askyesno("Historique", "Tout effacer ?"):
            moteur.effacer_historique()
            self.charger_histo()

    # --- glossaire
    def charger_glossaire(self):
        self.glos_liste.delete(0, "end")
        for a, n in sorted(moteur.charger_glossaire().items()):
            self.glos_liste.insert("end", f"{a} → {n}")

    def ajouter_glossaire(self):
        a, n = self.g_ancien.get().strip(), self.g_nouveau.get().strip()
        if not a or not n:
            return
        table = moteur.charger_glossaire()
        table[a] = n
        if moteur.sauver_glossaire(table):
            self.g_ancien.set("")
            self.g_nouveau.set("")
            self.charger_glossaire()

    def supprimer_glossaire(self):
        sel = self.glos_liste.curselection()
        if not sel:
            return
        table = moteur.charger_glossaire()
        cle = self.glos_liste.get(sel[0]).split(" → ")[0]
        table.pop(cle, None)
        moteur.sauver_glossaire(table)
        self.charger_glossaire()

    # --- divers
    def _bascule_auto(self, *_a):
        if self.auto_var.get():
            self.clip.demarrer()
        else:
            self.clip.arreter()

    def _bascule_touche(self, *_a):
        try:
            self.ecoute.spec = self.touche_var.get().strip() or "F8"
            self.ecoute.demarrer()
        except ImportError:
            self.statut.set("pynput manquant : pip install -r requirements.txt")
        except Exception as e:
            self.statut.set("Touche invalide : " + str(e)[:100])

    def _bascule_overlay(self):
        if self.ov_var.get():
            self.overlay.afficher(self._resultat() or "…")
        else:
            self.overlay.withdraw()

    def fermer(self):
        src, dst = self._codes()
        moteur.sauver_config({"source": src, "cible": dst,
                              "presse_papiers_auto": self.auto_var.get(),
                              "overlay_visible": self.ov_var.get(),
                              "opacite": self.opa_var.get(),
                              "overlay_geo": self.overlay.geometry(),
                              "touche_capture": self.touche_var.get().strip() or "F8"})
        self.clip.arreter()
        self.ecoute.arreter()
        try:
            self.overlay.destroy()
        except tk.TclError:
            pass
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
