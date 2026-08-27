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
| `LYNCEUS_LLM_MODEL` | `anthropic/claude-sonnet-5` | Slug du modèle chez le fournisseur |
| `LYNCEUS_LLM_FOURNISSEUR` | *(déduit)* | Nom publié du fournisseur. Vide = nom d'hôte, ou « modèle auto-hébergé » sur une adresse privée |
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

## Protéger l'instance par clés d'accès

Par défaut, une instance est **ouverte** : aucune clé n'est exigée. C'est le bon réglage pour un usage personnel. Pour une instance exposée à d'autres, les clés limitent qui peut déclencher des analyses — elles coûtent de l'argent, contrairement aux consultations d'annuaire, qui restent toujours libres.

**Des clés auto-validantes.** Une clé porte elle-même sa date d'expiration, son quota journalier et une signature Ed25519. L'API vérifie la signature avec la clé publique de l'émetteur : **aucun annuaire de clés, aucune base de comptes**.

```bash
# 1. Une fois : générer la paire
lynceus cles-paire

# 2. Sur l'instance : renseigner la PUBLIQUE dans .env, puis redémarrer
LYNCEUS_CLE_PUBLIQUE=…

# 3. Chez l'émetteur (jamais sur l'instance) : émettre des clés
LYNCEUS_CLE_PRIVEE=… lynceus cle-emettre --jours 365 --quota 50 --nombre 10
```

La clé se colle dans les réglages de l'extension. Elle **n'est pas un compte** : ni nom, ni adresse, ni identifiant de son porteur — seulement une date limite et un quota.

| Ce que ça résout | Ce que ça ne résout pas |
|---|---|
| Authentifier sans annuaire ni inscription | Une clé partagée reste valide — le quota limite les dégâts |
| Expiration automatique, sans maintenance | La révocation exige une liste, mais elle ne contient que les clés abusives (`LYNCEUS_CLES_REVOQUEES`) |
| Séparer émetteur et valideur : compromettre l'instance ne permet pas de forger des clés | |

> **La clé privée ne doit jamais quitter l'émetteur.** La placer dans l'extension reviendrait à la publier : n'importe qui pourrait alors émettre des clés à volonté.

Le quota n'est décompté que pour une **analyse réelle** : resservir une page déjà présente dans l'annuaire ne coûte rien et n'entame pas le quota — pénaliser la mutualisation irait contre l'intérêt du réseau.

## Modérer les contestations

Les contestations (charte §6) sont enregistrées et **visibles publiquement en nombre** sur chaque analyse, mais leur contenu est réservé à l'opérateur de l'instance — un signalement peut contenir un contact.

Activer la modération : définir `LYNCEUS_ADMIN_TOKEN` côté serveur **et** dans l'environnement du CLI.

```bash
export LYNCEUS_ADMIN_TOKEN=…                          # le même que côté serveur
.venv/bin/lynceus signalements                        # les contestations reçues
.venv/bin/lynceus signalements --statut nouveau       # celles en attente
.venv/bin/lynceus traiter 3 --statut examine --decision "Catégorie corrigée, analyse relancée."
.venv/bin/lynceus verifier-page 4 --url https://…     # motif « page modifiée » : vérification automatique
```

`verifier-page` est le seul traitement automatisable : il re-télécharge la page, compare son contenu à celui analysé, relance l'analyse si elle a changé, et classe le signalement en conséquence. Les autres motifs relèvent du jugement humain.

Statuts : `nouveau` → `examine` (fondé, action prise) · `rejete` (infondé) · `sans_objet` (page modifiée, analyse remplacée). **La justification est obligatoire** et conservée : écarter une contestation sans motif reviendrait à l'opacité que Lynceus dénonce.

> Sans opérateur pour les traiter, les contestations restent stockées et consultables — c'est ce que le message rendu à l'utilisateur annonce, ni plus ni moins.

## Tests

```bash
.venv/bin/python -m pytest    # 28 tests, LLM simulé, aucun réseau requis
```
