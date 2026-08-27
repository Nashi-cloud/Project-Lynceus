"""Configuration de l'instance — variables d'environnement LYNCEUS_* (cf. docs/ARCHITECTURE.md)."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Parametres(BaseSettings):
    # env_file en tuple : trouvé qu'on lance depuis api/ (« .env ») ou depuis la racine (« api/.env »)
    model_config = SettingsConfigDict(env_prefix="LYNCEUS_", env_file=(".env", "api/.env"), extra="ignore")

    # Base de données (SQLite par défaut : zéro config pour essayer)
    database_url: str = "sqlite:///./lynceus.sqlite3"

    # Fournisseur LLM — tout endpoint compatible OpenAI (/chat/completions)
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_api_key: str = ""
    llm_model: str = "anthropic/claude-sonnet-5"
    # Nom du fournisseur tel qu'il sera publié : dans /v1/meta, dans chaque analyse et sur
    # les pages légales du portail. Vide = déduit de l'adresse ci-dessus, ce qui suffit
    # rarement : un routeur d'inférence n'est pas celui qui exécute le modèle, et le nom
    # d'hôte d'un modèle auto-hébergé n'a pas à être publié. Exemples : « Mistral AI »,
    # « OpenRouter, qui sous-traite l'inférence », « Ollama sur la machine de l'instance ».
    llm_fournisseur: str = ""
    llm_temperature: float = 0.2
    llm_timeout_s: float = 180.0
    # none : le prompt exige du JSON (universel) · json_object / json_schema : si le fournisseur les supporte
    llm_response_format: str = "none"

    # Garde-fous
    # Analyses menées de front. Chacune mobilise un thread pendant tout l'appel au modèle
    # (10 à 60 s) ; sans plafond, elles épuiseraient le pool de threads du serveur et les
    # consultations d'annuaire — normalement instantanées — attendraient derrière elles.
    # Les demandes au-delà de ce nombre patientent sans consommer de thread.
    analyses_simultanees: int = 12

    contenu_min_cars: int = 200
    contenu_max_cars: int = 60000
    rate_limit_analyses: int = 10  # requêtes / minute / IP sur POST /v1/analyses

    # Modération : sans jeton, les routes /v1/admin/* restent fermées (défaut sûr).
    admin_token: str = ""

    # Clés d'accès (Ed25519). Vide = instance ouverte, aucune clé exigée : c'est le défaut
    # pour un usage personnel ou auto-hébergé. Renseigner la clé PUBLIQUE de l'émetteur
    # ferme les analyses aux seuls porteurs d'une clé valide.
    cle_publique: str = ""
    # Identifiants de clés révoquées, séparés par des virgules. Ne contient que les clés
    # abusives : ce n'est pas un annuaire, seulement une liste noire.
    cles_revoquees: str = ""

    # Derrière un proxy ou un tunnel (Cloudflare Tunnel, reverse proxy…), toutes les
    # requêtes arrivent avec l'adresse du proxy : le compteur par IP deviendrait commun à
    # tout le monde. Cette option nomme l'en-tête portant l'adresse réelle du visiteur
    # (« CF-Connecting-IP » pour Cloudflare, « X-Real-IP » pour nginx).
    #
    # VIDE PAR DÉFAUT, et c'est important : un en-tête est trivial à falsifier. Ne
    # l'activer que si l'instance n'est JOIGNABLE QUE par le proxy — sinon n'importe qui
    # contournerait la limite en forgeant l'en-tête.
    entete_ip_reelle: str = ""

    # Connexions à la base gardées ouvertes. Le défaut de SQLAlchemy (5 + 10 de débord)
    # est inférieur au nombre de threads du serveur : sous charge, des requêtes attendraient
    # une connexion libre alors que la base, elle, n'est pas saturée.
    bdd_pool_size: int = 20
    bdd_max_overflow: int = 20
    # Recycle les connexions inactives : certains pare-feux et proxys coupent silencieusement
    # les connexions longues, ce qui produit des erreurs déroutantes après une accalmie.
    bdd_pool_recycle_s: int = 1800

    # Divers
    cors_origins: str = "*"
    prompt_version: str = "latest"
    api_url: str = "http://localhost:8000"  # utilisé par le CLI


@lru_cache
def parametres() -> Parametres:
    return Parametres()


@lru_cache
def trouver_racine() -> Path:
    """Racine du dépôt (contient prompts/, docs/, schema/).

    Ordre : LYNCEUS_RACINE_DONNEES > remontée depuis le cwd > remontée depuis ce fichier.
    """
    env = os.environ.get("LYNCEUS_RACINE_DONNEES")
    if env:
        return Path(env)
    for base in (Path.cwd(), Path(__file__).resolve()):
        for candidat in (base, *base.parents):
            if (candidat / "prompts" / "analyse").is_dir():
                return candidat
    raise RuntimeError(
        "Racine du dépôt introuvable (dossier prompts/analyse). "
        "Définir LYNCEUS_RACINE_DONNEES vers le dossier qui contient prompts/, docs/ et schema/."
    )
