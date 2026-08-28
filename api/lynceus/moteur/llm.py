"""Adapter LLM — un seul contrat : endpoint compatible OpenAI (POST {base_url}/chat/completions).
Couvre OpenRouter, Ollama, vLLM, LiteLLM… Le choix du fournisseur appartient à chaque instance."""

from __future__ import annotations

import ipaddress
import json
import re
from urllib.parse import urlsplit

import httpx

from ..config import Parametres

# Un modèle joint sur une de ces adresses tourne chez l'exploitant : le texte analysé ne
# quitte pas son infrastructure. La liste est volontairement large, un faux « local »
# ferait promettre au portail une confidentialité qui n'existe pas.
_HOTES_LOCAUX = {"localhost", "host.docker.internal"}
_SUFFIXES_LOCAUX = (".local", ".lan", ".internal", ".intranet", ".home.arpa")


def _est_local(hote: str) -> bool:
    if not hote:
        return False
    if hote in _HOTES_LOCAUX or hote.endswith(_SUFFIXES_LOCAUX):
        return True
    if "." not in hote:
        # Nom de service Docker (« ollama », « vllm ») ou machine du réseau local.
        return True
    try:
        adresse = ipaddress.ip_address(hote)
    except ValueError:
        return False
    return adresse.is_private or adresse.is_loopback


def fournisseur_annonce(base_url: str, libelle: str = "") -> tuple[str, bool]:
    """Comment nommer publiquement le fournisseur de modèle, et si le texte sort de l'instance.

    Deux raisons de ne pas se contenter du nom d'hôte, comme c'était le cas jusqu'ici.
    D'abord il est faux dès qu'il y a un intermédiaire : un routeur d'inférence porte son
    propre nom, pas celui de l'entreprise qui exécute le modèle. Ensuite le nom d'hôte d'un
    endpoint privé n'a rien à faire dans une carte publiée : il ne dit rien au lecteur et
    renseigne le réseau de l'exploitant. D'où un libellé configurable, et un repli qui
    annonce un modèle auto-hébergé pour ce qu'il est, sans nommer la machine."""
    hote = (urlsplit(base_url).hostname or "").lower()
    if not hote:
        # Instance non configurée : rien ne permet de promettre que le texte reste ici.
        return (libelle or "non renseigné"), True
    distant = not _est_local(hote)
    if libelle:
        return libelle, distant
    return (hote if distant else "modèle auto-hébergé"), distant


class ErreurLLM(Exception):
    """Échec de l'appel au fournisseur LLM."""


# Erreurs fréquentes du fournisseur → cause probable et remède, en clair
_AIDES = {
    401: "clé refusée ou absente — vérifier LYNCEUS_LLM_API_KEY dans api/.env, puis REDÉMARRER le serveur (le .env est lu au démarrage)",
    402: "crédit insuffisant chez le fournisseur — recharger le compte",
    403: "accès refusé par le fournisseur (clé restreinte à certains modèles ?)",
    404: "modèle introuvable chez le fournisseur — vérifier LYNCEUS_LLM_MODEL (slugs : openrouter.ai/models)",
    429: "limite de débit du fournisseur atteinte — réessayer dans quelques instants",
}


def marquer_le_cache(messages: list[dict]) -> list[dict]:
    """Annonce le prompt système comme réutilisable d'un appel à l'autre.

    Il fait environ 3 500 tokens et ne change jamais, quand la page analysée en pèse
    quelques centaines : c'est lui qui domine la facture d'entrée. Le marquer le fait
    facturer au tarif de relecture, nettement moindre, dès le deuxième appel.

    La forme est celle qu'attendent les fournisseurs qui demandent des points de césure
    explicites : le contenu devient une liste de blocs, et le dernier porte la marque. Ceux
    qui mettent en cache d'eux-mêmes la reçoivent sans s'en servir, ce qui est sans effet.
    Un message déjà découpé en blocs est laissé tel quel plutôt que réemballé."""
    marques = []
    for message in messages:
        contenu = message.get("content")
        if message.get("role") == "system" and isinstance(contenu, str):
            message = {**message, "content": [
                {"type": "text", "text": contenu, "cache_control": {"type": "ephemeral"}}
            ]}
        marques.append(message)
    return marques


# Le vocabulaire du fournisseur, repris tel quel, comme le fait déjà `llm_response_format`
# avec « json_object » et « json_schema ». Traduire « low » en « faible » obligerait
# l'exploitant à une conversion que la documentation de son fournisseur ne lui donne pas.
_RAISONNEMENT = {
    "off": {"enabled": False},
    "low": {"effort": "low"},
    "medium": {"effort": "medium"},
    "high": {"effort": "high"},
}


def reglage_raisonnement(demande: str) -> dict | None:
    """Le paramètre à envoyer, ou None pour laisser le fournisseur décider.

    Un réglage inconnu ne fait pas échouer l'analyse : il est ignoré, et l'instance se
    comporte comme si rien n'avait été demandé. Une faute de frappe dans un fichier .env ne
    doit pas éteindre le service."""
    return _RAISONNEMENT.get(demande.strip().lower())


def appeler(messages: list[dict], p: Parametres, schema_json: dict | None = None) -> str:
    """Retourne le texte de la réponse du modèle. Lève ErreurLLM en cas d'échec."""
    charge: dict = {
        "model": p.llm_model,
        "messages": marquer_le_cache(messages) if p.llm_cache_prompt else messages,
        "temperature": p.llm_temperature,
    }
    raisonnement = reglage_raisonnement(p.llm_raisonnement)
    if raisonnement is not None:
        charge["reasoning"] = raisonnement

    if p.llm_response_format == "json_object":
        charge["response_format"] = {"type": "json_object"}
    elif p.llm_response_format == "json_schema" and schema_json is not None:
        charge["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "carte_lynceus", "strict": True, "schema": schema_json},
        }

    entetes = {"Content-Type": "application/json"}
    if p.llm_api_key:
        entetes["Authorization"] = f"Bearer {p.llm_api_key}"

    try:
        reponse = httpx.post(
            f"{p.llm_base_url.rstrip('/')}/chat/completions",
            json=charge,
            headers=entetes,
            timeout=p.llm_timeout_s,
        )
    except httpx.HTTPError as exc:
        raise ErreurLLM(f"Fournisseur LLM injoignable : {exc}") from exc

    if reponse.status_code >= 400:
        aide = _AIDES.get(reponse.status_code)
        precision = f" ({aide})" if aide else ""
        raise ErreurLLM(f"Fournisseur LLM : HTTP {reponse.status_code}{precision} — {reponse.text[:300]}")

    try:
        return reponse.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise ErreurLLM(f"Réponse LLM inattendue : {reponse.text[:300]}") from exc


def extraire_json(texte: str) -> dict:
    """Extrait l'objet JSON d'une réponse (tolère les clôtures ``` et le texte parasite)."""
    t = texte.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\s*", "", t)
        t = re.sub(r"\s*```\s*$", "", t)
    debut, fin = t.find("{"), t.rfind("}")
    if debut == -1 or fin <= debut:
        raise ValueError("aucun objet JSON trouvé dans la réponse du modèle")
    donnees = json.loads(t[debut:fin + 1])
    if not isinstance(donnees, dict):
        raise ValueError("la réponse JSON n'est pas un objet")
    return donnees
