"""Mesure d'audience du portail, faite par le serveur.

Trois propriétés valent plus que le reste, et sont testées comme telles :
  · rien ne part tant que les deux réglages ne sont pas renseignés ;
  · l'annuaire et les appels de l'extension ne sont jamais comptés, parce que la page de
    confidentialité promet qu'il n'existe aucun journal de ces consultations ;
  · un Umami absent ne change rien pour le visiteur.
"""

import json as json_
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from lynceus.portail import audience, creer_portail
from tests.test_portail import parametres_portail_test

UMAMI = "https://umami.interne.test"
SITE = "00000000-0000-4000-8000-000000000000"


class FauxUmami:
    """Enregistre ce que le portail lui envoie, ou tombe en panne sur demande."""

    def __init__(self, en_panne: bool = False):
        self.recues: list[httpx.Request] = []
        self.en_panne = en_panne

    def __call__(self, requete: httpx.Request) -> httpx.Response:
        if self.en_panne:
            raise httpx.ConnectError("réseau interne injoignable", request=requete)
        self.recues.append(requete)
        return httpx.Response(200, json={"cache": "jeton"})

    def attendre(self, nombre: int = 1, delai_s: float = 2.0) -> list[httpx.Request]:
        """L'envoi est une tâche de fond sur la boucle du portail : on lui laisse le
        temps d'arriver, sans jamais attendre plus que nécessaire."""
        limite = time.monotonic() + delai_s
        while len(self.recues) < nombre and time.monotonic() < limite:
            time.sleep(0.01)
        return self.recues


def _portail(faux: FauxUmami | None, **surcharges):
    reglages = dict(umami_url=UMAMI, umami_site=SITE) if faux is not None else {}
    reglages.update(surcharges)
    p = parametres_portail_test(**reglages)
    client = TestClient(creer_portail(p))
    client.__enter__()
    if faux is not None:
        client.app.state.audience.client = httpx.AsyncClient(transport=httpx.MockTransport(faux))
    return client


@pytest.fixture
def mesure():
    faux = FauxUmami()
    client = _portail(faux)
    yield client, faux
    client.__exit__(None, None, None)


# ------------------------------------------------------------------ ce qui part

def test_une_page_vue_est_signalee_avec_ce_que_la_page_de_confidentialite_decrit(mesure):
    client, faux = mesure
    reponse = client.get("/methodologie", headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Firefox/130.0",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.5",
        "Referer": "https://exemple.fr/billet?utm_source=lettre#section",
        "Host": "portail.test",
    })
    assert reponse.status_code == 200

    [requete] = faux.attendre()
    assert str(requete.url) == f"{UMAMI}/api/send"
    charge = json_.loads(requete.content)
    assert charge["type"] == "event"
    assert charge["payload"] == {
        "website": SITE,
        "hostname": "portail.test",
        "url": "/methodologie",
        "referrer": "https://exemple.fr/billet",  # ni paramètres, ni fragment
        "language": "fr-FR",
        "title": "",
    }
    assert requete.headers["User-Agent"].startswith("Mozilla/5.0")


def test_le_prefixe_de_langue_reste_dans_l_adresse_comptee(mesure):
    """Deux langues, deux pages : la mesure doit pouvoir les distinguer."""
    client, faux = mesure
    assert client.get("/en/methodologie").status_code == 200
    [requete] = faux.attendre()
    assert json_.loads(requete.content)["payload"]["url"] == "/en/methodologie"


def test_le_telechargement_de_l_extension_compte_comme_une_vue(tmp_path):
    """Ce n'est pas une page HTML, mais c'est la seule mesure qui dise si le portail
    sert à quelque chose."""
    import zipfile

    with zipfile.ZipFile(tmp_path / "lynceus-extension-v9.9.9.zip", "w") as archive:
        archive.writestr("manifest.json", "{}")
    faux = FauxUmami()
    client = _portail(faux, paquets=str(tmp_path))
    try:
        assert client.get("/telecharger").status_code == 200
        [requete] = faux.attendre()
        assert json_.loads(requete.content)["payload"]["url"] == "/telecharger"
    finally:
        client.__exit__(None, None, None)


# ------------------------------------------------------------------ l'adresse et le pays

def test_l_adresse_reelle_part_sous_l_en_tete_que_lit_umami_en_premier():
    """Sans adresse fiable, tous les visiteurs d'un même navigateur fusionnent en un seul.
    CF-Connecting-IP précède X-Forwarded-For dans la liste qu'Umami parcourt, et ne se
    concatène pas quand un proxy s'intercale : c'est lui qui porte l'adresse."""
    faux = FauxUmami()
    client = _portail(faux, entete_ip_reelle="CF-Connecting-IP")
    try:
        client.get("/", headers={"CF-Connecting-IP": "203.0.113.7", "CF-IPCountry": "RE"})
        [requete] = faux.attendre()
        assert requete.headers["CF-Connecting-IP"] == "203.0.113.7"
        assert requete.headers["X-Forwarded-For"] == "203.0.113.7"
        assert requete.headers["CF-IPCountry"] == "RE"
    finally:
        client.__exit__(None, None, None)


def test_sans_en_tete_configure_l_adresse_annoncee_est_ignoree(mesure):
    """Même règle que la limite de débit : un en-tête non configuré ne vaut rien, sinon
    n'importe qui se ferait passer pour n'importe où."""
    client, faux = mesure
    client.get("/", headers={"CF-Connecting-IP": "203.0.113.7"})
    [requete] = faux.attendre()
    assert requete.headers["CF-Connecting-IP"] == "testclient"  # l'adresse de la connexion
    assert "CF-IPCountry" not in requete.headers


# ------------------------------------------------------------------ ce qui ne part jamais

@pytest.mark.parametrize("chemin", ["/annuaire/recherche?q=https://exemple.fr/article",
                                    "/en/annuaire/recherche?q=exemple.fr",
                                    "/sante", "/statique/htmx.min.js"])
def test_l_annuaire_et_le_reste_ne_sont_jamais_comptes(mesure, chemin):
    client, faux = mesure
    client.get(chemin)
    # Une page qui, elle, est comptée : si elle arrive seule, l'autre n'est pas passée.
    client.get("/charte")
    [requete] = faux.attendre()
    assert json_.loads(requete.content)["payload"]["url"] == "/charte"


def test_une_inscription_n_est_pas_comptee(mesure):
    client, faux = mesure
    client.post("/v1/inscription")
    client.get("/charte")
    [requete] = faux.attendre()
    assert json_.loads(requete.content)["payload"]["url"] == "/charte"


def test_une_page_absente_n_est_pas_une_page_lue(mesure):
    client, faux = mesure
    assert client.get("/nulle-part").status_code == 404
    client.get("/charte")
    [requete] = faux.attendre()
    assert json_.loads(requete.content)["payload"]["url"] == "/charte"


def test_sans_reglage_rien_ne_part_et_la_page_n_en_parle_pas():
    client = _portail(None)
    try:
        assert not client.app.state.audience.active
        page = client.get("/confidentialite").text
        assert "Mesure d'audience" not in page
        assert "pas de traceur." in page
    finally:
        client.__exit__(None, None, None)


def test_un_seul_des_deux_reglages_ne_suffit_pas():
    client = _portail(None, umami_url=UMAMI)
    try:
        assert not client.app.state.audience.active
    finally:
        client.__exit__(None, None, None)


# ------------------------------------------------------------------ la page de confidentialité

def test_la_page_de_confidentialite_decrit_la_mesure_quand_elle_existe(mesure):
    client, _ = mesure
    page = client.get("/confidentialite").text
    assert "Mesure d'audience du site" in page
    assert "identifiant pseudonyme" in page
    assert "Umami" in page
    assert "sans cookie ni script" in page
    page_en = client.get("/en/confidentialite").text
    assert "Site audience measurement" in page_en
    assert "pseudonymous identifier" in page_en


# ------------------------------------------------------------------ Umami absent

def test_un_umami_injoignable_ne_change_rien_pour_le_visiteur(capsys):
    faux = FauxUmami(en_panne=True)
    client = _portail(faux)
    try:
        for _ in range(3):
            assert client.get("/charte").status_code == 200
    finally:
        client.__exit__(None, None, None)  # attend les envois en cours
    assert client.app.state.audience.en_panne
    # Une seule ligne pour trois échecs : l'avertissement dit la panne, pas chaque page.
    assert capsys.readouterr().err.count("Umami injoignable") == 1


# ------------------------------------------------------------------ fonctions pures

@pytest.mark.parametrize("methode, chemin, statut, type_contenu, attendu", [
    ("GET", "/methodologie", 200, "text/html; charset=utf-8", True),
    ("GET", "/telecharger", 200, "application/zip", True),
    ("GET", "/annuaire", 200, "text/html; charset=utf-8", True),
    ("GET", "/annuaire/recherche", 200, "text/html; charset=utf-8", False),
    ("GET", "/v1/meta", 200, "application/json", False),
    ("POST", "/contester", 200, "text/html; charset=utf-8", False),
    ("GET", "/charte", 302, "text/html; charset=utf-8", False),
    ("GET", "/sante", 200, "application/json", False),
])
def test_ce_qui_est_mesurable(methode, chemin, statut, type_contenu, attendu):
    assert audience.mesurable(methode, chemin, statut, type_contenu) is attendu
