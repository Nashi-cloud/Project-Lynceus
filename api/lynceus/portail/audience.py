"""Mesure d'audience du portail, faite par le serveur.

L'outil visé est Umami, auto-hébergé par l'exploitant. Sa façon habituelle de compter est
un script exécuté chez le visiteur, qui rapporte à l'adresse d'Umami. Le portail ne fait
pas ça, pour deux raisons qui se rejoignent.

La première est une promesse publiée : la page de confidentialité dit que les scripts
sont servis par ce serveur et que rien ne s'exécute pour compter le visiteur. Un script
de mesure, même servi depuis notre domaine, la romprait.

La seconde est pratique : Umami peut vivre sur un réseau interne, injoignable depuis un
navigateur. C'est le serveur qui, au moment où il répond, signale la page vue à Umami.
Rien n'est exposé, rien ne s'exécute chez le visiteur, et la mesure se coupe en retirant
deux variables d'environnement.

Ce qui est envoyé, et ce qui ne l'est pas, se lit dans `vue_depuis` : c'est ce que la
page de confidentialité décrit, et les deux doivent bouger ensemble.

Ce que le portail ne mesure jamais : les consultations de l'annuaire, parce que la même
page promet qu'il n'existe ni journal des consultations ni couple adresse et page ; les
appels de l'extension sous /v1/, pour la même raison ; et tout ce qui n'est pas une page
rendue à un visiteur.
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass, field
from typing import Callable

import httpx
from starlette.datastructures import Headers

# Préfixes de chemin jamais comptés, quelle que soit la réponse. Les chemins sont ceux
# vus par le routeur, donc sans préfixe de langue.
CHEMINS_EXCLUS = ("/annuaire/recherche", "/v1/", "/statique/", "/sante")

# Le téléchargement de l'extension n'est pas une page HTML mais compte comme une vue :
# c'est la seule mesure qui dise si le portail sert à quelque chose.
CHEMINS_INCLUS = ("/telecharger",)


def mesurable(methode: str, chemin: str, statut: int, type_contenu: str) -> bool:
    """Une page rendue avec succès à un visiteur, et rien d'autre.

    Une erreur ou une redirection n'est pas une page lue ; un POST est une action, pas
    une consultation ; une ressource statique est un détail de la page déjà comptée."""
    if methode != "GET" or statut != 200:
        return False
    for exclu in CHEMINS_EXCLUS:
        if chemin == exclu.rstrip("/") or chemin.startswith(exclu):
            return False
    return type_contenu.startswith("text/html") or chemin in CHEMINS_INCLUS


def vue_depuis(scope: dict, adresse_ip: str) -> tuple[dict, dict]:
    """Le corps et les en-têtes de la requête à Umami pour une page vue.

    Retourne (charge, en_tetes). La charge suit le format de /api/send d'Umami. Les
    en-têtes portent ce qu'Umami lit hors du corps : le navigateur, pour distinguer un
    robot d'une personne et pour l'identifiant de session ; l'adresse, pour le même
    identifiant et pour le pays.

    L'adresse va dans CF-Connecting-IP et non seulement dans X-Forwarded-For. Umami
    parcourt une liste ordonnée d'en-têtes et retient le premier présent, et
    CF-Connecting-IP y précède X-Forwarded-For. Un proxy entre le portail et Umami peut
    allonger X-Forwarded-For de sa propre adresse ; CF-Connecting-IP, lui, ne se
    concatène pas. Sans adresse fiable, tous les visiteurs d'un même navigateur
    fusionnent en un seul, et le décompte est faux avant même que la carte soit vide.

    Le pays est transmis tel que le tunnel l'a déterminé, quand il l'a fait. Umami lit
    les en-têtes de localisation avant d'interroger sa base GeoIP et s'arrête là : donner
    le pays seul est le moyen d'obtenir le pays sans la ville. Sans cet en-tête, Umami
    déduit lui-même pays et ville de l'adresse, ce que la page de confidentialité de
    l'instance doit alors dire."""
    en_tetes_requete = Headers(scope=scope)
    langue = scope.get("lynceus_langue", "")
    chemin = scope.get("lynceus_chemin", scope.get("path", "/"))
    if scope.get("lynceus_langue_explicite"):
        chemin = f"/{langue}{chemin}".rstrip("/") or "/"
    hote = en_tetes_requete.get("x-forwarded-host") or en_tetes_requete.get("host") or ""
    hote = hote.split(",")[0].split(":")[0].strip()
    # Le référent est réduit à son origine et son chemin : ses paramètres peuvent porter
    # des identifiants que rien ici n'a besoin de connaître.
    referent = en_tetes_requete.get("referer", "").split("?")[0].split("#")[0]
    accepte = en_tetes_requete.get("accept-language", "").split(",")[0].split(";")[0].strip()

    charge = {
        "type": "event",
        "payload": {
            "hostname": hote,
            "url": chemin,
            "referrer": referent,
            "language": accepte,
            "title": "",
        },
    }
    en_tetes = {
        "User-Agent": en_tetes_requete.get("user-agent", ""),
        "CF-Connecting-IP": adresse_ip,
        "X-Forwarded-For": adresse_ip,
    }
    pays = en_tetes_requete.get("cf-ipcountry", "")
    if pays:
        en_tetes["CF-IPCountry"] = pays
    return charge, en_tetes


@dataclass
class Audience:
    """Le lien du portail vers Umami. Inactif tant que l'adresse ou le site manque."""

    url: str
    site: str
    delai_s: float = 3.0
    client: httpx.AsyncClient | None = None
    # Références vers les envois en cours : une tâche sans référence peut être ramassée
    # avant d'avoir fini, et son résultat perdu sans un mot.
    taches: set[asyncio.Task] = field(default_factory=set)
    en_panne: bool = False

    @property
    def active(self) -> bool:
        return bool(self.url and self.site)

    def ouvrir(self) -> None:
        self.client = httpx.AsyncClient(timeout=self.delai_s)

    async def fermer(self) -> None:
        if self.taches:
            await asyncio.gather(*self.taches, return_exceptions=True)
        if self.client is not None:
            await self.client.aclose()

    def signaler(self, scope: dict, adresse_ip: str) -> None:
        """Programme l'envoi d'une vue, sans attendre la réponse d'Umami.

        La page est déjà partie chez le visiteur : un Umami lent ou absent ne doit ni
        retarder la suivante, ni faire échouer quoi que ce soit."""
        charge, en_tetes = vue_depuis(scope, adresse_ip)
        charge["payload"]["website"] = self.site
        tache = asyncio.create_task(self.envoyer(charge, en_tetes))
        self.taches.add(tache)
        tache.add_done_callback(self.taches.discard)

    async def envoyer(self, charge: dict, en_tetes: dict) -> None:
        """Un envoi par page vue, sans reprendre le jeton de cache qu'Umami renvoie.

        Le script habituel réémet ce jeton à chaque page, et on pourrait croire que sans
        lui chaque page devient une session. Vérifié contre un Umami réel : l'identifiant
        de session et celui de visite se recalculent à l'identique à partir de l'adresse
        et du navigateur, jeton ou pas. Deux envois rapprochés, même adresse et même
        navigateur, donnent la même session et la même visite ; changer l'un ou l'autre
        en donne une autre. Le jeton n'épargne à Umami qu'une recherche en base. Deux
        choses varient sans que ce soit une régression : la visite, close après une
        période d'inactivité, et la session, dont le sel tourne d'un jour à l'autre."""
        if self.client is None:
            return
        try:
            reponse = await self.client.post(
                f"{self.url.rstrip('/')}/api/send", json=charge, headers=en_tetes,
            )
            reponse.raise_for_status()
        except httpx.HTTPError as erreur:
            # Une ligne à la première panne, une autre au retour : entre les deux, rien.
            # Un avertissement par page vue noierait les journaux sans rien apprendre.
            if not self.en_panne:
                self.en_panne = True
                print(f"⚠  Mesure d'audience : Umami injoignable ({erreur!r}). "
                      "Les pages restent servies, elles ne sont plus comptées.",
                      file=sys.stderr)
            return
        if self.en_panne:
            self.en_panne = False
            print("Mesure d'audience : Umami répond de nouveau.", file=sys.stderr)


class MesureAudience:
    """Intergiciel ASGI : observe la réponse, et signale la page vue une fois envoyée.

    Il se place sous LangueDansLURL, pour lire le chemin sans préfixe de langue que voit
    le routeur et lui appliquer les exclusions."""

    def __init__(self, app, audience: Audience, adresse_de: Callable[[dict], str]):
        self.app = app
        self.audience = audience
        self.adresse_de = adresse_de

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not self.audience.active:
            return await self.app(scope, receive, send)

        statut = 0
        type_contenu = ""

        async def observer(message):
            nonlocal statut, type_contenu
            if message["type"] == "http.response.start":
                statut = message["status"]
                type_contenu = Headers(raw=message.get("headers", [])).get("content-type", "")
            await send(message)
            if message["type"] == "http.response.body" and not message.get("more_body"):
                chemin = scope.get("lynceus_chemin", scope["path"])
                if mesurable(scope["method"], chemin, statut, type_contenu):
                    self.audience.signaler(scope, self.adresse_de(scope))

        return await self.app(scope, receive, observer)


def adresse_reelle(entete_ip_reelle: str) -> Callable[[dict], str]:
    """L'adresse du visiteur, selon la même règle que le reste du portail : l'en-tête
    configuré s'il l'est, sinon l'adresse de la connexion."""

    def adresse(scope: dict) -> str:
        if entete_ip_reelle:
            premiere = Headers(scope=scope).get(entete_ip_reelle, "").split(",")[0].strip()
            if premiere:
                return premiere
        client = scope.get("client")
        return client[0] if client else ""

    return adresse

