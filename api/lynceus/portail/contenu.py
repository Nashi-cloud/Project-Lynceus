"""Contenu du portail — lu dans les fichiers que le moteur applique réellement.

Rien n'est recopié à la main. La taxonomie affichée est celle que le prompt injecte, les
pondérations affichées sont celles que le serveur calcule, la charte affichée est le
fichier du dépôt. C'est ce qui rend l'engagement de transparence (charte §2) vérifiable :
une page du site ne peut pas diverger de ce que le code fait, elle en est extraite.
"""

from __future__ import annotations

import posixpath
import re
from functools import lru_cache
from pathlib import Path

from markdown_it import MarkdownIt

from ..config import trouver_racine
from ..moteur import notation, prompt

_MOTIF_FAMILLE = re.compile(r"^##\s+Famille\s+([A-Z])\s+—\s+(.+?)\s*$", re.MULTILINE)

GRAVITES = {"haute": "Gravité haute", "moyenne": "Gravité moyenne", "faible": "Gravité faible"}

# Les documents de docs/ se lient entre eux par chemins relatifs. C'est juste dans le
# dépôt, et faux ici : « METHODOLOGIE.md » deviendrait /METHODOLOGIE.md, une page qui
# n'existe pas. Ce que le portail publie déjà est renvoyé vers sa page ; le reste vers le
# dépôt s'il est annoncé, et à défaut le lien cède la place au chemin, en clair.
PAGES_DU_PORTAIL = {
    "docs/ETHIQUE.md": "/charte",
    "docs/METHODOLOGIE.md": "/methodologie",
    "docs/TAXONOMIE.md": "/taxonomie",
    "prompts": "/prompt",
    "prompts/analyse": "/prompt",
    "corpus": "/calibration",
    "corpus/RESULTATS.md": "/calibration",
}


@lru_cache
def _rendu() -> MarkdownIt:
    # « commonmark » plutôt que le préréglage permissif : pas de HTML brut interprété
    # depuis un fichier de documentation, même si celui-ci vient du dépôt.
    return MarkdownIt("commonmark").enable("table")


def _reecrire_liens(jetons: list, depot_fichiers: str, dossier: str, prefixe: str) -> None:
    """Recale les liens relatifs d'un document du dépôt sur les adresses du portail.

    Les liens absolus, les ancres et les adresses de courriel sont laissés tels quels."""
    neutraliser = 0
    for jeton in jetons:
        if jeton.children:
            _reecrire_liens(jeton.children, depot_fichiers, dossier, prefixe)
        if jeton.type == "link_close" and neutraliser:
            jeton.tag = "code"
            neutraliser -= 1
            continue
        if jeton.type != "link_open":
            continue
        cible = jeton.attrGet("href") or ""
        # « mailto: », « https: » : le schéma se reconnaît avant la première barre.
        if not cible or cible.startswith(("/", "#")) or ":" in cible.split("/")[0]:
            continue
        barre = cible.endswith("/")
        chemin = posixpath.normpath(posixpath.join(dossier, cible.split("#")[0]))
        ancre = cible.partition("#")[2]
        if chemin in PAGES_DU_PORTAIL:
            jeton.attrSet("href",
                          prefixe + PAGES_DU_PORTAIL[chemin] + (f"#{ancre}" if ancre else ""))
        elif depot_fichiers:
            jeton.attrSet("href", f"{depot_fichiers.rstrip('/')}/{chemin}{'/' if barre else ''}"
                                  + (f"#{ancre}" if ancre else ""))
        else:
            jeton.tag = "code"
            jeton.attrs = {}
            neutraliser += 1


@lru_cache
def markdown_publie(chemin: str, depot_fichiers: str = "", prefixe: str = "") -> dict:
    """Rend un fichier markdown du dépôt en HTML. `chemin` part de la racine du dépôt.

    Le portail ne recopie aucun de ces textes : il sert le fichier que le moteur applique.
    Un document qui ne serait pas publié ici resterait une promesse invérifiable."""
    texte = (trouver_racine() / chemin).read_text(encoding="utf-8")
    premiere = next((l for l in texte.splitlines() if l.startswith("# ")), "# Document")
    corps = texte.split("\n", 1)[1] if texte.startswith("# ") else texte
    md = _rendu()
    jetons = md.parse(corps)
    _reecrire_liens(jetons, depot_fichiers, posixpath.dirname(chemin), prefixe)
    return {"titre": premiere[2:].strip(), "html": md.renderer.render(jetons, md.options, {})}


def document(nom: str, depot_fichiers: str = "", prefixe: str = "") -> dict:
    """Rend docs/<NOM>.md en HTML. Retourne {titre, html}."""
    return markdown_publie(f"docs/{nom}.md", depot_fichiers, prefixe)


def versions_prompt() -> list[str]:
    """Les versions de prompt présentes dans le dépôt, de la plus ancienne à la plus récente."""
    return prompt.versions_disponibles()


def prompt_publie(version: str, depot_fichiers: str = "", prefixe: str = "") -> dict:
    """Rend le fichier de prompt d'une version donnée, tel qu'il est versionné."""
    return markdown_publie(f"prompts/analyse/v{version}.md", depot_fichiers, prefixe)


def calibration(depot_fichiers: str = "", prefixe: str = "") -> dict:
    """Rend les résultats de la dernière passe de calibration.

    Seuls les résultats sont publiés : le corpus contient des captures de pages réelles,
    qui appartiennent à leurs auteurs et n'ont pas à être rediffusées ici."""
    return markdown_publie("corpus/RESULTATS.md", depot_fichiers, prefixe)


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
    for rang, dossier in enumerate(d.strip() for d in dossiers.split(",")):
        if not dossier:
            continue
        base = Path(dossier)
        if not base.is_dir():
            continue
        for chemin in base.glob("lynceus-extension-v*.zip"):
            m = _MOTIF_PAQUET.match(chemin.name)
            if m:
                # À version égale, le dossier cité en premier gagne : le rang est stocké
                # en négatif pour que le même `max` tranche les deux critères. Sans lui,
                # l'égalité se réglait sur l'ordre alphabétique des chemins, ce qui
                # revenait à laisser le hasard décider entre un zip déposé à la main et
                # celui de l'image.
                candidats.append((tuple(int(g) for g in m.groups()), -rang, chemin))
    if not candidats:
        return None

    version, _, chemin = max(candidats)
    return {
        "version": ".".join(str(n) for n in version),
        "nom": chemin.name,
        "chemin": chemin,
        "taille_ko": round(chemin.stat().st_size / 1024),
    }
