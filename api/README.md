# Lynceus API — le « kit » serveur

Serveur annuaire + moteur d'analyse. Python 3.11+, FastAPI, SQLite (zéro config) ou PostgreSQL. Contrat d'API et modèle de données : [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).

## Démarrage rapide

```bash
cd api
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
cp .env.example .env          # y mettre votre clé (OpenRouter, ou Ollama local…)
.venv/bin/uvicorn lynceus.main:creer_application --factory --reload
```

Puis, dans un autre terminal :

```bash
.venv/bin/lynceus analyser https://exemple.fr/un-article    # analyse via l'API
.venv/bin/lynceus lookup   https://exemple.fr/un-article    # consultation annuaire
.venv/bin/lynceus meta                                      # transparence de l'instance
.venv/bin/lynceus calibrer ../corpus/corpus.yaml            # passe de calibration
```

## Avec Docker (API + PostgreSQL)

```bash
cd api
LYNCEUS_LLM_API_KEY=sk-or-... docker compose up --build
```

## Configuration

Variables `LYNCEUS_*` (`.env` accepté) — liste complète dans [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md). L'essentiel :

| Variable | Défaut | Rôle |
|---|---|---|
| `LYNCEUS_LLM_BASE_URL` | `https://openrouter.ai/api/v1` | Tout endpoint compatible OpenAI. Ollama : `http://localhost:11434/v1` |
| `LYNCEUS_LLM_API_KEY` | — | Clé du fournisseur |
| `LYNCEUS_LLM_MODEL` | `anthropic/claude-sonnet-5` | Slug du modèle chez le fournisseur (vérifier sur openrouter.ai/models) |
| `LYNCEUS_DATABASE_URL` | `sqlite:///./lynceus.sqlite3` | PostgreSQL recommandé en production |

## Structure

```
lynceus/
├── main.py                 # app FastAPI (factory) : /v1/lookup, /v1/analyses, /v1/domaines, /v1/meta
├── config.py               # variables LYNCEUS_* + localisation des données du dépôt
├── normalisation.py        # URL → url_hash · Markdown → content_hash (les 2 clés de l'annuaire)
├── modeles.py              # SQLAlchemy : analyses, pages, domaines
├── annuaire.py             # résolution cache/dédup, profils de domaines
├── extraction.py           # fallback fetch serveur (trafilatura) pour le flux « URL seule »
├── moteur/
│   ├── prompt.py           # prompts versionnés + taxonomie + schémas (tout vient des fichiers publics)
│   ├── llm.py              # adapter compatible OpenAI (OpenRouter, Ollama, vLLM…)
│   ├── validation.py       # JSON Schema + ids du référentiel + extraits VERBATIM (anti-hallucination)
│   └── notation.py         # score pondéré → grade — calculé par le serveur, pas par le LLM
└── cli.py                  # lynceus analyser / lookup / calibrer / meta
```

Garanties du pipeline (testées) :

- **Anti-hallucination** : tout extrait cité doit être une sous-chaîne réelle du contenu (aux espaces près), sinon la détection est écartée et listée dans `detections_rejetees`.
- **Note serveur** : le LLM fournit les dimensions, le serveur calcule score et grade (pondérations publiées).
- **Dédup à double clé** : même URL → cache ; même contenu sous une autre URL → même analyse, sans nouvel appel LLM.
- **Retry encadré** : sortie non conforme → l'erreur est renvoyée une fois au modèle, sinon 502 explicite.

## Tests

```bash
.venv/bin/python -m pytest    # 28 tests, LLM simulé, aucun réseau requis
```
