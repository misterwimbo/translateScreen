"""Étape 5 — overlay toujours visible (voir SPEC.md)."""
import tkinter as tk


class Overlay(tk.Toplevel):
    """Petite fenêtre sans bordure, toujours au-dessus, déplaçable à la souris."""

    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg="#0f172a")
        self._x = self._y = 0
        self.lbl = tk.Label(
            self, text="…", bg="#0f172a", fg="#e2f5ff", font=("Segoe UI", 11),
            wraplength=340, justify="left", padx=12, pady=10)
        self.lbl.pack(side="left", fill="both", expand=True)
        tk.Button(self, text="×", command=self.withdraw, bg="#0f172a",
                  fg="#64748b", relief="flat", activebackground="#1e293b",
                  bd=0).pack(side="right", anchor="ne")
        for w in (self, self.lbl):
            w.bind("<ButtonPress-1>", self._debut)
            w.bind("<B1-Motion>", self._glisser)
        self.geometry("380x120+100+100")
        self.withdraw()

    def _debut(self, e):
        self._x, self._y = e.x, e.y

    def _glisser(self, e):
        self.geometry(f"+{self.winfo_x() + e.x - self._x}+{self.winfo_y() + e.y - self._y}")

    def afficher(self, texte):
        self.lbl.configure(text=(texte or "…")[:600])
        self.deiconify()
        self.attributes("-topmost", True)

    def set_opacite(self, valeur):
        try:
            self.attributes("-alpha", float(valeur))
        except tk.TclError:
            pass
