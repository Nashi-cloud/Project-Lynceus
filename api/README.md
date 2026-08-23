# Lynceus API — le « kit » serveur (phase 1)

Serveur annuaire + moteur d'analyse. Python 3.12+, FastAPI, PostgreSQL. Auto-hébergeable via Docker Compose.

## Structure prévue

```
api/
├── pyproject.toml
├── docker-compose.yml          # api + postgres
├── lynceus/
│   ├── main.py                 # app FastAPI, routes /v1/*
│   ├── config.py               # variables LYNCEUS_* (cf. docs/ARCHITECTURE.md)
│   ├── normalisation.py        # URL → url_hash · Markdown → content_hash
│   ├── annuaire.py             # résolution cache / dédup / agrégats domaine
│   ├── moteur/
│   │   ├── llm.py              # adapter compatible OpenAI (OpenRouter, Ollama…)
│   │   ├── prompt.py           # chargement prompts/ + injection taxonomie/schéma
│   │   ├── validation.py       # JSON Schema + ids taxonomie + extraits verbatim
│   │   └── notation.py         # score pondéré → grade (calcul serveur)
│   ├── modeles.py              # SQLAlchemy : pages, analyses, domaines, signalements
│   └── cli.py                  # `lynceus analyser <url|fichier.md>`, `lynceus calibrer`
└── tests/
```

## Configuration

Copier `.env.example` → `.env`. Fournisseur LLM par défaut : OpenRouter (`LYNCEUS_LLM_BASE_URL=https://openrouter.ai/api/v1`), modèle `anthropic/claude-sonnet-5` ou `anthropic/claude-haiku-4.5` pour les tests (slugs à vérifier sur openrouter.ai/models). Fonctionne aussi avec Ollama local : `LYNCEUS_LLM_BASE_URL=http://localhost:11434/v1`.

Contrat d'API et modèle de données : [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).
