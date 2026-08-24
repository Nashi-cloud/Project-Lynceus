"""Extraction serveur (fallback) — quand le client n'envoie qu'une URL, sans contenu.

Le chemin principal reste l'extraction locale par l'extension (cf. docs/ARCHITECTURE.md) :
le navigateur de l'utilisateur passe les protections anti-robots, un serveur non. On tente
ici trafilatura puis httpx avec des en-têtes de navigateur, et on échoue HONNÊTEMENT
(cause + remèdes) plutôt que de jouer à contourner les protections."""

from __future__ import annotations

import httpx


class ErreurExtraction(Exception):
    """Impossible de récupérer ou d'extraire le contenu de l'URL."""


# Certains sites refusent les clients identifiés comme robots mais acceptent ces en-têtes.
_ENTETES_NAVIGATEUR = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr,fr-FR;q=0.9,en;q=0.6",
}

_CONSEIL_BLOCAGE = (
    "Ce site bloque le téléchargement automatique (protection anti-robots). "
    "L'extension navigateur (phase 2) analysera ces pages sans difficulté : l'extraction s'y fera "
    "localement, après que VOTRE navigateur a passé la protection. En attendant : copier le contenu "
    "dans un fichier puis « lynceus analyser fichier.md --url <url> », ou le coller sur l'entrée "
    "standard : « lynceus analyser - --url <url> »."
)


def _telecharger(url: str) -> str:
    """trafilatura d'abord, puis httpx avec en-têtes de navigateur en secours."""
    import trafilatura

    telecharge = trafilatura.fetch_url(url)
    if telecharge:
        return telecharge

    try:
        reponse = httpx.get(url, headers=_ENTETES_NAVIGATEUR, follow_redirects=True, timeout=30)
    except httpx.HTTPError as exc:
        raise ErreurExtraction(f"Téléchargement impossible ({exc.__class__.__name__}) : {url}") from exc
    if reponse.status_code >= 400:
        raise ErreurExtraction(f"Téléchargement refusé (HTTP {reponse.status_code}) : {url}. {_CONSEIL_BLOCAGE}")
    return reponse.text


def recuperer_markdown(url: str) -> tuple[str | None, str]:
    """Télécharge la page et retourne (titre, markdown). Lève ErreurExtraction sinon."""
    import trafilatura

    telecharge = _telecharger(url)

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
