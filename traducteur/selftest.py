"""Auto-diagnostic : `python -m traducteur.selftest` (à lancer dans traducteur/)."""
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path


def check(nom, ok, conseil=""):
    print(f"[{'OK ' if ok else 'KO '}] {nom}" + ("" if ok and not conseil else f" — {conseil}"))
    return ok


def main():
    tout_ok = True
    tout_ok &= check("Python 3.10+", sys.version_info >= (3, 10), sys.version.split()[0])

    mods = {}
    for m in ("tkinter", "mss", "PIL", "pytesseract", "deep_translator"):
        try:
            __import__(m)
            mods[m] = True
        except ImportError:
            mods[m] = False
    tout_ok &= check("tkinter (stdlib)", mods["tkinter"], "réinstaller Python avec tcl/tk")
    for m in ("mss", "PIL", "pytesseract", "deep_translator"):
        tout_ok &= check(f"pip : {m}", mods[m], "pip install -r requirements.txt")

    t = shutil.which("tesseract")
    check("Tesseract (capture OCR)", bool(t),
          t or "optionnel : https://github.com/UB-Mannheim/tesseract/wiki (sinon mode presse-papiers)")

    try:
        with tempfile.TemporaryDirectory() as d:
            con = sqlite3.connect(str(Path(d) / "t.db"))
            con.execute("CREATE TABLE t(a TEXT)")
            con.close()
        check("SQLite (historique)", True)
    except OSError as e:
        tout_ok &= check("SQLite (historique)", False, str(e))

    try:
        from traducteur.moteur import traduire
        t = traduire("Hello", source="en", cible="fr")
        tout_ok &= check("Traduction en ligne", bool(t and t.strip()), (t or "")[:60])
    except ImportError:
        tout_ok &= check("Traduction en ligne", False, "pip install -r requirements.txt")
    except Exception as e:
        tout_ok &= check("Traduction en ligne", False, str(e)[:100])

    print("\nVerdict : " + ("PRÊT ✔" if tout_ok else "À COMPLÉTER ✘ (voir KO ci-dessus)"))
    return 0 if tout_ok else 1


if __name__ == "__main__":
    sys.exit(main())
