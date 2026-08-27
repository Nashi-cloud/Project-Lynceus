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
    # Dossiers contenant les archives lynceus-extension-v*.zip, séparés par des virgules.
    # Typiquement un volume alimenté à la main et le paquet embarqué dans l'image : la
    # version la plus haute l'emporte, d'où qu'elle vienne. Vide = le portail annonce
    # honnêtement qu'aucun paquet n'est publié.
    paquets: str = ""

    # Adresse publique de ce portail, glissée dans l'archive téléchargée pour que
    # l'extension sache à qui demander sa clé. Vide = déduite de la requête, ce qui suffit
    # dans la plupart des cas mais se trompe de schéma derrière un proxy qui ne transmet
    # pas X-Forwarded-Proto.
    adresse: str = ""

    # --- Identité légale de l'exploitant ---
    # Obligatoire dès qu'une instance est ouverte au public en France : la loi pour la
    # confiance dans l'économie numérique impose d'identifier l'éditeur d'un service de
    # communication au public en ligne. Ces champs sont configurables et non codés en dur
    # parce que chaque instance a son propre exploitant : le projet est auto-hébergeable,
    # et publier l'identité de quelqu'un d'autre serait faux.
    #
    # Non renseignés, les pages légales le disent au lieu d'inventer, et le portail
    # avertit au démarrage. Un usage strictement personnel n'a pas à les remplir.
    editeur_nom: str = ""
    editeur_statut: str = ""          # ex. « entrepreneur individuel (EI) »
    editeur_adresse: str = ""
    editeur_identifiant: str = ""     # SIREN, numéro d'entreprise, équivalent local
    editeur_directeur: str = ""       # directeur de la publication
    editeur_contact: str = ""         # adresse électronique de contact

    hebergeur_nom: str = ""
    hebergeur_adresse: str = ""
    hebergeur_site: str = ""

    # Juridiction dont relèvent les conditions d'utilisation. Vide = non précisée.
    droit_applicable: str = ""

    # --- Code source ---
    # Adresse publique du code source de CETTE instance. L'AGPL-3.0 impose (article 13) de
    # proposer le code correspondant, modifications comprises, aux personnes qui utilisent
    # le service à distance : un portail ouvert au public sans cette adresse n'est pas en
    # règle avec sa propre licence. Vide = les pages parlent du dépôt sans lien plutôt que
    # d'en inventer un, et le portail avertit au démarrage.
    depot: str = ""
    # Préfixe pour désigner un fichier précis du dépôt, branche comprise :
    # « https://…/blob/main » sur GitHub ou GitLab, « …/src/branch/main » sur Forgejo.
    # Chaque forge a sa forme, d'où une variable distincte plutôt qu'une adresse devinée.
    # Vide = les chemins cités dans les documents s'affichent sans lien.
    depot_fichiers: str = ""

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
