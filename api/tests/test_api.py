from fastapi.testclient import TestClient

from lynceus import extraction
from lynceus.main import AVERTISSEMENT_IA, creer_application
from lynceus.moteur import llm
from lynceus.normalisation import hacher_url
from tests.conftest import CONTENU_TEST, GRADE_ATTENDU, SCORE_ATTENDU, SORTIE_LLM, parametres_test

URL_TEST = "https://sante.exemple/remede?utm_source=infolettre"


def test_analyse_complete(appli):
    client, compteur = appli
    reponse = client.post("/v1/analyses", json={
        "url": URL_TEST, "contenu_markdown": CONTENU_TEST, "titre": "Le remède interdit",
    })
    assert reponse.status_code == 200, reponse.text
    donnees = reponse.json()
    assert donnees["en_cache"] is False
    carte = donnees["carte"]

    # Note calculée par le SERVEUR à partir des dimensions
    assert carte["note"]["score"] == SCORE_ATTENDU
    assert carte["note"]["grade"] == GRADE_ATTENDU
    assert carte["categorie"] == "pseudo_science"

    # Filtrage anti-hallucination et hors-référentiel
    assert {t["id"] for t in carte["techniques_detectees"]} == {"verite_cachee", "conflit_interet_commercial"}
    assert len(donnees["detections_rejetees"]) == 2

    # Champs posés par le serveur
    assert carte["url"] == URL_TEST
    assert carte["domaine"] == "sante.exemple"
    from lynceus.moteur import prompt as module_prompt
    assert carte["meta"]["prompt_version"] == module_prompt.resoudre_version("latest")
    assert AVERTISSEMENT_IA in carte["avertissements"]
    assert compteur["appels"] == 1


def test_cache_et_dedup_contenu(appli):
    client, compteur = appli
    r1 = client.post("/v1/analyses", json={"url": URL_TEST, "contenu_markdown": CONTENU_TEST})
    assert r1.json()["en_cache"] is False

    # Même URL, même contenu → cache
    r2 = client.post("/v1/analyses", json={"url": URL_TEST, "contenu_markdown": CONTENU_TEST})
    assert r2.json()["en_cache"] is True

    # Même contenu copié sous une AUTRE URL → cache aussi (dédup par content_hash)
    r3 = client.post("/v1/analyses", json={"url": "https://copieur.exemple/plagiat", "contenu_markdown": CONTENU_TEST})
    assert r3.json()["en_cache"] is True

    assert compteur["appels"] == 1  # un seul appel LLM pour les trois requêtes

    # La seconde URL est désormais connue de l'annuaire
    lookup = client.get("/v1/lookup", params={"url": "https://copieur.exemple/plagiat"}).json()
    assert lookup["statut"] == "connue"


def test_lookup(appli):
    client, _ = appli
    client.post("/v1/analyses", json={"url": URL_TEST, "contenu_markdown": CONTENU_TEST})

    # Par URL (normalisée côté serveur : les utm_* ne comptent pas)
    connue = client.get("/v1/lookup", params={"url": "https://sante.exemple/remede"}).json()
    assert connue["statut"] == "connue"
    assert connue["carte"]["note"]["grade"] == GRADE_ATTENDU
    assert connue["domaine"]["nb_analyses"] == 1

    # Par hash (le chemin de l'extension — aucune URL en clair)
    par_hash = client.get("/v1/lookup", params={"url_hash": hacher_url(URL_TEST)}).json()
    assert par_hash["statut"] == "connue"

    inconnue = client.get("/v1/lookup", params={"url": "https://jamais-vue.exemple/page"}).json()
    assert inconnue["statut"] == "inconnue" and inconnue["carte"] is None

    assert client.get("/v1/lookup").status_code == 400


def test_domaines_et_analyses(appli):
    client, _ = appli
    client.post("/v1/analyses", json={"url": URL_TEST, "contenu_markdown": CONTENU_TEST})

    profil = client.get("/v1/domaines/sante.exemple").json()
    assert profil["nb_analyses"] == 1
    assert profil["distribution_grades"] == {GRADE_ATTENDU: 1}
    assert client.get("/v1/domaines/inconnu.exemple").status_code == 404

    assert client.get("/v1/analyses/1").json()["carte"]["categorie"] == "pseudo_science"
    assert client.get("/v1/analyses/999").status_code == 404


def test_meta(appli):
    client, _ = appli
    meta = client.get("/v1/meta").json()
    from lynceus.moteur import prompt as module_prompt
    assert meta["prompt_version"] == module_prompt.resoudre_version("latest")
    assert meta["taxonomie"]["nb_techniques"] == 31
    assert meta["modele"] == "test/modele"


def test_erreurs_entree(appli):
    client, _ = appli
    assert client.post("/v1/analyses", json={}).status_code == 400
    assert client.post("/v1/analyses", json={"contenu_markdown": "trop court"}).status_code == 400
    assert client.post("/v1/analyses", json={"url": "ftp://x/y", "contenu_markdown": CONTENU_TEST}).status_code == 400


def test_rate_limit(tmp_path, monkeypatch):
    import json as json_

    monkeypatch.setattr(llm, "appeler", lambda messages, p, schema_json=None: json_.dumps(SORTIE_LLM, ensure_ascii=False))
    client = TestClient(creer_application(parametres_test(tmp_path, rate_limit_analyses=1)))

    r1 = client.post("/v1/analyses", json={"url": "https://a.exemple/1", "contenu_markdown": CONTENU_TEST})
    assert r1.status_code == 200
    # Contenu différent (hash différent) → travail LLM requis → limite atteinte
    r2 = client.post("/v1/analyses", json={"url": "https://a.exemple/2", "contenu_markdown": CONTENU_TEST + " Variante."})
    assert r2.status_code == 429
    # Mais le cache reste servi sans limite
    r3 = client.post("/v1/analyses", json={"url": "https://a.exemple/1", "contenu_markdown": CONTENU_TEST})
    assert r3.status_code == 200 and r3.json()["en_cache"] is True


def test_url_seule_avec_fetch_serveur(appli, monkeypatch):
    client, compteur = appli
    telechargements = {"n": 0}

    def faux_fetch(url):
        telechargements["n"] += 1
        return "Titre extrait", CONTENU_TEST + " Version distante."

    monkeypatch.setattr(extraction, "recuperer_markdown", faux_fetch)

    r1 = client.post("/v1/analyses", json={"url": "https://distant.exemple/article"})
    assert r1.status_code == 200
    assert r1.json()["en_cache"] is False
    assert r1.json()["carte"]["titre"] == "Titre extrait"
    assert telechargements["n"] == 1

    # URL déjà connue → réponse annuaire, AUCUN nouveau téléchargement ni appel LLM
    r2 = client.post("/v1/analyses", json={"url": "https://distant.exemple/article"})
    assert r2.json()["en_cache"] is True
    assert telechargements["n"] == 1
    assert compteur["appels"] == 1


def test_retry_sur_json_invalide(tmp_path, monkeypatch):
    import json as json_

    tentatives = {"n": 0}

    def llm_hesitant(messages, p, schema_json=None):
        tentatives["n"] += 1
        if tentatives["n"] == 1:
            return "Voici mon analyse : ce n'est pas du JSON."
        return json_.dumps(SORTIE_LLM, ensure_ascii=False)

    monkeypatch.setattr(llm, "appeler", llm_hesitant)
    client = TestClient(creer_application(parametres_test(tmp_path)))
    reponse = client.post("/v1/analyses", json={"url": URL_TEST, "contenu_markdown": CONTENU_TEST})
    assert reponse.status_code == 200
    assert tentatives["n"] == 2  # l'erreur a été renvoyée au modèle, qui a corrigé


def test_contenu_tronque_signale_dans_la_carte(appli):
    """La carte est mise en cache et resservie à d'autres lecteurs : une analyse portant sur
    un texte partiel doit le dire, sinon elle circulerait comme si elle couvrait tout."""
    from lynceus.main import AVERTISSEMENT_TRONQUE

    client, _ = appli
    reponse = client.post("/v1/analyses", json={
        "url": "https://exemple.fr/long-article",
        "contenu_markdown": CONTENU_TEST,
        "tronque": True,
    })
    assert reponse.status_code == 200
    assert AVERTISSEMENT_TRONQUE in reponse.json()["carte"]["avertissements"]


def test_contenu_complet_sans_avertissement_de_troncature(appli):
    from lynceus.main import AVERTISSEMENT_TRONQUE

    client, _ = appli
    reponse = client.post("/v1/analyses", json={
        "url": "https://exemple.fr/article-court", "contenu_markdown": CONTENU_TEST,
    })
    assert AVERTISSEMENT_TRONQUE not in reponse.json()["carte"]["avertissements"]


def test_point_de_sante(appli):
    """L'orchestrateur s'en sert pour savoir si l'instance peut servir du trafic."""
    client, _ = appli
    reponse = client.get("/sante")
    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "ok"


def test_point_de_sante_signale_une_base_injoignable(tmp_path, monkeypatch):
    """Un processus vivant mais sans base doit être signalé en panne : sinon
    l'orchestrateur lui enverrait du trafic qu'il ne peut pas servir."""
    import json as json_

    from lynceus.main import creer_application
    from lynceus.moteur import llm
    from tests.conftest import SORTIE_LLM, parametres_test

    monkeypatch.setattr(llm, "appeler", lambda m, p, schema_json=None: json_.dumps(SORTIE_LLM))
    client = TestClient(creer_application(parametres_test(tmp_path)))

    # On coupe la base après démarrage, comme une panne en cours d'exploitation.
    def base_hs(*args, **kwargs):
        raise RuntimeError("connexion perdue")

    monkeypatch.setattr("sqlalchemy.orm.Session.execute", base_hs)
    reponse = client.get("/sante")
    assert reponse.status_code == 503
