"""CLI Lynceus — client de l'API pour tester, analyser et calibrer.

  lynceus analyser https://exemple.fr/article
  lynceus analyser article.md --url https://exemple.fr/article
  lynceus lookup https://exemple.fr/article
  lynceus calibrer ../corpus/corpus.yaml
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(help="Lynceus — la vigie de l'information.", no_args_is_help=True)
console = Console()

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
        f"[bold {couleur}]Indice {note['grade']}[/] — score {note['score']}/100 · "
        f"catégorie : [bold]{carte['categorie']}[/] · confiance de l'analyse : {note['confiance']:.0%}"
    )
    if en_cache:
        entete += "  [dim](annuaire — déjà analysée)[/dim]"
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
    console.print(f"[dim]— {meta['modele']} · prompt v{meta['prompt_version']} · {meta['analyse_le']}[/dim]")


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
        entrees = [e for e in entrees if filtre.lower() in str(e.get("titre", "") or e.get("fichier", "") or e.get("url", "")).lower()]

    racine = fichier.parent
    table = Table(show_header=True, header_style="bold")
    for colonne in ("Cas", "Attendu", "Obtenu", "Verdict"):
        table.add_column(colonne, overflow="fold")

    rapport, graves, mineurs = [], 0, 0

    for entree in entrees:
        etiquette = entree.get("titre") or entree.get("fichier") or entree.get("url") or "(sans titre)"
        corps = _corps_demande(entree, racine)
        if corps is None:
            graves += 1
            table.add_row(etiquette, "-", "-", "[red]entrée invalide (ni fichier ni url)[/red]")
            continue

        try:
            reponse = httpx.post(f"{_api()}/v1/analyses", json=corps, timeout=600)
        except httpx.HTTPError as exc:
            graves += 1
            table.add_row(etiquette, "-", f"réseau : {exc}", "[red]ERREUR[/red]")
            continue
        if reponse.status_code != 200:
            graves += 1
            table.add_row(etiquette, "-", f"HTTP {reponse.status_code}", f"[red]{_erreur_http(reponse)[:80]}[/red]")
            continue

        carte = reponse.json()["carte"]
        ecarts_graves, ecarts_mineurs = _comparer(entree, carte)
        graves += bool(ecarts_graves)
        mineurs += bool(ecarts_mineurs and not ecarts_graves)

        if ecarts_graves:
            verdict = "[red]" + " · ".join(ecarts_graves) + "[/red]"
        elif ecarts_mineurs:
            verdict = "[yellow]" + " · ".join(ecarts_mineurs) + "[/yellow]"
        else:
            verdict = "[green]OK[/green]"

        attendu = f"{entree.get('categorie_attendue', '?')} {entree.get('grade_attendu', '')}"
        obtenu = f"{carte['categorie']} {carte['note']['grade']} ({carte['note']['score']})"
        table.add_row(etiquette, attendu, obtenu, verdict)
        rapport.append({
            "cas": etiquette,
            "attendu": {k: v for k, v in entree.items() if k.endswith(("_attendue", "_attendu", "_attendues", "_interdites", "_min", "_acceptables"))},
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
    conformes = total - graves - mineurs
    console.print(
        f"\n[bold]{conformes}/{total} conformes[/bold] · "
        f"[yellow]{mineurs} écart(s) mineur(s)[/yellow] · [red]{graves} échec(s) grave(s)[/red]"
    )
    if rapport:
        modele = rapport[0] and httpx.get(f"{_api()}/v1/meta", timeout=30).json()
        console.print(f"[dim]Instance : {modele['modele']} · prompt v{modele['prompt_version']}[/dim]")

    if json_sortie:
        json_sortie.write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
        console.print(f"[dim]Rapport détaillé écrit dans {json_sortie}[/dim]")

    if graves:
        raise typer.Exit(1)


def _corps_demande(entree: dict, racine: Path) -> dict | None:
    """Construit le corps POST /v1/analyses depuis une entrée de corpus."""
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


def _comparer(entree: dict, carte: dict) -> tuple[list[str], list[str]]:
    """Compare une carte aux attentes. Retourne (écarts graves, écarts mineurs)."""
    graves, mineurs = [], []
    grades = ["A", "B", "C", "D", "E"]

    # `categorie_attendue` (exacte) ou `categories_acceptables` (liste) — certains contenus
    # relèvent légitimement de plusieurs catégories : un article pseudo-médical qui vend un
    # produit est à la fois pseudo_science et publicite_sponsorise. Exiger une catégorie
    # unique testerait alors un choix arbitraire, pas la qualité de l'analyse.
    acceptables = entree.get("categories_acceptables")
    attendue = entree.get("categorie_attendue")
    if acceptables:
        if carte["categorie"] not in acceptables:
            graves.append(f"catégorie {carte['categorie']} ∉ {acceptables}")
    elif attendue and carte["categorie"] != attendue:
        graves.append(f"catégorie {carte['categorie']} ≠ {attendue}")

    fourchette = entree.get("grade_attendu")
    if fourchette and carte["note"]["grade"] not in fourchette:
        obtenu = carte["note"]["grade"]
        # Un cran d'écart = mineur ; au-delà = grave.
        distance = min(abs(grades.index(obtenu) - grades.index(g)) for g in fourchette if g in grades)
        (mineurs if distance <= 1 else graves).append(f"grade {obtenu} ∉ {fourchette}")

    ids = {t["id"] for t in carte["techniques_detectees"]}
    for manquante in [t for t in entree.get("techniques_attendues", []) if t not in ids]:
        graves.append(f"technique manquante : {manquante}")
    for faux_positif in [t for t in entree.get("techniques_interdites", []) if t in ids]:
        graves.append(f"faux positif : {faux_positif}")

    plancher = entree.get("confiance_min")
    if plancher is not None and carte["note"]["confiance"] < plancher:
        mineurs.append(f"confiance {carte['note']['confiance']:.2f} < {plancher}")

    return graves, mineurs


@app.command()
def meta():
    """Transparence de l'instance interrogée."""
    reponse = httpx.get(f"{_api()}/v1/meta", timeout=30)
    console.print_json(reponse.text)


if __name__ == "__main__":
    app()
