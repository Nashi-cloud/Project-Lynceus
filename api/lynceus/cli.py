"""CLI Lynceus : client de l'API pour tester, analyser et calibrer.

  lynceus analyser https://exemple.fr/article
  lynceus analyser article.md --url https://exemple.fr/article
  lynceus lookup https://exemple.fr/article
  lynceus calibrer ../corpus/corpus.yaml
"""

from __future__ import annotations

import contextlib
import json
from enum import Enum
import os
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import sys
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .normalisation import hacher_contenu

app = typer.Typer(help="Lynceus, la vigie de l'information.", no_args_is_help=True)
console = Console()
# Tout ce qui n'est pas une donnée exploitable part sur la sortie d'erreur : titres,
# avertissements, explications. « lynceus env recette > .env » écrit alors un fichier
# directement valide, pendant que l'humain garde ses explications à l'écran.
aide = Console(stderr=True)

COULEURS_GRADE = {"A": "green", "B": "green3", "C": "yellow", "D": "dark_orange", "E": "red"}


def _api() -> str:
    return os.environ.get("LYNCEUS_API_URL", "http://localhost:8000").rstrip("/")


def _erreur_http(reponse: httpx.Response) -> str:
    """Le détail de l'erreur API, en clair (sinon le corps brut)."""
    try:
        return reponse.json().get("detail", reponse.text)
    except Exception:
        return reponse.text


def _afficher_carte(carte: dict, en_cache: bool | None = None) -> None:
    note = carte["note"]
    couleur = COULEURS_GRADE.get(note["grade"], "white")
    entete = (
        f"[bold {couleur}]Indice {note['grade']}[/] · score {note['score']}/100 · "
        f"catégorie : [bold]{carte['categorie']}[/] · confiance de l'analyse : {note['confiance']:.0%}"
    )
    if en_cache:
        entete += "  [dim](déjà dans l'annuaire)[/dim]"
    console.print(Panel(entete, title=carte.get("titre") or carte.get("url") or "Analyse Lynceus"))

    table = Table(show_header=True, header_style="bold")
    table.add_column("Dimension")
    table.add_column("Score", justify="right")
    table.add_column("Détail", overflow="fold")
    for nom in ("sources", "factualite", "ton", "transparence"):
        d = carte["dimensions"][nom]
        table.add_row(nom, str(d["score"]), d["detail"])
    console.print(table)

    if carte["techniques_detectees"]:
        console.print("\n[bold]Techniques relevées :[/bold]")
        for t in carte["techniques_detectees"]:
            console.print(f"  • [bold]{t['id']}[/bold] (gravité {t['gravite']})")
            console.print(f"    [dim]« {t['extrait']} »[/dim]")
            console.print(f"    {t['explication']}")
    else:
        console.print("\n[green]Aucune technique de manipulation relevée.[/green]")

    if carte["points_positifs"]:
        console.print("\n[bold]Points positifs :[/bold]")
        for pt in carte["points_positifs"]:
            console.print(f"  ✓ {pt}")

    console.print("\n[bold]Questions à se poser :[/bold]")
    for q in carte["questions_a_se_poser"]:
        console.print(f"  ? {q}")

    console.print(f"\n[italic]{carte['resume_neutre']}[/italic]")
    for avert in carte.get("avertissements", []):
        console.print(f"[dim]⚠ {avert}[/dim]")
    meta = carte["meta"]
    console.print(f"[dim]{meta['modele']} · prompt v{meta['prompt_version']} · {meta['analyse_le']}[/dim]")


@app.command()
def analyser(
    cible: str = typer.Argument(help="URL à analyser, chemin d'un fichier Markdown, ou - pour lire l'entrée standard"),
    url: str = typer.Option(None, help="URL d'origine si la cible est un fichier"),
    titre: str = typer.Option(None, help="Titre de la page"),
):
    """Analyse une page (URL) ou un contenu local (fichier .md) via l'API."""
    corps: dict = {"titre": titre}
    if cible == "-":
        corps["contenu_markdown"] = sys.stdin.read()
        corps["url"] = url
    elif Path(cible).is_file():
        corps["contenu_markdown"] = Path(cible).read_text(encoding="utf-8")
        corps["url"] = url
    elif cible.startswith(("http://", "https://")):
        corps["url"] = cible
    else:
        console.print(f"[red]Cible invalide :[/red] {cible} (URL http(s) ou fichier existant attendu)")
        raise typer.Exit(2)

    with console.status("Analyse en cours…"):
        reponse = httpx.post(f"{_api()}/v1/analyses", json=corps, timeout=300)
    if reponse.status_code != 200:
        console.print(f"[red]Erreur {reponse.status_code} :[/red] {_erreur_http(reponse)}")
        raise typer.Exit(1)
    donnees = reponse.json()
    _afficher_carte(donnees["carte"], en_cache=donnees.get("en_cache"))
    if donnees.get("detections_rejetees"):
        console.print(f"[dim]Détections écartées par le serveur : {donnees['detections_rejetees']}[/dim]")


@app.command()
def lookup(url: str):
    """Consulte l'annuaire sans déclencher d'analyse."""
    reponse = httpx.get(f"{_api()}/v1/lookup", params={"url": url}, timeout=30)
    if reponse.status_code != 200:
        console.print(f"[red]Erreur {reponse.status_code} :[/red] {_erreur_http(reponse)}")
        raise typer.Exit(1)
    donnees = reponse.json()
    if donnees["statut"] == "connue":
        _afficher_carte(donnees["carte"], en_cache=True)
    else:
        console.print("Page [yellow]inconnue[/yellow] de l'annuaire.")
    if donnees.get("domaine"):
        d = donnees["domaine"]
        console.print(
            f"[dim]Domaine {d['domaine']} : {d['nb_analyses']} analyse(s), "
            f"score moyen {d['score_moyen']}, grades {d['distribution_grades']}[/dim]"
        )


@app.command()
def calibrer(
    fichier: Path = typer.Argument(help="corpus YAML (cf. corpus/README.md)"),
    json_sortie: Path = typer.Option(None, "--json", help="écrire le rapport détaillé en JSON"),
    filtre: str = typer.Option(None, "--filtre", help="ne traiter que les entrées dont le titre/chemin contient ce texte"),
    parallele: int = typer.Option(4, "--parallele", help="cas analysés de front (le serveur plafonne aussi de son côté)"),
    ecrire: bool = typer.Option(False, "--ecrire", help="enregistrer la passe et réengendrer le tableau publié"),
):
    """Passe le corpus de calibration et vérifie catégories, grades et techniques.

    Chaque entrée porte soit `fichier` (spécimen figé du dépôt, reproductible et hors ligne),
    soit `url` (page réelle). Les écarts sont classés : un faux positif sur une technique
    interdite ou une erreur de catégorie sont des échecs GRAVES ; un grade hors fourchette
    d'un cran est signalé comme un écart mineur.
    """
    import yaml

    entrees = yaml.safe_load(fichier.read_text(encoding="utf-8")) or []
    if not isinstance(entrees, list):
        console.print("[red]Le corpus doit être une liste YAML.[/red]")
        raise typer.Exit(2)
    if filtre:
        # Titre ET chemin, pas l'un ou l'autre : « --filtre satire » doit trouver le
        # spécimen dont le nom de fichier porte ce mot, même si son titre ne le dit pas.
        def _porte(entree: dict) -> bool:
            champs = (entree.get("titre"), entree.get("fichier"), entree.get("capture"), entree.get("url"))
            return any(filtre.lower() in str(c).lower() for c in champs if c)

        entrees = [e for e in entrees if _porte(e)]

    racine = fichier.parent
    table = Table(show_header=True, header_style="bold")
    for colonne in ("Cas", "Attendu", "Obtenu", "Verdict"):
        table.add_column(colonne, overflow="fold")

    rapport, graves, mineurs, ignores = [], 0, 0, 0

    def mesurer(entree: dict) -> dict:
        """Analyse un cas et le compare à ses attentes. Ne lève pas : tout écart, y compris
        une panne réseau, revient sous forme de résultat pour figurer au rapport."""
        etiquette = entree.get("titre") or entree.get("fichier") or entree.get("url") or "(sans titre)"
        try:
            corps = _corps_demande(entree, racine)
        except CaptureManquante as exc:
            return {"etiquette": etiquette, "ignore": str(exc)}
        if corps is None:
            return {"etiquette": etiquette, "erreur": "entrée invalide (ni fichier, ni capture, ni url)"}

        # Le serveur limite le débit par adresse : une passe parallèle le heurte forcément.
        # On patiente et on reprend plutôt que de déclarer le cas en échec, ce qui
        # signalerait un problème de qualité là où il n'y a qu'une file d'attente.
        for tentative in range(6):
            try:
                reponse = httpx.post(f"{_api()}/v1/analyses", json=corps, timeout=600)
            except httpx.HTTPError as exc:
                return {"etiquette": etiquette, "erreur": f"réseau : {exc}"}
            if reponse.status_code != 429:
                break
            time.sleep(min(2 ** tentative, 20))
        if reponse.status_code != 200:
            return {"etiquette": etiquette, "erreur": f"HTTP {reponse.status_code} : {_erreur_http(reponse)[:80]}"}

        donnees = reponse.json()
        carte = donnees["carte"]
        ecarts = _ecarts(entree, carte)
        return {
            "etiquette": etiquette, "entree": entree, "carte": carte, "ecarts": ecarts,
            "en_cache": bool(donnees.get("en_cache")),
            "graves": [_phrase_console(e) for e in ecarts if e["gravite"] == "grave"],
            "mineurs": [_phrase_console(e) for e in ecarts if e["gravite"] == "mineur"],
        }

    # Les analyses sont indépendantes : les mener de front divise l'attente d'autant.
    # Le serveur plafonne de toute façon sa propre concurrence, inutile de le noyer.
    with console.status(f"Calibration de {len(entrees)} cas ({parallele} de front)…"):
        with ThreadPoolExecutor(max_workers=max(1, parallele)) as pool:
            resultats = list(pool.map(mesurer, entrees))

    for resultat in resultats:
        etiquette = resultat["etiquette"]
        if "ignore" in resultat:
            ignores += 1
            table.add_row(etiquette, "-", "-", f"[yellow]ignoré : {resultat['ignore']}[/yellow]")
            continue
        if "erreur" in resultat:
            graves += 1
            table.add_row(etiquette, "-", "-", f"[red]{resultat['erreur']}[/red]")
            continue

        entree, carte = resultat["entree"], resultat["carte"]
        ecarts_graves, ecarts_mineurs = resultat["graves"], resultat["mineurs"]
        graves += bool(ecarts_graves)
        mineurs += bool(ecarts_mineurs and not ecarts_graves)

        if ecarts_graves:
            verdict = "[red]" + " · ".join(ecarts_graves) + "[/red]"
        elif ecarts_mineurs:
            verdict = "[yellow]" + " · ".join(ecarts_mineurs) + "[/yellow]"
        else:
            verdict = "[green]OK[/green]"

        attendu = f"{entree.get('categorie_attendue') or entree.get('categories_acceptables', '?')} {entree.get('grade_attendu', '')}"
        obtenu = f"{carte['categorie']} {carte['note']['grade']} ({carte['note']['score']})"
        table.add_row(etiquette, attendu, obtenu, verdict)
        rapport.append({
            "cas": etiquette,
            "attendu": {k: v for k, v in entree.items()
                        if k.endswith(("_attendue", "_attendu", "_attendues", "_interdites", "_min", "_acceptables"))},
            "obtenu": {
                "categorie": carte["categorie"],
                "grade": carte["note"]["grade"],
                "score": carte["note"]["score"],
                "confiance": carte["note"]["confiance"],
                "techniques": [t["id"] for t in carte["techniques_detectees"]],
            },
            "ecarts_graves": ecarts_graves,
            "ecarts_mineurs": ecarts_mineurs,
        })

    console.print(table)
    total = len(entrees)
    mesures = total - ignores
    conformes = mesures - graves - mineurs
    console.print(
        f"\n[bold]{conformes}/{mesures} conformes[/bold] · "
        f"[yellow]{mineurs} écart(s) mineur(s)[/yellow] · [red]{graves} échec(s) grave(s)[/red]"
        + (f" · [dim]{ignores} cas ignoré(s) faute de capture locale[/dim]" if ignores else "")
    )
    if rapport:
        modele = rapport[0] and httpx.get(f"{_api()}/v1/meta", timeout=30).json()
        console.print(f"[dim]Instance : {modele['modele']} · prompt v{modele['prompt_version']}[/dim]")

    if json_sortie:
        json_sortie.write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
        console.print(f"[dim]Rapport détaillé écrit dans {json_sortie}[/dim]")

    if ecrire:
        if filtre:
            console.print("[red]--ecrire refusé avec --filtre : un tableau publié qui ne "
                          "porterait que sur une partie du corpus tromperait son lecteur.[/red]")
            raise typer.Exit(2)
        _publier_la_passe(fichier, entrees, resultats, conformes, mesures)

    if graves:
        raise typer.Exit(1)


def _publier_la_passe(corpus: Path, entrees: list, resultats: list, conformes: int, mesures: int) -> None:
    """Ajoute la passe au journal, puis réengendre le tableau publié dans les deux langues.

    C'est ici que le chiffre publié cesse d'être déclaratif. Tant que ce tableau s'écrivait
    à la main, rien n'empêchait de faire passer l'estampille d'une version de prompt à la
    suivante sans avoir relancé une seule analyse."""
    from datetime import date

    from . import calibration

    meta = httpx.get(f"{_api()}/v1/meta", timeout=30).json()
    cas = []
    for entree, resultat in zip(entrees, resultats):
        identifiant = entree.get("fichier") or entree.get("capture") or entree.get("url") or resultat["etiquette"]
        enregistrement = {
            "id": identifiant,
            "titre": entree.get("titre") or identifiant,
            "titre_en": entree.get("titre_en") or entree.get("titre") or identifiant,
        }
        if "carte" in resultat:
            carte = resultat["carte"]
            enregistrement |= {
                "categorie": carte["categorie"],
                "grade": carte["note"]["grade"],
                "score": carte["note"]["score"],
                "techniques": sorted(t["id"] for t in carte["techniques_detectees"]),
                "ecarts": resultat["ecarts"],
            }
        else:
            # Un cas non mesuré figure quand même : l'effacer du tableau donnerait un corpus
            # qui rétrécit sans qu'on sache pourquoi.
            detail = resultat.get("ignore") or resultat.get("erreur") or "raison inconnue"
            enregistrement["ecarts"] = [{"gravite": "grave", "type": "non_mesure", "detail": detail}]
        cas.append(enregistrement)

    # Une passe intégralement resservie depuis l'annuaire n'est pas un nouveau tirage : elle
    # rejoue une mesure déjà faite. Le compter permet de ne pas prendre trois copies d'une
    # même analyse pour trois passes indépendantes.
    depuis_cache = sum(1 for r in resultats if r.get("en_cache"))
    passe = {
        "date": date.today().isoformat(),
        "depuis_cache": depuis_cache,
        "modele": meta["modele"],
        "fournisseur": meta.get("fournisseur") or "",
        "temperature": meta.get("temperature", 0),
        "prompt_version": meta["prompt_version"],
        "corpus": calibration.empreinte(corpus),
        "conformes": conformes,
        "mesures": mesures,
        "cas": cas,
    }
    journal = corpus.parent / "passes.jsonl"
    calibration.enregistrer(journal, passe)
    console.print(f"[dim]Passe enregistrée dans {journal}[/dim]")

    for chemin, langue in _rapports_publies(corpus.parent):
        if not chemin.is_file():
            continue
        liste = calibration.passes_courantes(journal, meta["prompt_version"])
        if calibration.remplacer_bloc(chemin, calibration.bloc(liste, langue)):
            console.print(f"[dim]Tableau réengendré dans {chemin}[/dim]")
    _restamper_traductions(corpus.parent)


def _rapports_publies(dossier: Path) -> list[tuple[Path, str]]:
    """Le rapport dans chaque langue servie. L'original en premier : les traductions
    portent son empreinte, et il faut donc l'écrire avant de les réestampiller."""
    from .portail.i18n import LANGUE_SOURCE, LANGUES

    rapports = [(dossier / "RESULTATS.md", LANGUE_SOURCE)]
    rapports += [(dossier / langue / "RESULTATS.md", langue)
                 for langue in LANGUES if langue != LANGUE_SOURCE]
    return rapports


def _restamper_traductions(dossier: Path) -> None:
    """Le tableau vient de changer dans les deux langues : l'empreinte doit suivre.

    Sans ça, `verifier.sh` déclarerait la traduction en retard alors qu'elle vient d'être
    réengendrée depuis les mêmes mesures."""
    import re

    from . import calibration
    from .portail.i18n import LANGUE_SOURCE, LANGUES

    original = dossier / "RESULTATS.md"
    if not original.is_file():
        return
    empreinte = calibration.empreinte(original)
    for langue in LANGUES:
        if langue == LANGUE_SOURCE:
            continue
        traduction = dossier / langue / "RESULTATS.md"
        if not traduction.is_file():
            continue
        texte = traduction.read_text(encoding="utf-8")
        remplace = re.sub(r"(traduit-de:\s*\S+\s+sha256:)[0-9a-f]+", r"\g<1>" + empreinte,
                          texte, count=1)
        if remplace != texte:
            traduction.write_text(remplace, encoding="utf-8")


class CaptureManquante(Exception):
    """Capture absente ou divergente : le cas ne peut pas être mesuré de façon fiable."""


def _lire_capture(entree: dict, racine: Path) -> str:
    """Lit une capture locale et vérifie son empreinte.

    Les captures de pages réelles ne sont pas versionnées (droit d'auteur) : seul le
    manifeste l'est. L'empreinte garantit que tout le monde mesure bien le même contenu,
    sans elle, deux contributeurs compareraient des résultats incomparables."""
    chemin = racine / entree["capture"]
    if not chemin.is_file():
        raise CaptureManquante(
            f"capture absente : {entree['capture']}, la recréer depuis {entree.get('url', '?')} "
            "(voir corpus/README.md)"
        )
    contenu = chemin.read_text(encoding="utf-8")
    attendu = entree.get("content_hash")
    if attendu:
        reel = hacher_contenu(contenu)
        if reel != attendu:
            raise CaptureManquante(
                f"capture divergente : {entree['capture']}, empreinte {reel[:12]}… "
                f"au lieu de {attendu[:12]}…. La page a changé depuis la capture de référence : "
                "recapturer et réexaminer les attentes plutôt que de les ajuster à l'aveugle."
            )
    return contenu


def _corps_demande(entree: dict, racine: Path) -> dict | None:
    """Construit le corps POST /v1/analyses depuis une entrée de corpus."""
    if entree.get("capture"):
        return {
            "contenu_markdown": _lire_capture(entree, racine),
            "titre": entree.get("titre"),
            "url": entree.get("url"),
            "langue": entree.get("langue", "fr"),
        }
    if entree.get("fichier"):
        chemin = racine / entree["fichier"]
        contenu = chemin.read_text(encoding="utf-8")
        # L'en-tête YAML du spécimen documente le cas : il ne fait pas partie du contenu analysé.
        if contenu.startswith("---"):
            fin = contenu.find("\n---", 3)
            if fin != -1:
                contenu = contenu[fin + 4:].lstrip()
        return {
            "contenu_markdown": contenu,
            "titre": entree.get("titre"),
            "url": entree.get("url"),
            "langue": entree.get("langue", "fr"),
        }
    if entree.get("url"):
        return {"url": entree["url"], "titre": entree.get("titre")}
    return None


def _ecarts(entree: dict, carte: dict) -> list[dict]:
    """Compare une carte à ses attentes et rend les écarts sous forme de faits.

    Des faits, et non des phrases : le rapport de calibration est publié en français et en
    anglais, et une phrase française ne s'y traduirait pas. Chaque écart porte sa gravité,
    son type, et ce qu'il fallait comparer."""
    ecarts = []
    grades = ["A", "B", "C", "D", "E"]

    # `categorie_attendue` (exacte) ou `categories_acceptables` (liste). Certains contenus
    # relèvent légitimement de plusieurs catégories : un article pseudo-médical qui vend un
    # produit est à la fois pseudo_science et publicite_sponsorise. Exiger une catégorie
    # unique testerait alors un choix arbitraire, pas la qualité de l'analyse.
    acceptables = entree.get("categories_acceptables")
    attendue = entree.get("categorie_attendue")
    if acceptables:
        if carte["categorie"] not in acceptables:
            ecarts.append({"gravite": "grave", "type": "categorie",
                           "obtenu": carte["categorie"], "attendu": acceptables})
    elif attendue and carte["categorie"] != attendue:
        ecarts.append({"gravite": "grave", "type": "categorie",
                       "obtenu": carte["categorie"], "attendu": attendue})

    fourchette = entree.get("grade_attendu")
    if fourchette and carte["note"]["grade"] not in fourchette:
        obtenu = carte["note"]["grade"]
        # Un cran d'écart = mineur ; au-delà = grave.
        distance = min(abs(grades.index(obtenu) - grades.index(g)) for g in fourchette if g in grades)
        ecarts.append({"gravite": "mineur" if distance <= 1 else "grave", "type": "grade",
                       "obtenu": obtenu, "attendu": fourchette})

    ids = {t["id"] for t in carte["techniques_detectees"]}
    for manquante in [t for t in entree.get("techniques_attendues", []) if t not in ids]:
        ecarts.append({"gravite": "grave", "type": "technique_manquante", "id": manquante})
    for faux_positif in [t for t in entree.get("techniques_interdites", []) if t in ids]:
        ecarts.append({"gravite": "grave", "type": "faux_positif", "id": faux_positif})

    # La langue de rédaction est une attente comme une autre depuis le prompt v0.1.2 :
    # une analyse rendue dans la mauvaise langue est inutilisable pour qui lit la page,
    # même si tout le reste est juste.
    langue_attendue = entree.get("langue_attendue")
    if langue_attendue:
        obtenue = (carte.get("langue") or "")[:2]
        if obtenue != langue_attendue[:2]:
            ecarts.append({"gravite": "grave", "type": "langue",
                           "obtenu": obtenue or "(absente)", "attendu": langue_attendue})

    plancher = entree.get("confiance_min")
    if plancher is not None and carte["note"]["confiance"] < plancher:
        ecarts.append({"gravite": "mineur", "type": "confiance",
                       "obtenu": f"{carte['note']['confiance']:.2f}", "attendu": plancher})

    return ecarts


def _phrase_console(ecart: dict) -> str:
    """L'écart tel qu'il s'affiche dans le terminal, en français et en compact.

    Le rapport publié a son propre rendu, dans les deux langues : c'est pourquoi les écarts
    circulent sous forme de faits, et non de phrases déjà écrites."""
    type_ecart = ecart["type"]
    if type_ecart == "categorie":
        relation = "∉" if isinstance(ecart["attendu"], list) else "≠"
        return f"catégorie {ecart['obtenu']} {relation} {ecart['attendu']}"
    if type_ecart == "grade":
        return f"grade {ecart['obtenu']} ∉ {ecart['attendu']}"
    if type_ecart == "technique_manquante":
        return f"technique manquante : {ecart['id']}"
    if type_ecart == "faux_positif":
        return f"faux positif : {ecart['id']}"
    if type_ecart == "langue":
        return f"langue {ecart['obtenu']} ≠ {ecart['attendu']}"
    return f"confiance {ecart['obtenu']} < {ecart['attendu']}"


def _comparer(entree: dict, carte: dict) -> tuple[list[str], list[str]]:
    """Les écarts d'un cas, séparés en graves et mineurs, prêts pour le terminal."""
    ecarts = _ecarts(entree, carte)
    return ([_phrase_console(e) for e in ecarts if e["gravite"] == "grave"],
            [_phrase_console(e) for e in ecarts if e["gravite"] == "mineur"])


def _entetes_admin() -> dict:
    jeton = os.environ.get("LYNCEUS_ADMIN_TOKEN", "")
    if not jeton:
        console.print(
            "[red]LYNCEUS_ADMIN_TOKEN non défini.[/red] Les contestations peuvent contenir un "
            "contact : leur consultation est réservée à l'opérateur de l'instance.\n"
            "Définir le même jeton côté serveur (api/.env) et dans cet environnement."
        )
        raise typer.Exit(2)
    return {"X-Lynceus-Admin": jeton}


@app.command()
def signalements(
    statut: str = typer.Option(None, help="filtrer : nouveau, examine, rejete, sans_objet"),
    limite: int = typer.Option(50, help="nombre maximum de signalements"),
):
    """Liste les contestations reçues par l'instance (opérateur)."""
    reponse = httpx.get(
        f"{_api()}/v1/admin/signalements",
        params={k: v for k, v in {"statut": statut, "limite": limite}.items() if v},
        headers=_entetes_admin(),
        timeout=30,
    )
    if reponse.status_code != 200:
        console.print(f"[red]Erreur {reponse.status_code} :[/red] {_erreur_http(reponse)}")
        raise typer.Exit(1)

    liste = reponse.json()["signalements"]
    if not liste:
        console.print("Aucune contestation" + (f" au statut « {statut} »." if statut else "."))
        return

    table = Table(show_header=True, header_style="bold")
    for colonne in ("id", "analyse", "motif", "message", "statut", "reçue le"):
        table.add_column(colonne, overflow="fold")
    for s in liste:
        couleur = {"nouveau": "yellow", "examine": "green", "rejete": "dim", "sans_objet": "dim"}
        table.add_row(
            str(s["id"]),
            str(s["analyse_id"]),
            s["motif"],
            s["message"][:120] + ("…" if len(s["message"]) > 120 else ""),
            f"[{couleur.get(s['statut'], 'white')}]{s['statut']}[/]",
            s["cree_le"][:10],
        )
    console.print(table)
    nouveaux = sum(1 for s in liste if s["statut"] == "nouveau")
    console.print(f"{len(liste)} contestation(s), dont [yellow]{nouveaux} en attente[/yellow].")


@app.command()
def traiter(
    signalement_id: int = typer.Argument(help="identifiant du signalement"),
    statut: str = typer.Option(help="examine (fondé) | rejete (infondé) | sans_objet"),
    decision: str = typer.Option(help="justification, conservée et auditable"),
):
    """Enregistre la décision de l'opérateur sur une contestation.

    La justification est obligatoire : écarter une contestation sans motif reviendrait à
    l'opacité que Lynceus dénonce (docs/ETHIQUE.md §2)."""
    reponse = httpx.post(
        f"{_api()}/v1/admin/signalements/{signalement_id}",
        json={"statut": statut, "decision": decision},
        headers=_entetes_admin(),
        timeout=30,
    )
    if reponse.status_code != 200:
        console.print(f"[red]Erreur {reponse.status_code} :[/red] {_erreur_http(reponse)}")
        raise typer.Exit(1)
    console.print(f"[green]Signalement {signalement_id} : {reponse.json()['statut']}.[/green]")


@app.command()
def verifier_page(
    signalement_id: int = typer.Argument(help="signalement au motif « page_modifiee »"),
    url: str = typer.Option(help="URL de la page à re-vérifier"),
):
    """Vérifie si une page a réellement changé, et relance l'analyse le cas échéant.

    Seul motif de contestation mécaniquement vérifiable : on compare le contenu actuel à
    celui analysé. Les autres motifs relèvent du jugement humain."""
    entetes = _entetes_admin()
    with console.status("Récupération de la page…"):
        reponse = httpx.post(f"{_api()}/v1/analyses", json={"url": url}, timeout=600)
    if reponse.status_code != 200:
        console.print(f"[red]Impossible de récupérer la page :[/red] {_erreur_http(reponse)}")
        console.print("[dim]Site protégé contre le téléchargement ? Analyser via l'extension.[/dim]")
        raise typer.Exit(1)

    donnees = reponse.json()
    carte = donnees["carte"]
    if donnees["en_cache"]:
        console.print("[yellow]Le contenu est inchangé[/yellow] : l'analyse en cache correspond toujours.")
        conclusion = "Contenu inchangé à la re-vérification : l'analyse reste valable."
        statut = "rejete"
    else:
        console.print(f"[green]Page modifiée[/green] : nouvelle analyse "
                      f"{carte['categorie']} · grade {carte['note']['grade']} ({carte['note']['score']}/100)")
        conclusion = (f"Page modifiée depuis l'analyse contestée. Nouvelle analyse : "
                      f"{carte['categorie']}, grade {carte['note']['grade']}.")
        statut = "sans_objet"

    httpx.post(
        f"{_api()}/v1/admin/signalements/{signalement_id}",
        json={"statut": statut, "decision": conclusion},
        headers=entetes,
        timeout=30,
    )
    console.print(f"[dim]Signalement {signalement_id} classé « {statut} » : {conclusion}[/dim]")


@app.command()
def capturer(
    fichier: Path = typer.Argument(help="fichier Markdown contenant le texte de la page (ou - pour l'entrée standard)"),
    url: str = typer.Option(help="URL d'origine de la page"),
    titre: str = typer.Option(None, help="titre de la page"),
    vers: Path = typer.Option(Path("corpus/captures"), help="dossier des captures"),
    nom: str = typer.Option(None, help="nom du fichier de capture (déduit de l'URL sinon)"),
):
    """Enregistre une capture de page réelle pour le corpus, et affiche l'entrée à ajouter.

    Les captures ne sont pas versionnées : reproduire des pages entières dans le dépôt
    poserait un problème de droit d'auteur. Seul le manifeste (URL, date, empreinte,
    attentes) l'est, l'empreinte garantissant que tous mesurent le même contenu."""
    from datetime import date

    contenu = sys.stdin.read() if str(fichier) == "-" else fichier.read_text(encoding="utf-8")
    contenu = contenu.strip()
    if len(contenu) < 200:
        console.print("[red]Contenu trop court[/red] (200 caractères minimum) pour une analyse fiable.")
        raise typer.Exit(2)

    if not nom:
        morceaux = [m for m in url.split("/") if m and "." not in m[:4]]
        base = (morceaux[-1] if morceaux else "page")[:60]
        nom = "".join(c if c.isalnum() or c in "-_" else "-" for c in base).strip("-") or "page"
    if not nom.endswith(".md"):
        nom += ".md"

    vers.mkdir(parents=True, exist_ok=True)
    chemin = vers / nom
    chemin.write_text(contenu, encoding="utf-8")
    empreinte = hacher_contenu(contenu)

    console.print(f"[green]Capture enregistrée :[/green] {chemin} ({len(contenu)} caractères)")
    console.print("\n[bold]Entrée à ajouter dans corpus/corpus.yaml[/bold] "
                  "[dim](compléter les attentes APRÈS avoir analysé la page)[/dim] :\n")
    console.print(
        f"- capture: captures/{nom}\n"
        f"  url: {url}\n"
        + (f"  titre: {titre}\n" if titre else "")
        + f"  content_hash: {empreinte}\n"
        f"  capture_le: {date.today().isoformat()}\n"
        f"  # categorie_attendue: …\n"
        f"  # grade_attendu: [?, ?]\n"
        f"  # techniques_attendues: []\n"
        f"  # notes: pourquoi ce cas figure au corpus\n"
    )


@app.command("cles-paire")
def cles_paire():
    """Génère une paire de clés Ed25519 pour émettre des clés d'accès.

    La PRIVÉE reste chez l'émetteur (elle seule permet d'émettre) ; la PUBLIQUE va dans la
    configuration de chaque instance qui doit accepter ces clés. Compromettre une instance
    ne permet donc jamais de forger des clés."""
    from .cles import generer_paire

    privee, publique = generer_paire()
    console.print("[bold red]Clé PRIVÉE[/bold red], à garder secrète, chez l'émetteur uniquement :")
    console.print(f"  LYNCEUS_CLE_PRIVEE={privee}\n", soft_wrap=True)
    console.print("[bold green]Clé PUBLIQUE[/bold green], à mettre dans le .env de chaque instance :")
    console.print(f"  LYNCEUS_CLE_PUBLIQUE={publique}\n", soft_wrap=True)
    console.print(
        "[dim]Tant que LYNCEUS_CLE_PUBLIQUE est vide, l'instance reste ouverte et n'exige "
        "aucune clé : c'est le défaut pour un usage personnel.[/dim]"
    )


@app.command("cle-emettre")
def cle_emettre(
    jours: int = typer.Option(365, help="durée de validité"),
    quota: int = typer.Option(50, help="analyses autorisées par jour"),
    nombre: int = typer.Option(1, help="nombre de clés à émettre"),
):
    """Émet une ou plusieurs clés d'accès signées.

    Nécessite LYNCEUS_CLE_PRIVEE dans l'environnement. À n'exécuter que côté émetteur :
    la clé privée ne doit jamais être distribuée, sinon n'importe qui pourrait émettre."""
    from .cles import emettre

    privee = os.environ.get("LYNCEUS_CLE_PRIVEE", "")
    if not privee:
        console.print(
            "[red]LYNCEUS_CLE_PRIVEE non définie.[/red] Générez une paire avec "
            "[bold]lynceus cles-paire[/bold], puis exportez la clé privée."
        )
        raise typer.Exit(2)

    for _ in range(max(1, nombre)):
        try:
            cle, droits = emettre(privee, jours=jours, quota_jour=quota)
        except Exception as exc:
            console.print(f"[red]Émission impossible :[/red] {exc}")
            raise typer.Exit(1) from exc
        console.print(cle, soft_wrap=True)  # jamais de retour à la ligne : la clé se copie-colle
        console.print(
            f"[dim]  id {droits.identifiant} · expire le {droits.expire_le} · "
            f"{droits.quota_jour} analyses/jour[/dim]"
        )


@app.command("cle-verifier")
def cle_verifier(cle: str = typer.Argument(help="clé à vérifier")):
    """Vérifie une clé avec la clé publique configurée (LYNCEUS_CLE_PUBLIQUE)."""
    from .cles import CleInvalide, valider

    publique = os.environ.get("LYNCEUS_CLE_PUBLIQUE", "")
    if not publique:
        console.print("[red]LYNCEUS_CLE_PUBLIQUE non définie.[/red]")
        raise typer.Exit(2)
    try:
        droits = valider(cle, publique)
    except CleInvalide as exc:
        console.print(f"[red]Clé refusée :[/red] {exc}")
        raise typer.Exit(1) from exc
    console.print(
        f"[green]Clé valide[/green] · id {droits.identifiant} · émise le {droits.emise_le} · "
        f"expire le {droits.expire_le} · {droits.quota_jour} analyses/jour"
    )


@app.command()
def meta():
    """Transparence de l'instance interrogée."""
    reponse = httpx.get(f"{_api()}/v1/meta", timeout=30)
    console.print_json(reponse.text)

# ---------------------------------------------------------------- variables d'environnement

class CibleEnv(str, Enum):
    production = "production"
    recette = "recette"


@dataclass
class Variable:
    """Une ligne de fichier .env, et ce qu'il faut en dire.

    `note_si_vide` n'apparaît que si personne n'a rempli la valeur : le commentaire qui
    explique pourquoi une variable est laissée vide devient faux dès qu'elle ne l'est plus.
    """

    nom: str
    valeur: str = ""
    note: str = ""
    note_si_vide: str = ""


def _rendre(elements: list[Variable | str]) -> list[str]:
    lignes: list[str] = []
    for element in elements:
        if isinstance(element, str):
            lignes.append(element)
            continue
        for source in (element.note, "" if element.valeur else element.note_si_vide):
            lignes.extend(f"# {texte}" for texte in source.splitlines() if source)
        lignes.append(f"{element.nom}={element.valeur}")
    return lignes


SEPARATEUR = "# " + "=" * 74


def _bloc(titre: str, destination: str, elements: list[Variable | str]) -> None:
    """Affiche un bloc de variables prêt à coller.

    Le titre est écrit en COMMENTAIRE sur la sortie standard, avec les variables, et non
    à part sur la sortie d'erreur. Une cible de production produit deux fichiers, un par
    machine, qui portent les mêmes noms de variables avec des valeurs différentes : sans
    marqueur, une redirection les colle bout à bout et le second recouvre le premier en
    silence. En commentaire, le marqueur survit à la redirection et laisse couper au bon
    endroit, sans rendre le fichier invalide.

    Les variables passent par `print` plutôt que par la console riche, qui replie les
    lignes trop longues sur la largeur du terminal : une clé coupée en deux, recopiée dans
    Portainer, donne une configuration fausse et muette."""
    print(f"\n{SEPARATEUR}")
    print(f"# {titre}")
    print(f"# {destination}")
    print(f"{SEPARATEUR}\n")
    for ligne in _rendre(elements):
        print(ligne)


class Questionneur:
    """Pose les questions, ou pas.

    Muet, il rend des chaînes vides : la sortie redevient un modèle à trous, ce qui est le
    comportement voulu en script et en CI. Toutes les invites partent sur la sortie
    d'erreur, faute de quoi « lynceus env > .env » écrirait les questions dans le fichier.
    """

    def __init__(self, actif: bool):
        self.actif = actif

    def texte(self, question: str, *, defaut: str = "", secret: bool = False) -> str:
        if not self.actif:
            return defaut if not secret else ""
        reponse = typer.prompt(question, default=defaut, hide_input=secret,
                               show_default=bool(defaut), err=True)
        return (reponse or "").strip()

    def adresse(self, question: str, *, defaut: str = "") -> str:
        """Une adresse publique, vérifiée sommairement.

        Une adresse sans schéma est le genre d'erreur qui passe la configuration et se
        manifeste chez l'utilisateur : l'extension reçoit une adresse qu'elle ne sait pas
        joindre, longtemps après le déploiement."""
        while True:
            reponse = self.texte(question, defaut=defaut)
            if not reponse or reponse.startswith(("http://", "https://")):
                return reponse.rstrip("/")
            aide.print("[yellow]Il faut une adresse complète, commençant par http:// ou https://[/yellow]")

    def oui_non(self, question: str, *, defaut: bool = False) -> bool:
        """Question fermée, en français.

        `typer.confirm` n'accepte que y/n : dans une interface entièrement française,
        répondre « o » renvoie « Error: invalid input », ce qui est absurde. On accepte les
        deux langues, et on affiche celle de l'interface."""
        if not self.actif:
            return defaut
        suffixe = "[O/n]" if defaut else "[o/N]"
        while True:
            reponse = self.texte(f"{question} {suffixe}").lower()
            if not reponse:
                return defaut
            if reponse in ("o", "oui", "y", "yes"):
                return True
            if reponse in ("n", "non", "no"):
                return False
            aide.print("[yellow]Répondez par o ou n.[/yellow]")


def _forge_connue(depot: str) -> bool:
    """Sait-on construire l'adresse d'un fichier à partir de celle du dépôt ?

    Seulement pour les forges dont la forme est connue. Ailleurs, mieux vaut laisser la
    variable vide, que l'exploitant remplira, qu'une adresse fabriquée qui tombe à côté."""
    hote = urlsplit(depot).hostname or ""
    return hote in {"github.com", "gitlab.com"} or hote.startswith(("github.", "gitlab."))


@app.command("traductions")
def traductions(
    langue: str = typer.Option(
        "", "--langue",
        help="code de la langue à inspecter. Vide : toutes celles que le projet sert.",
    ),
):
    """Où en est la traduction des documents suivis du dépôt.

    Une traduction est une copie : elle dérive dès que l'original bouge, et rien ne le
    signale puisque les deux fichiers se lisent aussi bien. Cette commande est le seul
    endroit où lire l'état réel, plutôt que d'ouvrir les pages une par une.

    Sans `--langue`, toutes les langues servies sont inspectées, ce qui couvre les deux
    conventions du dépôt : les textes qui engagent le projet, traduits depuis le français,
    et la façade de la forge, traduite depuis l'anglais.
    """
    from .portail import contenu, i18n

    langues = [langue] if langue else list(i18n.LANGUES)
    inventaire = [
        entree for code in langues for entree in contenu.etat_traductions(code)
    ]
    couleurs = {"à jour": "green", "manquante": "yellow",
                "en retard": "red", "sans empreinte": "red"}
    table = Table(show_header=True, header_style="bold")
    for colonne in ("Document", "Traduction", "État"):
        table.add_column(colonne, overflow="fold")
    for entree in inventaire:
        etat = entree["etat"]
        table.add_row(entree["source"], entree["traduction"],
                      f"[{couleurs[etat]}]{etat}[/{couleurs[etat]}]")
    console.print(table)

    defauts = [e for e in inventaire if e["etat"] in ("en retard", "sans empreinte")]
    manquantes = [e for e in inventaire if e["etat"] == "manquante"]
    if manquantes:
        console.print(f"[yellow]{len(manquantes)} document(s) encore à traduire : le lecteur "
                      f"reçoit l'original, et le portail l'annonce.[/yellow]")
    if defauts:
        console.print(f"[red]{len(defauts)} traduction(s) en retard sur leur original. "
                      f"Relire, puis mettre à jour la ligne « traduit-de ».[/red]")
        raise typer.Exit(1)


@app.command("calibration")
def calibration_publiee(
    corpus: Path = typer.Option(Path("corpus/corpus.yaml"), "--corpus", help="corpus de référence"),
    reengendrer: bool = typer.Option(
        False, "--reengendrer",
        help="réécrire le tableau depuis le journal, sans relancer d'analyse",
    ),
):
    """Vérifie que les chiffres publiés viennent bien d'une passe enregistrée.

    Le tableau de `corpus/RESULTATS.md` est engendré depuis `corpus/passes.jsonl`, journal
    des passes réellement exécutées. Cette commande le réengendre et le compare à ce qui est
    publié : un chiffre modifié à la main, une estampille de version avancée sans mesure, ou
    une traduction dont le tableau n'a pas suivi, tout cela devient un échec au lieu de
    passer inaperçu.
    """
    from . import calibration
    from .moteur import prompt as moteur_prompt

    journal = corpus.parent / "passes.jsonl"
    version = moteur_prompt.versions_disponibles()[-1]
    liste = calibration.passes_courantes(journal, version)
    if not liste:
        console.print(
            f"[red]Aucune passe enregistrée pour le prompt v{version}.[/red]\n"
            f"Les chiffres publiés ne se rapporteraient à rien. Lancer :\n"
            f"  lynceus calibrer {corpus} --ecrire"
        )
        raise typer.Exit(1)

    ecarts = []
    for chemin, langue in _rapports_publies(corpus.parent):
        if not chemin.is_file():
            continue
        attendu = calibration.bloc(liste, langue)
        # Le rendu peut changer sans que la mesure bouge : une colonne ajoutée, une phrase
        # reformulée. Réengendrer évite alors de relancer des analyses pour rien.
        if reengendrer:
            if calibration.remplacer_bloc(chemin, attendu):
                console.print(f"[dim]Tableau réengendré dans {chemin}[/dim]")
            continue
        if calibration.bloc_publie(chemin) != attendu:
            ecarts.append(chemin)
    if reengendrer:
        _restamper_traductions(corpus.parent)

    passes_str = ", ".join(f"{p['conformes']}/{p['mesures']}" for p in liste)
    if ecarts:
        console.print("[red]Le tableau publié ne correspond pas au journal des passes :[/red]")
        for chemin in ecarts:
            console.print(f"  [red]{chemin}[/red]")
        console.print("Réengendrer avec « lynceus calibrer --ecrire », ou restaurer le fichier.")
        raise typer.Exit(1)
    console.print(f"[green]v{version} : {len(liste)} passe(s) enregistrée(s) ({passes_str}), "
                  f"tableau publié conforme au journal.[/green]")


@app.command("env")
def env(
    cible: CibleEnv = typer.Argument(CibleEnv.production, help="Environnement à configurer."),
    cle_privee: str = typer.Option(
        "", "--cle-privee",
        help="Réutiliser une paire existante plutôt que d'en engendrer une. La publique s'en déduit.",
    ),
    questions: bool = typer.Option(
        None, "--questions/--sans-questions",
        help="Poser les questions. Par défaut, oui si la commande tourne dans un terminal.",
    ),
    quota: int = typer.Option(20, "--quota", help="Analyses par jour et par clé délivrée."),
    validite: int = typer.Option(0, "--validite", help="Validité des clés en jours. 0 = défaut de la cible."),
):
    """Engendre les variables d'environnement d'un déploiement, prêtes à coller.

    Dans un terminal, la commande pose ses questions : adresse du registre, clé du
    fournisseur de modèle, adresses publiques, jetons de tunnel, identité légale. Ce qui
    peut être engendré l'est sans rien demander : mot de passe de base, jeton
    d'administration, et une SEULE paire de clés pour les deux machines. C'est l'erreur la
    plus facile à commettre que de lancer deux fois `cles-paire` et de déployer un portail
    qui signe avec une clé que l'instance ne reconnaît pas.

    Toute réponse peut rester vide : la variable est alors laissée vide plutôt que remplie
    d'un exemple, pour que Compose refuse de démarrer en la nommant, au lieu de démarrer
    sur une valeur fausse.

    Redirigée (`lynceus env recette > .env`), la commande ne pose rien et écrit un fichier
    à trous : questions et explications passent par la sortie d'erreur, jamais par la
    sortie standard.
    """
    import secrets as _secrets

    from .cles import CleInvalide, generer_paire, publique_de

    if cle_privee:
        try:
            privee, publique = cle_privee, publique_de(cle_privee)
        except CleInvalide as exc:
            aide.print(f"[red]Clé privée illisible :[/red] {exc}")
            raise typer.Exit(1) from exc
    else:
        privee, publique = generer_paire()

    demande = Questionneur(sys.stdin.isatty() if questions is None else questions)
    motdepasse = _secrets.token_urlsafe(24)
    jeton_admin = _secrets.token_urlsafe(32)
    jours = validite or (30 if cible is CibleEnv.recette else 365)
    recette = cible is CibleEnv.recette

    if demande.actif:
        aide.print(
            "[dim]Chaque réponse peut rester vide : la variable sera laissée à remplir "
            "plus tard, et Compose refusera de démarrer en la nommant.[/dim]\n"
        )

    # La sortie standard est détournée pendant les questions. Click écrit l'invite sur la
    # sortie d'erreur, mais confie les espaces qui la terminent à `input()`, lequel écrit
    # sur la sortie standard : une espace par question, en tête du fichier engendré. Le
    # détournement met à l'abri de ce genre de fuite, celle-ci comme les prochaines.
    with contextlib.redirect_stdout(sys.stderr):
        image = demande.texte("Adresse de l'image (registre compris)")
        base_llm = demande.texte("Adresse du fournisseur de modèle (API compatible OpenAI)",
                                 defaut="https://openrouter.ai/api/v1")
        cle_llm = demande.texte("Clé du fournisseur de modèle", secret=True)
        modele = demande.texte("Modèle d'analyse", defaut="z-ai/glm-5.2")
        # Ce nom est publié : /v1/meta, chaque analyse de l'annuaire, la page de
        # confidentialité du portail. Vide, il est déduit de l'adresse, ce qui donne le nom
        # d'hôte, faux dès qu'il y a un intermédiaire.
        libelle_llm = demande.texte("Nom public de ce fournisseur (vide = déduit de l'adresse)")
        adresse_instance = demande.adresse("Adresse publique de l'instance")
        adresse_portail = demande.adresse("Adresse publique du portail")

        # L'AGPL-3.0 impose (article 13) de proposer le code correspondant aux personnes
        # qui utilisent le service à distance. C'est une adresse à donner, pas une case à
        # cocher : le portail avertit au démarrage tant qu'elle manque.
        depot = demande.adresse("Adresse publique du code source (AGPL, article 13)",
                                defaut="https://github.com/Nashi-cloud/Project-Lynceus")
        depot_fichiers = f"{depot.rstrip('/')}/blob/main" if _forge_connue(depot) else ""

        # Deux machines, donc deux tunnels : un jeton par tunnel, jamais le même.
        jeton_tunnel_instance = demande.texte(
            "Jeton Cloudflare Tunnel" + ("" if recette else " de l'instance"), secret=True)
        jeton_tunnel_portail = "" if recette else demande.texte(
            "Jeton Cloudflare Tunnel du portail", secret=True)

        # Question à conséquence : un en-tête se falsifie. Sur une instance joignable en
        # direct, s'y fier laisse contourner la limite de débit en annonçant l'adresse qu'on
        # veut. Elle n'a donc de sens que si le tunnel est la SEULE voie d'accès.
        seulement_tunnel = bool(jeton_tunnel_instance) and demande.oui_non(
            "L'instance est-elle joignable UNIQUEMENT par le tunnel ?", defaut=False)
        entete = "CF-Connecting-IP" if seulement_tunnel else ""

        identite: dict[str, str] = {}
        if not recette and demande.oui_non(
            "Renseigner l'identité légale de l'exploitant maintenant ?", defaut=False
        ):
            aide.print(
                "[dim]Obligatoire dès que le portail est ouvert au public (LCEN). "
                "Non renseignée, chaque page légale l'annonce.[/dim]"
            )
            for nom, question in [
                ("EDITEUR_NOM", "Éditeur : nom ou raison sociale"),
                ("EDITEUR_STATUT", "Éditeur : forme juridique"),
                ("EDITEUR_ADRESSE", "Éditeur : adresse postale"),
                ("EDITEUR_IDENTIFIANT", "Éditeur : identifiant (SIREN, RNA…)"),
                ("EDITEUR_DIRECTEUR", "Directeur de la publication"),
                ("EDITEUR_CONTACT", "Contact (courriel)"),
                ("HEBERGEUR_NOM", "Hébergeur : nom"),
                ("HEBERGEUR_ADRESSE", "Hébergeur : adresse"),
                ("HEBERGEUR_SITE", "Hébergeur : site"),
            ]:
                identite[nom] = demande.texte(question)

    aide.print(
        Panel(
            "Cette sortie contient des secrets : mot de passe de base, jeton "
            "d'administration et clé privée d'émission.\n"
            "Elle n'a rien à faire dans un ticket, un dépôt, ni une conversation.",
            border_style="red",
            title="[bold red]À traiter comme un trousseau",
        )
    )

    bloc_llm = [
        "# Chaque variable répond aussi à un nom anglais : LYNCEUS_LLM_FOURNISSEUR accepte",
        "# LYNCEUS_LLM_PROVIDER, LYNCEUS_CLE_PUBLIQUE accepte LYNCEUS_PUBLIC_KEY, et ainsi",
        "# de suite. La table complète est dans api/DEPLOIEMENT.md. Le nom français reste",
        "# le nom canonique : c'est lui qui est engendré ici, et lui qui l'emporte si les",
        "# deux sont posés.",
        Variable("LYNCEUS_LLM_BASE_URL", base_llm),
        Variable("LYNCEUS_LLM_API_KEY", cle_llm,
                 note_si_vide="Sans elle, l'instance refuse de démarrer en le disant, ce qui\n"
                              "vaut mieux qu'une clé d'exemple qui échouerait à la première analyse."),
        Variable("LYNCEUS_LLM_MODEL", modele),
        Variable("LYNCEUS_LLM_FOURNISSEUR", libelle_llm,
                 note="Nom du fournisseur tel qu'il sera publié : /v1/meta, chaque analyse,\n"
                      "et les pages légales du portail. Vide = déduit de l'adresse, ce qui\n"
                      "donne « modèle auto-hébergé » sur une adresse privée."),
        # Les deux réglages de facture sortent vides : ils changent ce que l'instance
        # demande au fournisseur, et un défaut posé par le générateur serait un choix fait
        # à la place de l'exploitant. Ils figurent quand même, avec leur mode d'emploi,
        # parce qu'un réglage qu'on ne voit pas dans son .env n'existe pas.
        Variable("LYNCEUS_LLM_RAISONNEMENT",
                 note="Ce que le modèle « pense » avant de répondre est facturé en sortie\n"
                      "puis jeté : mesuré à 2 331 tokens pour une carte qui en fait moins de\n"
                      "1 500, soit le premier poste de dépense. Vide = défaut du fournisseur.\n"
                      "off = désactivé · low / medium / high = ampleur réglée.\n"
                      "À ne changer qu'avec une passe de calibration à l'appui : sur une\n"
                      "passe unique, couper divise le coût par 2,8 et la latence par 2, mais\n"
                      "coûte un cas conforme."),
        Variable("LYNCEUS_LLM_CACHE_PROMPT",
                 note="Marque le prompt système comme réutilisable. Inutile chez un\n"
                      "fournisseur qui met en cache de lui-même, ce que fait OpenRouter ;\n"
                      "nécessaire chez ceux qui exigent un point de césure explicite.\n"
                      "À laisser vide devant un endpoint auto-hébergé minimal, qui peut\n"
                      "refuser un contenu découpé en blocs."),
    ]
    note_entete = (
        "Adresse réelle du visiteur, transmise par le tunnel. À n'activer que si\n"
        "l'instance n'est joignable QUE par le tunnel : un en-tête se falsifie, et une\n"
        "instance joignable en direct verrait sa limite de débit contournée."
    )

    if recette:
        _bloc(
            "Recette : stack unique",
            "docker-compose.staging.yml, ou variables de la stack Portainer",
            [
                Variable("LYNCEUS_IMAGE", image),
                Variable("LYNCEUS_SUFFIXE", "-staging"),
                "",
                Variable("POSTGRES_PASSWORD", motdepasse),
                Variable("LYNCEUS_ADMIN_TOKEN", jeton_admin),
                "",
                *bloc_llm,
                "",
                Variable("LYNCEUS_CLE_PUBLIQUE", publique,
                         note="Paire d'émission PROPRE À LA RECETTE. Reprendre celle de production\n"
                              "ferait accepter par la production les clés émises pour les essais."),
                Variable("LYNCEUS_PORTAIL_CLE_PRIVEE", privee),
                "",
                Variable("LYNCEUS_PORTAIL_INSTANCE", adresse_instance,
                         note="Adresse annoncée aux extensions, joignable depuis un navigateur."),
                Variable("LYNCEUS_PORTAIL_ADRESSE", adresse_portail,
                         note="Adresse inscrite dans l'archive téléchargée. Sans elle, elle serait\n"
                              "déduite de la requête, donc peut-être en http derrière un tunnel."),
                Variable("LYNCEUS_PORTAIL_NOM", "Lynceus (recette)"),
                Variable("LYNCEUS_PORTAIL_DEPOT", depot),
                Variable("LYNCEUS_PORTAIL_DEPOT_FICHIERS", depot_fichiers),
                Variable("LYNCEUS_PORTAIL_QUOTA_JOUR", str(quota)),
                Variable("LYNCEUS_PORTAIL_VALIDITE_JOURS", str(jours)),
                "",
                "# Identité légale laissée vide DÉLIBÉRÉMENT : les pages légales annoncent",
                "# alors qu'elles ne le sont pas. Une recette ne doit pas pouvoir passer",
                "# pour un service ouvert au public.",
                "",
                Variable("LYNCEUS_BIND", "127.0.0.1"),
                Variable("LYNCEUS_PAQUETS", "/opt/lynceus/paquets-staging"),
                Variable("CLOUDFLARE_TUNNEL_TOKEN", jeton_tunnel_instance),
                Variable("COMPOSE_PROFILES", "tunnel" if jeton_tunnel_instance else "",
                         note="Active le service de tunnel, qui vit derrière un profil Compose et\nn'existe donc pas tant qu'on ne le nomme pas. En ligne de commande,\n« --profile tunnel » fait la même chose ; depuis Portainer, où il n'y a\npas de drapeau à passer, c'est cette variable qui l'active."),
                Variable("LYNCEUS_ENTETE_IP_REELLE", entete, note=note_entete),
            ],
        )
        aide.print(
            "\n[dim]Un seul tunnel dessert les deux services : côté Cloudflare, deux "
            "hostnames, l'un vers http://api:8000, l'autre vers http://portail:8080.[/dim]"
        )
        return

    _bloc(
        "1. Instance (la machine exposée)",
        "api/.env, à côté de docker-compose.prod.yml",
        [
            Variable("LYNCEUS_IMAGE", image),
            Variable("LYNCEUS_SUFFIXE"),
            "",
            Variable("POSTGRES_PASSWORD", motdepasse),
            Variable("LYNCEUS_ADMIN_TOKEN", jeton_admin),
            "",
            *bloc_llm,
            "",
            Variable("LYNCEUS_CLE_PUBLIQUE", publique,
                     note="Clé PUBLIQUE : elle vérifie les clés d'accès, elle n'en émet aucune.\n"
                          "Une instance compromise ne permet donc pas d'en forger."),
            Variable("LYNCEUS_CLES_REVOQUEES"),
            "",
            Variable("LYNCEUS_BIND", "127.0.0.1"),
            Variable("CLOUDFLARE_TUNNEL_TOKEN", jeton_tunnel_instance),
            Variable("COMPOSE_PROFILES", "tunnel" if jeton_tunnel_instance else "",
                     note="Active le service de tunnel, qui vit derrière un profil Compose et\nn'existe donc pas tant qu'on ne le nomme pas. En ligne de commande,\n« --profile tunnel » fait la même chose ; depuis Portainer, où il n'y a\npas de drapeau à passer, c'est cette variable qui l'active."),
            Variable("LYNCEUS_ENTETE_IP_REELLE", entete, note=note_entete),
        ],
    )

    _bloc(
        "2. Portail (idéalement une AUTRE machine)",
        "api/.env, à côté de docker-compose.portail.yml",
        [
            Variable("LYNCEUS_IMAGE", image),
            Variable("LYNCEUS_SUFFIXE"),
            "",
            Variable("LYNCEUS_PORTAIL_CLE_PRIVEE", privee,
                     note="Clé PRIVÉE : elle seule émet. C'est le secret le mieux gardé du\n"
                          "déploiement, et la raison pour laquelle le portail ne vit pas sur\n"
                          "l'instance."),
            Variable("LYNCEUS_PORTAIL_QUOTA_JOUR", str(quota)),
            Variable("LYNCEUS_PORTAIL_VALIDITE_JOURS", str(jours)),
            Variable("LYNCEUS_PORTAIL_CLES_PAR_IP_JOUR", "0"),
            "",
            Variable("LYNCEUS_PORTAIL_INSTANCE", adresse_instance,
                     note="Adresse publique de l'instance, telle qu'un navigateur la joint."),
            Variable("LYNCEUS_PORTAIL_INSTANCE_INTERNE",
                     note="Adresse par laquelle le portail interroge lui-même l'instance.\n"
                          "Vide = la même que ci-dessus."),
            Variable("LYNCEUS_PORTAIL_ADRESSE", adresse_portail,
                     note="Adresse publique de CE portail, inscrite dans l'archive téléchargée."),
            Variable("LYNCEUS_PORTAIL_NOM", "Lynceus"),
            Variable("LYNCEUS_PORTAIL_CONTACT", identite.get("EDITEUR_CONTACT", "")),
            "",
            "# Code source. L'AGPL-3.0 impose (article 13) de proposer le code correspondant",
            "# aux personnes qui utilisent le service à distance. Vide, les pages parlent du",
            "# dépôt sans pouvoir y renvoyer, et le portail avertit au démarrage.",
            Variable("LYNCEUS_PORTAIL_DEPOT", depot),
            Variable("LYNCEUS_PORTAIL_DEPOT_FICHIERS", depot_fichiers,
                     note="Préfixe désignant un fichier du dépôt, branche comprise. GitHub et\n"
                          "GitLab : <dépôt>/blob/main. Forgejo : <dépôt>/src/branch/main."),
            "",
            "# Identité légale. Obligatoire dès que le portail est ouvert au public (LCEN).",
            "# Non renseignée, chaque page légale l'annonce, et le portail avertit au",
            "# démarrage plutôt que d'inventer une mention.",
            *[Variable(f"LYNCEUS_PORTAIL_{nom}", identite.get(nom, "")) for nom in (
                "EDITEUR_NOM", "EDITEUR_STATUT", "EDITEUR_ADRESSE", "EDITEUR_IDENTIFIANT",
                "EDITEUR_DIRECTEUR", "EDITEUR_CONTACT", "HEBERGEUR_NOM", "HEBERGEUR_ADRESSE",
                "HEBERGEUR_SITE")],
            Variable("LYNCEUS_PORTAIL_DROIT_APPLICABLE", "français"),
            "",
            Variable("LYNCEUS_PORTAIL_BIND", "127.0.0.1"),
            Variable("LYNCEUS_PAQUETS", "/opt/lynceus/paquets"),
            Variable("CLOUDFLARE_TUNNEL_TOKEN", jeton_tunnel_portail,
                     note="Tunnel du PORTAIL, distinct de celui de l'instance : deux machines,\n"
                          "deux tunnels, deux jetons."),
            Variable("COMPOSE_PROFILES", "tunnel" if jeton_tunnel_portail else "",
                     note="Active le service de tunnel, qui vit derrière un profil Compose et\nn'existe donc pas tant qu'on ne le nomme pas. En ligne de commande,\n« --profile tunnel » fait la même chose ; depuis Portainer, où il n'y a\npas de drapeau à passer, c'est cette variable qui l'active."),
        ],
    )

    aide.print(
        "\n[dim]Les deux blocs viennent de la MÊME paire : la publique du premier vérifie "
        "ce que la privée du second signe. Pour reconfigurer une seule machine plus tard, "
        "rappelez cette commande avec --cle-privee, la publique s'en déduit.[/dim]"
    )


if __name__ == "__main__":
    app()
