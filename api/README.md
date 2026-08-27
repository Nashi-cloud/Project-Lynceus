# Lynceus API, the server "kit"

**English** · [Français](README.fr.md)

Directory server plus analysis engine. Python 3.11+, FastAPI, SQLite (zero configuration) or PostgreSQL. API contract and data model: [docs/en/ARCHITECTURE.md](../docs/en/ARCHITECTURE.md).

## Quick start

```bash
cd api
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
cp .env.example .env          # put your key in it (OpenRouter, or a local Ollama…)
.venv/bin/uvicorn lynceus.main:creer_application --factory --reload
```

Then, in another terminal:

```bash
.venv/bin/lynceus analyser https://example.org/an-article   # analyse through the API
.venv/bin/lynceus lookup   https://example.org/an-article   # directory lookup
.venv/bin/lynceus meta                                      # what the instance discloses
.venv/bin/lynceus calibrer ../corpus/corpus.yaml            # a calibration pass
```

## With Docker (API plus PostgreSQL)

```bash
cd api
LYNCEUS_LLM_API_KEY=sk-or-... docker compose up --build
```

## Configuration

`LYNCEUS_*` variables (a `.env` file is accepted). The full list is in [docs/en/ARCHITECTURE.md](../docs/en/ARCHITECTURE.md). The essentials:

| Variable | Default | Role |
|---|---|---|
| `LYNCEUS_LLM_BASE_URL` | `https://openrouter.ai/api/v1` | Any OpenAI-compatible endpoint. Ollama: `http://localhost:11434/v1` |
| `LYNCEUS_LLM_API_KEY` | — | The provider's key |
| `LYNCEUS_LLM_MODEL` | `anthropic/claude-sonnet-5` | The model slug at that provider |
| `LYNCEUS_LLM_FOURNISSEUR` | *(inferred)* | The provider name as published. Empty means the hostname, or "self-hosted model" on a private address |
| `LYNCEUS_DATABASE_URL` | `sqlite:///./lynceus.sqlite3` | PostgreSQL recommended in production |

## Layout

```
lynceus/
├── main.py                 # FastAPI app (factory): /v1/lookup, /v1/analyses, /v1/domaines, /v1/meta
├── config.py               # LYNCEUS_* variables and where the repository data lives
├── normalisation.py        # URL → url_hash · Markdown → content_hash (the directory's two keys)
├── modeles.py              # SQLAlchemy: analyses, pages, domains
├── annuaire.py             # cache and dedup resolution, domain profiles
├── extraction.py           # server-side fetch fallback (trafilatura) for the "URL only" flow
├── moteur/
│   ├── prompt.py           # versioned prompts, taxonomy and schemas (all read from the public files)
│   ├── llm.py              # OpenAI-compatible adapter (OpenRouter, Ollama, vLLM…)
│   ├── validation.py       # JSON Schema, reference ids, VERBATIM passages (anti-hallucination)
│   └── notation.py         # weighted score → grade, computed by the server, not by the LLM
└── cli.py                  # lynceus analyser / lookup / calibrer / meta
```

Guarantees of the pipeline (all tested):

- **Anti-hallucination**: every quoted passage must be a real substring of the content (up to whitespace), otherwise the detection is dropped and listed in `detections_rejetees`.
- **Server-side grade**: the LLM supplies the dimensions, the server computes score and grade (weightings published).
- **Two-key deduplication**: same URL means cache; same content under another URL means the same analysis, with no new LLM call.
- **Bounded retry**: a non-conforming output sends the error back to the model once, otherwise an explicit 502.

## Protecting the instance with access keys

By default an instance is **open**: no key is required. That is the right setting for personal use. For an instance exposed to other people, keys limit who can trigger analyses, which cost money, unlike directory lookups, which always stay free.

**Self-validating keys.** A key carries its own expiry date, its daily quota and an Ed25519 signature. The API verifies the signature with the issuer's public key: **no key directory, no account database**.

```bash
# 1. Once: generate the pair
lynceus cles-paire

# 2. On the instance: put the PUBLIC one in .env, then restart
LYNCEUS_CLE_PUBLIQUE=…

# 3. At the issuer (never on the instance): issue keys
LYNCEUS_CLE_PRIVEE=… lynceus cle-emettre --jours 365 --quota 50 --nombre 10
```

The key is pasted into the extension settings. It **is not an account**: no name, no address, no identifier of its holder, only an expiry date and a quota.

| What it solves | What it does not solve |
|---|---|
| Authenticating with no directory and no sign-up | A shared key stays valid; the quota limits the damage |
| Automatic expiry, no maintenance | Revocation needs a list, but it only ever contains abusive keys (`LYNCEUS_CLES_REVOQUEES`) |
| Separating issuer from validator: compromising the instance does not let anyone forge keys | |

> **The private key must never leave the issuer.** Putting it in the extension would amount to publishing it: anyone could then issue keys at will.

The quota is only charged for a **real analysis**: serving a page already present in the directory costs nothing and does not eat into the quota. Penalising sharing would work against the interest of the network.

## Moderating disputes

Disputes (charter §6) are recorded and their **number is publicly visible** on each analysis, but their content is reserved to the operator of the instance, since a report may contain a contact.

To enable moderation, set `LYNCEUS_ADMIN_TOKEN` on the server **and** in the CLI's environment.

```bash
export LYNCEUS_ADMIN_TOKEN=…                          # the same one as on the server
.venv/bin/lynceus signalements                        # the disputes received
.venv/bin/lynceus signalements --statut nouveau       # the pending ones
.venv/bin/lynceus traiter 3 --statut examine --decision "Catégorie corrigée, analyse relancée."
.venv/bin/lynceus verifier-page 4 --url https://…     # ground "page changed": automatic check
```

`verifier-page` is the only ground that can be automated: it downloads the page again, compares its content with the analysed one, re-runs the analysis if it changed, and files the report accordingly. The other grounds call for human judgement.

Statuses: `nouveau` → `examine` (well founded, action taken) · `rejete` (unfounded) · `sans_objet` (page changed, analysis replaced). **A justification is mandatory** and is kept: dismissing a dispute with no reason would be exactly the opacity Lynceus denounces.

> With no operator to handle them, disputes stay stored and readable. That is what the message shown to the user says, no more and no less.

## Tests

```bash
.venv/bin/python -m pytest    # 244 tests, the LLM is simulated, no network needed
```
