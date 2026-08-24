import json

import pytest
from fastapi.testclient import TestClient

from lynceus.config import Parametres
from lynceus.main import creer_application
from lynceus.moteur import llm

# Contenu de test : contient les extraits VERBATIM que le faux LLM va citer
# (dont un qui traverse un retour à la ligne, pour tester la normalisation d'espaces).
CONTENU_TEST = """# Le remède que personne ne veut voir

Ce que les laboratoires ne veulent surtout pas que vous sachiez : une plante ancestrale
soignerait tous les maux. Des chercheurs américains l'ont confirmé dans plusieurs études.

Notre équipe a rassemblé des témoignages du monde entier. Marie, 54 ans, dit avoir retrouvé
la forme en quelques jours. Pour en profiter, commandez notre extrait concentré avant la
rupture de stock. Le temps presse, cet article pourrait être supprimé à tout moment.
"""

# Sortie simulée du LLM : 2 techniques valides, 1 extrait inventé (anti-hallucination),
# 1 id hors référentiel — les deux dernières doivent être écartées par le serveur.
SORTIE_LLM = {
    "categorie": "pseudo_science",
    "langue": "fr",
    "note": {"confiance": 0.9},
    "dimensions": {
        "sources": {"score": 10, "detail": "Aucune source vérifiable."},
        "factualite": {"score": 20, "detail": "Affirmations extraordinaires sans preuve."},
        "ton": {"score": 30, "detail": "Urgence et peur dominantes."},
        "transparence": {"score": 40, "detail": "Boutique liée, auteur absent."},
    },
    "techniques_detectees": [
        {"id": "verite_cachee",
         "extrait": "Ce que les laboratoires ne veulent surtout pas que vous sachiez",
         "explication": "Rhétorique du secret.", "gravite": "haute"},
        {"id": "conflit_interet_commercial",
         "extrait": "commandez notre extrait concentré avant la rupture de stock",
         "explication": "Le discours débouche sur une vente.", "gravite": "haute"},
        {"id": "appel_a_la_peur",
         "extrait": "les extraterrestres contrôlent la météo",
         "explication": "Extrait inventé — doit être rejeté.", "gravite": "moyenne"},
        {"id": "technique_inconnue",
         "extrait": "commandez notre extrait concentré avant la rupture de stock",
         "explication": "Id hors référentiel — doit être rejeté.", "gravite": "faible"},
    ],
    "points_positifs": ["Le texte est daté."],
    "questions_a_se_poser": ["Que vend ce site ?"],
    "resume_neutre": "Article vantant un remède universel et débouchant sur une vente.",
    "avertissements": [],
}
# Score attendu (calcul SERVEUR) : 0,30·10 + 0,30·20 + 0,20·30 + 0,20·40 = 23 → grade E
SCORE_ATTENDU, GRADE_ATTENDU = 23, "E"


def parametres_test(tmp_path, **surcharges) -> Parametres:
    """Configuration de test entièrement déterministe.

    Chaque champ sensible est fixé explicitement : sans cela, Parametres() lirait le .env
    de la machine et les tests dépendraient de la configuration locale (un jeton
    d'administration réel y suffisait à faire échouer le test de modération fermée)."""
    defauts = dict(
        database_url=f"sqlite:///{tmp_path}/test.sqlite3",
        llm_api_key="cle-test",
        llm_base_url="https://exemple-fournisseur.test/v1",
        llm_model="test/modele",
        llm_temperature=0.2,
        llm_response_format="none",
        admin_token="",  # modération fermée sauf mention contraire du test
        prompt_version="latest",
        rate_limit_analyses=100,
        contenu_min_cars=200,
        contenu_max_cars=60000,
    )
    defauts.update(surcharges)
    return Parametres(**defauts)


@pytest.fixture
def appli(tmp_path, monkeypatch):
    """(client, compteur d'appels LLM) — le LLM est simulé, aucun réseau."""
    compteur = {"appels": 0}

    def faux_appel(messages, p, schema_json=None):
        compteur["appels"] += 1
        return json.dumps(SORTIE_LLM, ensure_ascii=False)

    monkeypatch.setattr(llm, "appeler", faux_appel)
    client = TestClient(creer_application(parametres_test(tmp_path)))
    return client, compteur
