"""Lookup k-anonyme et signalements — les deux engagements de la charte rendus exécutables :
§4 (le serveur ne doit pas pouvoir savoir quelle page est consultée) et §6 (toute analyse
est contestable)."""

from lynceus.annuaire import LONGUEUR_PREFIXE
from lynceus.normalisation import hacher_url
from tests.conftest import CONTENU_TEST, GRADE_ATTENDU

URL_A = "https://sante.exemple/remede"
URL_B = "https://autre.exemple/article"


def _analyser(client, url, contenu=CONTENU_TEST):
    return client.post("/v1/analyses", json={"url": url, "contenu_markdown": contenu})


# ---------- lookup k-anonyme ----------

def test_prefixe_retourne_les_correspondances(appli):
    client, _ = appli
    _analyser(client, URL_A)
    prefixe = hacher_url(URL_A)[:LONGUEUR_PREFIXE]

    reponse = client.get("/v1/lookup-prefixe", params={"prefixe": prefixe})
    assert reponse.status_code == 200
    donnees = reponse.json()
    assert donnees["prefixe"] == prefixe.lower()
    assert len(donnees["correspondances"]) == 1
    assert donnees["correspondances"][0]["grade"] == GRADE_ATTENDU


def test_le_serveur_ne_recoit_jamais_le_hash_complet(appli):
    """LA propriété de vie privée : la réponse ne contient que des SUFFIXES. Le serveur ne
    voit passer qu'un préfixe partagé par de nombreuses URL, jamais l'empreinte complète."""
    client, _ = appli
    _analyser(client, URL_A)
    hash_complet = hacher_url(URL_A)
    prefixe = hash_complet[:LONGUEUR_PREFIXE]

    correspondances = client.get("/v1/lookup-prefixe", params={"prefixe": prefixe}).json()["correspondances"]
    suffixe = correspondances[0]["suffixe"]

    assert hash_complet not in str(correspondances), "le hash complet ne doit jamais être renvoyé"
    assert not suffixe.startswith(prefixe)
    # Le client reconstitue lui-même l'empreinte pour trancher, localement.
    assert prefixe + suffixe == hash_complet


def test_prefixe_inconnu_retourne_une_liste_vide(appli):
    client, _ = appli
    reponse = client.get("/v1/lookup-prefixe", params={"prefixe": "fffff"})
    assert reponse.status_code == 200
    assert reponse.json()["correspondances"] == []


def test_prefixe_de_mauvaise_longueur_refuse(appli):
    client, _ = appli
    for mauvais in ("abc", "abcdef", ""):
        assert client.get("/v1/lookup-prefixe", params={"prefixe": mauvais}).status_code == 422


def test_prefixe_non_hexadecimal_refuse(appli):
    client, _ = appli
    assert client.get("/v1/lookup-prefixe", params={"prefixe": "zzzzz"}).status_code == 422


def test_prefixe_insensible_a_la_casse(appli):
    client, _ = appli
    _analyser(client, URL_A)
    prefixe = hacher_url(URL_A)[:LONGUEUR_PREFIXE]
    minuscules = client.get("/v1/lookup-prefixe", params={"prefixe": prefixe.lower()}).json()
    majuscules = client.get("/v1/lookup-prefixe", params={"prefixe": prefixe.upper()}).json()
    assert minuscules["correspondances"] == majuscules["correspondances"]


def test_plusieurs_pages_sous_le_meme_prefixe(appli, monkeypatch):
    """Le seau doit pouvoir contenir plusieurs pages — c'est ce qui fonde l'anonymat."""
    client, _ = appli
    _analyser(client, URL_A)
    _analyser(client, URL_B, CONTENU_TEST + " Variante distincte.")

    # On interroge chaque préfixe réel : chaque page doit être retrouvable via le sien.
    for url in (URL_A, URL_B):
        prefixe = hacher_url(url)[:LONGUEUR_PREFIXE]
        correspondances = client.get("/v1/lookup-prefixe", params={"prefixe": prefixe}).json()["correspondances"]
        suffixes = {c["suffixe"] for c in correspondances}
        assert hacher_url(url)[LONGUEUR_PREFIXE:] in suffixes


# ---------- signalements ----------

def test_signalement_enregistre(appli):
    client, _ = appli
    _analyser(client, URL_A)

    reponse = client.post("/v1/signalements", json={
        "analyse_id": 1,
        "motif": "categorie_erronee",
        "message": "Ce site est satirique, pas complotiste — voir sa page « à propos ».",
    })
    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "nouveau"


def test_signalement_visible_sur_l_analyse(appli):
    """Une analyse contestée doit se voir : le compteur est public (charte §6)."""
    client, _ = appli
    _analyser(client, URL_A)
    assert client.get("/v1/analyses/1").json()["signalements"] == 0

    client.post("/v1/signalements", json={
        "analyse_id": 1, "motif": "note_injustifiee", "message": "La note me semble trop sévère ici.",
    })
    assert client.get("/v1/analyses/1").json()["signalements"] == 1


def test_signalement_sur_analyse_inconnue(appli):
    client, _ = appli
    reponse = client.post("/v1/signalements", json={
        "analyse_id": 999, "motif": "autre", "message": "Analyse qui n'existe pas.",
    })
    assert reponse.status_code == 404


def test_motif_inconnu_refuse(appli):
    client, _ = appli
    _analyser(client, URL_A)
    reponse = client.post("/v1/signalements", json={
        "analyse_id": 1, "motif": "motif_invente", "message": "Message suffisamment long.",
    })
    assert reponse.status_code == 400
    assert "Motifs acceptés" in reponse.json()["detail"]


def test_message_trop_court_refuse(appli):
    """Un signalement doit être argumenté pour être exploitable."""
    client, _ = appli
    _analyser(client, URL_A)
    reponse = client.post("/v1/signalements", json={
        "analyse_id": 1, "motif": "autre", "message": "nul",
    })
    assert reponse.status_code == 422


def test_contact_optionnel(appli):
    """Un signalement est anonyme par défaut : aucune donnée personnelle exigée."""
    client, _ = appli
    _analyser(client, URL_A)
    sans_contact = client.post("/v1/signalements", json={
        "analyse_id": 1, "motif": "droit_de_reponse", "message": "Je suis l'éditeur de ce site.",
    })
    assert sans_contact.status_code == 200

    avec_contact = client.post("/v1/signalements", json={
        "analyse_id": 1, "motif": "droit_de_reponse",
        "message": "Je suis l'éditeur et souhaite une réponse.",
        "contact": "editeur@exemple.fr",
    })
    assert avec_contact.status_code == 200


def test_motifs_exposes_par_l_api(appli):
    client, _ = appli
    motifs = client.get("/v1/motifs-signalement").json()["motifs"]
    assert "droit_de_reponse" in motifs
    assert "categorie_erronee" in motifs


def test_meta_annonce_les_capacites(appli):
    """Un client doit pouvoir découvrir ce que l'instance sait faire, sans le coder en dur."""
    client, _ = appli
    capacites = client.get("/v1/meta").json()["capacites"]
    assert capacites["lookup_k_anonyme"] is True
    assert capacites["longueur_prefixe"] == LONGUEUR_PREFIXE
    assert capacites["signalements"] is True
    assert "droit_de_reponse" in capacites["motifs_signalement"]
