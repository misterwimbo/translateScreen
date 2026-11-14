"""Sources : presse-papiers (étape 3) + capture écran + OCR (étape 4). Voir SPEC.md."""
import shutil
import tkinter as tk
from pathlib import Path


class PressePapiers:
    """Appelle `callback(texte)` à chaque nouveau contenu texte copié."""

    def __init__(self, root, delai_ms=600, callback=None):
        self.root = root
        self.delai = delai_ms
        self.callback = callback
        self.actif = False
        self.dernier = None
        self._job = None

    def _lire(self):
        try:
            return self.root.clipboard_get()
        except tk.TclError:
            return None

    def demarrer(self):
        if self.actif:
            return
        self.actif = True
        self.dernier = self._lire()
        self._boucle()

    def arreter(self):
        self.actif = False
        if self._job is not None:
            try:
                self.root.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None

    def _boucle(self):
        if not self.actif:
            return
        try:
            v = self._lire()
            if v and v != self.dernier:
                self.dernier = v
                if self.callback is not None:
                    self.callback(v)
        finally:
            self._job = self.root.after(self.delai, self._boucle)


# --- étape 4 : capture + OCR
TESSERACT_CHEMINS = [
    r"E:\prog\tesseract\tesseract.EXE",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]

LANGUES_TESSERACT = {
    "auto": "eng+fra", "fr": "fra", "en": "eng", "de": "deu", "es": "spa",
    "it": "ita", "pt": "por", "nl": "nld", "pl": "pol", "ru": "rus",
    "ja": "jpn", "zh": "chi_sim", "ko": "kor",
}


def trouver_tesseract():
    w = shutil.which("tesseract")
    if w:
        return w
    for c in TESSERACT_CHEMINS:
        if Path(c).is_file():
            return c
    return None


def capturer_zone(root):
    """Overlay plein écran : dessiner un rectangle. Rend (x, y, l, h) ou None."""
    resultat = {}
    root.withdraw()
    try:
        sel = tk.Toplevel(root)
        sel.attributes("-fullscreen", True)
        sel.attributes("-alpha", 0.35)
        sel.configure(bg="black", cursor="crosshair")
        sel.attributes("-topmost", True)
        canvas = tk.Canvas(sel, bg="black", highlightthickness=0, cursor="crosshair")
        canvas.pack(fill="both", expand=True)
        depart, rect = {}, {}

        def debut(e):
            depart["x"], depart["y"] = e.x, e.y
            rect["id"] = canvas.create_rectangle(e.x, e.y, e.x, e.y, outline="red", width=2)

        def glisser(e):
            if "id" in rect:
                canvas.coords(rect["id"], depart["x"], depart["y"], e.x, e.y)

        def fin(e):
            x1, y1 = min(depart["x"], e.x), min(depart["y"], e.y)
            x2, y2 = max(depart["x"], e.x), max(depart["y"], e.y)
            if x2 - x1 > 10 and y2 - y1 > 10:
                resultat["box"] = (x1, y1, x2 - x1, y2 - y1)
            sel.destroy()

        canvas.bind("<ButtonPress-1>", debut)
        canvas.bind("<B1-Motion>", glisser)
        canvas.bind("<ButtonRelease-1>", fin)
        sel.bind("<Escape>", lambda _e: sel.destroy())
        sel.grab_set()
        root.wait_window(sel)
    finally:
        root.deiconify()
    return resultat.get("box")


def photographier(box):
    import mss
    from PIL import Image
    x, y, w, h = (int(v) for v in box)
    with mss.mss() as sct:
        shot = sct.grab({"left": x, "top": y, "width": w, "height": h})
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")


def ocr(image, code_langue="auto", tesseract_cmd=None):
    """Rend le texte détecté ( upscale x2 + niveaux de gris)."""
    import pytesseract
    from PIL import Image, ImageOps
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    img = ImageOps.grayscale(image)
    w, h = img.size
    img = img.resize((w * 2, h * 2), resample=Image.LANCZOS)
    lang = LANGUES_TESSERACT.get(code_langue, "eng")
    try:
        texte = pytesseract.image_to_string(img, lang=lang)
    except Exception:
        if "+" in lang:  # ex : fra manquant → repli anglais
            texte = pytesseract.image_to_string(img, lang="eng")
        else:
            raise
    return " ".join(texte.split())
