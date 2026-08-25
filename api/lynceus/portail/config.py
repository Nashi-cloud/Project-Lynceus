"""Configuration du portail — variables d'environnement LYNCEUS_PORTAIL_*.

Le portail est un service **distinct de l'instance**, et c'est le seul endroit du projet
qui détient la clé privée d'émission. Cette séparation est la raison d'être du fichier :
si le portail partageait le processus de l'API, la clé privée se retrouverait sur la
machine exposée, et compromettre l'instance suffirait à forger des clés à volonté.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class ParametresPortail(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LYNCEUS_PORTAIL_", env_file=(".env", "api/.env"), extra="ignore"
    )

    # --- Identité ---
    nom: str = "Lynceus"
    # Affiché sur la page « contester » et dans le pied de page. Vide = pas de contact publié.
    contact: str = ""

    # --- Émission de clés ---
    # Clé PRIVÉE Ed25519 (base64url), produite par `lynceus cles-paire`. Vide = portail
    # vitrine : les pages restent servies, l'inscription répond 503 en le disant.
    cle_privee: str = ""
    # Adresse de l'instance annoncée dans le billet d'accès — celle que l'extension
    # utilisera. Doit être joignable depuis le navigateur des visiteurs.
    instance: str = ""
    # Adresse par laquelle le portail lui-même joint l'instance (nom de service Docker,
    # adresse interne…). Vide = on réutilise `instance`.
    instance_interne: str = ""
    quota_jour: int = 20
    validite_jours: int = 365
    # Nombre de clés délivrées par adresse et par jour. 0 = illimité (défaut : l'inscription
    # est libre et anonyme). Le relever ne demande qu'un redémarrage, sans changement de code,
    # si l'inscription ouverte attirait des scripts.
    cles_par_ip_jour: int = 0

    # --- Distribution de l'extension ---
    # Dossier contenant les archives lynceus-extension-v*.zip. La plus récente est proposée
    # au téléchargement. Vide = le portail annonce honnêtement qu'aucun paquet n'est publié.
    paquets: str = ""

    # --- Réseau ---
    # L'extension appelle /v1/inscription depuis chrome-extension://<id>, identifiant qui
    # change à chaque installation non empaquetée : le CORS ne peut pas servir de filtre ici.
    cors_origins: str = "*"
    # Même précaution que côté API : ne renseigner que si le portail n'est joignable QUE
    # par le proxy, un en-tête étant trivial à falsifier.
    entete_ip_reelle: str = ""
    delai_instance_s: float = 5.0


@lru_cache
def parametres_portail() -> ParametresPortail:
    return ParametresPortail()
