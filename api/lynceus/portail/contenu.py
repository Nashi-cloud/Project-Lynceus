"""Contenu du portail — lu dans les fichiers que le moteur applique réellement.

Rien n'est recopié à la main. La taxonomie affichée est celle que le prompt injecte, les
pondérations affichées sont celles que le serveur calcule, la charte affichée est le
fichier du dépôt. C'est ce qui rend l'engagement de transparence (charte §2) vérifiable :
une page du site ne peut pas diverger de ce que le code fait, elle en est extraite.
"""

from __future__ import annotations

import hashlib
import posixpath
import re
from functools import lru_cache
from pathlib import Path

from markdown_it import MarkdownIt

from ..config import trouver_racine
from ..moteur import notation, prompt
from . import i18n
from .i18n import LANGUE_SOURCE, N_

_MOTIF_FAMILLE = re.compile(r"^##\s+Famille\s+([A-Z])\s+—\s+(.+?)\s*$", re.MULTILINE)

GRAVITES = {"haute": N_("Gravité haute"), "moyenne": N_("Gravité moyenne"),
            "faible": N_("Gravité faible")}

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


def fichier_du_depot(chemin: str) -> Path:
    """Résout un chemin relatif à la racine du dépôt, et refuse d'en sortir.

    Aujourd'hui aucun de ces chemins ne vient d'une requête : les noms de documents sont
    des littéraux, et la langue ne peut valoir que l'un des codes servis. L'analyse
    statique le signale pourtant, et elle a raison de le faire : « ce n'est pas atteignable
    aujourd'hui » est le raisonnement qui vieillit le plus mal. Le jour où quelqu'un ajoute
    une route qui prend un nom de document dans l'URL, la traversée devient réelle et
    personne ne se souvient de cette conversation.

    La garde coûte deux lignes et rend ce cas impossible par construction.

    À l'attention du relecteur qui verra des alertes écartées ici : CodeQL signale
    `py/path-injection` sur cette fonction et ses deux appelants, et continue de le faire.
    La valeur venue d'une requête est pourtant filtrée par `i18n.code_servi`, qui ne rend
    qu'une constante du programme, et le chemin obtenu est vérifié ci-dessous. L'analyse ne
    reconnaît ni l'une ni l'autre de ces barrières. Deux réécritures ont été faites pour
    elle, toutes deux gardées parce qu'elles ont amélioré le code ; la troisième aurait été
    de la déformation. Les alertes sont donc écartées, avec cette explication."""
    racine = trouver_racine().resolve()
    cible = (racine / chemin).resolve()
    if not cible.is_relative_to(racine):
        raise ValueError(f"chemin hors du dépôt : {chemin}")
    return cible


@lru_cache
def markdown_publie(chemin: str, depot_fichiers: str = "", prefixe: str = "") -> dict:
    """Rend un fichier markdown du dépôt en HTML. `chemin` part de la racine du dépôt.

    Le portail ne recopie aucun de ces textes : il sert le fichier que le moteur applique.
    Un document qui ne serait pas publié ici resterait une promesse invérifiable."""
    texte = fichier_du_depot(chemin).read_text(encoding="utf-8")
    premiere = next((l for l in texte.splitlines() if l.startswith("# ")), "# Document")
    corps = texte.split("\n", 1)[1] if texte.startswith("# ") else texte
    md = _rendu()
    jetons = md.parse(corps)
    _reecrire_liens(jetons, depot_fichiers, posixpath.dirname(chemin), prefixe)
    return {"titre": premiere[2:].strip(), "html": md.renderer.render(jetons, md.options, {})}


def publier(source: str, depot_fichiers: str = "", prefixe: str = "", langue: str = "") -> dict:
    """Rend un document du dépôt, dans la langue demandée si elle existe.

    Une traduction vit dans <dossier>/<langue>/<fichier>. À défaut, l'original est servi tel
    quel : mieux vaut le texte qui engage le projet, dans sa langue, qu'une page vide. Le
    drapeau `traduit` permet à la page de le dire au lecteur au lieu de le laisser deviner."""
    code = i18n.code_servi(langue)
    if code:
        traduction = chemin_traduction(source, code)
        if fichier_du_depot(traduction).exists():
            return {**markdown_publie(traduction, depot_fichiers, prefixe), "traduit": True}
    return {**markdown_publie(source, depot_fichiers, prefixe), "traduit": not langue}


def document(nom: str, depot_fichiers: str = "", prefixe: str = "", langue: str = "") -> dict:
    """Rend docs/<NOM>.md en HTML. Retourne {titre, html, traduit}."""
    return publier(f"docs/{nom}.md", depot_fichiers, prefixe, langue)


# Les documents du dépôt que le portail publie tels quels. Une traduction manquante ici se
# voit à l'écran, pas dans le code : d'où cet inventaire, seul endroit à tenir à jour quand
# un document devient publiable.
DOCUMENTS_PUBLIES = [
    ("docs/ETHIQUE.md", "/charte"),
    ("docs/METHODOLOGIE.md", "/methodologie"),
    ("docs/TAXONOMIE.md", "/taxonomie"),
    ("corpus/RESULTATS.md", "/calibration"),
]

# Deux documents du dépôt ne sont pas publiés par le portail mais se traduisent quand même :
# personne ne lira la conformité ou l'architecture en français par hasard. Ils suivent la
# même règle et le même contrôle de fraîcheur que les autres.
DOCUMENTS_NON_PUBLIES = [
    "docs/ARCHITECTURE.md",
    "docs/CONFORMITE.md",
    "docs/IA-GENERATIVE.md",
]

# La façade du dépôt : ce qu'on lit en arrivant sur la forge. Là, l'anglais est l'original,
# parce qu'un visiteur qui ne peut pas lire la première page ne lira pas la deuxième. Les
# textes qui engagent le projet gardent au contraire le français pour original : là où un
# fichier est une porte, l'anglais est à la porte ; là où un fichier fait loi, le français
# reste l'original.
LANGUE_FACADE = "en"
FACADE = [
    "README.md",
    "CONTRIBUTING.md",
    "INSTALLATION.md",
    "AUTHORS.md",
    "SECURITY.md",
    "api/README.md",
    "api/DEPLOIEMENT.md",
    "extension/README.md",
    "extension/PUBLICATION.md",
    "corpus/README.md",
    "corpus/specimens/README.md",
]

_EMPREINTE = re.compile(r"traduit-de:\s*(\S+)\s+sha256:([0-9a-f]+)")


def _empreinte(chemin: Path) -> str:
    """Les 16 premiers caractères du sha256 : assez pour repérer une modification, assez
    court pour tenir dans une ligne de fichier sans la rendre illisible."""
    return hashlib.sha256(chemin.read_bytes()).hexdigest()[:16]


def chemin_traduction(source: str, langue: str) -> str:
    """docs/ETHIQUE.md en anglais devient docs/en/ETHIQUE.md."""
    dossier, _, fichier = source.rpartition("/")
    return f"{dossier}/{langue}/{fichier}" if dossier else f"{langue}/{fichier}"


def chemin_traduction_facade(source: str, langue: str) -> str:
    """README.md en français devient README.fr.md.

    Un sous-dossier de langue conviendrait mal ici : une forge affiche le README du dossier
    qu'on ouvre, et le déplacer reviendrait à n'en plus avoir."""
    base, _, extension = source.rpartition(".")
    return f"{base}.{langue}.{extension}"


def paires_traduites(langue: str) -> list[tuple[str, str]]:
    """Chaque original suivi et le fichier censé le traduire dans cette langue.

    Les deux conventions se rejoignent ici, et chacune s'efface quand la langue demandée est
    déjà celle de son original : demander l'état du français ne concerne que la façade,
    demander celui de l'anglais ne concerne que les textes qui engagent le projet."""
    paires = []
    if langue != LANGUE_SOURCE:
        sources = [chemin for chemin, _ in DOCUMENTS_PUBLIES] + DOCUMENTS_NON_PUBLIES
        versions = versions_disponibles_du_prompt()
        if versions:
            sources.append(f"prompts/analyse/v{versions[-1]}.md")
        paires += [(source, chemin_traduction(source, langue)) for source in sources]
    if langue != LANGUE_FACADE:
        paires += [(source, chemin_traduction_facade(source, langue)) for source in FACADE]
    return paires


def etat_traductions(langue: str) -> list[dict]:
    """Où en est chaque document suivi, dans une langue donnée.

    Quatre états, et un seul est un défaut : « en retard » veut dire que l'original a changé
    depuis la traduction, donc que le dépôt porte deux textes qui ne disent plus la même
    chose. « manquante » est un travail à faire, pas une erreur."""
    racine = trouver_racine()
    inventaire = []
    for source, traduction in paires_traduites(langue):
        fichier = racine / traduction
        if not fichier.exists():
            etat = "manquante"
        else:
            # Les premières lignes seulement : plus bas, un document peut très bien
            # montrer la forme du marqueur en exemple, et CONTRIBUTING le fait.
            tete = "\n".join(fichier.read_text(encoding="utf-8").splitlines()[:6])
            trouve = _EMPREINTE.search(tete)
            if not trouve:
                etat = "sans empreinte"
            elif trouve.group(2) != _empreinte(racine / source):
                etat = "en retard"
            else:
                etat = "à jour"
        inventaire.append({"source": source, "traduction": traduction, "etat": etat})
    return inventaire


def versions_disponibles_du_prompt() -> list[str]:
    return prompt.versions_disponibles()


def versions_prompt() -> list[str]:
    """Les versions de prompt présentes dans le dépôt, de la plus ancienne à la plus récente."""
    return prompt.versions_disponibles()


def prompt_publie(version: str, depot_fichiers: str = "", prefixe: str = "",
                  langue: str = "") -> dict:
    """Rend le fichier de prompt d'une version donnée, tel qu'il est versionné.

    Une traduction n'est jamais envoyée au modèle : elle sert à lire ce qu'on lui demande.
    Traduire le prompt appliqué changerait les analyses, qui sont calibrées en français."""
    return publier(f"prompts/analyse/v{version}.md", depot_fichiers, prefixe, langue)


def calibration(depot_fichiers: str = "", prefixe: str = "", langue: str = "") -> dict:
    """Rend les résultats de la dernière passe de calibration.

    Seuls les résultats sont publiés : le corpus contient des captures de pages réelles,
    qui appartiennent à leurs auteurs et n'ont pas à être rediffusées ici."""
    return publier("corpus/RESULTATS.md", depot_fichiers, prefixe, langue)


# Motifs tolérants, pour lire un référentiel traduit. Ils ne servent qu'à l'affichage :
# la gravité, l'ordre et la liste des ids restent ceux du fichier français, seul appliqué.
_FAMILLE_TRADUITE = re.compile(r"^##\s+(?:Famille|Family)\s+([A-Z])\s+[—-]\s+(.+?)\s*$",
                               re.MULTILINE)
_TECHNIQUE_TRADUITE = re.compile(r"^###\s+`([a-z_]+)`\s+[—-]\s+(.+?)\s*(?:·.*)?$", re.MULTILINE)


@lru_cache
def _libelles_traduits(langue: str) -> tuple[dict, dict]:
    """(familles, techniques) d'un référentiel traduit, ou deux dictionnaires vides.

    On ne reprend que les libellés et les définitions : un référentiel traduit qui
    ajouterait ou renommerait un id ne serait pas suivi, et c'est voulu. La liste fermée
    est celle du fichier français, que le serveur valide et que le modèle reçoit."""
    chemin = trouver_racine() / chemin_traduction("docs/TAXONOMIE.md", langue)
    if not langue or not chemin.exists():
        return {}, {}
    texte = chemin.read_text(encoding="utf-8")
    familles = {m.group(1): m.group(2) for m in _FAMILLE_TRADUITE.finditer(texte)}
    techniques = {}
    trouvees = list(_TECHNIQUE_TRADUITE.finditer(texte))
    for i, m in enumerate(trouvees):
        fin = trouvees[i + 1].start() if i + 1 < len(trouvees) else len(texte)
        bloc = texte[m.end():fin]
        definition = next((l.strip() for l in bloc.splitlines() if l.strip()), "")
        techniques[m.group(1)] = {"nom": m.group(2), "definition": definition}
    return familles, techniques


@lru_cache
def taxonomie_par_famille(langue: str = "") -> list[dict]:
    """Les techniques du référentiel, regroupées par famille.

    Les identifiants et gravités viennent de `prompt.charger_taxonomie()` — donc du même
    parseur que celui qui alimente le modèle. Les familles, elles, ne servent qu'à
    l'affichage : elles n'existent pas dans le référentiel technique. Une traduction ne
    remplace que ce qui s'affiche."""
    texte = (trouver_racine() / "docs" / "TAXONOMIE.md").read_text(encoding="utf-8")
    familles_traduites, techniques_traduites = _libelles_traduits(langue)
    techniques = {tid: {**entree, **techniques_traduites.get(tid, {})}
                  for tid, entree in prompt.charger_taxonomie().items()}

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
        familles.append({"lettre": lettre, "nom": familles_traduites.get(lettre, nom),
                         "techniques": membres})

    orphelines = [t for f in familles for t in f["techniques"]]
    if len(orphelines) != len(techniques):  # pragma: no cover — filet contre un remaniement du fichier
        manquantes = sorted(set(techniques) - {t["id"] for t in orphelines})
        familles.append({"lettre": "?", "nom": "Hors famille",
                         "techniques": [{"id": tid, **techniques[tid]} for tid in manquantes]})
    return familles


def taxonomie_traduite(langue: str) -> bool:
    """Le référentiel affiché est-il celui de la langue demandée ?"""
    return bool(_libelles_traduits(langue)[1])


def nb_techniques() -> int:
    return len(prompt.charger_taxonomie())


def ponderations() -> list[dict]:
    """Les poids réellement appliqués par le serveur, dans l'ordre décroissant."""
    libelles = {
        "sources": N_("Qualité du sourçage"),
        "factualite": N_("Rigueur factuelle"),
        "ton": N_("Registre et procédés"),
        "transparence": N_("Transparence de l'éditeur"),
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
