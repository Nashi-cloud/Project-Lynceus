import copy

import pytest

from lynceus.moteur import prompt
from lynceus.moteur.validation import (
    SEUIL_CITATION_LIBRE,
    ErreurValidation,
    citations_inventees,
    extrait_verbatim,
    valider_sortie,
)
from lynceus.normalisation import normaliser_texte
from tests.conftest import CONTENU_TEST, SORTIE_LLM


def test_extrait_verbatim_tolerances():
    contenu = normaliser_texte(CONTENU_TEST)
    # traverse un retour à la ligne du source
    assert extrait_verbatim("commandez notre extrait concentré avant la rupture de stock", contenu)
    # habillage guillemets/ellipses toléré
    assert extrait_verbatim("« Ce que les laboratoires ne veulent surtout pas que vous sachiez »", contenu)
    assert extrait_verbatim("…une plante ancestrale soignerait tous les maux...", contenu)
    # inventé → refusé
    assert not extrait_verbatim("les extraterrestres contrôlent la météo", contenu)
    # trop court après nettoyage → refusé
    assert not extrait_verbatim("« maux »", contenu)


def test_filtrage_techniques():
    schema = prompt.schema_sortie_llm()
    ids = set(prompt.charger_taxonomie())
    donnees, rejets, _ = valider_sortie(copy.deepcopy(SORTIE_LLM), schema, ids, CONTENU_TEST)
    retenus = {t["id"] for t in donnees["techniques_detectees"]}
    assert retenus == {"verite_cachee", "conflit_interet_commercial"}
    raisons = {r["id"]: r["raison"] for r in rejets}
    assert "hors référentiel" in raisons["technique_inconnue"]
    assert "verbatim" in raisons["appel_a_la_peur"]


def test_schema_invalide_leve():
    schema = prompt.schema_sortie_llm()
    ids = set(prompt.charger_taxonomie())
    invalide = copy.deepcopy(SORTIE_LLM)
    del invalide["dimensions"]
    with pytest.raises(ErreurValidation):
        valider_sortie(invalide, schema, ids, CONTENU_TEST)


def test_citation_inventee_dans_un_champ_libre_est_relevee():
    """Le garde-fou verbatim ne couvrait que les techniques. Une citation fabriquée dans une
    question ou un résumé sortait telle quelle, dans la voix de l'outil."""
    contenu = normaliser_texte(CONTENU_TEST)
    donnees = {
        "questions_a_se_poser": [
            "Le texte affirme « les extraterrestres contrôlent entièrement la météo mondiale » : sur quoi ?",
            "Qui finance ce site, et comment le vérifier ?",
        ],
        "resume_neutre": "La page annonce « Ce que les laboratoires ne veulent surtout pas que vous sachiez ».",
    }
    releves = citations_inventees(donnees, contenu)
    assert len(releves) == 1, releves
    assert releves[0]["champ"] == "questions_a_se_poser"
    assert "extraterrestres" in releves[0]["citation"]


def test_citation_courte_non_relevee():
    """Sous le seuil, un guillemet est plus souvent une insistance qu'un emprunt. Relever
    « des études montrent » produirait des faux positifs en série."""
    contenu = normaliser_texte(CONTENU_TEST)
    courte = "x" * (SEUIL_CITATION_LIBRE - 2)
    assert citations_inventees({"resume_neutre": f"Le texte dit « {courte} »."}, contenu) == []


def test_champs_libres_sans_guillemets_intacts():
    """Une question générique n'attribue rien : elle ne doit jamais être relevée. C'est la
    raison pour laquelle la barrière porte sur les citations et non sur le vocabulaire."""
    contenu = normaliser_texte(CONTENU_TEST)
    donnees = {"questions_a_se_poser": [
        "Le site précise-t-il si les données sont anonymisées, et par quel moyen le vérifier ?",
        "Ce contenu commercial annonce-t-il clairement son intérêt ?",
    ]}
    assert citations_inventees(donnees, contenu) == []


def test_valider_sortie_rend_les_trois_listes():
    schema = prompt.schema_sortie_llm()
    ids = set(prompt.charger_taxonomie())
    sortie = copy.deepcopy(SORTIE_LLM)
    sortie["resume_neutre"] = "La page dit « une citation entièrement fabriquée pour ce test »."
    _, rejets, citations = valider_sortie(sortie, schema, ids, CONTENU_TEST)
    assert rejets and citations
    assert citations[0]["champ"] == "resume_neutre"
