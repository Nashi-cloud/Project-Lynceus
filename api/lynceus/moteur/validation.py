"""Validation de la sortie LLM : schéma JSON, ids du référentiel, extraits VERBATIM.
La vérification des extraits est le garde-fou anti-hallucination central : toute citation
doit être une sous-chaîne réelle du contenu source (aux espaces près).

La même règle s'applique aux **champs libres** (points positifs, questions, résumé,
avertissements). Ils échappaient à tout contrôle : le modèle pouvait y placer une citation
inventée, dans la voix de l'outil, sans qu'aucune barrière s'y oppose. Ce qui y est présenté
entre guillemets comme les mots de la page doit être les mots de la page."""

from __future__ import annotations

import re

import jsonschema

from ..normalisation import normaliser_texte


class ErreurValidation(Exception):
    """Sortie LLM non conforme (schéma, types…)."""


def _nettoyer_extrait(extrait: str) -> str:
    e = normaliser_texte(extrait)
    e = e.strip(" «»\"'…")  # guillemets et points de suspension d'habillage
    while e.startswith("..."):
        e = e[3:].lstrip()
    while e.endswith("..."):
        e = e[:-3].rstrip()
    return e


def extrait_verbatim(extrait: str, contenu_normalise: str) -> bool:
    e = _nettoyer_extrait(extrait)
    return len(e) >= 10 and e in contenu_normalise


#: Champs de texte libre rendus au lecteur dans la voix de l'outil.
CHAMPS_LIBRES = ("points_positifs", "questions_a_se_poser", "resume_neutre", "avertissements")

#: Une citation courte peut être un guillemet d'insistance ou une expression générique
#: (« des études montrent ») plutôt qu'un emprunt à la page. Au-delà de ce seuil, la seule
#: lecture raisonnable d'un passage entre guillemets est la citation, donc il doit tenir.
#: Le seuil est plus haut que celui des extraits (10) parce que le risque de faux positif
#: y est réel, alors qu'un extrait de technique est une citation par construction.
SEUIL_CITATION_LIBRE = 25

#: Les trois façons d'ouvrir une citation dans les langues servies. La longueur n'est pas
#: contrainte ici mais après nettoyage : le motif capture les espaces d'habillage, qui ne
#: sont pas de la citation et ne doivent pas compter dans le seuil.
_CITATIONS = re.compile(r"«([^»]+)»|\u201c([^\u201d]+)\u201d|\"([^\"]+)\"")


def _textes_libres(donnees: dict) -> list[tuple[str, str]]:
    """(champ, texte) pour chaque chaîne rendue au lecteur, listes aplaties."""
    paires = []
    for champ in CHAMPS_LIBRES:
        valeur = donnees.get(champ)
        if isinstance(valeur, str):
            paires.append((champ, valeur))
        elif isinstance(valeur, list):
            paires.extend((champ, v) for v in valeur if isinstance(v, str))
    return paires


def citations_inventees(donnees: dict, contenu_normalise: str) -> list[dict]:
    """Passages entre guillemets, dans les champs libres, absents du contenu source.

    Rendus au client plutôt que retirés : une citation inventée dans un résumé n'est pas
    une faute qu'on efface, c'est une mesure du comportement du modèle. Le texte reste
    affiché, l'écart est signalé, et le taux devient observable comme celui des détections.
    """
    rejets = []
    for champ, texte in _textes_libres(donnees):
        for trouve in _CITATIONS.finditer(texte):
            brute = next(g for g in trouve.groups() if g is not None)
            citation = _nettoyer_extrait(brute)
            if len(citation) < SEUIL_CITATION_LIBRE:
                continue  # guillemet d'insistance, pas un emprunt : on ne relève pas
            if not extrait_verbatim(citation, contenu_normalise):
                rejets.append({"champ": champ, "citation": citation,
                               "raison": "citation non verbatim dans un champ libre"})
    return rejets


def valider_sortie(donnees: dict, schema_llm: dict, ids_valides: set[str],
                   contenu_source: str) -> tuple[dict, list[dict], list[dict]]:
    """Valide contre le schéma, filtre les techniques, relève les citations libres inventées.

    Retourne (donnees_filtrees, rejets_techniques, citations_inventees). Lève ErreurValidation
    si le schéma n'est pas respecté.
    """
    try:
        jsonschema.validate(donnees, schema_llm)
    except jsonschema.ValidationError as exc:
        chemin = "/".join(str(x) for x in exc.absolute_path) or "(racine)"
        raise ErreurValidation(f"schéma non respecté à {chemin} : {exc.message}") from exc

    contenu_normalise = normaliser_texte(contenu_source)
    retenues, rejets = [], []
    for technique in donnees.get("techniques_detectees", []):
        if technique["id"] not in ids_valides:
            rejets.append({"id": technique["id"], "raison": "id hors référentiel"})
        elif not extrait_verbatim(technique["extrait"], contenu_normalise):
            rejets.append({"id": technique["id"], "raison": "extrait non verbatim (rejet anti-hallucination)"})
        else:
            retenues.append(technique)

    donnees = dict(donnees)
    donnees["techniques_detectees"] = retenues
    return donnees, rejets, citations_inventees(donnees, contenu_normalise)
