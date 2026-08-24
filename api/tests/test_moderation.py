"""Traitement des contestations par l'opérateur de l'instance.

Deux exigences testées ici : les contestations ne doivent JAMAIS être lisibles publiquement
(elles peuvent contenir un contact), et une décision doit toujours être justifiée."""

import pytest
from fastapi.testclient import TestClient

from lynceus.main import creer_application
from tests.conftest import CONTENU_TEST, parametres_test

JETON = "jeton-de-test"
URL = "https://sante.exemple/remede"


@pytest.fixture
def appli_admin(tmp_path, monkeypatch):
    """Instance avec modération activée, LLM simulé."""
    import json as json_

    from lynceus.moteur import llm
    from tests.conftest import SORTIE_LLM

    monkeypatch.setattr(llm, "appeler", lambda m, p, schema_json=None: json_.dumps(SORTIE_LLM, ensure_ascii=False))
    client = TestClient(creer_application(parametres_test(tmp_path, admin_token=JETON)))
    client.post("/v1/analyses", json={"url": URL, "contenu_markdown": CONTENU_TEST})
    client.post("/v1/signalements", json={
        "analyse_id": 1, "motif": "categorie_erronee", "message": "Ce contenu est satirique, pas complotiste.",
    })
    return client


ADMIN = {"X-Lynceus-Admin": JETON}


# ---------- confidentialité des contestations ----------

def test_liste_refusee_sans_jeton(appli_admin):
    """Les contestations peuvent contenir un contact : jamais publiques."""
    assert appli_admin.get("/v1/admin/signalements").status_code == 403


def test_liste_refusee_avec_mauvais_jeton(appli_admin):
    reponse = appli_admin.get("/v1/admin/signalements", headers={"X-Lynceus-Admin": "mauvais"})
    assert reponse.status_code == 403


def test_moderation_fermee_par_defaut(appli):
    """Sans LYNCEUS_ADMIN_TOKEN configuré, les routes restent fermées — un oubli de
    configuration ne doit pas exposer les contestations."""
    client, _ = appli
    reponse = client.get("/v1/admin/signalements", headers={"X-Lynceus-Admin": "n-importe-quoi"})
    assert reponse.status_code == 403
    assert "Modération désactivée" in reponse.json()["detail"]


def test_traitement_refuse_sans_jeton(appli_admin):
    """Corps volontairement VALIDE : sinon la validation du schéma (422) masquerait le
    contrôle d'accès qu'on veut vérifier ici."""
    reponse = appli_admin.post(
        "/v1/admin/signalements/1",
        json={"statut": "rejete", "decision": "Justification de longueur suffisante."},
    )
    assert reponse.status_code == 403


# ---------- lecture ----------

def test_liste_avec_jeton(appli_admin):
    liste = appli_admin.get("/v1/admin/signalements", headers=ADMIN).json()["signalements"]
    assert len(liste) == 1
    assert liste[0]["motif"] == "categorie_erronee"
    assert liste[0]["statut"] == "nouveau"
    assert liste[0]["traite_le"] is None


def test_filtre_par_statut(appli_admin):
    assert len(appli_admin.get("/v1/admin/signalements", params={"statut": "nouveau"}, headers=ADMIN).json()["signalements"]) == 1
    assert appli_admin.get("/v1/admin/signalements", params={"statut": "examine"}, headers=ADMIN).json()["signalements"] == []


# ---------- traitement ----------

def test_traitement_enregistre_la_decision(appli_admin):
    reponse = appli_admin.post("/v1/admin/signalements/1", headers=ADMIN, json={
        "statut": "examine", "decision": "Contestation fondée : la catégorie a été corrigée.",
    })
    assert reponse.status_code == 200

    signalement = appli_admin.get("/v1/admin/signalements", headers=ADMIN).json()["signalements"][0]
    assert signalement["statut"] == "examine"
    assert "fondée" in signalement["decision"]
    assert signalement["traite_le"] is not None


def test_decision_obligatoire(appli_admin):
    """Écarter une contestation sans justification reviendrait à l'opacité dénoncée (charte §2)."""
    for decision in ("", "ok"):
        reponse = appli_admin.post("/v1/admin/signalements/1", headers=ADMIN,
                                   json={"statut": "rejete", "decision": decision})
        assert reponse.status_code == 422


def test_statut_inconnu_refuse(appli_admin):
    reponse = appli_admin.post("/v1/admin/signalements/1", headers=ADMIN, json={
        "statut": "classe_sans_suite", "decision": "Justification suffisante.",
    })
    assert reponse.status_code == 400


def test_signalement_inconnu(appli_admin):
    reponse = appli_admin.post("/v1/admin/signalements/999", headers=ADMIN, json={
        "statut": "rejete", "decision": "Justification suffisante.",
    })
    assert reponse.status_code == 404


# ---------- message rendu à l'utilisateur ----------

def test_message_ne_promet_pas_d_examen_garanti(appli_admin):
    """Le message initial promettait « il sera examiné » — une promesse que rien ne tenait.
    Il doit décrire ce qui se passe réellement."""
    reponse = appli_admin.post("/v1/signalements", json={
        "analyse_id": 1, "motif": "autre", "message": "Un autre signalement de test.",
    })
    message = reponse.json()["message"]
    assert "sera examiné" not in message
    assert "opérateur" in message  # on nomme qui décide réellement
