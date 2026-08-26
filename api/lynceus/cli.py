"""CLI Lynceus : client de l'API pour tester, analyser et calibrer.

  lynceus analyser https://exemple.fr/article
  lynceus analyser article.md --url https://exemple.fr/article
  lynceus lookup https://exemple.fr/article
  lynceus calibrer ../corpus/corpus.yaml
"""

from __future__ import annotations

import json
from enum import Enum
import os
import time
from concurrent.futures import ThreadPoolExecutor
import sys
from pathlib import Path

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

        carte = reponse.json()["carte"]
        ecarts_graves, ecarts_mineurs = _comparer(entree, carte)
        return {
            "etiquette": etiquette, "entree": entree, "carte": carte,
            "graves": ecarts_graves, "mineurs": ecarts_mineurs,
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

    if graves:
        raise typer.Exit(1)


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


def _comparer(entree: dict, carte: dict) -> tuple[list[str], list[str]]:
    """Compare une carte aux attentes. Retourne (écarts graves, écarts mineurs)."""
    graves, mineurs = [], []
    grades = ["A", "B", "C", "D", "E"]

    # `categorie_attendue` (exacte) ou `categories_acceptables` (liste). Certains contenus
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


def _bloc(titre: str, destination: str, lignes: list[str]) -> None:
    """Affiche un bloc de variables prêt à coller.

    Deux précautions qui se voient à l'usage. Le titre part sur la sortie d'erreur, pour
    que la sortie standard ne contienne que des lignes NOM=valeur et reste redirigeable
    telle quelle dans un .env. Et les variables passent par `print` plutôt que par la
    console riche, qui replie les lignes trop longues sur la largeur du terminal : une clé
    coupée en deux, recopiée dans Portainer, donne une configuration fausse et muette."""
    aide.print(f"\n[bold]{titre}[/bold]")
    aide.print(f"[dim]{destination}[/dim]\n")
    for ligne in lignes:
        print(ligne)


@app.command("env")
def env(
    cible: CibleEnv = typer.Argument(CibleEnv.production, help="Environnement à configurer."),
    cle_privee: str = typer.Option(
        "", "--cle-privee",
        help="Réutiliser une paire existante plutôt que d'en engendrer une. La publique s'en déduit.",
    ),
    quota: int = typer.Option(20, "--quota", help="Analyses par jour et par clé délivrée."),
    validite: int = typer.Option(0, "--validite", help="Validité des clés en jours. 0 = défaut de la cible."),
):
    """Engendre les variables d'environnement d'un déploiement, prêtes à coller.

    Rien n'est écrit sur le disque : la sortie se recopie dans un fichier .env ou dans
    l'éditeur de variables de Portainer. Ce qui est engendré ici est engendré une fois ;
    ce que vous seul connaissez (adresse du registre, clé du fournisseur de modèle, jeton
    de tunnel, identité légale) est laissé VIDE plutôt que rempli d'un exemple, afin que
    Compose refuse de démarrer en le disant, au lieu de démarrer avec une valeur fausse.

    La paire de clés est engendrée une seule fois pour les deux blocs de production : c'est
    l'erreur la plus facile à commettre que de lancer deux fois `cles-paire` et de déployer
    un portail qui signe avec une clé que l'instance ne reconnaît pas.
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

    motdepasse = _secrets.token_urlsafe(24)
    jeton_admin = _secrets.token_urlsafe(32)
    jours = validite or (30 if cible is CibleEnv.recette else 365)

    aide.print(
        Panel(
            "Cette sortie contient des secrets : mot de passe de base, jeton "
            "d'administration et clé privée d'émission.\n"
            "Elle n'a rien à faire dans un ticket, un dépôt, ni une conversation.",
            border_style="red",
            title="[bold red]À traiter comme un trousseau",
        )
    )

    commun_llm = [
        "# Fournisseur de modèle. Laissé vide : sans lui, l'instance refuse de démarrer",
        "# en le disant, ce qui vaut mieux qu'une clé d'exemple qui échouerait à la",
        "# première analyse.",
        "LYNCEUS_LLM_BASE_URL=https://openrouter.ai/api/v1",
        "LYNCEUS_LLM_API_KEY=",
        "LYNCEUS_LLM_MODEL=z-ai/glm-5.2",
    ]
    note_entete = [
        "# Adresse réelle du visiteur, transmise par le tunnel. À DÉCOMMENTER seulement si",
        "# l'instance n'est joignable QUE par le tunnel : un en-tête se falsifie, et une",
        "# instance joignable en direct verrait sa limite de débit contournée.",
        "# LYNCEUS_ENTETE_IP_REELLE=CF-Connecting-IP",
    ]

    if cible is CibleEnv.recette:
        _bloc(
            "Recette : stack unique",
            "docker-compose.staging.yml, ou variables de la stack Portainer",
            [
                "LYNCEUS_IMAGE=",
                "LYNCEUS_SUFFIXE=-staging",
                "",
                f"POSTGRES_PASSWORD={motdepasse}",
                f"LYNCEUS_ADMIN_TOKEN={jeton_admin}",
                "",
                *commun_llm,
                "",
                "# Paire d'émission PROPRE À LA RECETTE. Reprendre celle de production ici",
                "# ferait accepter par la production toutes les clés émises pour les essais.",
                f"LYNCEUS_CLE_PUBLIQUE={publique}",
                f"LYNCEUS_PORTAIL_CLE_PRIVEE={privee}",
                "",
                "# Adresses publiques. La première est annoncée aux extensions, la seconde",
                "# est inscrite dans l'archive téléchargée : sans elle, l'adresse serait",
                "# déduite de la requête, donc peut-être en http derrière un tunnel.",
                "LYNCEUS_PORTAIL_INSTANCE=",
                "LYNCEUS_PORTAIL_ADRESSE=",
                "LYNCEUS_PORTAIL_NOM=Lynceus (recette)",
                f"LYNCEUS_PORTAIL_QUOTA_JOUR={quota}",
                f"LYNCEUS_PORTAIL_VALIDITE_JOURS={jours}",
                "",
                "# Identité légale laissée vide DÉLIBÉRÉMENT : les pages légales annoncent",
                "# alors qu'elles ne le sont pas. Une recette ne doit pas pouvoir passer",
                "# pour un service ouvert au public.",
                "",
                "LYNCEUS_BIND=127.0.0.1",
                "LYNCEUS_PAQUETS=/opt/lynceus/paquets-staging",
                "CLOUDFLARE_TUNNEL_TOKEN=",
                "COMPOSE_PROFILES=tunnel",
                *note_entete,
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
            "LYNCEUS_IMAGE=",
            "LYNCEUS_SUFFIXE=",
            "",
            f"POSTGRES_PASSWORD={motdepasse}",
            f"LYNCEUS_ADMIN_TOKEN={jeton_admin}",
            "",
            *commun_llm,
            "",
            "# Clé PUBLIQUE : elle vérifie les clés d'accès, elle n'en émet aucune.",
            "# Une instance compromise ne permet donc pas d'en forger.",
            f"LYNCEUS_CLE_PUBLIQUE={publique}",
            "LYNCEUS_CLES_REVOQUEES=",
            "",
            "LYNCEUS_BIND=127.0.0.1",
            "CLOUDFLARE_TUNNEL_TOKEN=",
            *note_entete,
        ],
    )

    _bloc(
        "2. Portail (idéalement une AUTRE machine)",
        "api/.env, à côté de docker-compose.portail.yml",
        [
            "LYNCEUS_IMAGE=",
            "LYNCEUS_SUFFIXE=",
            "",
            "# Clé PRIVÉE : elle seule émet. C'est le secret le mieux gardé du déploiement,",
            "# et la raison pour laquelle le portail ne vit pas sur l'instance.",
            f"LYNCEUS_PORTAIL_CLE_PRIVEE={privee}",
            f"LYNCEUS_PORTAIL_QUOTA_JOUR={quota}",
            f"LYNCEUS_PORTAIL_VALIDITE_JOURS={jours}",
            "LYNCEUS_PORTAIL_CLES_PAR_IP_JOUR=0",
            "",
            "# Adresse publique de l'instance, telle qu'un navigateur la joint.",
            "LYNCEUS_PORTAIL_INSTANCE=",
            "# Adresse par laquelle le portail interroge lui-même l'instance. Vide = la",
            "# même que ci-dessus.",
            "LYNCEUS_PORTAIL_INSTANCE_INTERNE=",
            "# Adresse publique de CE portail, inscrite dans l'archive téléchargée.",
            "LYNCEUS_PORTAIL_ADRESSE=",
            "LYNCEUS_PORTAIL_NOM=Lynceus",
            "LYNCEUS_PORTAIL_CONTACT=",
            "",
            "# Identité légale. Obligatoire dès que le portail est ouvert au public (LCEN).",
            "# Non renseignée, chaque page légale l'annonce, et le portail avertit au",
            "# démarrage plutôt que d'inventer une mention.",
            "LYNCEUS_PORTAIL_EDITEUR_NOM=",
            "LYNCEUS_PORTAIL_EDITEUR_STATUT=",
            "LYNCEUS_PORTAIL_EDITEUR_ADRESSE=",
            "LYNCEUS_PORTAIL_EDITEUR_IDENTIFIANT=",
            "LYNCEUS_PORTAIL_EDITEUR_DIRECTEUR=",
            "LYNCEUS_PORTAIL_EDITEUR_CONTACT=",
            "LYNCEUS_PORTAIL_HEBERGEUR_NOM=",
            "LYNCEUS_PORTAIL_HEBERGEUR_ADRESSE=",
            "LYNCEUS_PORTAIL_HEBERGEUR_SITE=",
            "LYNCEUS_PORTAIL_DROIT_APPLICABLE=français",
            "",
            "LYNCEUS_PORTAIL_BIND=127.0.0.1",
            "LYNCEUS_PAQUETS=/opt/lynceus/paquets",
            "CLOUDFLARE_TUNNEL_TOKEN=",
            "# LYNCEUS_PORTAIL_ENTETE_IP_REELLE=CF-Connecting-IP",
        ],
    )

    aide.print(
        "\n[dim]Les deux blocs viennent de la MÊME paire : la publique ci-dessus vérifie "
        "ce que la privée ci-dessous signe. Pour reconfigurer une seule machine plus tard, "
        "rappelez cette commande avec --cle-privee, la publique s'en déduit.[/dim]"
    )


if __name__ == "__main__":
    app()
