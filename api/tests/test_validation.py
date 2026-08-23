import copy

import pytest

from lynceus.moteur import prompt
from lynceus.moteur.validation import ErreurValidation, extrait_verbatim, valider_sortie
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
    donnees, rejets = valider_sortie(copy.deepcopy(SORTIE_LLM), schema, ids, CONTENU_TEST)
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
