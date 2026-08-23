"""CLI Lynceus — client de l'API pour tester, analyser et calibrer.

  lynceus analyser https://exemple.fr/article
  lynceus analyser article.md --url https://exemple.fr/article
  lynceus lookup https://exemple.fr/article
  lynceus calibrer ../corpus/corpus.yaml
"""

from __future__ import annotations

import os
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
    cible: str = typer.Argument(help="URL à analyser, ou chemin d'un fichier Markdown"),
    url: str = typer.Option(None, help="URL d'origine si la cible est un fichier"),
    titre: str = typer.Option(None, help="Titre de la page"),
):
    """Analyse une page (URL) ou un contenu local (fichier .md) via l'API."""
    corps: dict = {"titre": titre}
    if Path(cible).is_file():
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
        console.print(f"[red]Erreur {reponse.status_code} :[/red] {reponse.text}")
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
        console.print(f"[red]Erreur {reponse.status_code} :[/red] {reponse.text}")
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
def calibrer(fichier: Path = typer.Argument(help="corpus YAML (cf. corpus/README.md)")):
    """Passe le corpus de calibration et vérifie catégories, fourchettes de grades et techniques."""
    import yaml

    entrees = yaml.safe_load(fichier.read_text(encoding="utf-8")) or []
    if not isinstance(entrees, list):
        console.print("[red]Le corpus doit être une liste YAML.[/red]")
        raise typer.Exit(2)

    table = Table(show_header=True, header_style="bold")
    for colonne in ("URL", "Attendu", "Obtenu", "Verdict"):
        table.add_column(colonne, overflow="fold")
    echecs = 0

    for entree in entrees:
        cible = entree["url"]
        reponse = httpx.post(f"{_api()}/v1/analyses", json={"url": cible}, timeout=300)
        if reponse.status_code != 200:
            echecs += 1
            table.add_row(cible, "-", f"HTTP {reponse.status_code}", "[red]ERREUR[/red]")
            continue
        carte = reponse.json()["carte"]
        problemes = []
        if "categorie_attendue" in entree and carte["categorie"] != entree["categorie_attendue"]:
            problemes.append(f"catégorie {carte['categorie']} ≠ {entree['categorie_attendue']}")
        if "grade_attendu" in entree and carte["note"]["grade"] not in entree["grade_attendu"]:
            problemes.append(f"grade {carte['note']['grade']} ∉ {entree['grade_attendu']}")
        ids = {t["id"] for t in carte["techniques_detectees"]}
        for attendue in entree.get("techniques_attendues", []):
            if attendue not in ids:
                problemes.append(f"technique manquante : {attendue}")
        for interdite in entree.get("techniques_interdites", []):
            if interdite in ids:
                problemes.append(f"faux positif : {interdite}")
        verdict = "[green]OK[/green]" if not problemes else "[red]" + " · ".join(problemes) + "[/red]"
        echecs += bool(problemes)
        attendu = f"{entree.get('categorie_attendue', '?')} {entree.get('grade_attendu', '')}"
        table.add_row(cible, attendu, f"{carte['categorie']} {carte['note']['grade']}", verdict)

    console.print(table)
    console.print(f"{len(entrees) - echecs}/{len(entrees)} conformes.")
    if echecs:
        raise typer.Exit(1)


@app.command()
def meta():
    """Transparence de l'instance interrogée."""
    reponse = httpx.get(f"{_api()}/v1/meta", timeout=30)
    console.print_json(reponse.text)


if __name__ == "__main__":
    app()
