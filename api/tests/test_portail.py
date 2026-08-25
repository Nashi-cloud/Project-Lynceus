"""Portail public — pages, inscription, annuaire, contestation.

Deux propriétés comptent plus que l'affichage et sont testées comme telles :
  · une clé émise par le portail est acceptée par une vraie instance (bout en bout) ;
  · une recherche par adresse ne transmet à l'instance qu'un préfixe d'empreinte.
"""

import io
import json as json_
import zipfile

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from lynceus.annuaire import LONGUEUR_PREFIXE
from lynceus.cles import generer_paire
from lynceus.main import creer_application
from lynceus.moteur import llm, notation, prompt
from lynceus.normalisation import hacher_url
from lynceus.portail import FICHIER_PORTAIL, creer_portail
from lynceus.portail.config import ParametresPortail
from lynceus.portail.contenu import paquet_le_plus_recent
from lynceus.portail import RACINE
from tests.conftest import CONTENU_TEST, SORTIE_LLM, parametres_test

URL = "https://exemple.fr/article"


def parametres_portail_test(**surcharges) -> ParametresPortail:
    """Comme pour l'API : configuration explicite, pour ne pas hériter du .env de la machine."""
    defauts = dict(nom="Lynceus", contact="", cle_privee="", instance="",
                   instance_interne="", paquets="", adresse="", cles_par_ip_jour=0)
    defauts.update(surcharges)
    return ParametresPortail(**defauts)


@pytest.fixture
def portail():
    """Portail émettant des clés, sans instance joignable."""
    privee, publique = generer_paire()
    p = parametres_portail_test(cle_privee=privee, instance="https://instance.test")
    with TestClient(creer_portail(p)) as client:
        yield client, publique


def brancher_sur(client_portail: TestClient, application: FastAPI) -> None:
    """Fait passer les appels sortants du portail par une application ASGI en mémoire.

    Le portail parle à l'instance par HTTP, jamais par la base : on peut donc lui
    substituer n'importe quelle application, y compris une vraie API."""
    client_portail.app.state.client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application), base_url="http://instance.test"
    )


# ------------------------------------------------------------------ pages

@pytest.mark.parametrize("chemin", ["/", "/installer", "/methodologie", "/taxonomie",
                                    "/charte", "/auto-hebergement", "/annuaire", "/contester"])
def test_les_pages_se_rendent(portail, chemin):
    client, _ = portail
    reponse = client.get(chemin)
    assert reponse.status_code == 200
    assert reponse.headers["content-type"].startswith("text/html")


def test_la_taxonomie_affichee_est_celle_du_moteur():
    """La page ne recopie pas le référentiel : elle l'affiche. Aucune technique ne doit
    manquer, sans quoi le site promettrait une liste fermée qu'il ne montre pas en entier."""
    p = parametres_portail_test()
    with TestClient(creer_portail(p)) as client:
        html = client.get("/taxonomie").text
    for identifiant in prompt.charger_taxonomie():
        assert identifiant in html, f"{identifiant} absent de la page publique"


def test_la_methodologie_affiche_les_vraies_ponderations():
    """Publier des pondérations différentes de celles appliquées serait le pire des
    manquements à la transparence : la page serait fausse tout en s'en réclamant."""
    p = parametres_portail_test()
    with TestClient(creer_portail(p)) as client:
        html = client.get("/methodologie").text
    for poids in notation.POIDS.values():
        assert f"{int(poids * 100)} %" in html
    for seuil, grade in notation.SEUILS:
        assert f">{grade}<" in html and str(seuil) in html


def test_le_recit_ne_masque_rien_sans_javascript(portail):
    """Le contenu de l'accueil ne doit dépendre d'aucun script : c'est la classe posée
    par le navigateur qui active l'apparition, pas le CSS seul."""
    client, _ = portail
    html = client.get("/").text
    assert "Un homme à la proue" in html and "js-anime" in html


# ------------------------------------------------------------ inscription

def test_une_cle_emise_par_le_portail_est_acceptee_par_une_instance(portail, tmp_path, monkeypatch):
    """Le test qui compte : portail et instance ne partagent aucun secret, seulement la
    clé publique. Si l'émission et la validation divergeaient, l'inscription délivrerait
    des clés inutilisables — et personne ne s'en apercevrait avant les utilisateurs."""
    client, publique = portail
    billet = client.post("/v1/inscription").json()

    monkeypatch.setattr(llm, "appeler", lambda m, p, schema_json=None: json_.dumps(SORTIE_LLM))
    api = TestClient(creer_application(parametres_test(tmp_path, cle_publique=publique)))

    sans_cle = api.post("/v1/analyses", json={"url": URL, "contenu_markdown": CONTENU_TEST})
    assert sans_cle.status_code == 401

    avec_cle = api.post("/v1/analyses", json={"url": URL, "contenu_markdown": CONTENU_TEST},
                        headers={"X-Lynceus-Cle": billet["cle"]})
    assert avec_cle.status_code == 200
    assert billet["instance"] == "https://instance.test"
    assert billet["quota_jour"] > 0


def test_le_billet_ne_contient_aucune_donnee_personnelle(portail):
    """Une clé anonyme qui porterait un identifiant stable de son porteur n'aurait
    d'anonyme que le nom."""
    client, _ = portail
    billet = client.post("/v1/inscription").json()
    assert set(billet) == {"instance", "cle", "quota_jour", "expire_le", "portail"}
    premier = client.post("/v1/inscription").json()["cle"]
    assert premier != billet["cle"]  # deux clés distinctes, aucun identifiant réutilisé


def test_sans_cle_privee_l_inscription_le_dit_clairement():
    p = parametres_portail_test(instance="https://instance.test")
    with TestClient(creer_portail(p)) as client:
        reponse = client.post("/v1/inscription")
    assert reponse.status_code == 503
    assert "ne délivre pas de clés" in reponse.json()["detail"]


def test_sans_instance_declaree_l_inscription_refuse():
    """Délivrer une clé sans dire où l'utiliser produirait un billet inexploitable."""
    privee, _ = generer_paire()
    p = parametres_portail_test(cle_privee=privee)
    with TestClient(creer_portail(p)) as client:
        assert client.post("/v1/inscription").status_code == 503


def test_l_inscription_est_illimitee_par_defaut(portail):
    """Choix assumé : l'inscription est libre. Le plafond existe mais reste à zéro."""
    client, _ = portail
    for _ in range(5):
        assert client.post("/v1/inscription").status_code == 200


def test_le_plafond_par_adresse_s_applique_quand_il_est_actif():
    privee, _ = generer_paire()
    p = parametres_portail_test(cle_privee=privee, instance="https://instance.test",
                                cles_par_ip_jour=2)
    with TestClient(creer_portail(p)) as client:
        assert client.post("/v1/inscription").status_code == 200
        assert client.post("/v1/inscription").status_code == 200
        refus = client.post("/v1/inscription")
        assert refus.status_code == 429
        assert "hébergez votre propre instance" in refus.json()["detail"]


# --------------------------------------------------------------- annuaire

class _InstanceEspionne:
    """Instance minimale qui note ce qu'on lui a demandé."""

    def __init__(self) -> None:
        self.prefixes: list[str] = []
        self.app = FastAPI()

        @self.app.get("/v1/lookup-prefixe")
        def lookup_prefixe(prefixe: str):
            self.prefixes.append(prefixe)
            return {"prefixe": prefixe, "correspondances": []}

        @self.app.get("/v1/domaines/{domaine}")
        def domaines(domaine: str):
            return {"domaine": domaine, "nb_analyses": 3, "score_moyen": 72.0,
                    "distribution_grades": {"A": 1, "B": 2}, "maj_le": "2026-08-25T00:00:00"}


def test_la_recherche_par_adresse_n_envoie_qu_un_prefixe(portail):
    """Charte §4 : l'instance ne doit pas pouvoir savoir quelle page est consultée. Cette
    garantie vaut aussi lorsque la demande passe par le portail — c'est justement le cas
    où il serait tentant de transmettre l'empreinte entière « puisque c'est un serveur »."""
    client, _ = portail
    espionne = _InstanceEspionne()
    brancher_sur(client, espionne.app)

    url = "https://exemple.fr/un/article/precis"
    reponse = client.get("/annuaire/recherche", params={"q": url})

    assert reponse.status_code == 200
    assert espionne.prefixes == [hacher_url(url)[:LONGUEUR_PREFIXE]]
    assert len(espionne.prefixes[0]) == LONGUEUR_PREFIXE
    assert hacher_url(url) not in reponse.request.url.query.decode()


def test_la_recherche_par_domaine_affiche_le_profil(portail):
    client, _ = portail
    brancher_sur(client, _InstanceEspionne().app)
    html = client.get("/annuaire/recherche", params={"q": "Exemple.FR"}).text
    assert "exemple.fr" in html and "3 pages analysées" in html


def test_une_instance_injoignable_degrade_sans_planter(portail):
    """Le portail sert ses pages sans l'instance : une panne de l'une ne doit pas
    produire une erreur 500 sur l'autre."""
    client, _ = portail
    client.app.state.client = httpx.AsyncClient(base_url="http://instance-eteinte.invalid")
    reponse = client.get("/annuaire/recherche", params={"q": "exemple.fr"})
    assert reponse.status_code == 200
    assert "injoignable" in reponse.text


def test_la_sante_distingue_le_portail_de_l_instance(portail):
    client, _ = portail
    client.app.state.client = httpx.AsyncClient(base_url="http://instance-eteinte.invalid")
    sante = client.get("/sante").json()
    assert sante["statut"] == "ok"           # le portail va bien…
    assert sante["instance"] == "injoignable"  # …et le dit de l'instance, sans confondre
    assert sante["emission_de_cles"] is True


# ----------------------------------------------------------- contestation

def test_la_contestation_est_transmise_a_l_instance(portail, tmp_path, monkeypatch):
    """Charte §6 de bout en bout : contester depuis le site, sans extension."""
    client, _ = portail
    monkeypatch.setattr(llm, "appeler", lambda m, p, schema_json=None: json_.dumps(SORTIE_LLM))
    api = creer_application(parametres_test(tmp_path))
    with TestClient(api) as api_client:
        api_client.post("/v1/analyses", json={"url": URL, "contenu_markdown": CONTENU_TEST})
    brancher_sur(client, api)

    reponse = client.post("/contester", data={
        "analyse_id": 1, "motif": "droit_de_reponse",
        "message": "Je suis l'éditeur de ce site et cette analyse me paraît fausse.",
    })
    assert reponse.status_code == 200
    assert "enregistrée" in reponse.text


def test_une_contestation_refusee_est_annoncee_comme_telle(portail, tmp_path):
    """Le pire retour possible serait « merci » alors que rien n'a été enregistré."""
    client, _ = portail
    brancher_sur(client, creer_application(parametres_test(tmp_path)))
    reponse = client.post("/contester", data={
        "analyse_id": 99999, "motif": "autre", "message": "Analyse qui n'existe pas.",
    })
    assert "refusée" in reponse.text and "Analyse inconnue" in reponse.text


# ------------------------------------------------------------ paquet zip

def _archive(chemin, entrees=None):
    """Écrit un zip minimal mais réel : les tests de téléchargement le rouvrent."""
    with zipfile.ZipFile(chemin, "w") as z:
        for nom, contenu_ in (entrees or {"manifest.json": '{"version":"1.0.0"}'}).items():
            z.writestr(nom, contenu_)


def test_le_paquet_propose_est_la_version_la_plus_haute(tmp_path):
    """Tri par version, pas par date de fichier : restaurer une sauvegarde ne doit pas
    faire régresser ce qui est distribué."""
    for nom in ("lynceus-extension-v0.9.0.zip", "lynceus-extension-v0.10.0.zip",
                "lynceus-extension-v0.2.0.zip", "brouillon.zip"):
        _archive(tmp_path / nom)
    (tmp_path / "lynceus-extension-v0.9.0.zip").touch()  # la plus récente sur le disque

    paquet = paquet_le_plus_recent(str(tmp_path))
    assert paquet["version"] == "0.10.0"


def test_le_paquet_du_volume_l_emporte_sur_celui_de_l_image(tmp_path):
    """L'image embarque un paquet pour qu'un déploiement neuf ne parte pas les mains vides,
    et un zip déposé dans le volume publie une mise à jour sans reconstruire l'image. Le
    départage se fait sur la version, jamais sur l'ordre des dossiers."""
    image, volume = tmp_path / "image", tmp_path / "volume"
    image.mkdir(); volume.mkdir()
    _archive(image / "lynceus-extension-v1.0.0.zip")
    _archive(volume / "lynceus-extension-v1.1.0.zip")

    dossiers = f"{volume},{image}"
    assert paquet_le_plus_recent(dossiers)["version"] == "1.1.0"

    # Un zip plus ancien déposé dans le volume ne doit PAS faire régresser la distribution.
    _archive(volume / "lynceus-extension-v0.5.0.zip")
    assert paquet_le_plus_recent(dossiers)["version"] == "1.1.0"


def test_un_dossier_absent_ne_fait_pas_echouer_la_resolution(tmp_path):
    """Le volume peut ne pas être monté : le portail doit alors servir le paquet de l'image
    plutôt que de tomber en panne."""
    _archive(tmp_path / "lynceus-extension-v1.0.0.zip")
    assert paquet_le_plus_recent(f"/inexistant,{tmp_path}")["version"] == "1.0.0"
    assert paquet_le_plus_recent("/inexistant,/pas-davantage") is None


def test_un_paquet_depose_apres_le_demarrage_est_propose_sans_redemarrage(tmp_path):
    """Régression : la version était résolue une fois pour toutes à la création de
    l'application, si bien que déposer un zip ne changeait rien jusqu'au redémarrage,
    contrairement à ce qu'annonçait la documentation de déploiement."""
    p = parametres_portail_test(paquets=str(tmp_path))
    with TestClient(creer_portail(p)) as client:
        assert client.get("/sante").json()["paquet"] is None
        assert client.get("/telecharger").status_code == 503

        _archive(tmp_path / "lynceus-extension-v2.0.0.zip")

        assert client.get("/sante").json()["paquet"] == "2.0.0"
        assert client.get("/telecharger").status_code == 200
        assert "2.0.0" in client.get("/installer").text


# ------------------------------------------------- adresse dans l'archive

def test_l_archive_telechargee_porte_l_adresse_du_portail(tmp_path):
    """Le paquet publié est neutre, pour qu'une seule image serve à tous les portails.
    L'adresse est ajoutée à la volée : sans elle, chaque personne devrait recopier
    l'adresse du portail à la main avant de pouvoir demander une clé."""
    _archive(tmp_path / "lynceus-extension-v1.0.0.zip",
             {"manifest.json": '{"version":"1.0.0"}', "fond.js": "// code"})
    p = parametres_portail_test(paquets=str(tmp_path))
    with TestClient(creer_portail(p)) as client:
        reponse = client.get("/telecharger")

    assert reponse.headers["content-type"] == "application/zip"
    archive = zipfile.ZipFile(io.BytesIO(reponse.content))
    assert archive.testzip() is None, "archive corrompue"
    assert set(archive.namelist()) == {"manifest.json", "fond.js", FICHIER_PORTAIL}
    assert json_.loads(archive.read(FICHIER_PORTAIL))["portail"] == "http://testserver"


def test_l_adresse_configuree_prime_sur_celle_deduite_de_la_requete(tmp_path):
    """Derrière un tunnel, l'application ne voit qu'un nom d'hôte interne. Une adresse
    explicite doit donc pouvoir être imposée."""
    _archive(tmp_path / "lynceus-extension-v1.0.0.zip")
    p = parametres_portail_test(paquets=str(tmp_path), adresse="https://lynceus.exemple.fr/")
    with TestClient(creer_portail(p)) as client:
        archive = zipfile.ZipFile(io.BytesIO(client.get("/telecharger").content))
    assert json_.loads(archive.read(FICHIER_PORTAIL))["portail"] == "https://lynceus.exemple.fr"


def test_le_schema_du_proxy_est_respecte(tmp_path):
    """Servi derrière un tunnel HTTPS, le portail ne doit pas inscrire une adresse en
    http : l'extension enverrait alors ses demandes de clé en clair, ou échouerait."""
    _archive(tmp_path / "lynceus-extension-v1.0.0.zip")
    p = parametres_portail_test(paquets=str(tmp_path))
    with TestClient(creer_portail(p)) as client:
        reponse = client.get("/telecharger", headers={"X-Forwarded-Proto": "https"})
    archive = zipfile.ZipFile(io.BytesIO(reponse.content))
    assert json_.loads(archive.read(FICHIER_PORTAIL))["portail"].startswith("https://")


def test_une_adresse_deja_presente_dans_l_archive_est_remplacee(tmp_path):
    """Un paquet construit localement avec --portail, redéposé sur un autre portail, ne
    doit pas se retrouver avec deux adresses contradictoires."""
    _archive(tmp_path / "lynceus-extension-v1.0.0.zip",
             {"manifest.json": "{}", FICHIER_PORTAIL: '{"portail": "https://ancien.test"}'})
    p = parametres_portail_test(paquets=str(tmp_path), adresse="https://nouveau.test")
    with TestClient(creer_portail(p)) as client:
        archive = zipfile.ZipFile(io.BytesIO(client.get("/telecharger").content))
    assert archive.namelist().count(FICHIER_PORTAIL) == 1
    assert json_.loads(archive.read(FICHIER_PORTAIL))["portail"] == "https://nouveau.test"


def test_sans_paquet_le_telechargement_explique_quoi_faire(portail):
    client, _ = portail
    reponse = client.get("/telecharger")
    assert reponse.status_code == 503
    assert "npm run paquet" in reponse.json()["detail"]


def test_le_telechargement_sert_l_archive(tmp_path):
    _archive(tmp_path / "lynceus-extension-v1.2.3.zip")
    p = parametres_portail_test(paquets=str(tmp_path))
    with TestClient(creer_portail(p)) as client:
        assert "1.2.3" in client.get("/installer").text
        reponse = client.get("/telecharger")
    assert reponse.status_code == 200
    assert reponse.headers["content-type"] == "application/zip"
    assert 'filename="lynceus-extension-v1.2.3.zip"' in reponse.headers["content-disposition"]


# ------------------------------------------------------- mise en page

def test_aucune_grille_n_impose_une_largeur_superieure_a_l_ecran():
    """Régression signalée depuis un téléphone : les tuiles débordaient à droite.

    Une grille « repeat(auto-fit, minmax(N, 1fr)) » réserve N pixels par colonne même
    quand la fenêtre est plus étroite, et pousse alors la page hors de l'écran. La forme
    « minmax(min(100%, N), 1fr) » laisse la colonne se replier. La règle vaut pour toutes
    les grilles du portail, pas seulement celles qui débordaient ce jour-là."""
    css = (RACINE / "statique" / "lynceus.css").read_text(encoding="utf-8")
    fautives = [
        ligne.strip()
        for ligne in css.splitlines()
        if "auto-fit" in ligne and "minmax(min(" not in ligne
    ]
    assert not fautives, "grille sans repli sur écran étroit : " + " | ".join(fautives)


def test_les_scenes_du_recit_ne_sont_pas_centrees_en_flex():
    """Cause exacte du débordement : un conteneur flex en colonne avec « align-items:
    center » dimensionne ses enfants sur leur contenu maximal, et non sur la largeur
    disponible. Les scènes doivent rester en flux normal."""
    css = (RACINE / "statique" / "lynceus.css").read_text(encoding="utf-8")
    debut = css.index(".scene {")
    bloc = css[debut:css.index("}", debut)]
    assert "display: flex" not in bloc, bloc


def test_aucun_tiret_cadratin_dans_les_pages():
    """Demande explicite de l'utilisateur : pas de « — » dans les textes affichés.

    Vérifié sur les gabarits plutôt que sur le rendu, pour couvrir aussi les branches
    conditionnelles qu'une page donnée n'emprunte pas. Les documents de docs/ rendus par
    le portail sont couverts séparément, puisqu'ils vivent hors de ce dossier."""
    coupables = {
        chemin.name: [l.strip() for l in chemin.read_text(encoding="utf-8").splitlines() if "\u2014" in l]
        for chemin in sorted((RACINE / "gabarits").glob("*.html"))
    }
    coupables = {k: v for k, v in coupables.items() if v}
    assert not coupables, coupables


def test_aucun_tiret_cadratin_dans_les_documents_publies():
    """Même exigence pour la charte et la méthodologie : elles sont rendues telles quelles
    sur le site. docs/TAXONOMIE.md est exclu à dessein : son parseur (moteur/prompt.py)
    découpe les titres sur « — », et l'en retirer casserait le chargement du référentiel."""
    from lynceus.config import trouver_racine
    for nom in ("ETHIQUE", "METHODOLOGIE"):
        texte = (trouver_racine() / "docs" / f"{nom}.md").read_text(encoding="utf-8")
        lignes = [l.strip() for l in texte.splitlines() if "\u2014" in l]
        assert not lignes, f"{nom}.md : {lignes}"
