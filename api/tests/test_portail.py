"""Portail public — pages, inscription, annuaire, contestation.

Deux propriétés comptent plus que l'affichage et sont testées comme telles :
  · une clé émise par le portail est acceptée par une vraie instance (bout en bout) ;
  · une recherche par adresse ne transmet à l'instance qu'un préfixe d'empreinte.
"""

import io
import re
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
                   instance_interne="", paquets="", adresse="", cles_par_ip_jour=0,
                   editeur_nom="", editeur_statut="", editeur_adresse="",
                   editeur_identifiant="", editeur_directeur="", editeur_contact="",
                   hebergeur_nom="", hebergeur_adresse="", hebergeur_site="",
                   droit_applicable="", depot="", depot_fichiers="")
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


PAGES = ["/", "/installer", "/methodologie", "/taxonomie", "/charte", "/prompt",
         "/calibration", "/auto-hebergement", "/annuaire", "/contester", "/conditions",
         "/confidentialite", "/mentions-legales"]


@pytest.mark.parametrize("chemin", PAGES)
def test_aucune_page_ne_publie_de_lien_relatif(portail, chemin):
    """Un lien relatif servi par le portail est un lien mort.

    Le cas vient des documents du dépôt : « METHODOLOGIE.md » est juste dans docs/, et
    devient /METHODOLOGIE.md une fois rendu ici. Les cibles connues sont renvoyées vers
    la page correspondante, les autres vers le dépôt, et à défaut le lien disparaît."""
    client, _ = portail
    liens = re.findall(r'href="([^"]*)"', client.get(chemin).text)
    assert liens
    for lien in liens:
        assert lien.startswith(("/", "#", "http://", "https://", "mailto:", "data:")), lien


# ------------------------------------------------------------------ langues

def test_le_prefixe_de_langue_sert_la_meme_page_traduite(portail):
    """« /en/charte » et « /charte » sont la même page. Le français reste à la racine :
    aucune adresse déjà publiée ne change en devenant bilingue."""
    client, _ = portail
    assert client.get("/charte").status_code == 200
    anglais = client.get("/en/charte")
    assert anglais.status_code == 200
    assert 'lang="en"' in anglais.text
    assert ">Install<" in anglais.text          # bandeau traduit
    assert ">Installer<" not in anglais.text


def test_les_liens_internes_restent_dans_la_langue_de_la_page(portail):
    """Un lien écrit en dur ramènerait le lecteur anglophone au français au premier clic."""
    client, _ = portail
    html = client.get("/en/charte").text
    assert 'href="/en/methodologie"' in html
    assert 'href="/methodologie"' not in html


def test_la_racine_negocie_la_langue_du_navigateur(portail):
    """Seule la racine nue négocie : ailleurs, le préfixe fait foi, sinon un lien partagé
    s'ouvrirait dans une autre langue que celle où il a été écrit."""
    client, _ = portail
    reponse = client.get("/", headers={"accept-language": "en-GB,en;q=0.9"},
                         follow_redirects=False)
    assert reponse.status_code == 302
    assert reponse.headers["location"] == "/en/"
    assert "Accept-Language" in reponse.headers.get("vary", "")

    assert client.get("/", headers={"accept-language": "fr-FR,fr;q=0.9"},
                      follow_redirects=False).status_code == 200
    # Une langue que le portail ne parle pas ne le fait pas hésiter.
    assert client.get("/", headers={"accept-language": "de-DE,de"},
                      follow_redirects=False).status_code == 200


def test_une_adresse_explicite_ne_rebondit_jamais(portail):
    """Le sélecteur vise « /fr/ » et non « / » : sinon un anglophone qui choisit le
    français serait renvoyé à l'anglais par la négociation, sans pouvoir en sortir."""
    client, _ = portail
    reponse = client.get("/fr/", headers={"accept-language": "en-GB,en;q=0.9"},
                         follow_redirects=False)
    assert reponse.status_code == 200
    assert ">Installer<" in reponse.text


def test_chaque_page_annonce_ses_autres_langues(portail):
    """Sans hreflang, un moteur de recherche sert la mauvaise version, et le lecteur ne
    sait pas que l'autre existe."""
    client, _ = portail
    html = client.get("/en/annuaire").text
    assert 'hreflang="fr" href="http://testserver/fr/annuaire"' in html
    assert 'hreflang="en" href="http://testserver/en/annuaire"' in html
    assert 'hreflang="x-default"' in html


def test_aucune_phrase_de_gabarit_n_est_laissee_sans_traduction():
    """Le garde-fou de la traduction.

    Les msgid sont les phrases françaises : une phrase modifiée devient une phrase inconnue
    du catalogue, et ce test la signale au lieu de laisser la version anglaise afficher
    silencieusement l'ancien texte, ou du français au milieu de l'anglais."""
    import re

    from lynceus.portail import i18n

    # Les littéraux adjacents sont recollés : Python concatène « "a" "b" » en une seule
    # phrase, et n'en chercher que la première moitié dans le catalogue ne prouverait rien.
    morceau = r'"(?:[^"\\]|\\.)*"'
    motif = re.compile(r"\bN?_\(\s*((?:" + morceau + r"\s*)+)")
    fichiers = [*(RACINE / "gabarits").glob("*.html"), *RACINE.glob("*.py")]
    phrases = set()
    for fichier in fichiers:
        for trouve in motif.findall(fichier.read_text(encoding="utf-8")):
            phrases.add("".join(bout[1:-1].replace('\\"', '"')
                                for bout in re.findall(morceau, trouve)))
    assert phrases, "aucune phrase marquée : le motif de détection ne correspond plus"

    for langue in i18n.LANGUES:
        if langue == i18n.LANGUE_SOURCE:
            continue
        catalogue = i18n.catalogue(langue)
        manquantes = sorted(p for p in phrases if not catalogue.get(p))
        assert not manquantes, f"{langue} : {len(manquantes)} phrase(s) sans traduction, " \
                               f"à commencer par « {manquantes[0]} »"


def test_une_phrase_traduite_garde_sa_mise_en_forme_et_echappe_ses_valeurs(portail):
    """Les phrases portent souvent un lien ou une mise en valeur : échappées comme du texte
    brut, elles afficheraient leurs balises. Ce qui vient du visiteur, en revanche, doit
    rester échappé, sans quoi la traduction ouvrirait une injection."""
    client, _ = portail
    assert "<strong>adresse de page</strong>" in client.get("/annuaire").text
    assert "<strong>page address</strong>" in client.get("/en/annuaire").text

    hostile = client.get("/annuaire/recherche", params={"q": "<script>alerte()</script>"}).text
    assert "<script>" not in hostile


def test_les_libelles_venus_du_code_sont_traduits_aussi(portail):
    """Les motifs de contestation sont définis en Python, avant qu'une langue existe.
    Sans traduction au rendu, un formulaire anglais proposerait des choix en français."""
    client, _ = portail
    assert "I publish this site and I dispute this" in client.get("/en/contester").text
    # L'apostrophe est échappée par Jinja : on cherche un fragment qui n'en porte pas.
    assert "et je conteste" in client.get("/contester").text


def test_un_document_traduit_est_servi_dans_la_langue_demandee(portail):
    """La charte existe en anglais : c'est elle qui doit s'afficher, sans l'encart qui
    signale un document non traduit."""
    client, _ = portail
    html = client.get("/en/charte").text
    assert "Lynceus ethical charter" in html
    assert "A lookout, not a judge" in html
    assert "published in its original language" not in html


def test_un_document_sans_traduction_sert_l_original_en_le_disant(portail):
    """Mieux vaut le texte qui engage le projet, dans sa langue, qu'une page vide. Mais le
    lecteur doit savoir pourquoi il lit du français au milieu de l'anglais.

    Les versions de prompt antérieures ne sont pas traduites, et n'ont pas à l'être : elles
    restent lisibles parce que des analyses les annoncent, pas pour être relues."""
    from lynceus.moteur import prompt as moteur_prompt

    client, _ = portail
    ancienne = moteur_prompt.versions_disponibles()[0]
    html = client.get(f"/en/prompt?version={ancienne}").text
    assert "published in its original language" in html
    # Une phrase du fichier français, sans apostrophe : Jinja échappe les apostrophes.
    assert "Tu es une vigie, pas un juge" in html


def test_la_traduction_annonce_l_original_qui_fait_foi(portail):
    """Une traduction de texte normatif n'a pas la portée de l'original : le dire dans le
    document lui-même, pas seulement sur la page qui le sert."""
    client, _ = portail
    assert "the one that binds the project" in client.get("/en/charte").text


def test_le_prompt_publie_est_celui_que_le_moteur_applique(portail):
    """La charte promet le prompt public (§2). Une page qui le recopierait ne prouverait
    rien : c'est le fichier versionné qui est rendu, celui-là même que le moteur lit."""
    from lynceus.moteur import prompt as moteur_prompt
    client, _ = portail
    version = moteur_prompt.versions_disponibles()[-1]
    html = client.get("/prompt").text
    assert f"v{version}" in html
    # Une phrase de posture, présente dans le fichier, absente de tout gabarit.
    assert "Tu es une vigie, pas un juge" in html


def test_une_version_de_prompt_inconnue_ne_renvoie_pas_la_derniere(portail):
    """Sinon une adresse fautive afficherait un texte qui n'est pas celui qu'on demande."""
    client, _ = portail
    assert client.get("/prompt?version=9.9.9").status_code == 404


def test_les_anciennes_versions_de_prompt_restent_lisibles(portail):
    """L'annuaire annonce la version qui a produit chaque analyse : elle doit rester
    consultable, sinon la mention ne renvoie à rien."""
    from lynceus.moteur import prompt as moteur_prompt
    client, _ = portail
    for version in moteur_prompt.versions_disponibles():
        reponse = client.get(f"/prompt?version={version}")
        assert reponse.status_code == 200, version
        assert f"v{version}" in reponse.text


def test_la_calibration_publie_les_resultats_pas_le_corpus(portail):
    """Les captures du corpus appartiennent à leurs auteurs : le portail publie la mesure,
    pas les pages mesurées."""
    client, _ = portail
    html = client.get("/calibration").text
    assert "conformes" in html
    assert "<img" not in html


def test_un_document_renvoie_vers_les_pages_du_portail_avant_la_forge():
    """Ce que le portail publie lui-même reste chez lui ; le reste part vers le dépôt.

    L'ordre compte : envoyer le lecteur sur une forge pour lire un texte que le site sert
    déjà, c'est lui demander de faire confiance à une copie qu'il ne peut pas vérifier."""
    from lynceus.portail import contenu

    html = contenu.document("CONFORMITE", "https://forge.test/lynceus/blob/main")["html"]
    assert 'href="https://forge.test/lynceus/blob/main/DCO.txt"' in html

    p = parametres_portail_test(instance="https://instance.test",
                                depot="https://forge.test/lynceus",
                                depot_fichiers="https://forge.test/lynceus/blob/main")
    with TestClient(creer_portail(p)) as client:
        charte = client.get("/charte").text
    assert 'href="/prompt"' in charte
    assert 'href="/methodologie"' in charte


def test_la_marque_de_la_forge_suit_l_adresse_du_depot():
    """Le projet est auto-hébergeable, son dépôt aussi : afficher la marque de GitHub
    devant une adresse Forgejo serait faux. Une forge non reconnue reçoit un signe neutre."""
    from lynceus.portail import forge_de

    assert forge_de("https://github.com/org/projet") == "github"
    assert forge_de("https://forge.exemple.fr/vous/lynceus") == ""
    assert forge_de("") == ""


def test_le_pied_de_page_montre_la_marque_de_la_forge():
    """Le logo est dessiné dans la page, jamais chargé depuis un domaine tiers : la
    politique de confidentialité promet qu'aucune ressource extérieure n'est appelée."""
    p = parametres_portail_test(instance="https://instance.test",
                                depot="https://github.com/org/projet")
    with TestClient(creer_portail(p)) as client:
        html = client.get("/").text
    assert 'class="lien-forge"' in html
    assert "<svg" in html.split('class="lien-forge"')[1][:400]
    assert "githubusercontent" not in html and "githubassets" not in html


def test_le_depot_d_origine_est_annonce_sans_configuration():
    """Une instance qui fait tourner le code publié tel quel n'a rien à configurer : le
    défaut renvoie au dépôt d'origine, ce qui est exact et satisfait l'AGPL (article 13).
    L'exploitant qui modifie le code doit y mettre le sien, la configuration le dit."""
    from lynceus.portail.config import ParametresPortail

    p = ParametresPortail(_env_file=None)
    assert p.depot.startswith("https://")
    assert p.depot_fichiers.startswith(p.depot)


def test_sans_depot_annonce_le_pied_de_page_ne_promet_pas_de_code_source(portail):
    """Mieux vaut ne rien proposer qu'un lien vers une adresse inventée."""
    client, _ = portail
    assert "Code source de cette instance" not in client.get("/").text


def test_le_depot_annonce_est_joignable_depuis_toutes_les_pages():
    """L'AGPL (article 13) demande que le code soit proposé, donc atteignable partout."""
    p = parametres_portail_test(instance="https://instance.test",
                                depot="https://forge.test/lynceus")
    with TestClient(creer_portail(p)) as client:
        for chemin in PAGES:
            assert 'href="https://forge.test/lynceus"' in client.get(chemin).text, chemin


def test_la_confidentialite_nomme_le_fournisseur_annonce_par_l_instance(portail, tmp_path):
    """La politique n'est pas écrite à la main : elle nomme ce que l'instance déclare.

    Une politique de confidentialité recopiée diverge de la configuration au premier
    changement de fournisseur, et personne ne s'en aperçoit."""
    client, _ = portail
    api = creer_application(parametres_test(
        tmp_path, llm_base_url="https://api.mistral.ai/v1", llm_fournisseur="Mistral AI"))
    brancher_sur(client, api)
    html = client.get("/confidentialite").text
    assert "Mistral AI" in html
    assert "transmis à un fournisseur de modèle de langage tiers" in html


def test_un_modele_auto_heberge_ne_fait_plus_de_promesse_de_transfert(portail, tmp_path):
    """Chez un auto-hébergeur, le texte ne sort pas : annoncer un transfert vers un tiers
    serait faux, et l'inverse de ce que le projet dit de l'auto-hébergement."""
    client, _ = portail
    api = creer_application(parametres_test(tmp_path, llm_base_url="http://ollama:11434/v1"))
    brancher_sur(client, api)
    html = client.get("/confidentialite").text
    assert "hébergé par cette instance" in html
    assert "transmis à un fournisseur de modèle de langage tiers" not in html


def test_une_instance_muette_est_supposee_envoyer_le_texte_au_dehors(portail):
    """Instance injoignable ou trop ancienne : on annonce le cas le moins favorable."""
    client, _ = portail
    client.app.state.client = httpx.AsyncClient(base_url="http://instance-eteinte.invalid")
    assert "transmis à un fournisseur de modèle de langage tiers" in client.get("/confidentialite").text


def test_le_referentiel_traduit_garde_les_ids_et_les_gravites_du_fichier_applique(portail):
    """Une traduction ne remplace que ce qui s'affiche.

    La liste fermée, les identifiants et les gravités restent ceux du fichier français :
    c'est lui que le serveur valide et que le modèle reçoit. Un référentiel traduit qui
    ajouterait ou renommerait un id ne doit pas pouvoir déplacer cette frontière."""
    from lynceus.moteur import prompt as moteur_prompt
    from lynceus.portail import contenu

    reference = moteur_prompt.charger_taxonomie()
    anglais = contenu.taxonomie_par_famille("en")
    membres = {t["id"]: t for f in anglais for t in f["techniques"]}
    assert set(membres) == set(reference)
    for tid, entree in membres.items():
        assert entree["gravite"] == reference[tid]["gravite"]
    assert membres["appel_a_la_peur"]["nom"] == "Appeal to fear"

    client, _ = portail
    html = client.get("/en/taxonomie").text
    assert "Emotional register" in html
    assert "published in its original language" not in html


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
    assert "exemple.fr" in html and "Pages analysées : 3" in html


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


def test_a_version_egale_le_premier_dossier_l_emporte(tmp_path):
    """Le cas courant : on redépose à la main le zip d'une version déjà embarquée, pour
    servir une variante. L'égalité doit se trancher sur l'ordre annoncé des dossiers, et
    non sur l'ordre alphabétique des chemins, qui laisserait le hasard décider."""
    image, volume = tmp_path / "aaa-image", tmp_path / "zzz-volume"
    image.mkdir(); volume.mkdir()
    _archive(image / "lynceus-extension-v1.0.0.zip")
    _archive(volume / "lynceus-extension-v1.0.0.zip")

    # Le volume est cité en premier, comme dans le défaut « /paquets,/app/paquets-image ».
    retenu = paquet_le_plus_recent(f"{volume},{image}")
    assert retenu["chemin"].parent == volume

    # Ordre inverse : c'est l'image qui gagne. Le nom des dossiers n'y est pour rien.
    retenu = paquet_le_plus_recent(f"{image},{volume}")
    assert retenu["chemin"].parent == image


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


def test_le_lien_de_telechargement_est_present_sur_toutes_les_pages(tmp_path):
    """Un lien direct enfoui dans une seule page est un lien qu'on ne trouve pas. Il doit
    être atteignable depuis n'importe où, et porter la version pour être vérifiable."""
    _archive(tmp_path / "lynceus-extension-v3.1.4.zip")
    p = parametres_portail_test(paquets=str(tmp_path))
    with TestClient(creer_portail(p)) as client:
        for chemin in ("/", "/taxonomie", "/charte", "/annuaire", "/contester"):
            html = client.get(chemin).text
            assert '/telecharger' in html, chemin
            assert "v3.1.4" in html, chemin


def test_sans_paquet_aucun_lien_de_telechargement_n_est_affiche():
    """Proposer un lien qui répondrait 503 serait pire que ne rien proposer."""
    with TestClient(creer_portail(parametres_portail_test())) as client:
        assert "/telecharger" not in client.get("/").text


# ------------------------------------------------------------------ légal

# Exploitant fictif, comme les spécimens du corpus : un test ne doit pas dépendre de
# l'identité réelle de qui que ce soit, ni la diffuser.
EXPLOITANT = dict(
    editeur_nom="Association Vigie Exemple",
    editeur_statut="association loi 1901",
    editeur_adresse="1 rue de l'Exemple, 75000 Ville",
    editeur_identifiant="SIREN 000 000 000",
    editeur_directeur="Camille Exemple",
    editeur_contact="contact@exemple.fr",
    hebergeur_nom="Hébergeur Exemple SAS",
    hebergeur_adresse="2 rue du Serveur, 59000 Ville",
)


def test_les_pages_legales_publient_l_identite_configuree():
    """Un service ouvert au public doit identifier son éditeur. Les valeurs viennent de la
    configuration et non du code, puisque chaque instance a son propre exploitant."""
    with TestClient(creer_portail(parametres_portail_test(**EXPLOITANT))) as client:
        html = client.get("/mentions-legales").text
    # Portions sans apostrophe : Jinja les échappe en &#39; dans le rendu.
    for attendu in ("Association Vigie Exemple", "SIREN 000 000 000", "75000 Ville",
                    "Hébergeur Exemple SAS", "contact@exemple.fr"):
        assert attendu in html, attendu


def test_une_identite_absente_est_annoncee_plutot_qu_inventee():
    """Le pire des cas serait une page de mentions légales affichant un exploitant
    plausible mais faux. Elle doit reconnaître qu'elle n'est pas renseignée."""
    with TestClient(creer_portail(parametres_portail_test())) as client:
        for chemin in ("/mentions-legales", "/confidentialite"):
            html = client.get(chemin).text
            assert "non renseignées sur cette instance" in html.lower() or \
                   "Mentions non renseignées" in html, chemin


def test_la_politique_annonce_le_transfert_vers_le_fournisseur_de_modele():
    """Le flux de données le plus important du système est le texte de la page envoyé au
    fournisseur de modèle. Une politique qui vante le k-anonymat sans le mentionner serait
    trompeuse par omission, et le projet se donne pour objet de repérer ce procédé."""
    with TestClient(creer_portail(parametres_portail_test(**EXPLOITANT))) as client:
        html = client.get("/confidentialite").text
    assert "transmis à un fournisseur de modèle de langage tiers" in html
    assert "hors de l'Union européenne" in html
    # Et le remède doit être proposé dans la même phrase, pas relégué ailleurs.
    assert "/auto-hebergement" in html


def test_la_politique_nomme_le_fournisseur_reellement_configure():
    """Écrit à la main, le nom du sous-traitant deviendrait faux le jour où l'instance
    change de fournisseur, sans que personne s'en aperçoive. Il est donc lu dans /v1/meta."""
    instance = FastAPI()

    @instance.get("/v1/meta")
    def meta():
        return {"modele": "fournisseur-test/modele-x", "fournisseur": "exemple-llm.test",
                "limites": {"contenu_max_cars": 60000}}

    parametres = parametres_portail_test(instance="https://instance.test", **EXPLOITANT)
    with TestClient(creer_portail(parametres)) as client:
        brancher_sur(client, instance)
        html = client.get("/confidentialite").text
    assert "exemple-llm.test" in html
    assert "fournisseur-test/modele-x" in html


def test_la_politique_reste_lisible_si_l_instance_est_injoignable():
    """Une instance éteinte ne doit pas faire disparaître l'obligation d'information."""
    parametres = parametres_portail_test(instance="https://instance.test", **EXPLOITANT)
    with TestClient(creer_portail(parametres)) as client:
        client.app.state.client = httpx.AsyncClient(base_url="http://eteinte.invalid")
        reponse = client.get("/confidentialite")
    assert reponse.status_code == 200
    assert "fournisseur de modèle de langage tiers" in reponse.text


def test_les_pages_legales_sont_accessibles_depuis_toutes_les_pages():
    with TestClient(creer_portail(parametres_portail_test(**EXPLOITANT))) as client:
        for chemin in ("/", "/taxonomie", "/annuaire"):
            html = client.get(chemin).text
            for lien in ("/mentions-legales", "/confidentialite", "/conditions"):
                assert lien in html, f"{lien} absent de {chemin}"


def test_la_charte_publie_le_transfert_vers_le_modele():
    """La charte est contraignante. Elle promettait la vie privée sans mentionner le seul
    transfert qu'un utilisateur du service hébergé ne peut pas éviter."""
    from lynceus.config import trouver_racine
    charte = (trouver_racine() / "docs" / "ETHIQUE.md").read_text(encoding="utf-8")
    assert "fournisseur de modèle" in charte
    assert "hors de l'Union européenne" in charte
