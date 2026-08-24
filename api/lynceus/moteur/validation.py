"""Validation de la sortie LLM : schéma JSON, ids du référentiel, extraits VERBATIM.
La vérification des extraits est le garde-fou anti-hallucination central : toute citation
doit être une sous-chaîne réelle du contenu source (aux espaces près)."""

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


def valider_sortie(donnees: dict, schema_llm: dict, ids_valides: set[str], contenu_source: str) -> tuple[dict, list[dict]]:
    """Valide contre le schéma puis filtre les techniques (id inconnu / extrait non verbatim).

    Retourne (donnees_filtrees, rejets). Lève ErreurValidation si le schéma n'est pas respecté.
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
    return donnees, rejets
