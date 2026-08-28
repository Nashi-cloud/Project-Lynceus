"""Le tableau publié de la calibration, engendré depuis un journal de passes.

Le portail publie des scores de calibration. Jusqu'ici ce tableau s'écrivait à la main, et
`verifier.sh` ne contrôlait qu'une chose : que la version de prompt annoncée corresponde à
celle des prompts. Rien n'empêchait donc de faire passer l'estampille d'une version à la
suivante sans avoir relancé la moindre analyse : le vert se serait allumé quand même, et le
portail aurait publié des chiffres ne se rapportant plus à rien.

D'où ce module. Chaque passe réelle est ajoutée à un journal versionné (`corpus/passes.jsonl`),
et le tableau publié est **engendré** depuis ce journal, entre deux marques. Le reste du
document, la lecture des résultats et les enseignements, reste écrit à la main : une machine
ne peut pas dire ce qu'un écart signifie.

Le contrôle devient alors réel plutôt que déclaratif : `verifier.sh` réengendre le bloc et
échoue s'il diffère de celui qui est publié, ou si aucune passe n'existe pour la version de
prompt en vigueur.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

MARQUE_DEBUT = "<!-- calibration:début (engendré par « lynceus calibrer --ecrire », ne pas modifier à la main) -->"
MARQUE_FIN = "<!-- calibration:fin -->"

# Les quelques phrases fixes du bloc. Les titres des cas viennent du corpus, les chiffres de
# la mesure : il ne reste ici que la charpente, et elle tient en une poignée de lignes.
PHRASES = {
    "fr": {
        "entete": "Dernière passe : **{date}** · modèle `{modele}`{fournisseur} · prompt **v{version}** · température **{temperature}**",
        "via": " (via {nom})",
        "passes_1": "**Une passe** enregistrée sur cette version du prompt : **{scores}** conformes. Une passe unique ne dit rien de solide, puisque le modèle ne rend pas deux fois la même analyse du même texte.",
        "passes_n": "**{nombre} passes** enregistrées sur cette version du prompt : **{scores}** conformes. Une passe unique ne dirait rien de solide, puisque le modèle ne rend pas deux fois la même analyse du même texte.",
        "colonnes": ("Cas", "Catégorie", "Grade", "Score", "Écarts relevés"),
        "resservie": "Les passes marquées d'une astérisque ont été intégralement resservies depuis l'annuaire : elles rejouent une mesure déjà enregistrée au lieu d'en produire une nouvelle. Pour un tirage réellement indépendant, il faut une base vierge.",
        "intervalle": "{min} à {max}",
        "aucun": "—",
        "sur_passes": " ({nombre} passe(s) sur {total})",
        "categorie": "catégorie `{obtenu}` au lieu de {attendu}",
        "grade": "grade {obtenu} hors de la fourchette {attendu}",
        "technique_manquante": "technique manquante : `{id}`",
        "faux_positif": "faux positif : `{id}`",
        "langue": "analyse rendue en {obtenu} au lieu de {attendu}",
        "confiance": "confiance {obtenu} sous le plancher de {attendu}",
        "non_mesure": "cas non mesuré : {detail}",
    },
    "en": {
        "entete": "Latest run: **{date}** · model `{modele}`{fournisseur} · prompt **v{version}** · temperature **{temperature}**",
        "via": " (through {nom})",
        "passes_1": "**One run** recorded on this prompt version: **{scores}** conforming. A single run says nothing solid, since the model does not return the same analysis of the same text twice.",
        "passes_n": "**{nombre} runs** recorded on this prompt version: **{scores}** conforming. A single run would say nothing solid, since the model does not return the same analysis of the same text twice.",
        "colonnes": ("Case", "Category", "Grade", "Score", "Discrepancies"),
        "resservie": "Runs marked with an asterisk were served entirely from the directory cache: they replay an already recorded measurement instead of producing a new one. A genuinely independent draw needs a blank database.",
        "intervalle": "{min} to {max}",
        "aucun": "—",
        "sur_passes": " ({nombre} of {total} runs)",
        "categorie": "category `{obtenu}` instead of {attendu}",
        "grade": "grade {obtenu} outside the expected range {attendu}",
        "technique_manquante": "technique missing: `{id}`",
        "faux_positif": "false positive: `{id}`",
        "langue": "analysis written in {obtenu} instead of {attendu}",
        "confiance": "confidence {obtenu} below the floor of {attendu}",
        "non_mesure": "case not measured: {detail}",
    },
}


def empreinte(chemin: Path) -> str:
    """Les 16 premiers caractères du sha256, comme pour les traductions."""
    return hashlib.sha256(chemin.read_bytes()).hexdigest()[:16]


def enregistrer(journal: Path, passe: dict) -> None:
    """Ajoute une passe au journal, sans jamais en retirer.

    Un journal qu'on réécrit ne prouve rien. Celui-ci ne fait que croître, et l'historique
    git montre chaque ajout : reculer devient un acte visible."""
    journal.parent.mkdir(parents=True, exist_ok=True)
    with journal.open("a", encoding="utf-8") as sortie:
        sortie.write(json.dumps(passe, ensure_ascii=False, sort_keys=True) + "\n")


def passes(journal: Path, version_prompt: str = "", modele: str = "") -> list[dict]:
    """Les passes enregistrées, éventuellement filtrées sur une version de prompt et un modèle.

    Filtrer est le comportement utile : une passe menée sous une version antérieure ne
    mesure pas ce que l'instance applique aujourd'hui, et l'afficher tromperait."""
    if not journal.is_file():
        return []
    lues = [json.loads(ligne) for ligne in journal.read_text(encoding="utf-8").splitlines() if ligne.strip()]
    if version_prompt:
        lues = [p for p in lues if p.get("prompt_version") == version_prompt]
    if modele:
        lues = [p for p in lues if p.get("modele") == modele]
    return lues


def passes_courantes(journal: Path, version_prompt: str) -> list[dict]:
    """Les passes qui décrivent ce que l'instance rend aujourd'hui.

    Le modèle compte autant que la version de prompt. Deux modèles ne donnent pas les mêmes
    notes sur le même texte, et un tableau qui mélangerait leurs passes afficherait des
    intervalles de score qui ne mesureraient plus la variabilité d'un modèle mais l'écart
    entre deux. Ne sont donc retenues que les passes du modèle de la plus récente."""
    toutes = passes(journal, version_prompt)
    if not toutes:
        return []
    return [p for p in toutes if p.get("modele") == toutes[-1].get("modele")]


def _texte(ecart: dict, mots: dict) -> str:
    modele = mots.get(ecart["type"], "{type}")
    return modele.format(**{**ecart, "attendu": _lisible(ecart.get("attendu")),
                            "obtenu": _lisible(ecart.get("obtenu"))})


def _lisible(valeur) -> str:
    if isinstance(valeur, (list, tuple)):
        return ", ".join(str(v) for v in valeur)
    return "" if valeur is None else str(valeur)


def _cellule_ecarts(ecarts_par_passe: list[list[dict]], mots: dict) -> str:
    """Les écarts d'un cas, agrégés sur toutes les passes.

    Un écart qui n'apparaît pas partout est le plus intéressant des trois : il dit que le
    modèle hésite. Le taux est donc affiché, plutôt que gommé."""
    total = len(ecarts_par_passe)
    comptes: dict[str, int] = {}
    for ecarts in ecarts_par_passe:
        for phrase in dict.fromkeys(_texte(e, mots) for e in ecarts):
            comptes[phrase] = comptes.get(phrase, 0) + 1
    if not comptes:
        return mots["aucun"]
    rendus = [
        phrase if compte == total else phrase + mots["sur_passes"].format(nombre=compte, total=total)
        for phrase, compte in comptes.items()
    ]
    return " ; ".join(rendus)


def _temperature(valeur) -> str:
    """0.0 s'écrit « 0 », et 0.2 « 0,2 » : le tableau se lit, il ne se déverse pas."""
    texte = f"{float(valeur):g}"
    return texte


def bloc(liste_passes: list[dict], langue: str = "fr") -> str:
    """Le tableau publié, engendré depuis les passes fournies.

    L'ordre des cas est celui du corpus, pris sur la passe la plus récente : c'est l'ordre
    dans lequel un lecteur les a rencontrés dans `corpus.yaml`."""
    mots = PHRASES.get(langue, PHRASES["fr"])
    if not liste_passes:
        return ""
    derniere = liste_passes[-1]
    lignes = [MARQUE_DEBUT, ""]
    lignes.append(mots["entete"].format(
        date=derniere["date"],
        modele=derniere["modele"],
        fournisseur=mots["via"].format(nom=derniere["fournisseur"]) if derniere.get("fournisseur") else "",
        version=derniere["prompt_version"],
        temperature=_temperature(derniere.get("temperature", 0)),
    ))
    lignes.append("")

    # Une passe resservie depuis l'annuaire n'est pas un nouveau tirage. Le taire laisserait
    # croire à une mesure indépendante là où il n'y a qu'une relecture.
    def _marque(passe: dict) -> str:
        resservie = passe.get("depuis_cache", 0) and passe["depuis_cache"] >= passe["mesures"]
        return f"{passe['conformes']}/{passe['mesures']}" + ("\\*" if resservie else "")

    scores = ", ".join(_marque(p) for p in liste_passes)
    gabarit = mots["passes_1"] if len(liste_passes) == 1 else mots["passes_n"]
    lignes.append(gabarit.format(nombre=len(liste_passes), scores=scores))
    if any(p.get("depuis_cache", 0) >= p["mesures"] for p in liste_passes):
        lignes.append("")
        lignes.append(mots["resservie"])
    lignes.append("")

    lignes.append("| " + " | ".join(mots["colonnes"]) + " |")
    lignes.append("|" + "---|" * len(mots["colonnes"]))

    for cas in derniere["cas"]:
        identifiant = cas["id"]
        # Le même cas dans chaque passe, quand il y figure : un corpus peut avoir grandi
        # entre deux passes, et un cas absent d'une passe ne doit pas décaler les autres.
        presences = [
            autre for passe in liste_passes
            for autre in passe["cas"] if autre["id"] == identifiant
        ]
        titre = cas.get(f"titre_{langue}") or cas["titre"]
        categories = list(dict.fromkeys(c["categorie"] for c in presences if c.get("categorie")))
        grades = [c["grade"] for c in presences if c.get("grade")]
        valeurs = [c["score"] for c in presences if c.get("score") is not None]

        grade = grades[0] if grades and len(set(grades)) == 1 else " ".join(grades)
        if not valeurs:
            score = mots["aucun"]
        elif min(valeurs) == max(valeurs):
            score = str(valeurs[0])
        else:
            score = mots["intervalle"].format(min=min(valeurs), max=max(valeurs))

        lignes.append("| " + " | ".join([
            titre,
            " / ".join(categories) or mots["aucun"],
            grade or mots["aucun"],
            score,
            _cellule_ecarts([c.get("ecarts", []) for c in presences], mots),
        ]) + " |")

    lignes += ["", MARQUE_FIN]
    return "\n".join(lignes)


def bloc_publie(fichier: Path) -> str:
    """Le bloc tel qu'il figure dans le document, marques comprises. Vide s'il n'y en a pas."""
    texte = fichier.read_text(encoding="utf-8")
    debut = texte.find(MARQUE_DEBUT)
    fin = texte.find(MARQUE_FIN)
    if debut == -1 or fin == -1:
        return ""
    return texte[debut:fin + len(MARQUE_FIN)]


def remplacer_bloc(fichier: Path, nouveau: str) -> bool:
    """Remplace le bloc engendré, laisse le reste intact. Rend True si le fichier a changé.

    Sans marques, le bloc est inséré après le premier paragraphe suivant le titre, ce qui
    n'arrive qu'une fois par document : la position est ensuite tenue par les marques."""
    texte = fichier.read_text(encoding="utf-8")
    debut = texte.find(MARQUE_DEBUT)
    fin = texte.find(MARQUE_FIN)
    if debut != -1 and fin != -1:
        remplace = texte[:debut] + nouveau + texte[fin + len(MARQUE_FIN):]
    else:
        lignes = texte.splitlines()
        insertion = next((i for i, l in enumerate(lignes) if i and l.startswith("#")), len(lignes))
        remplace = "\n".join(lignes[:insertion] + [nouveau, ""] + lignes[insertion:]) + "\n"
    if remplace == texte:
        return False
    fichier.write_text(remplace, encoding="utf-8")
    return True
