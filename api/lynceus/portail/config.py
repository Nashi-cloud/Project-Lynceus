"""Configuration du portail — variables d'environnement LYNCEUS_PORTAIL_*.

Le portail est un service **distinct de l'instance**, et c'est le seul endroit du projet
qui détient la clé privée d'émission. Cette séparation est la raison d'être du fichier :
si le portail partageait le processus de l'API, la clé privée se retrouverait sur la
machine exposée, et compromettre l'instance suffirait à forger des clés à volonté.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from ..noms import ReglagesTolerants, deux_noms


class ParametresPortail(ReglagesTolerants):
    # populate_by_name : un alias de validation remplace le nom du champ. Sans cette
    # option, construire l'objet en Python cesserait d'accepter le nom du champ, ce dont
    # vivent les tests et la CLI.
    model_config = SettingsConfigDict(
        populate_by_name=True, env_prefix="LYNCEUS_PORTAIL_",
        env_file=(".env", "api/.env"), extra="ignore",
    )

    # --- Identité ---
    nom: str = deux_noms("LYNCEUS_PORTAIL_NOM", "LYNCEUS_PORTAL_NAME", "Lynceus")
    # Affiché sur la page « contester » et dans le pied de page. Vide = pas de contact publié.
    contact: str = deux_noms("LYNCEUS_PORTAIL_CONTACT", "LYNCEUS_PORTAL_CONTACT", "")

    # --- Émission de clés ---
    # Clé PRIVÉE Ed25519 (base64url), produite par `lynceus cles-paire`. Vide = portail
    # vitrine : les pages restent servies, l'inscription répond 503 en le disant.
    cle_privee: str = deux_noms("LYNCEUS_PORTAIL_CLE_PRIVEE", "LYNCEUS_PORTAL_PRIVATE_KEY", "")
    # Adresse de l'instance annoncée dans le billet d'accès — celle que l'extension
    # utilisera. Doit être joignable depuis le navigateur des visiteurs.
    instance: str = deux_noms("LYNCEUS_PORTAIL_INSTANCE", "LYNCEUS_PORTAL_INSTANCE", "")
    # Adresse par laquelle le portail lui-même joint l'instance (nom de service Docker,
    # adresse interne…). Vide = on réutilise `instance`.
    instance_interne: str = deux_noms("LYNCEUS_PORTAIL_INSTANCE_INTERNE", "LYNCEUS_PORTAL_INTERNAL_INSTANCE", "")
    quota_jour: int = deux_noms("LYNCEUS_PORTAIL_QUOTA_JOUR", "LYNCEUS_PORTAL_DAILY_QUOTA", 20)
    validite_jours: int = deux_noms("LYNCEUS_PORTAIL_VALIDITE_JOURS", "LYNCEUS_PORTAL_VALIDITY_DAYS", 365)
    # Nombre de clés délivrées par adresse et par jour. 0 = illimité (défaut : l'inscription
    # est libre et anonyme). Le relever ne demande qu'un redémarrage, sans changement de code,
    # si l'inscription ouverte attirait des scripts.
    cles_par_ip_jour: int = deux_noms("LYNCEUS_PORTAIL_CLES_PAR_IP_JOUR", "LYNCEUS_PORTAL_KEYS_PER_IP_DAY", 0)

    # --- Distribution de l'extension ---
    # Dossiers contenant les archives lynceus-extension-v*.zip, séparés par des virgules.
    # Typiquement un volume alimenté à la main et le paquet embarqué dans l'image : la
    # version la plus haute l'emporte, d'où qu'elle vienne. Vide = le portail annonce
    # honnêtement qu'aucun paquet n'est publié.
    paquets: str = deux_noms("LYNCEUS_PORTAIL_PAQUETS", "LYNCEUS_PORTAL_PACKAGES", "")

    # Adresse publique de ce portail, glissée dans l'archive téléchargée pour que
    # l'extension sache à qui demander sa clé. Vide = déduite de la requête, ce qui suffit
    # dans la plupart des cas mais se trompe de schéma derrière un proxy qui ne transmet
    # pas X-Forwarded-Proto.
    adresse: str = deux_noms("LYNCEUS_PORTAIL_ADRESSE", "LYNCEUS_PORTAL_ADDRESS", "")

    # --- Identité légale de l'exploitant ---
    # Obligatoire dès qu'une instance est ouverte au public en France : la loi pour la
    # confiance dans l'économie numérique impose d'identifier l'éditeur d'un service de
    # communication au public en ligne. Ces champs sont configurables et non codés en dur
    # parce que chaque instance a son propre exploitant : le projet est auto-hébergeable,
    # et publier l'identité de quelqu'un d'autre serait faux.
    #
    # Non renseignés, les pages légales le disent au lieu d'inventer, et le portail
    # avertit au démarrage. Un usage strictement personnel n'a pas à les remplir.
    editeur_nom: str = deux_noms("LYNCEUS_PORTAIL_EDITEUR_NOM", "LYNCEUS_PORTAL_PUBLISHER_NAME", "")
    editeur_statut: str = deux_noms("LYNCEUS_PORTAIL_EDITEUR_STATUT", "LYNCEUS_PORTAL_PUBLISHER_STATUS", "")  # ex. « entrepreneur individuel (EI) »
    editeur_adresse: str = deux_noms("LYNCEUS_PORTAIL_EDITEUR_ADRESSE", "LYNCEUS_PORTAL_PUBLISHER_ADDRESS", "")
    editeur_identifiant: str = deux_noms("LYNCEUS_PORTAIL_EDITEUR_IDENTIFIANT", "LYNCEUS_PORTAL_PUBLISHER_ID", "")  # SIREN, numéro d'entreprise, équivalent local
    editeur_directeur: str = deux_noms("LYNCEUS_PORTAIL_EDITEUR_DIRECTEUR", "LYNCEUS_PORTAL_PUBLISHER_DIRECTOR", "")  # directeur de la publication
    editeur_contact: str = deux_noms("LYNCEUS_PORTAIL_EDITEUR_CONTACT", "LYNCEUS_PORTAL_PUBLISHER_CONTACT", "")  # adresse électronique de contact

    hebergeur_nom: str = deux_noms("LYNCEUS_PORTAIL_HEBERGEUR_NOM", "LYNCEUS_PORTAL_HOST_NAME", "")
    hebergeur_adresse: str = deux_noms("LYNCEUS_PORTAIL_HEBERGEUR_ADRESSE", "LYNCEUS_PORTAL_HOST_ADDRESS", "")
    hebergeur_site: str = deux_noms("LYNCEUS_PORTAIL_HEBERGEUR_SITE", "LYNCEUS_PORTAL_HOST_SITE", "")

    # Juridiction dont relèvent les conditions d'utilisation. Vide = non précisée.
    droit_applicable: str = deux_noms("LYNCEUS_PORTAIL_DROIT_APPLICABLE", "LYNCEUS_PORTAL_GOVERNING_LAW", "")

    # --- Code source ---
    # Adresse publique du code source de CETTE instance. L'AGPL-3.0 impose (article 13) de
    # proposer le code correspondant, modifications comprises, aux personnes qui utilisent
    # le service à distance : un portail ouvert au public sans cette adresse n'est pas en
    # règle avec sa propre licence.
    #
    # Le défaut renvoie au dépôt d'origine, ce qui est exact tant que l'instance fait
    # tourner le code publié tel quel. **Dès que vous le modifiez, remplacez cette adresse
    # par celle de VOTRE dépôt** : c'est votre version qui doit être proposée, pas la
    # nôtre. Vide = les pages parlent du dépôt sans lien, et le portail avertit au
    # démarrage.
    depot: str = deux_noms("LYNCEUS_PORTAIL_DEPOT", "LYNCEUS_PORTAL_REPOSITORY", "https://github.com/Nashi-cloud/Project-Lynceus")
    # Préfixe pour désigner un fichier précis du dépôt, branche comprise :
    # « https://…/blob/main » sur GitHub ou GitLab, « …/src/branch/main » sur Forgejo.
    # Chaque forge a sa forme, d'où une variable distincte plutôt qu'une adresse devinée.
    # Vide = les chemins cités dans les documents s'affichent sans lien.
    depot_fichiers: str = deux_noms("LYNCEUS_PORTAIL_DEPOT_FICHIERS", "LYNCEUS_PORTAL_REPOSITORY_FILES", "https://github.com/Nashi-cloud/Project-Lynceus/blob/main")

    # --- Réseau ---
    # L'extension appelle /v1/inscription depuis chrome-extension://<id>, identifiant qui
    # change à chaque installation non empaquetée : le CORS ne peut pas servir de filtre ici.
    cors_origins: str = deux_noms("LYNCEUS_PORTAIL_CORS_ORIGINS", "LYNCEUS_PORTAL_CORS_ORIGINS", "*")
    # Même précaution que côté API : ne renseigner que si le portail n'est joignable QUE
    # par le proxy, un en-tête étant trivial à falsifier.
    entete_ip_reelle: str = deux_noms("LYNCEUS_PORTAIL_ENTETE_IP_REELLE", "LYNCEUS_PORTAL_REAL_IP_HEADER", "")
    delai_instance_s: float = deux_noms("LYNCEUS_PORTAIL_DELAI_INSTANCE_S", "LYNCEUS_PORTAL_INSTANCE_TIMEOUT_S", 5.0)


@lru_cache
def parametres_portail() -> ParametresPortail:
    return ParametresPortail()
