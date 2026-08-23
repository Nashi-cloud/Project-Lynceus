"""Extraction serveur (fallback) — quand le client n'envoie qu'une URL, sans contenu.
Le chemin principal reste l'extraction locale par l'extension (cf. docs/ARCHITECTURE.md)."""

from __future__ import annotations


class ErreurExtraction(Exception):
    """Impossible de récupérer ou d'extraire le contenu de l'URL."""


def recuperer_markdown(url: str) -> tuple[str | None, str]:
    """Télécharge la page et retourne (titre, markdown). Lève ErreurExtraction sinon."""
    import trafilatura  # import différé : dépendance lourde, inutile pour le flux extension

    telecharge = trafilatura.fetch_url(url)
    if telecharge is None:
        raise ErreurExtraction(f"Téléchargement impossible : {url}")

    markdown = trafilatura.extract(telecharge, output_format="markdown", include_comments=False, include_tables=True)
    if not markdown:
        raise ErreurExtraction(f"Aucun contenu textuel extractible : {url}")

    titre = None
    try:
        meta = trafilatura.extract_metadata(telecharge)
        titre = meta.title if meta else None
    except Exception:  # le titre est un bonus, jamais bloquant
        pass
    return titre, markdown
