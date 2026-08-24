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
    llm_temperature: float = 0.2
    llm_timeout_s: float = 180.0
    # none : le prompt exige du JSON (universel) · json_object / json_schema : si le fournisseur les supporte
    llm_response_format: str = "none"

    # Garde-fous
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
