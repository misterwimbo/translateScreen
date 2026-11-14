"""Étape 2 — moteur : traduction + cache + historique + glossaire (voir SPEC.md)."""
import json
import re
import sqlite3
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
CONFIG_F = BASE / "config.json"
GLOSSAIRE_F = BASE / "glossaire.json"
HISTO_F = BASE / "historique.db"

DEFAUT_CONFIG = {"source": "auto", "cible": "fr"}


def charger_config():
    try:
        cfg = json.loads(CONFIG_F.read_text(encoding="utf-8"))
        return {**DEFAUT_CONFIG, **cfg}
    except (OSError, ValueError):
        return dict(DEFAUT_CONFIG)


def charger_glossaire():
    try:
        data = json.loads(GLOSSAIRE_F.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def appliquer_glossaire(texte, table):
    for ancien, nouveau in table.items():
        if ancien and ancien in texte:
            texte = texte.replace(ancien, str(nouveau))
    return texte


def _init_db():
    con = sqlite3.connect(str(HISTO_F))
    con.execute("""CREATE TABLE IF NOT EXISTS traductions
        (id INTEGER PRIMARY KEY, ts TEXT, source TEXT, cible TEXT,
         texte TEXT, traduction TEXT, moteur TEXT)""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_cache ON traductions(texte, source, cible)")
    con.commit()
    return con


def lire_cache(texte, source, cible):
    try:
        con = _init_db()  # crée le fichier/table au 1er lancement
        row = con.execute(
            "SELECT traduction FROM traductions WHERE texte=? AND source=? AND cible=? "
            "ORDER BY id DESC LIMIT 1",
            (texte, source, cible)).fetchone()
        con.close()
        return row[0] if row else None
    except OSError:
        return None


def sauver(texte, source, cible, traduction, moteur):
    try:
        con = _init_db()
        con.execute(
            "INSERT INTO traductions(ts, source, cible, texte, traduction, moteur) "
            "VALUES(?,?,?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), source, cible,
             texte, traduction, moteur))
        con.commit()
        con.close()
    except OSError:
        pass


def sauver_config(patch):
    cfg = charger_config()
    cfg.update(patch or {})
    try:
        CONFIG_F.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def historique_recent(n=50):
    try:
        con = _init_db()
        rows = con.execute(
            "SELECT ts, texte, traduction FROM traductions ORDER BY id DESC LIMIT ?",
            (n,)).fetchall()
        con.close()
        return rows
    except OSError:
        return []


def effacer_historique():
    try:
        con = _init_db()
        con.execute("DELETE FROM traductions")
        con.commit()
        con.close()
    except OSError:
        pass


def sauver_glossaire(table):
    try:
        GLOSSAIRE_F.write_text(json.dumps(table, ensure_ascii=False, indent=2),
                               encoding="utf-8")
        return True
    except OSError:
        return False


def _google(texte, source, cible):
    from deep_translator import GoogleTranslator
    return GoogleTranslator(source=source, target=cible).translate(texte)


def _gtx(texte, source, cible):
    """Repli stdlib : endpoint gratuit translate.googleapis.com (sans clé)."""
    sl = "auto" if source in ("auto", None) else source
    q = {"client": "gtx", "sl": sl, "tl": cible, "dt": "t", "q": texte}
    req = urllib.request.Request(
        "https://translate.googleapis.com/translate_a/single?" + urllib.parse.urlencode(q),
        headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode("utf-8"))
    return "".join(seg[0] for seg in data[0] if seg and seg[0])


def _morceaux(texte):
    """Découpe en phrases en conservant les séparateurs (anti-troncature :
    certains backends gratuits ne rendent que le 1er segment)."""
    return [p for p in re.split(r"(?<=[.!?…])(\s+)", texte) if p]


def _traduire_morceau(morceau, source, cible, essais):
    derniere = None
    for i in range(essais):
        try:
            return _google(morceau, source, cible), "google"
        except Exception as e:  # quota 429, réseau… : on patiente et on réessaie
            derniere = e
            time.sleep(2 ** i)
    try:
        return _gtx(morceau, source, cible), "gtx-repli"
    except Exception as e:
        raise RuntimeError(
            f"Traduction impossible ({type(derniere).__name__} puis {type(e).__name__}). "
            "Vérifie internet et réessaie dans une minute.") from e


def traduire(texte, source="auto", cible="fr", essais=3):
    texte = (texte or "").strip()
    if not texte:
        return ""
    hit = lire_cache(texte, source, cible)
    if hit is not None:
        return hit
    traduits, moteurs = [], []
    for morceau in _morceaux(texte):
        if not morceau.strip():
            traduits.append(morceau)  # espaces/retours conservés tels quels
            continue
        h = lire_cache(morceau, source, cible)
        if h is not None:
            traduits.append(h)
            continue
        t, m = _traduire_morceau(morceau, source, cible, essais)
        sauver(morceau, source, cible, t, m)
        traduits.append(t)
        moteurs.append(m)
    trad = "".join(traduits)
    trad = appliquer_glossaire(trad, charger_glossaire())
    sauver(texte, source, cible, trad, "+".join(sorted(set(moteurs))) or "cache")
    return trad
