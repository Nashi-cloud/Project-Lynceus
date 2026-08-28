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
