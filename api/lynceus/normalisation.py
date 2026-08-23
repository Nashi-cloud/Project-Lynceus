"""Normalisation des URL et des contenus — les deux clés de l'annuaire (cf. docs/ARCHITECTURE.md)."""

from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Paramètres de tracking supprimés à la normalisation (liste volontairement conservatrice)
_PREFIXES_TRACKING = ("utm_",)
_PARAMS_TRACKING = {
    "fbclid", "gclid", "gclsrc", "dclid", "msclkid", "twclid", "yclid",
    "igshid", "mc_cid", "mc_eid", "_hsenc", "_hsmi", "wt_mc",
}


def _est_tracking(nom: str) -> bool:
    nom = nom.lower()
    return nom.startswith(_PREFIXES_TRACKING) or nom in _PARAMS_TRACKING


def normaliser_url(url: str) -> str:
    """URL canonique : schéma/hôte en minuscules, port par défaut retiré, fragment supprimé,
    paramètres de tracking supprimés, paramètres restants triés, slash final retiré (sauf racine)."""
    url = url.strip()
    morceaux = urlsplit(url)
    if morceaux.scheme.lower() not in ("http", "https"):
        raise ValueError(f"URL non supportée (http/https attendu) : {url!r}")

    schema = morceaux.scheme.lower()
    hote = (morceaux.hostname or "").lower()
    if not hote:
        raise ValueError(f"URL sans hôte : {url!r}")
    port = morceaux.port
    if port and not (schema == "http" and port == 80) and not (schema == "https" and port == 443):
        hote = f"{hote}:{port}"

    chemin = morceaux.path or "/"
    if len(chemin) > 1:
        chemin = chemin.rstrip("/") or "/"

    params = [(n, v) for n, v in parse_qsl(morceaux.query, keep_blank_values=True) if not _est_tracking(n)]
    requete = urlencode(sorted(params))

    return urlunsplit((schema, hote, chemin, requete, ""))


def hacher_url(url: str) -> str:
    """SHA-256 hex de l'URL normalisée — la clé publique de l'annuaire."""
    return hashlib.sha256(normaliser_url(url).encode("utf-8")).hexdigest()


def extraire_domaine(url: str) -> str:
    hote = urlsplit(url.strip()).hostname or ""
    return hote.lower()


def normaliser_texte(texte: str) -> str:
    """Espaces réduits, bords nettoyés — base du hash de contenu et de la vérification des extraits."""
    return re.sub(r"\s+", " ", texte).strip()


def hacher_contenu(markdown: str) -> str:
    """SHA-256 hex du Markdown normalisé — détecte le même contenu sous d'autres URL."""
    return hashlib.sha256(normaliser_texte(markdown).encode("utf-8")).hexdigest()
