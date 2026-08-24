"""Contrôle d'accès par clé au niveau de l'API, et respect du quota journalier."""

import json as json_

import pytest
from fastapi.testclient import TestClient

from lynceus.cles import emettre, generer_paire
from lynceus.main import creer_application
from lynceus.moteur import llm
from tests.conftest import CONTENU_TEST, SORTIE_LLM, parametres_test

URL = "https://exemple.fr/article"


@pytest.fixture
def instance_fermee(tmp_path, monkeypatch):
    """Instance exigeant une clé, avec LLM simulé. Retourne (client, clé valide)."""
    monkeypatch.setattr(llm, "appeler", lambda m, p, schema_json=None: json_.dumps(SORTIE_LLM, ensure_ascii=False))
    privee, publique = generer_paire()
    client = TestClient(creer_application(parametres_test(tmp_path, cle_publique=publique)))
    cle, _ = emettre(privee, quota_jour=3)
    return client, cle


def _analyser(client, contenu, cle=None):
    entetes = {"X-Lynceus-Cle": cle} if cle else {}
    return client.post("/v1/analyses", json={"url": URL, "contenu_markdown": contenu}, headers=entetes)


# ---------- instance ouverte (défaut) ----------

def test_instance_ouverte_n_exige_aucune_cle(appli):
    """Un usage personnel auto-hébergé ne doit pas être compliqué par des clés."""
    client, _ = appli
    assert _analyser(client, CONTENU_TEST).status_code == 200
    assert client.get("/v1/meta").json()["capacites"]["cle_requise"] is False


# ---------- instance fermée ----------

def test_analyse_refusee_sans_cle(instance_fermee):
    client, _ = instance_fermee
    reponse = _analyser(client, CONTENU_TEST)
    assert reponse.status_code == 401
    assert "clé d'accès" in reponse.json()["detail"]


def test_analyse_acceptee_avec_cle_valide(instance_fermee):
    client, cle = instance_fermee
    assert _analyser(client, CONTENU_TEST, cle).status_code == 200


def test_cle_d_un_autre_emetteur_refusee(instance_fermee):
    """Une clé authentique mais émise par quelqu'un d'autre ne doit pas ouvrir cette instance."""
    client, _ = instance_fermee
    autre_privee, _ = generer_paire()
    cle_etrangere, _ = emettre(autre_privee)
    reponse = _analyser(client, CONTENU_TEST, cle_etrangere)
    assert reponse.status_code == 401
    assert "Signature invalide" in reponse.json()["detail"]


def test_meta_annonce_qu_une_cle_est_requise(instance_fermee):
    """Le client doit pouvoir le découvrir plutôt que de se heurter à un 401."""
    client, _ = instance_fermee
    assert client.get("/v1/meta").json()["capacites"]["cle_requise"] is True


def test_lookup_reste_accessible_sans_cle(instance_fermee):
    """Le lookup est bon marché et alimente le badge : l'exiger casserait l'expérience
    sans rien protéger — c'est l'analyse qui coûte de l'argent."""
    client, cle = instance_fermee
    _analyser(client, CONTENU_TEST, cle)
    from lynceus.normalisation import hacher_url

    assert client.get("/v1/lookup", params={"url_hash": hacher_url(URL)}).status_code == 200
    assert client.get("/v1/lookup-prefixe", params={"prefixe": hacher_url(URL)[:5]}).status_code == 200


# ---------- quota ----------

def test_quota_journalier_respecte(instance_fermee):
    client, cle = instance_fermee  # quota = 3
    for i in range(3):
        reponse = _analyser(client, CONTENU_TEST + f" Variante {i}.", cle)
        assert reponse.status_code == 200, f"analyse {i + 1} refusée à tort"

    refusee = _analyser(client, CONTENU_TEST + " Variante de trop.", cle)
    assert refusee.status_code == 429
    assert "Quota journalier atteint" in refusee.json()["detail"]


def test_cache_ne_consomme_pas_de_quota(instance_fermee):
    """Une page déjà dans l'annuaire ne coûte rien : la resservir ne doit pas être
    décomptée, sinon on pénaliserait la mutualisation qui fait tout l'intérêt du réseau."""
    client, cle = instance_fermee  # quota = 3
    assert _analyser(client, CONTENU_TEST, cle).status_code == 200

    for _ in range(10):
        reponse = _analyser(client, CONTENU_TEST, cle)  # même contenu : cache
        assert reponse.status_code == 200
        assert reponse.json()["en_cache"] is True

    # Le quota reste disponible pour de vraies analyses
    assert _analyser(client, CONTENU_TEST + " Nouveau contenu.", cle).status_code == 200


def test_quotas_independants_entre_cles(instance_fermee, tmp_path):
    """Le compteur est par clé : l'usage de l'un ne doit pas bloquer l'autre."""
    client, cle = instance_fermee
    privee, publique = generer_paire()
    # Même instance, seconde clé émise par le même émetteur : on reconstruit une appli
    # partageant la clé publique d'origine n'est pas possible ici, on vérifie donc la
    # séparation au niveau du compteur.
    from lynceus.annuaire import consommer_quota
    from lynceus.modeles import Base
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    moteur = create_engine(f"sqlite:///{tmp_path}/quotas.sqlite3")
    Base.metadata.create_all(moteur)
    with sessionmaker(bind=moteur)() as session:
        for _ in range(3):
            assert consommer_quota(session, "cle-A", 3)[0] is True
        assert consommer_quota(session, "cle-A", 3)[0] is False, "quota de A épuisé"
        assert consommer_quota(session, "cle-B", 3)[0] is True, "B ne doit pas être affectée"
