"""API Lynceus — annuaire + moteur d'analyse (contrat : docs/ARCHITECTURE.md).

Lancement : uvicorn lynceus.main:creer_application --factory
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from urllib.parse import urlsplit

import jsonschema
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import VERSION_SCHEMA, __version__, annuaire, extraction
from .config import Parametres, parametres
from .modeles import Analyse, Base
from .moteur import llm, notation, prompt, validation
from .normalisation import extraire_domaine, hacher_contenu, hacher_url, normaliser_url

AVERTISSEMENT_IA = (
    "Cette analyse est produite par une intelligence artificielle : elle peut comporter des erreurs. "
    "Elle décrit des procédés rhétoriques, pas la valeur des personnes qui partagent ce contenu."
)


class DemandeAnalyse(BaseModel):
    url: str | None = None
    contenu_markdown: str | None = None
    titre: str | None = Field(default=None, max_length=500)
    langue: str | None = Field(default=None, max_length=10)


def creer_application(p: Parametres | None = None) -> FastAPI:
    p = p or parametres()

    arguments_moteur: dict = {}
    if p.database_url.startswith("sqlite"):
        arguments_moteur["connect_args"] = {"check_same_thread": False}
    moteur_bdd = create_engine(p.database_url, **arguments_moteur)
    Base.metadata.create_all(moteur_bdd)
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

    def verifier_limite(requete: Request) -> None:
        """Limiteur en mémoire, par IP, sur le travail coûteux (fetch serveur, appel LLM).
        Conformément à la charte (§4), rien n'est journalisé : la structure ne vit qu'en mémoire."""
        ip = requete.client.host if requete.client else "inconnue"
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
            {"role": "user", "content": prompt.message_utilisateur(url, titre, langue, contenu)},
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
                        version: str, duree_ms: int) -> dict:
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
            "avertissements": list(dict.fromkeys([*sortie.get("avertissements", []), AVERTISSEMENT_IA])),
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

    @app.post("/v1/analyses")
    def analyser(demande: DemandeAnalyse, requete: Request):
        if not demande.url and not demande.contenu_markdown:
            raise HTTPException(400, "Fournir au moins url ou contenu_markdown.")

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

        # Le travail coûteux (fetch serveur, LLM) n'est décompté qu'une fois par requête
        limite_verifiee = False

        def limiter() -> None:
            nonlocal limite_verifiee
            if not limite_verifiee:
                verifier_limite(requete)
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
                                    version=version, duree_ms=duree_ms)

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
            return {"carte": analyse.carte}

    @app.get("/v1/domaines/{domaine}")
    def obtenir_domaine(domaine: str):
        with fabrique() as session:
            profil = annuaire.profil_domaine(session, domaine.lower())
            if profil is None:
                raise HTTPException(404, "Domaine inconnu de l'annuaire.")
            return profil

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
        }

    return app
