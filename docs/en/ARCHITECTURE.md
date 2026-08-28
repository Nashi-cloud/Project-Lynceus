# Technical architecture

<!-- traduit-de: docs/ARCHITECTURE.md sha256:99d63073efd2323e -->

> Translation for information. The French version, `docs/ARCHITECTURE.md`, is the one the project follows: should the two ever diverge, it is the one that counts.

## Overview

```
┌─ Browser ───────────────────────┐        ┌─ Lynceus server (the “kit”) ─────────┐
│ Chrome extension (MV3, TS)      │        │  Directory API: FastAPI (Python)     │
│  · passive badge ───────────────┼─GET──▶ │  /v1/lookup ───▶ Directory           │
│  · right click, “Analyse”       │        │                  (PostgreSQL)        │
│  · LOCAL extraction             │        │  /v1/analyses                        │
│    Readability.js → Turndown ───┼─POST─▶ │    │ not in the directory            │
│  · side panel (card) ◀──────────┼─JSON── │    ▼                                 │
└─────────────────────────────────┘        │  Analysis engine                     │
              CLI (test/scripts) ─┼──────▶ │  · OpenAI-compatible adapter         │
                                           │  · JSON Schema validation and retry  │
                                           │  · grade computed by the server      │
                                           └──────────────────────────────────────┘
```

Three deliverables: **`api/`** (the self-hostable server kit, Docker Compose), **`extension/`** (Chrome client), **CLI** (a client for testing and bulk import, shipped inside `api/`).

## Structural choices

1. **Extraction on the client side.** The extension extracts the text locally (Readability.js, the engine behind Firefox's reader mode, then conversion to Markdown with Turndown). The benefits: it works behind a paywall or a login and on JavaScript-heavy pages; there is no scraping infrastructure to run; and a site cannot serve different content to the analyser than to the reader (cloaking). A server-side fetch (trafilatura) remains available as a fallback for pure API and CLI use.
2. **The grade is computed by the server**, not by the LLM (weightings published in [METHODOLOGIE.md](METHODOLOGIE.md)): determinism, auditability, consistency between instances.
3. **The LLM layer is a single OpenAI-compatible adapter** (`POST {base_url}/chat/completions`). It covers OpenRouter (development and production), Ollama and vLLM (self-hosting, free of charge), and LiteLLM (a multi-provider gateway). The choice of provider and model belongs to each instance.
4. **Prompts versioned in the repository** ([prompts/](../../prompts/)): loaded from the files, never hard-coded.

## API v1 (the contract)

| Method | Route | Role |
|---|---|---|
| `GET` | `/v1/lookup?url_hash={sha256}` | Directory lookup. Response: `{ statut: "connue"\|"inconnue", carte?, domaine? }`. Never logged with identifiers. |
| `POST` | `/v1/analyses` | Body: `{ url?, contenu_markdown?, titre?, langue? }`. Cache hit gives `200` and the card. Otherwise an analysis is run (synchronous in the MVP, roughly 10 to 30 s) and returns `200` and the card. A bare `url` falls back to a server-side fetch. |
| `GET` | `/v1/analyses/{id}` | Fetch a card by id. |
| `GET` | `/v1/domaines/{domaine}` | Aggregated profile: number of analyses, mean score, distribution of grades. |
| `GET` | `/v1/lookup-prefixe?prefixe={5 hex}` | **K-anonymous lookup**: the client sends only the first 5 characters of the hash and does the final match locally. Response: suffixes plus summaries (grade, category, score, id). The server cannot tell which page is being read. |
| `POST` | `/v1/signalements` | Disputing an analysis: `{ analyse_id, motif, message, contact? }`. Anonymous by default. |
| `GET` | `/v1/motifs-signalement` | The accepted grounds, so clients do not have to hard-code them. |
| `GET` | `/v1/admin/signalements` | **Operator** (`X-Lynceus-Admin` header): disputes received, filterable by status. |
| `POST` | `/v1/admin/signalements/{id}` | **Operator**: records the decision (`statut` plus a justified `decision`, both required). |
| `GET` | `/v1/meta` | Instance version, `prompt_version`, configured model, taxonomy: the transparency of the instance. |

## Deduplication: the heart of the directory

Two independent keys:

1. **`url_hash`** is the SHA-256 of the *normalised* URL:
   - scheme and host lowercased; strip `www.`? **No** (subdomains carry meaning), but the `#…` fragment is stripped;
   - tracking parameters removed (`utm_*`, `fbclid`, `gclid`, `mc_cid` and so on), remaining parameters sorted alphabetically;
   - trailing slash removed; superfluous percent-encoding decoded.
2. **`content_hash`** is the SHA-256 of the normalised Markdown (trimmed, runs of whitespace collapsed, case preserved).

How resolution works at analysis time:

```
url_hash known, content_hash identical      → cached card (free, instant)
url_hash known, content_hash different      → content changed: re-analysis and a new version (history kept)
content_hash known under ANOTHER url        → copied or syndicated article: the card is reused, the URL linked to the existing analysis
nothing known                               → full LLM analysis
```

The third case is the strategic one: misleading content is duplicated across sites on a large scale, and a single analysis covers all of its copies.

**Invalidation**: a card can be re-analysed if its `content_hash` changes or if the major or minor `prompt_version` increases. Old cards are kept (the public history of a site that improves, or degrades).

## Data model (PostgreSQL)

```
pages        id PK · url · url_normalisee · url_hash UNIQUE · domaine (index)
             analyse_courante_id FK · premiere_vue · derniere_vue

analyses     id PK · content_hash (index) · prompt_version · schema_version
             carte JSONB · categorie · score · grade · confiance
             modele · fournisseur · duree_ms · cree_le
             UNIQUE (content_hash, prompt_version)

domaines     domaine PK · nb_analyses · score_moyen · distribution_grades JSONB
             maj_le            -- recomputed on every new analysis of the domain

signalements id PK · analyse_id FK (index) · motif · message · contact (optional)
             statut (index) · decision · traite_le · cree_le
```

Several `pages` rows can point at the same `analyses` row (duplicated content). `pgvector` is being considered for phase 3 and beyond, to detect near-duplicates (the same article paraphrased).

## Schema evolution

Migrations are managed by **Alembic** and applied **at startup**: a self-hosted instance updates itself without a manual command. Three situations are covered and tested:

| Situation | Behaviour |
|---|---|
| Fresh database | every migration is applied from the beginning |
| Instance predating Alembic (tables created by `create_all`) | the database is stamped at the initial revision without replaying it, otherwise Alembic would try to recreate existing tables; the later migrations then apply |
| Instance already tracked | only the pending migrations are applied |

After any change to `modeles.py`:

```bash
cd api && .venv/bin/alembic revision --autogenerate -m "description"
```

**Always read the generated file.** Autogeneration does not guess renames (it turns them into a drop plus a create, which means data loss) nor content migrations, and it sometimes produces incorrect code: the initial migration was missing an import. A test (`test_schema_conforme_aux_modeles`) checks that the resulting schema matches the models, which catches a forgotten migration.

`render_as_batch` is enabled: SQLite cannot alter a column in place, so Alembic recreates the table cleanly. It has no effect on PostgreSQL.

## The life of an analysis

```
POST /v1/analyses
  1. Normalise the URL → url_hash; normalise the Markdown → content_hash
  2. Resolve against the directory (see above): if found, return immediately
  3. Guardrails: minimum and maximum content size, rate limiting, language
  4. Call the LLM: system = prompts/analyse/vX.Y.Z.md plus the taxonomy; user = title, URL, Markdown
     · response_format json_schema when the provider supports it, otherwise a JSON instruction plus validation
  5. Validation: JSON Schema (the card), technique ids ∈ taxonomy, quoted passages present in the source content
     · on failure → one retry with the error in context → otherwise an explicit 502
  6. Server-side computation: weighted score → grade; meta assembled (model, prompt_version, date)
  7. Write pages and analyses, recompute the domain → 200 with the card
```

Step 5 includes the **anti-hallucination check on quoted passages**: every `extrait` of a technique must be a substring of the source Markdown (up to whitespace normalisation), otherwise the detection is rejected.

## Configuration (environment variables)

| Variable | Default | Role |
|---|---|---|
| `LYNCEUS_DATABASE_URL` | none | PostgreSQL |
| `LYNCEUS_LLM_BASE_URL` | `https://openrouter.ai/api/v1` | Any OpenAI-compatible endpoint (Ollama: `http://localhost:11434/v1`) |
| `LYNCEUS_LLM_API_KEY` | none | The provider's key |
| `LYNCEUS_LLM_MODEL` | `anthropic/claude-sonnet-5` | The analysis model, in the format the provider expects |
| `LYNCEUS_LLM_FOURNISSEUR` | *(inferred from the address)* | The provider name as published: `/v1/meta`, every analysis, the portal's legal pages |
| `LYNCEUS_LLM_TEMPERATURE` | `0` | Zero by default: the grade has to be reproducible. Measured, see [corpus/RESULTATS.md](../../corpus/en/RESULTATS.md) |
| `LYNCEUS_LLM_CACHE_PROMPT` | `false` | Marks the system prompt as reusable. Pointless with a provider that caches on its own, needed with those requiring an explicit breakpoint |
| `LYNCEUS_LLM_RAISONNEMENT` | *(provider default)* | `off`, `low`, `medium`, `high`. Reasoning is billed as output and then discarded: it is the biggest cost item |
| `LYNCEUS_CONTENU_MAX_CARS` | `60000` | Size guardrail (roughly tokens × 4) |
| `LYNCEUS_RATE_LIMIT` | `10/minute` | Per IP, on `/v1/analyses` |

## Security, abuse, privacy

- **Rate limiting** on `/v1/analyses` (a lookup is cheap, an analysis is not). Optional API keys for public instances.
- **No IP plus URL logging** on `/v1/lookup` (see [ETHIQUE.md](ETHIQUE.md) §4).
- **K-anonymous lookup** (`/v1/lookup-prefixe`, the HaveIBeenPwned model): the client sends 5 hexadecimal characters of the hash, which is 1,048,576 buckets, and compares the returned suffixes locally. The server never sees the full digest, so it cannot reconstruct the URL being read. The extension prefers it automatically when the instance announces it in `/v1/meta`, and falls back to `/v1/lookup` otherwise.
- **The badge costs nothing in privacy**: the prefix is enough to display the grade and the page border. The full card is only requested (`/v1/analyses/{id}`) if the panel is actually open.
- Submitted content is untrusted data: never interpreted as an instruction (the prompt delimits it explicitly), bounded in size, HTML refused (Markdown only).
- CORS restricted to the extension, and configurable per instance.

## Federation (phase 4, sketch)

- Each instance exposes `/v1/meta` plus a signed export feed of its cards (JSONL, instance key).
- **Pull** synchronisation between trusted instances (a configured list of peers); imported cards keep their provenance (`instance_origine`) and remain re-verifiable locally.
- No global consensus: a web of trust built one small step at a time (the Mastodon relay model rather than a blockchain: simple, auditable, revocable).

## Target repository layout

```
Project-Lynceus/
├── api/          # FastAPI, analysis engine, CLI, Docker Compose (phase 1)
├── extension/    # Chrome MV3 extension, TypeScript (phase 2)
├── schema/       # JSON Schema of the card plus examples (the shared source of truth)
├── prompts/      # Versioned analysis prompts
├── corpus/       # Calibration corpus
└── docs/         # ETHIQUE, METHODOLOGIE, TAXONOMIE, ARCHITECTURE
```
