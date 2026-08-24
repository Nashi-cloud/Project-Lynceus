"""API Lynceus — annuaire + moteur d'analyse (contrat : docs/ARCHITECTURE.md).

Lancement : uvicorn lynceus.main:creer_application --factory
"""

from __future__ import annotations

import sys
import secrets
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit

import jsonschema
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from . import VERSION_SCHEMA, __version__, annuaire, cles, extraction
from .config import Parametres, parametres
from .migrations import appliquer as appliquer_migrations
from .modeles import Analyse, Base
from .moteur import llm, notation, prompt, validation
from .normalisation import extraire_domaine, hacher_contenu, hacher_url, normaliser_url

AVERTISSEMENT_TRONQUE = (
    "Cet article dépassait la taille analysable : seul son début a été examiné. "
    "La suite du texte peut contenir des éléments non pris en compte ici."
)

AVERTISSEMENT_IA = (
    "Cette analyse est produite par une intelligence artificielle : elle peut comporter des erreurs. "
    "Elle décrit des procédés rhétoriques, pas la valeur des personnes qui partagent ce contenu."
)


MOTIFS_SIGNALEMENT = {
    "analyse_erronee",       # le contenu de l'analyse est faux
    "extrait_hors_contexte", # la citation existe mais son sens est déformé
    "categorie_erronee",     # ex. satire classée comme désinformation
    "note_injustifiee",      # le grade ne correspond pas au contenu
    "page_modifiee",         # la page a changé depuis l'analyse
    "droit_de_reponse",      # l'éditeur du site conteste
    "autre",
}


class DemandeSignalement(BaseModel):
    analyse_id: int
    motif: str
    message: str = Field(min_length=10, max_length=4000)
    contact: str | None = Field(default=None, max_length=320)


class DecisionSignalement(BaseModel):
    statut: str
    decision: str = Field(min_length=5, max_length=2000, description="Justification, conservée et auditable")


class DemandeAnalyse(BaseModel):
    url: str | None = None
    contenu_markdown: str | None = None
    titre: str | None = Field(default=None, max_length=500)
    langue: str | None = Field(default=None, max_length=10)
    # Déclaré par le client quand la page dépassait la limite de l'instance. La carte étant
    # mise en cache et resservie à d'autres, elle DOIT porter la mention : sans quoi une
    # analyse partielle circulerait comme si elle couvrait tout l'article.
    tronque: bool = False


def creer_application(p: Parametres | None = None) -> FastAPI:
    p = p or parametres()

    if not p.llm_api_key and not any(h in p.llm_base_url for h in ("localhost", "127.0.0.1")):
        print(
            "⚠  LYNCEUS_LLM_API_KEY est vide : toute analyse échouera (502). "
            "Renseigner api/.env puis redémarrer le serveur (le .env est lu au démarrage).",
            file=sys.stderr,
        )

    arguments_moteur: dict = {}
    if p.database_url.startswith("sqlite"):
        arguments_moteur["connect_args"] = {"check_same_thread": False}
    moteur_bdd = create_engine(p.database_url, **arguments_moteur)
    # Alembic fait autorité sur le schéma (création comprise) : create_all() créerait des
    # tables hors de son suivi, que les migrations suivantes ne retrouveraient pas.
    appliquer_migrations(moteur_bdd)
    fabrique = sessionmaker(bind=moteur_bdd, expire_on_commit=False)

    app = FastAPI(title="Lynceus API", version=__version__)
    app.state.parametres = p
    app.state.acces_analyses = {}

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in p.cors_origins.split(",")],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # ---------- utilitaires ----------

    revoquees = {c.strip() for c in p.cles_revoquees.split(",") if c.strip()}

    def verifier_cle(requete: Request) -> cles.Droits | None:
        """Valide la clé d'accès si l'instance en exige une.

        La validation est purement cryptographique : aucune consultation d'annuaire. Une
        instance sans `cle_publique` reste ouverte — c'est le cas d'un usage personnel."""
        if not p.cle_publique:
            return None
        fournie = requete.headers.get("X-Lynceus-Cle", "")
        if not fournie:
            raise HTTPException(
                401,
                "Cette instance demande une clé d'accès. Renseignez-la dans les réglages de "
                "l'extension (en-tête X-Lynceus-Cle).",
            )
        try:
            return cles.valider(fournie, p.cle_publique, revoquees)
        except cles.CleInvalide as exc:
            raise HTTPException(401, str(exc)) from exc

    def adresse_visiteur(requete: Request) -> str:
        """Adresse servant de clé au compteur de débit.

        Derrière un tunnel ou un proxy, l'adresse de transport est celle du proxy : sans
        l'en-tête configuré, tous les visiteurs partageraient un même compteur. L'en-tête
        n'est lu QUE s'il a été explicitement nommé dans la configuration — il est trivial
        à falsifier, et n'a de valeur que si l'instance n'est joignable que par le proxy."""
        if p.entete_ip_reelle:
            valeur = requete.headers.get(p.entete_ip_reelle, "")
            # Certains proxys chaînent les adresses : la première est celle du visiteur.
            premiere = valeur.split(",")[0].strip()
            if premiere:
                return premiere
        return requete.client.host if requete.client else "inconnue"

    def verifier_limite(requete: Request) -> None:
        """Limiteur en mémoire, par adresse, sur le travail coûteux (fetch serveur, appel LLM).
        Conformément à la charte (§4), rien n'est journalisé : la structure ne vit qu'en mémoire."""
        ip = adresse_visiteur(requete)
        maintenant = time.monotonic()
        acces = app.state.acces_analyses.setdefault(ip, [])
        acces[:] = [t for t in acces if maintenant - t < 60]
        if len(acces) >= p.rate_limit_analyses:
            raise HTTPException(429, "Trop de demandes d'analyse — réessayez dans une minute.")
        acces.append(maintenant)

    def appeler_moteur(url: str | None, titre: str | None, langue: str | None,
                       contenu: str, version: str) -> tuple[dict, list[dict]]:
        """Appel LLM + validation, avec un retry qui renvoie l'erreur au modèle. 502 en dernier recours."""
        schema_llm = prompt.schema_sortie_llm()
        ids_valides = set(prompt.charger_taxonomie())
        messages = [
            {"role": "system", "content": prompt.prompt_systeme(version)},
            {"role": "user", "content": prompt.message_utilisateur(
                url, titre, langue, contenu,
                date_analyse=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            )},
        ]
        derniere_erreur: Exception | None = None
        for _ in range(2):
            try:
                texte = llm.appeler(messages, p, schema_json=schema_llm)
            except llm.ErreurLLM as exc:
                raise HTTPException(502, f"Fournisseur LLM en échec : {exc}") from exc
            try:
                donnees = llm.extraire_json(texte)
                return validation.valider_sortie(donnees, schema_llm, ids_valides, contenu)
            except (ValueError, validation.ErreurValidation) as exc:
                derniere_erreur = exc
                messages = messages + [
                    {"role": "assistant", "content": texte},
                    {"role": "user", "content": (
                        f"Ta réponse était invalide ({exc}). "
                        "Renvoie uniquement l'objet JSON corrigé, conforme au schéma, sans aucun texte autour."
                    )},
                ]
        raise HTTPException(502, f"Sortie du modèle invalide après retry : {derniere_erreur}")

    def assembler_carte(sortie: dict, *, url: str | None, titre: str | None, langue: str | None,
                        version: str, duree_ms: int, tronque: bool = False) -> dict:
        """La carte finale : matière du LLM + note calculée par le SERVEUR + métadonnées de transparence."""
        dimensions = sortie["dimensions"]
        score = notation.calculer_score(dimensions)
        carte: dict = {
            "version_schema": VERSION_SCHEMA,
            "categorie": sortie["categorie"],
            "note": {
                "grade": notation.calculer_grade(score),
                "score": score,
                "confiance": sortie["note"]["confiance"],
            },
            "dimensions": dimensions,
            "techniques_detectees": sortie["techniques_detectees"],
            "points_positifs": sortie["points_positifs"],
            "questions_a_se_poser": sortie["questions_a_se_poser"],
            "resume_neutre": sortie["resume_neutre"],
            "avertissements": list(dict.fromkeys([
                *sortie.get("avertissements", []),
                *([AVERTISSEMENT_TRONQUE] if tronque else []),
                AVERTISSEMENT_IA,
            ])),
            "meta": {
                "modele": p.llm_model,
                "fournisseur": urlsplit(p.llm_base_url).hostname or "inconnu",
                "prompt_version": version,
                "analyse_le": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "duree_ms": duree_ms,
            },
        }
        if url:
            carte["url"] = url
            carte["domaine"] = extraire_domaine(url)
        if titre:
            carte["titre"] = titre[:500]
        if langue or sortie.get("langue"):
            carte["langue"] = langue or sortie.get("langue")

        jsonschema.validate(carte, prompt.charger_schema_carte())  # ceinture et bretelles
        return carte

    # ---------- routes ----------

    @app.get("/v1/lookup")
    def lookup(url_hash: str | None = Query(default=None, min_length=64, max_length=64),
               url: str | None = Query(default=None)):
        """Consultation de l'annuaire — jamais journalisée avec identifiants (charte §4)."""
        domaine = None
        if url_hash is None:
            if url is None:
                raise HTTPException(400, "Fournir url_hash (préféré) ou url.")
            try:
                url_hash = hacher_url(url)
                domaine = extraire_domaine(url)
            except ValueError as exc:
                raise HTTPException(400, str(exc)) from exc

        with fabrique() as session:
            page = annuaire.chercher_page(session, url_hash)
            if page is not None:
                domaine = page.domaine
                if page.analyse_courante_id:
                    analyse = session.get(Analyse, page.analyse_courante_id)
                    return {
                        "statut": "connue",
                        "carte": analyse.carte,
                        "domaine": annuaire.profil_domaine(session, domaine),
                    }
            return {
                "statut": "inconnue",
                "carte": None,
                "domaine": annuaire.profil_domaine(session, domaine) if domaine else None,
            }

    @app.get("/v1/lookup-prefixe")
    def lookup_prefixe(prefixe: str = Query(min_length=annuaire.LONGUEUR_PREFIXE,
                                            max_length=annuaire.LONGUEUR_PREFIXE,
                                            pattern="^[0-9a-fA-F]+$")):
        """Consultation k-anonyme : le client envoie les premiers caractères du hash d'URL
        et fait la correspondance finale lui-même. Le serveur ne peut donc pas savoir quelle
        page est consultée — engagement de la charte §4, modèle HaveIBeenPwned."""
        with fabrique() as session:
            correspondances = annuaire.chercher_par_prefixe(session, prefixe)
        return {"prefixe": prefixe.lower(), "correspondances": correspondances}

    @app.post("/v1/signalements")
    def signaler(demande: DemandeSignalement, requete: Request):
        """Contestation d'une analyse — ouverte à tous, y compris aux éditeurs des sites
        analysés (charte §6 : toute analyse est contestable)."""
        if demande.motif not in MOTIFS_SIGNALEMENT:
            raise HTTPException(400, f"Motif inconnu. Motifs acceptés : {sorted(MOTIFS_SIGNALEMENT)}")
        verifier_limite(requete)  # même garde-fou que l'analyse : évite le noyage
        with fabrique() as session:
            if session.get(Analyse, demande.analyse_id) is None:
                raise HTTPException(404, "Analyse inconnue.")
            signalement = annuaire.enregistrer_signalement(
                session,
                analyse_id=demande.analyse_id,
                motif=demande.motif,
                message=demande.message,
                contact=demande.contact,
            )
            session.commit()
            return {
                "id": signalement.id,
                "statut": signalement.statut,
                # Honnêteté : cette instance n'a pas d'équipe de modération. On décrit ce qui
                # se passe réellement, sans promettre un examen dont rien ne garantit la tenue.
                "message": "Contestation enregistrée et visible publiquement sur cette analyse. "
                           "Elle est mise à disposition de l'opérateur de cette instance, qui "
                           "décide des suites. Si vous signalez que la page a changé, une "
                           "nouvelle analyse la remplacera automatiquement à la prochaine visite.",
            }

    def verifier_operateur(requete: Request) -> None:
        """Les routes de modération exigent le jeton d'administration de l'instance.
        Sans jeton configuré, elles sont fermées : une instance publique ne doit pas exposer
        les contestations (elles peuvent contenir un contact) par simple oubli de configuration."""
        if not p.admin_token:
            raise HTTPException(
                403,
                "Modération désactivée : définir LYNCEUS_ADMIN_TOKEN pour activer ces routes.",
            )
        fourni = requete.headers.get("X-Lynceus-Admin", "")
        if not secrets.compare_digest(fourni, p.admin_token):
            raise HTTPException(403, "Jeton d'administration invalide.")

    @app.get("/v1/admin/signalements")
    def lister_signalements(requete: Request, statut: str | None = None, limite: int = Query(default=50, le=200)):
        """Contestations à examiner — réservé à l'opérateur de l'instance."""
        verifier_operateur(requete)
        with fabrique() as session:
            signalements = annuaire.lister_signalements(session, statut=statut, limite=limite)
            return {
                "signalements": [
                    {
                        "id": s.id,
                        "analyse_id": s.analyse_id,
                        "motif": s.motif,
                        "message": s.message,
                        "contact": s.contact,
                        "statut": s.statut,
                        "decision": s.decision,
                        "cree_le": s.cree_le.isoformat(),
                        "traite_le": s.traite_le.isoformat() if s.traite_le else None,
                    }
                    for s in signalements
                ]
            }

    @app.post("/v1/admin/signalements/{signalement_id}")
    def traiter_signalement(signalement_id: int, decision: DecisionSignalement, requete: Request):
        """Enregistre la décision de l'opérateur, avec sa justification (obligatoire)."""
        verifier_operateur(requete)
        with fabrique() as session:
            try:
                signalement = annuaire.traiter_signalement(
                    session, signalement_id, statut=decision.statut, decision=decision.decision
                )
            except ValueError as exc:
                raise HTTPException(400, str(exc)) from exc
            if signalement is None:
                raise HTTPException(404, "Signalement inconnu.")
            session.commit()
            return {"id": signalement.id, "statut": signalement.statut}

    @app.get("/v1/motifs-signalement")
    def motifs_signalement():
        """Motifs acceptés — permet aux clients de construire leur formulaire sans les coder en dur."""
        return {"motifs": sorted(MOTIFS_SIGNALEMENT)}

    @app.post("/v1/analyses")
    def analyser(demande: DemandeAnalyse, requete: Request):
        if not demande.url and not demande.contenu_markdown:
            raise HTTPException(400, "Fournir au moins url ou contenu_markdown.")

        droits = verifier_cle(requete)

        version = prompt.resoudre_version(p.prompt_version)

        # Clés URL (si URL fournie)
        url_brute, url_normalisee, url_hash, domaine = demande.url, None, None, None
        if url_brute:
            try:
                url_normalisee = normaliser_url(url_brute)
                url_hash = hacher_url(url_brute)
                domaine = extraire_domaine(url_brute)
            except ValueError as exc:
                raise HTTPException(400, str(exc)) from exc

        # Le travail coûteux (fetch serveur, LLM) n'est décompté qu'une fois par requête.
        # Une réponse servie depuis l'annuaire ne consomme donc NI limite NI quota : elle
        # ne coûte rien, et pénaliser sa mutualisation irait contre l'intérêt du réseau.
        limite_verifiee = False

        def limiter() -> None:
            nonlocal limite_verifiee
            if limite_verifiee:
                return
            verifier_limite(requete)
            if droits is not None:
                with fabrique() as session_quota:
                    autorise, consommees = annuaire.consommer_quota(
                        session_quota, droits.identifiant, droits.quota_jour
                    )
                    session_quota.commit()
                if not autorise:
                    raise HTTPException(
                        429,
                        f"Quota journalier atteint ({consommees}/{droits.quota_jour} analyses). "
                        "Les pages déjà présentes dans l'annuaire restent consultables sans limite.",
                    )
            limite_verifiee = True

        # 1. Contenu : fourni par le client (chemin principal) ou récupéré par le serveur (fallback).
        #    URL seule → on regarde d'abord l'annuaire par URL : pas de fetch si la page est déjà connue.
        titre, contenu = demande.titre, demande.contenu_markdown
        if contenu is None:
            with fabrique() as session:
                page = annuaire.chercher_page(session, url_hash)
                if page is not None and page.analyse_courante_id:
                    analyse = session.get(Analyse, page.analyse_courante_id)
                    if analyse is not None and analyse.prompt_version == version:
                        return {"en_cache": True, "carte": analyse.carte}
            limiter()
            try:
                titre_extrait, contenu = extraction.recuperer_markdown(url_brute)
                titre = titre or titre_extrait
            except extraction.ErreurExtraction as exc:
                raise HTTPException(502, str(exc)) from exc

        if len(contenu) < p.contenu_min_cars:
            raise HTTPException(400, f"Contenu trop court pour une analyse fiable (< {p.contenu_min_cars} caractères).")
        if len(contenu) > p.contenu_max_cars:
            raise HTTPException(413, f"Contenu trop long (> {p.contenu_max_cars} caractères).")

        content_hash = hacher_contenu(contenu)

        with fabrique() as session:
            # 2. Résolution annuaire : même contenu déjà analysé (ici ou copié ailleurs) → cache
            analyse = annuaire.chercher_analyse(session, content_hash, version)
            if analyse is not None:
                if url_hash:
                    annuaire.lier_page(session, url=url_brute, url_normalisee=url_normalisee,
                                       url_hash=url_hash, domaine=domaine, analyse=analyse)
                    session.commit()
                return {"en_cache": True, "carte": analyse.carte}

            # 3. Analyse LLM complète
            limiter()
            debut = time.monotonic()
            sortie, rejets = appeler_moteur(url_brute, titre, demande.langue, contenu, version)
            duree_ms = int((time.monotonic() - debut) * 1000)
            carte = assembler_carte(sortie, url=url_brute, titre=titre, langue=demande.langue,
                                    version=version, duree_ms=duree_ms, tronque=demande.tronque)

            analyse = Analyse(
                content_hash=content_hash,
                prompt_version=version,
                schema_version=VERSION_SCHEMA,
                carte=carte,
                categorie=carte["categorie"],
                score=carte["note"]["score"],
                grade=carte["note"]["grade"],
                confiance=carte["note"]["confiance"],
                modele=carte["meta"]["modele"],
                fournisseur=carte["meta"]["fournisseur"],
                duree_ms=duree_ms,
            )
            session.add(analyse)
            session.flush()
            if url_hash:
                annuaire.lier_page(session, url=url_brute, url_normalisee=url_normalisee,
                                   url_hash=url_hash, domaine=domaine, analyse=analyse)
            session.commit()

            reponse: dict = {"en_cache": False, "carte": carte}
            if rejets:
                reponse["detections_rejetees"] = rejets  # transparence : ce que le serveur a écarté
            return reponse

    @app.get("/v1/analyses/{analyse_id}")
    def obtenir_analyse(analyse_id: int):
        with fabrique() as session:
            analyse = session.get(Analyse, analyse_id)
            if analyse is None:
                raise HTTPException(404, "Analyse inconnue.")
            # Le nombre de contestations est public : une analyse contestée doit se voir.
            return {
                "carte": analyse.carte,
                "signalements": annuaire.compter_signalements(session, analyse_id),
            }

    @app.get("/v1/domaines/{domaine}")
    def obtenir_domaine(domaine: str):
        with fabrique() as session:
            profil = annuaire.profil_domaine(session, domaine.lower())
            if profil is None:
                raise HTTPException(404, "Domaine inconnu de l'annuaire.")
            return profil

    @app.get("/sante")
    def sante():
        """Point de santé pour l'orchestrateur — vérifie la base, pas seulement le processus.

        Un serveur qui répond mais dont la base est injoignable doit être signalé en panne,
        sinon l'orchestrateur le laisserait recevoir du trafic qu'il ne peut pas servir."""
        try:
            with fabrique() as session:
                session.execute(text("SELECT 1"))
        except Exception as exc:  # noqa: BLE001 — on veut signaler toute panne, quelle qu'elle soit
            raise HTTPException(503, f"Base de données injoignable : {exc}") from exc
        return {"statut": "ok", "version": __version__}

    @app.get("/v1/meta")
    def meta():
        """Transparence de l'instance : qui analyse, avec quoi, selon quelle version."""
        return {
            "nom": "lynceus-api",
            "version": __version__,
            "schema_version": VERSION_SCHEMA,
            "prompt_version": prompt.resoudre_version(p.prompt_version),
            "modele": p.llm_model,
            "fournisseur": urlsplit(p.llm_base_url).hostname or "inconnu",
            "taxonomie": {"nb_techniques": len(prompt.charger_taxonomie())},
            "limites": {"contenu_max_cars": p.contenu_max_cars, "analyses_par_minute": p.rate_limit_analyses},
            "capacites": {
                "cle_requise": bool(p.cle_publique),
                "lookup_k_anonyme": True,
                "longueur_prefixe": annuaire.LONGUEUR_PREFIXE,
                "signalements": True,
                "motifs_signalement": sorted(MOTIFS_SIGNALEMENT),
            },
        }

    return app
