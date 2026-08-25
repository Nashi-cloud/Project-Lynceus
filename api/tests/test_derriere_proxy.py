"""Comportement derrière un proxy ou un tunnel (Cloudflare Tunnel, reverse proxy).

Enjeu : sans traitement particulier, toutes les requêtes arrivent avec l'adresse du proxy
et partagent donc le même compteur de débit — un seul utilisateur épuiserait la limite de
tous. Mais faire confiance à un en-tête sans condition permettrait de la contourner."""

import json as json_

import pytest
from fastapi.testclient import TestClient

from lynceus.main import creer_application
from lynceus.moteur import llm
from tests.conftest import CONTENU_TEST, SORTIE_LLM, parametres_test

ENTETE = "CF-Connecting-IP"


def _appli(tmp_path, monkeypatch, **surcharges):
    monkeypatch.setattr(llm, "appeler", lambda m, p, schema_json=None: json_.dumps(SORTIE_LLM, ensure_ascii=False))
    return TestClient(creer_application(parametres_test(tmp_path, rate_limit_analyses=1, **surcharges)))


def _analyser(client, variante, ip=None):
    entetes = {ENTETE: ip} if ip else {}
    return client.post(
        "/v1/analyses",
        json={"url": f"https://exemple.fr/{variante}", "contenu_markdown": CONTENU_TEST + f" {variante}"},
        headers=entetes,
    )


def test_sans_configuration_l_entete_est_ignore(tmp_path, monkeypatch):
    """Défaut sûr : un en-tête non configuré ne doit RIEN changer, sinon n'importe qui
    contournerait la limite en le forgeant."""
    client = _appli(tmp_path, monkeypatch)  # entete_ip_reelle vide

    assert _analyser(client, "a", ip="1.1.1.1").status_code == 200
    # Adresse annoncée différente, mais l'en-tête est ignoré : la limite s'applique quand même.
    assert _analyser(client, "b", ip="2.2.2.2").status_code == 429


def test_entete_configure_separe_les_visiteurs(tmp_path, monkeypatch):
    """Derrière un tunnel, c'est ce qui évite qu'un visiteur épuise la limite des autres."""
    client = _appli(tmp_path, monkeypatch, entete_ip_reelle=ENTETE)

    assert _analyser(client, "a", ip="1.1.1.1").status_code == 200
    assert _analyser(client, "b", ip="2.2.2.2").status_code == 200, "un autre visiteur ne doit pas être bloqué"
    assert _analyser(client, "c", ip="1.1.1.1").status_code == 429, "le premier a bien épuisé sa limite"


def test_chaine_d_adresses_prend_la_premiere(tmp_path, monkeypatch):
    """Certains proxys chaînent les adresses : « visiteur, proxy1, proxy2 »."""
    client = _appli(tmp_path, monkeypatch, entete_ip_reelle=ENTETE)

    assert _analyser(client, "a", ip="9.9.9.9, 10.0.0.1, 10.0.0.2").status_code == 200
    assert _analyser(client, "b", ip="9.9.9.9, 10.0.0.5").status_code == 429


def test_entete_absent_retombe_sur_l_adresse_de_transport(tmp_path, monkeypatch):
    """Si le proxy n'envoie pas l'en-tête, on ne doit pas cesser de limiter."""
    client = _appli(tmp_path, monkeypatch, entete_ip_reelle=ENTETE)

    assert _analyser(client, "a").status_code == 200
    assert _analyser(client, "b").status_code == 429


def test_entete_vide_ignore(tmp_path, monkeypatch):
    client = _appli(tmp_path, monkeypatch, entete_ip_reelle=ENTETE)
    assert _analyser(client, "a", ip="   ").status_code == 200
    assert _analyser(client, "b", ip="   ").status_code == 429
