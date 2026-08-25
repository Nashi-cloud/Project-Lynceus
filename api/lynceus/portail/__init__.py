"""Portail Lynceus — le site public : récit, méthodologie, annuaire, inscription.

Lancement : uvicorn lynceus.portail:creer_portail --factory --port 8080

**Service distinct de l'instance.** Le portail détient la clé privée d'émission ; l'API ne
connaît que la publique. Les faire tourner dans le même processus reviendrait à poser la
clé privée sur la machine exposée aux analyses — voir portail/config.py.

Le portail ne touche jamais la base de l'instance : il l'interroge par son API publique,
exactement comme le ferait l'extension. Une instance en panne dégrade le site (l'annuaire
répond « injoignable ») sans l'empêcher de servir ses pages.
"""

from __future__ import annotations

import io
import json
import sys
import zipfile
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .. import __version__
from ..annuaire import LONGUEUR_PREFIXE
from ..cles import emettre
from ..normalisation import extraire_domaine, hacher_url, normaliser_url
from . import contenu
from .config import ParametresPortail, parametres_portail

RACINE = Path(__file__).parent

# Fichier déposé dans l'archive au moment du téléchargement. Il porte l'adresse du portail
# qui l'a servie, et rien d'autre : l'extension l'y lit pour proposer « Obtenir une clé »
# sans que personne ait à recopier une adresse.
FICHIER_PORTAIL = "portail.json"

MOTIFS = [
    ("analyse_erronee", "L'analyse est fausse"),
    ("extrait_hors_contexte", "Une citation est déformée"),
    ("categorie_erronee", "La catégorie est erronée (satire, opinion…)"),
    ("note_injustifiee", "La note ne correspond pas au contenu"),
    ("page_modifiee", "La page a changé depuis l'analyse"),
    ("droit_de_reponse", "Je suis l'éditeur de ce site et je conteste"),
    ("autre", "Autre"),
]


class TropDeCles(Exception):
    """Plafond d'émission atteint pour une adresse. Levée seulement si le plafond est actif."""


class _CompteurCles:
    """Compte les clés délivrées par adresse et par jour, en mémoire.

    Désactivé par défaut (`cles_par_ip_jour = 0`) : l'inscription est libre et anonyme.
    En mémoire, donc remis à zéro au redémarrage et non partagé entre plusieurs processus —
    c'est un frein, pas une barrière, et c'est dit tel quel dans DEPLOIEMENT.md."""

    def __init__(self) -> None:
        self._compte: dict[tuple[str, str], int] = {}

    def enregistrer(self, adresse: str, plafond: int) -> None:
        if plafond <= 0:
            return
        jour = datetime.now(timezone.utc).date().isoformat()
        # Purge des jours révolus : sans elle, le dictionnaire grossirait indéfiniment.
        for cle in [c for c in self._compte if c[1] != jour]:
            del self._compte[cle]
        cle = (adresse, jour)
        if self._compte.get(cle, 0) >= plafond:
            raise TropDeCles
        self._compte[cle] = self._compte.get(cle, 0) + 1


def identite_legale(p: ParametresPortail) -> dict:
    """Ce que le portail sait de son exploitant, et s'il en sait assez.

    `complete` conditionne l'affichage des pages légales : mieux vaut une page qui
    reconnaît ne pas être renseignée qu'une page qui affiche des mentions inventées."""
    champs = {
        "nom": p.editeur_nom,
        "statut": p.editeur_statut,
        "adresse": p.editeur_adresse,
        "identifiant": p.editeur_identifiant,
        "directeur": p.editeur_directeur,
        "contact": p.editeur_contact,
    }
    hebergeur = {
        "nom": p.hebergeur_nom,
        "adresse": p.hebergeur_adresse,
        "site": p.hebergeur_site,
    }
    # Le minimum imposé par la LCEN : qui édite, où le joindre, qui héberge.
    obligatoires = ("nom", "adresse", "contact")
    return {
        **champs,
        "hebergeur": hebergeur,
        "droit_applicable": p.droit_applicable,
        "complete": all(champs[c] for c in obligatoires) and bool(hebergeur["nom"]),
    }


def creer_portail(p: ParametresPortail | None = None) -> FastAPI:
    p = p or parametres_portail()
    instance_interne = (p.instance_interne or p.instance).rstrip("/")
    instance_publique = p.instance.rstrip("/")
    compteur = _CompteurCles()
    legal = identite_legale(p)

    if instance_publique and not legal["complete"]:
        print(
            "⚠  Identité de l'exploitant incomplète (LYNCEUS_PORTAIL_EDITEUR_*, "
            "LYNCEUS_PORTAIL_HEBERGEUR_NOM). Un portail ouvert au public doit publier "
            "des mentions légales : en l'état, les pages légales indiquent qu'elles ne "
            "sont pas renseignées.",
            file=sys.stderr,
        )

    @asynccontextmanager
    async def cycle_de_vie(app: FastAPI):
        async with httpx.AsyncClient(timeout=p.delai_instance_s) as client:
            app.state.client = client
            yield

    app = FastAPI(title=f"Portail {p.nom}", version=__version__, lifespan=cycle_de_vie)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in p.cors_origins.split(",") if o.strip()],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.mount("/statique", StaticFiles(directory=RACINE / "statique"), name="statique")
    gabarits = Jinja2Templates(directory=str(RACINE / "gabarits"))

    gabarits.env.globals.update(
        nom=p.nom,
        contact=p.contact,
        version=__version__,
        instance=instance_publique,
        inscription_ouverte=bool(p.cle_privee and instance_publique),
        nb_techniques=contenu.nb_techniques(),
        legal=legal,
    )

    def paquet_courant() -> dict | None:
        """Relu à chaque appel : déposer un zip dans le volume publie la mise à jour
        immédiatement, sans redémarrer le conteneur."""
        return contenu.paquet_le_plus_recent(p.paquets)

    def adresse(requete: Request) -> str:
        if p.entete_ip_reelle:
            premiere = requete.headers.get(p.entete_ip_reelle, "").split(",")[0].strip()
            if premiere:
                return premiere
        return requete.client.host if requete.client else "inconnue"

    def adresse_portail(requete: Request) -> str:
        """Adresse publique de ce portail, telle qu'un navigateur peut la joindre.

        Configurée de préférence : derrière un tunnel ou un proxy, l'application ne voit
        que le nom d'hôte transmis dans les en-têtes, et le schéma qu'elle croit servir
        est http même quand le visiteur est en https. À défaut de configuration, on
        déduit de la requête, en tenant compte de l'en-tête de schéma du proxy."""
        if p.adresse:
            return p.adresse.rstrip("/")
        base = str(requete.base_url).rstrip("/")
        schema = requete.headers.get("x-forwarded-proto", "").split(",")[0].strip()
        if schema in ("http", "https") and "://" in base:
            base = f"{schema}://{base.split('://', 1)[1]}"
        return base

    def page(requete: Request, gabarit: str, **valeurs) -> HTMLResponse:
        valeurs.setdefault("paquet", paquet_courant())
        valeurs.setdefault("adresse_portail", adresse_portail(requete))
        return gabarits.TemplateResponse(requete, gabarit, valeurs)

    # ---------------------------------------------------------------- pages

    @app.get("/", response_class=HTMLResponse)
    def accueil(requete: Request):
        return page(requete, "accueil.html")

    @app.get("/methodologie", response_class=HTMLResponse)
    def methodologie(requete: Request):
        return page(requete, "methodologie.html",
                    ponderations=contenu.ponderations(), seuils=contenu.seuils(),
                    detail=contenu.document("METHODOLOGIE"))

    @app.get("/taxonomie", response_class=HTMLResponse)
    def taxonomie(requete: Request):
        return page(requete, "taxonomie.html",
                    familles=contenu.taxonomie_par_famille(), gravites=contenu.GRAVITES)

    @app.get("/charte", response_class=HTMLResponse)
    def charte(requete: Request):
        return page(requete, "document.html", document=contenu.document("ETHIQUE"))

    @app.get("/auto-hebergement", response_class=HTMLResponse)
    def auto_hebergement(requete: Request):
        return page(requete, "auto-hebergement.html")

    @app.get("/installer", response_class=HTMLResponse)
    def installer(requete: Request):
        return page(requete, "installer.html")

    # ------------------------------------------------------------- légal

    @app.get("/mentions-legales", response_class=HTMLResponse)
    def mentions_legales(requete: Request):
        return page(requete, "mentions-legales.html")

    @app.get("/confidentialite", response_class=HTMLResponse)
    async def confidentialite(requete: Request):
        """La politique nomme le fournisseur de modèle réellement configuré.

        Il est lu dans /v1/meta de l'instance plutôt qu'écrit à la main : une politique de
        confidentialité qui désigne un sous-traitant que l'instance n'utilise plus serait
        fausse, et personne ne s'en apercevrait."""
        return page(requete, "confidentialite.html",
                    moteur=await _meta_instance(app.state.client, instance_interne))

    @app.get("/conditions", response_class=HTMLResponse)
    def conditions(requete: Request):
        return page(requete, "conditions.html")

    # ---------------------------------------------------- téléchargement

    @app.get("/telecharger")
    def telecharger(requete: Request):
        """Sert l'archive, en y glissant l'adresse de ce portail.

        L'image publiée contient un paquet **neutre**, valable pour n'importe quel
        portail : c'est ce qui permet à tout le monde de déployer la même image. L'adresse
        est donc ajoutée à la volée, à la seule archive téléchargée. Sans cela il faudrait
        soit reconstruire l'extension par portail, soit demander à chaque utilisateur de
        recopier une adresse à la main."""
        paquet = paquet_courant()
        if paquet is None:
            raise HTTPException(
                503,
                "Aucun paquet n'est publié sur ce portail. Construisez l'extension depuis "
                "les sources : npm run paquet, dans extension/. Le dépôt est libre.",
            )
        contenu_zip = _archive_configuree(paquet["chemin"], adresse_portail(requete))
        return Response(
            contenu_zip,
            media_type="application/zip",
            headers={"content-disposition": f'attachment; filename="{paquet["nom"]}"'},
        )

    # ------------------------------------------------------- inscription

    @app.post("/v1/inscription")
    def inscription(requete: Request):
        """Délivre un « billet d'accès » : l'adresse de l'instance ET une clé pour elle.

        Aucun compte, aucune adresse électronique, aucun identifiant : la clé ne porte
        qu'une date d'expiration et un quota. Le portail ne conserve rien de ce qu'il
        délivre — il ne pourrait donc pas dire qui a obtenu quoi, même sous contrainte."""
        if not p.cle_privee:
            raise HTTPException(503, "Ce portail ne délivre pas de clés : aucune clé d'émission "
                                     "n'y est configurée.")
        if not instance_publique:
            raise HTTPException(503, "Ce portail ne déclare aucune instance : il ne peut pas "
                                     "indiquer où utiliser la clé.")
        try:
            compteur.enregistrer(adresse(requete), p.cles_par_ip_jour)
        except TropDeCles:
            raise HTTPException(
                429,
                f"Ce portail délivre au plus {p.cles_par_ip_jour} clé(s) par jour et par "
                "adresse. Réessayez demain, ou hébergez votre propre instance : elle "
                "n'exige aucune clé.",
            ) from None

        cle, droits = emettre(p.cle_privee, jours=p.validite_jours, quota_jour=p.quota_jour)
        return {
            "instance": instance_publique,
            "cle": cle,
            "quota_jour": droits.quota_jour,
            "expire_le": droits.expire_le,
            "portail": p.nom,
        }

    # ----------------------------------------------------------- annuaire

    @app.get("/annuaire", response_class=HTMLResponse)
    def annuaire_page(requete: Request):
        return page(requete, "annuaire.html")

    @app.get("/annuaire/recherche", response_class=HTMLResponse)
    async def annuaire_recherche(requete: Request, texte: str = Query(alias="q", default="")):
        texte = texte.strip()
        if not texte:
            return page(requete, "frag_annuaire.html", vide=True)
        try:
            resultat = await _consulter(app.state.client, instance_interne, texte)
        except httpx.HTTPError:
            return page(requete, "frag_annuaire.html", injoignable=True)
        return page(requete, "frag_annuaire.html", **resultat)

    # -------------------------------------------------------- contestation

    @app.get("/contester", response_class=HTMLResponse)
    def contester_page(requete: Request, analyse: int | None = None):
        return page(requete, "contester.html", motifs=MOTIFS, analyse_id=analyse)

    @app.post("/contester", response_class=HTMLResponse)
    async def contester(
        requete: Request,
        analyse_id: int = Form(),
        motif: str = Form(),
        message: str = Form(),
        contact: str = Form(default=""),
    ):
        corps = {"analyse_id": analyse_id, "motif": motif, "message": message.strip(),
                 "contact": contact.strip() or None}
        try:
            reponse = await app.state.client.post(f"{instance_interne}/v1/signalements", json=corps)
        except httpx.HTTPError:
            return page(requete, "frag_contestation.html", injoignable=True)
        if reponse.status_code >= 400:
            detail = None
            if "json" in reponse.headers.get("content-type", ""):
                detail = reponse.json().get("detail")
            return page(requete, "frag_contestation.html",
                        erreur=detail or f"HTTP {reponse.status_code}")
        return page(requete, "frag_contestation.html", recu=reponse.json())

    # -------------------------------------------------------------- santé

    @app.get("/sante")
    async def sante():
        """Le portail est en bonne santé même si l'instance ne l'est pas : il sert ses
        pages sans elle. L'état de l'instance est rapporté, pas confondu avec le sien."""
        etat_instance = "non configurée"
        if instance_interne:
            try:
                reponse = await app.state.client.get(f"{instance_interne}/sante")
                etat_instance = "ok" if reponse.status_code == 200 else f"http {reponse.status_code}"
            except httpx.HTTPError:
                etat_instance = "injoignable"
        return {
            "statut": "ok",
            "version": __version__,
            "emission_de_cles": bool(p.cle_privee),
            "paquet": (paquet_courant() or {}).get("version"),
            "instance": etat_instance,
        }

    return app


def _archive_configuree(chemin: Path, portail: str) -> bytes:
    """Recopie l'archive en y ajoutant (ou remplaçant) portail.json.

    Le zip fait une quinzaine de kilo-octets : le reconstruire en mémoire coûte quelques
    millisecondes, et évite d'avoir à écrire une variante par portail sur le disque. Une
    entrée existante du même nom est écartée, pour qu'un paquet déjà configuré ne se
    retrouve pas avec deux adresses contradictoires."""
    tampon = io.BytesIO()
    with zipfile.ZipFile(chemin) as source, \
         zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED) as sortie:
        for info in source.infolist():
            if info.filename == FICHIER_PORTAIL:
                continue
            sortie.writestr(info, source.read(info.filename))
        sortie.writestr(FICHIER_PORTAIL,
                        json.dumps({"portail": portail}, ensure_ascii=False))
    return tampon.getvalue()


async def _consulter(client: httpx.AsyncClient, instance: str, texte: str) -> dict:
    """Cherche dans l'annuaire de l'instance : une page précise, ou un domaine.

    Une URL passe par le lookup **k-anonyme** : le portail n'envoie que les premiers
    caractères du hash et fait la correspondance lui-même. L'instance ne peut donc pas
    savoir quelle page un visiteur du site a consultée — la même garantie que dans
    l'extension (charte §4), plutôt qu'une exception parce que c'est un serveur qui demande."""
    if texte.startswith(("http://", "https://")) or "/" in texte:
        url = texte if "://" in texte else f"https://{texte}"
        try:
            url_hash = hacher_url(url)
            domaine = extraire_domaine(normaliser_url(url))
        except ValueError:
            return {"invalide": texte}

        reponse = await client.get(f"{instance}/v1/lookup-prefixe",
                                   params={"prefixe": url_hash[:LONGUEUR_PREFIXE]})
        reponse.raise_for_status()
        # L'instance ne renvoie que le SUFFIXE de chaque empreinte, jamais l'empreinte
        # entière : c'est ce qui l'empêche de reconstituer les URL qu'elle connaît à
        # partir de ses propres réponses. La correspondance se fait donc ici.
        suffixe_attendu = url_hash[LONGUEUR_PREFIXE:]
        correspondance = next(
            (c for c in reponse.json()["correspondances"] if c["suffixe"] == suffixe_attendu),
            None,
        )
        if correspondance is None:
            return {"page_inconnue": texte, "domaine": await _domaine(client, instance, domaine)}

        detail = await client.get(f"{instance}/v1/analyses/{correspondance['analyse_id']}")
        detail.raise_for_status()
        donnees = detail.json()
        # La carte est indexée par CONTENU, pas par adresse : un même texte publié à deux
        # adresses n'est analysé qu'une fois, et la carte servie peut donc ne porter ni
        # l'URL ni le titre de la page demandée. On affiche l'adresse demandée, la seule
        # dont on soit certain qu'elle corresponde à ce que le visiteur a saisi.
        return {
            "carte": donnees["carte"],
            "url_demandee": url,
            "analyse_id": correspondance["analyse_id"],
            "signalements": donnees.get("signalements", 0),
            "domaine": await _domaine(client, instance, domaine),
        }

    domaine = texte.lower().removeprefix("www.")
    profil = await _domaine(client, instance, domaine)
    return {"domaine": profil} if profil else {"domaine_inconnu": domaine}


async def _meta_instance(client: httpx.AsyncClient, instance: str) -> dict | None:
    """Modèle et fournisseur annoncés par l'instance, ou None si elle est injoignable."""
    if not instance:
        return None
    try:
        reponse = await client.get(f"{instance}/v1/meta")
        reponse.raise_for_status()
        donnees = reponse.json()
    except (httpx.HTTPError, ValueError):
        return None
    return {
        "modele": donnees.get("modele"),
        "fournisseur": donnees.get("fournisseur"),
        "contenu_max_cars": donnees.get("limites", {}).get("contenu_max_cars"),
    }


async def _domaine(client: httpx.AsyncClient, instance: str, domaine: str | None) -> dict | None:
    if not domaine:
        return None
    reponse = await client.get(f"{instance}/v1/domaines/{domaine}")
    if reponse.status_code == 404:
        return None
    reponse.raise_for_status()
    return reponse.json()
