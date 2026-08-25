"""Contenu du portail — lu dans les fichiers que le moteur applique réellement.

Rien n'est recopié à la main. La taxonomie affichée est celle que le prompt injecte, les
pondérations affichées sont celles que le serveur calcule, la charte affichée est le
fichier du dépôt. C'est ce qui rend l'engagement de transparence (charte §2) vérifiable :
une page du site ne peut pas diverger de ce que le code fait, elle en est extraite.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from markdown_it import MarkdownIt

from ..config import trouver_racine
from ..moteur import notation, prompt

_MOTIF_FAMILLE = re.compile(r"^##\s+Famille\s+([A-Z])\s+—\s+(.+?)\s*$", re.MULTILINE)

GRAVITES = {"haute": "Gravité haute", "moyenne": "Gravité moyenne", "faible": "Gravité faible"}


@lru_cache
def _rendu() -> MarkdownIt:
    # « commonmark » plutôt que le préréglage permissif : pas de HTML brut interprété
    # depuis un fichier de documentation, même si celui-ci vient du dépôt.
    return MarkdownIt("commonmark").enable("table")


@lru_cache
def document(nom: str) -> dict:
    """Rend docs/<NOM>.md en HTML. Retourne {titre, html}."""
    chemin = trouver_racine() / "docs" / f"{nom}.md"
    texte = chemin.read_text(encoding="utf-8")
    premiere = next((l for l in texte.splitlines() if l.startswith("# ")), "# Document")
    corps = texte.split("\n", 1)[1] if texte.startswith("# ") else texte
    return {"titre": premiere[2:].strip(), "html": _rendu().render(corps)}


@lru_cache
def taxonomie_par_famille() -> list[dict]:
    """Les techniques du référentiel, regroupées par famille.

    Les identifiants et gravités viennent de `prompt.charger_taxonomie()` — donc du même
    parseur que celui qui alimente le modèle. Les familles, elles, ne servent qu'à
    l'affichage : elles n'existent pas dans le référentiel technique."""
    texte = (trouver_racine() / "docs" / "TAXONOMIE.md").read_text(encoding="utf-8")
    techniques = prompt.charger_taxonomie()

    bornes = [(m.start(), m.group(1), m.group(2)) for m in _MOTIF_FAMILLE.finditer(texte)]
    positions = {tid: texte.find(f"### `{tid}`") for tid in techniques}

    familles: list[dict] = []
    for i, (debut, lettre, nom) in enumerate(bornes):
        fin = bornes[i + 1][0] if i + 1 < len(bornes) else len(texte)
        membres = [
            {"id": tid, **techniques[tid]}
            for tid, pos in positions.items()
            if debut < pos < fin
        ]
        membres.sort(key=lambda t: positions[t["id"]])
        familles.append({"lettre": lettre, "nom": nom, "techniques": membres})

    orphelines = [t for f in familles for t in f["techniques"]]
    if len(orphelines) != len(techniques):  # pragma: no cover — filet contre un remaniement du fichier
        manquantes = sorted(set(techniques) - {t["id"] for t in orphelines})
        familles.append({"lettre": "?", "nom": "Hors famille",
                         "techniques": [{"id": tid, **techniques[tid]} for tid in manquantes]})
    return familles


def nb_techniques() -> int:
    return len(prompt.charger_taxonomie())


def ponderations() -> list[dict]:
    """Les poids réellement appliqués par le serveur, dans l'ordre décroissant."""
    libelles = {
        "sources": "Qualité du sourçage",
        "factualite": "Rigueur factuelle",
        "ton": "Registre et procédés",
        "transparence": "Transparence de l'éditeur",
    }
    return [
        {"cle": cle, "libelle": libelles.get(cle, cle), "poids": int(poids * 100)}
        for cle, poids in sorted(notation.POIDS.items(), key=lambda kv: -kv[1])
    ]


def seuils() -> list[dict]:
    """Les seuils de grade tels qu'appliqués, du meilleur au moins bon, E compris."""
    lignes = []
    precedent = 100
    for seuil, grade in notation.SEUILS:
        lignes.append({"grade": grade, "de": seuil, "a": precedent})
        precedent = seuil - 1
    lignes.append({"grade": "E", "de": 0, "a": precedent})
    return lignes


_MOTIF_PAQUET = re.compile(r"^lynceus-extension-v(\d+)\.(\d+)\.(\d+)\.zip$")


def paquet_le_plus_recent(dossiers: str) -> dict | None:
    """L'archive d'extension de plus haute version, parmi plusieurs dossiers.

    Plusieurs dossiers séparés par des virgules, dans l'ordre : typiquement un volume
    alimenté à la main et le paquet embarqué dans l'image. Le plus haut numéro l'emporte,
    d'où qu'il vienne, ce qui permet de publier une mise à jour en déposant un zip sans
    reconstruire l'image, sans pour autant qu'une image neuve reparte de rien.

    Tri par **version** et non par date de fichier : une copie ou une restauration de
    sauvegarde ne doit pas faire régresser ce qui est proposé au téléchargement.

    Relu à chaque appel, jamais mémorisé au démarrage : un zip déposé pendant que le
    portail tourne doit être proposé immédiatement. C'est un parcours de quelques entrées
    de dossier, négligeable devant le rendu d'un gabarit."""
    candidats = []
    for dossier in (d.strip() for d in dossiers.split(",")):
        if not dossier:
            continue
        base = Path(dossier)
        if not base.is_dir():
            continue
        for chemin in base.glob("lynceus-extension-v*.zip"):
            m = _MOTIF_PAQUET.match(chemin.name)
            if m:
                candidats.append((tuple(int(g) for g in m.groups()), chemin))
    if not candidats:
        return None

    version, chemin = max(candidats)
    return {
        "version": ".".join(str(n) for n in version),
        "nom": chemin.name,
        "chemin": chemin,
        "taille_ko": round(chemin.stat().st_size / 1024),
    }
