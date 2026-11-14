"""Étape 5 — overlay toujours visible, redimensionnable (voir SPEC.md)."""
import tkinter as tk


class Overlay(tk.Toplevel):
    """Fenêtre sans bordure, toujours au-dessus, déplaçable + redimensionnable."""

    def __init__(self, master, geo=None):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg="#0f172a")
        self._x = self._y = 0
        self._rw = self._rh = self._rx = self._ry = 0
        self.lbl = tk.Label(
            self, text="…", bg="#0f172a", fg="#e2f5ff", font=("Segoe UI", 11),
            wraplength=340, justify="left", padx=12, pady=10)
        self.lbl.pack(side="left", fill="both", expand=True)
        droite = tk.Frame(self, bg="#0f172a")
        droite.pack(side="right", fill="y")
        tk.Button(droite, text="×", command=self.withdraw, bg="#0f172a",
                  fg="#64748b", relief="flat", activebackground="#1e293b",
                  bd=0).pack(anchor="ne")
        self.grip = tk.Label(droite, text="◢", bg="#0f172a", fg="#475569",
                              cursor="sizing")
        self.grip.pack(side="bottom", anchor="se", padx=2, pady=2)
        for w in (self, self.lbl):
            w.bind("<ButtonPress-1>", self._debut)
            w.bind("<B1-Motion>", self._glisser)
        self.grip.bind("<ButtonPress-1>", self._debut_resize)
        self.grip.bind("<B1-Motion>", self._glisser_resize)
        self.geometry(geo or "380x140+100+100")
        self.withdraw()

    # --- déplacement
    def _debut(self, e):
        self._x, self._y = e.x, e.y

    def _glisser(self, e):
        self.geometry(f"+{self.winfo_x() + e.x - self._x}+{self.winfo_y() + e.y - self._y}")

    # --- redimensionnement manuel (poignée ◢)
    def _debut_resize(self, e):
        self._rx, self._ry = e.x_root, e.y_root
        self._rw, self._rh = self.winfo_width(), self.winfo_height()

    def _glisser_resize(self, e):
        w = max(220, self._rw + e.x_root - self._rx)
        h = max(80, self._rh + e.y_root - self._ry)
        self.geometry(f"{w}x{h}+{self.winfo_x()}+{self.winfo_y()}")
        self.lbl.configure(wraplength=max(160, w - 70))

    def afficher(self, texte):
        self.lbl.configure(text=(texte or "…")[:2000])
        self.lbl.configure(wraplength=max(160, self.winfo_width() - 70)
                           if self.winfo_width() > 70 else 340)
        self.deiconify()
        self.attributes("-topmost", True)

    def set_opacite(self, valeur):
        try:
            self.attributes("-alpha", float(valeur))
        except tk.TclError:
            pass
