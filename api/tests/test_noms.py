"""Les variables d'environnement répondent à leurs deux noms.

Le code du projet est en français et le restera. Mais une variable d'environnement n'est
pas du code : c'est la porte de l'exploitant, celle qu'il ouvre avec un guide de
déploiement anglais à côté. Ces tests garantissent que les deux portes ouvrent sur la même
pièce, et qu'aucune instance déjà déployée n'a à bouger."""

import pytest

from lynceus import noms
from lynceus.config import Parametres
from lynceus.portail.config import ParametresPortail


@pytest.fixture(autouse=True)
def sans_environnement(monkeypatch):
    """Les variables du poste ne doivent pas décider du résultat d'un test."""
    for cle in list(noms.ALIAS) + list(noms.ALIAS.values()):
        monkeypatch.delenv(cle, raising=False)


@pytest.mark.parametrize("nom", ["LYNCEUS_CLE_PUBLIQUE", "LYNCEUS_PUBLIC_KEY"])
def test_l_instance_repond_aux_deux_noms(monkeypatch, nom):
    monkeypatch.setenv(nom, "clé-de-test")
    assert Parametres(_env_file=None).cle_publique == "clé-de-test"


@pytest.mark.parametrize("nom", ["LYNCEUS_PORTAIL_EDITEUR_NOM", "LYNCEUS_PORTAL_PUBLISHER_NAME"])
def test_le_portail_repond_aux_deux_noms(monkeypatch, nom):
    monkeypatch.setenv(nom, "Nashi.cloud")
    assert ParametresPortail(_env_file=None).editeur_nom == "Nashi.cloud"


def test_le_nom_francais_l_emporte_si_les_deux_sont_poses(monkeypatch):
    """Les fichiers déjà déployés portent le nom français : c'est lui qui doit gagner,
    sans quoi une mise à jour changerait le comportement d'une instance en production."""
    monkeypatch.setenv("LYNCEUS_CONTENU_MAX_CARS", "1000")
    monkeypatch.setenv("LYNCEUS_CONTENT_MAX_CHARS", "2000")
    assert Parametres(_env_file=None).contenu_max_cars == 1000


def test_un_conflit_est_annonce_plutot_que_subi():
    """Un réglage ignoré en silence est le genre de panne qui coûte une soirée."""
    conflits = noms.avertir_des_conflits({
        "LYNCEUS_CONTENU_MAX_CARS": "1000",
        "LYNCEUS_CONTENT_MAX_CHARS": "2000",
    })
    assert len(conflits) == 1
    assert "LYNCEUS_CONTENU_MAX_CARS" in conflits[0] and "s'applique" in conflits[0]


def test_deux_noms_d_accord_ne_derangent_personne():
    assert noms.avertir_des_conflits({
        "LYNCEUS_CONTENU_MAX_CARS": "1000",
        "LYNCEUS_CONTENT_MAX_CHARS": "1000",
    }) == []


def test_le_nom_du_champ_reste_utilisable_en_python():
    """Un alias de validation remplace le nom du champ : sans populate_by_name, la CLI et
    les tests cesseraient de pouvoir construire ces objets."""
    assert Parametres(cle_publique="k", _env_file=None).cle_publique == "k"
    assert ParametresPortail(quota_jour=7, _env_file=None).quota_jour == 7


def test_aucun_alias_anglais_ne_porte_deux_fois_le_meme_nom():
    """Deux champs partageant un alias en feraient un synonyme silencieux de l'autre."""
    anglais = list(noms.ALIAS.values())
    assert len(anglais) == len(set(anglais))
    assert len(noms.ALIAS) > 30, "le scan n'a presque rien trouvé : les alias ont disparu"


# ---------- une variable vide vaut « non renseignée » ----------

def test_un_booleen_vide_ne_fait_pas_tomber_l_instance(monkeypatch):
    """Le bug qui a mis la recette à genoux.

    `lynceus env` engendre « LYNCEUS_LLM_CACHE_PROMPT= » sans valeur, à dessein. Cette
    ligne faisait échouer la validation, l'API refusait de démarrer, le portail attendait
    une API saine qui ne venait jamais, et le proxy renvoyait 502 sans nommer la cause."""
    monkeypatch.setenv("LYNCEUS_LLM_CACHE_PROMPT", "")
    assert Parametres(_env_file=None).llm_cache_prompt is False


@pytest.mark.parametrize("nom", ["LYNCEUS_ANALYSES_SIMULTANEES", "LYNCEUS_CONCURRENT_ANALYSES"])
def test_un_entier_vide_vaut_son_defaut_sous_les_deux_noms(monkeypatch, nom):
    """Chercher le champ par son seul nom laisserait passer tous les réglages aliassés,
    c'est-à-dire précisément ceux que ce projet a ajoutés."""
    monkeypatch.setenv(nom, "")
    assert Parametres(_env_file=None).analyses_simultanees == 12


def test_un_entier_vide_du_portail_vaut_aussi_son_defaut(monkeypatch):
    monkeypatch.setenv("LYNCEUS_PORTAIL_QUOTA_JOUR", "")
    assert ParametresPortail(_env_file=None).quota_jour > 0


def test_une_chaine_vide_reste_une_valeur(monkeypatch):
    """Le vide veut dire quelque chose pour une chaîne : LYNCEUS_LLM_FOURNISSEUR vide
    demande de déduire le nom du fournisseur de l'adresse. Ce n'est pas « rien dire »."""
    monkeypatch.setenv("LYNCEUS_LLM_FOURNISSEUR", "")
    assert Parametres(_env_file=None).llm_fournisseur == ""


def test_une_valeur_renseignee_reste_prioritaire(monkeypatch):
    monkeypatch.setenv("LYNCEUS_LLM_CACHE_PROMPT", "true")
    monkeypatch.setenv("LYNCEUS_ANALYSES_SIMULTANEES", "3")
    p = Parametres(_env_file=None)
    assert p.llm_cache_prompt is True and p.analyses_simultanees == 3


def test_le_fichier_engendre_par_env_demarre_une_instance(tmp_path, monkeypatch):
    """Le garde-fou de bout en bout : ce que `lynceus env` écrit doit démarrer.

    C'est exactement ce qui manquait. Le générateur produisait un fichier que l'instance
    refusait de lire, et rien dans la chaîne ne le disait."""
    from typer.testing import CliRunner

    from lynceus.cli import app

    sortie = CliRunner().invoke(app, ["env", "recette"]).stdout
    variables = dict(
        ligne.split("=", 1) for ligne in sortie.splitlines()
        if "=" in ligne and not ligne.startswith("#")
    )
    for nom, valeur in variables.items():
        if nom.startswith("LYNCEUS_"):
            monkeypatch.setenv(nom, valeur)
    monkeypatch.setenv("LYNCEUS_DATABASE_URL", f"sqlite:///{tmp_path}/essai.sqlite3")
    Parametres(_env_file=None)
    ParametresPortail(_env_file=None)
