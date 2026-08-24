"""Adapter LLM — un seul contrat : endpoint compatible OpenAI (POST {base_url}/chat/completions).
Couvre OpenRouter, Ollama, vLLM, LiteLLM… Le choix du fournisseur appartient à chaque instance."""

from __future__ import annotations

import json
import re

import httpx

from ..config import Parametres


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


def appeler(messages: list[dict], p: Parametres, schema_json: dict | None = None) -> str:
    """Retourne le texte de la réponse du modèle. Lève ErreurLLM en cas d'échec."""
    charge: dict = {
        "model": p.llm_model,
        "messages": messages,
        "temperature": p.llm_temperature,
    }
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
