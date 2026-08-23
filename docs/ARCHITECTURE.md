# Architecture technique

## Vue d'ensemble

```
┌─ Navigateur ────────────────────┐        ┌─ Serveur Lynceus (le « kit ») ───────┐
│ Extension Chrome (MV3, TS)      │        │  API annuaire — FastAPI (Python)     │
│  · badge passif ────────────────┼─GET──▶ │  /v1/lookup ───▶ Annuaire            │
│  · clic droit « Analyser »      │        │                  (PostgreSQL)        │
│  · extraction LOCALE            │        │  /v1/analyses                        │
│    Readability.js → Turndown ───┼─POST─▶ │    │ absent de l'annuaire            │
│  · side panel (carte) ◀─────────┼─JSON── │    ▼                                 │
└─────────────────────────────────┘        │  Moteur d'analyse                    │
              CLI (test/scripts) ─┼──────▶ │  · adapter compatible OpenAI         │
                                           │  · validation JSON Schema + retry    │
                                           │  · calcul de la note (serveur)       │
                                           └──────────────────────────────────────┘
```

Trois livrables : **`api/`** (le kit serveur auto-hébergeable, Docker Compose), **`extension/`** (client Chrome), **CLI** (client de test et d'import en masse, inclus dans `api/`).

## Choix structurants

1. **Extraction côté client.** L'extension extrait le texte localement (Readability.js — le moteur du mode lecture Firefox — puis conversion Markdown via Turndown). Avantages : fonctionne derrière paywall/login et sur les pages JS ; pas d'infra de scraping ; un site ne peut pas servir un contenu différent à l'analyseur (cloaking). Un fetch serveur (trafilatura) reste disponible en fallback pour l'usage API pur / CLI.
2. **La note est calculée par le serveur**, pas par le LLM (pondérations publiées dans [METHODOLOGIE.md](METHODOLOGIE.md)) : déterminisme, auditabilité, cohérence entre instances.
3. **Couche LLM = un seul adapter, compatible OpenAI** (`POST {base_url}/chat/completions`). Couvre OpenRouter (dev/prod), Ollama et vLLM (auto-hébergement, gratuit), LiteLLM (passerelle multi-fournisseurs). Le choix du fournisseur/modèle appartient à chaque instance.
4. **Prompts versionnés dans le dépôt** ([prompts/](../prompts/)) — chargés depuis les fichiers, jamais codés en dur.

## API v1 (contrat)

| Méthode | Route | Rôle |
|---|---|---|
| `GET` | `/v1/lookup?url_hash={sha256}` | Consultation annuaire. Réponse : `{ statut: "connue"\|"inconnue", carte?, domaine? }`. Jamais journalisé avec identifiants. |
| `POST` | `/v1/analyses` | Corps : `{ url?, contenu_markdown?, titre?, langue? }`. Cache hit → `200` + carte. Sinon analyse (synchrone au MVP, ~10–30 s) → `200` + carte. `url` seul → fetch serveur fallback. |
| `GET` | `/v1/analyses/{id}` | Récupération d'une carte par id. |
| `GET` | `/v1/domaines/{domaine}` | Profil agrégé : nb d'analyses, score moyen, distribution des grades. |
| `POST` | `/v1/signalements` | Contestation d'une analyse (phase 3). |
| `GET` | `/v1/meta` | Version de l'instance, `prompt_version`, modèle configuré, taxonomie — transparence de l'instance. |

## Déduplication — le cœur de l'annuaire

Deux clés indépendantes :

1. **`url_hash`** = SHA-256 de l'URL *normalisée* :
   - schéma et hôte en minuscules ; suppression de `www.` ? **non** (sous-domaines significatifs), mais suppression du fragment `#…` ;
   - suppression des paramètres de tracking (`utm_*`, `fbclid`, `gclid`, `mc_cid`…), tri alphabétique des paramètres restants ;
   - suppression du slash final ; décodage percent-encoding superflu.
2. **`content_hash`** = SHA-256 du Markdown normalisé (trim, espaces multiples réduits, casse conservée).

Logique de résolution à l'analyse :

```
url_hash connu, content_hash identique      → carte en cache (gratuit, instantané)
url_hash connu, content_hash différent      → contenu modifié : ré-analyse + nouvelle version (historique conservé)
content_hash connu sous une AUTRE url       → article copié/syndiqué : carte réutilisée, URL liée à l'analyse existante
tout inconnu                                → analyse LLM complète
```

Le cas 3 est stratégique : les contenus trompeurs sont massivement dupliqués entre sites — une analyse les couvre tous.

**Invalidation** : une carte est ré-analysable si `content_hash` change ou si `prompt_version` majeure/mineure augmente. Les anciennes cartes sont conservées (historique public d'un site qui s'améliore ou se dégrade).

## Modèle de données (PostgreSQL)

```
pages        id PK · url · url_normalisee · url_hash UNIQUE · domaine (index)
             analyse_courante_id FK · premiere_vue · derniere_vue

analyses     id PK · content_hash (index) · prompt_version · schema_version
             carte JSONB · categorie · score · grade · confiance
             modele · fournisseur · duree_ms · cree_le
             UNIQUE (content_hash, prompt_version)

domaines     domaine PK · nb_analyses · score_moyen · distribution_grades JSONB
             maj_le            -- recalculé à chaque nouvelle analyse du domaine

signalements id PK · analyse_id FK · motif · message · statut · cree_le   (phase 3)
```

Plusieurs `pages` peuvent pointer la même `analyses` (contenu dupliqué). `pgvector` envisagé en phase 3+ pour détecter les quasi-doublons (même article paraphrasé).

## Cycle de vie d'une analyse

```
POST /v1/analyses
  1. Normalisation URL → url_hash ; normalisation Markdown → content_hash
  2. Résolution annuaire (cf. ci-dessus) — hit → retour immédiat
  3. Garde-fous : taille min/max du contenu, rate limiting, langue
  4. Appel LLM : system = prompts/analyse/vX.Y.Z.md + taxonomie ; user = titre + URL + Markdown
     · response_format json_schema si le fournisseur le supporte, sinon consigne JSON + validation
  5. Validation : JSON Schema (carte) + ids de techniques ∈ taxonomie + extraits présents dans le contenu source
     · échec → 1 retry avec l'erreur en contexte → sinon 502 explicite
  6. Calcul serveur : score pondéré → grade ; assemblage meta (modele, prompt_version, date)
  7. Écriture pages/analyses + recalcul domaine → 200 carte
```

L'étape 5 inclut la **vérification anti-hallucination des extraits** : tout `extrait` d'une technique doit être une sous-chaîne du Markdown source (à la normalisation d'espaces près), sinon la détection est rejetée.

## Configuration (variables d'environnement)

| Variable | Défaut | Rôle |
|---|---|---|
| `LYNCEUS_DATABASE_URL` | — | PostgreSQL |
| `LYNCEUS_LLM_BASE_URL` | `https://openrouter.ai/api/v1` | Tout endpoint compatible OpenAI (Ollama : `http://localhost:11434/v1`) |
| `LYNCEUS_LLM_API_KEY` | — | Clé du fournisseur |
| `LYNCEUS_LLM_MODEL` | `anthropic/claude-sonnet-5` *(slug OpenRouter — à vérifier sur openrouter.ai/models)* | Modèle d'analyse |
| `LYNCEUS_LLM_TEMPERATURE` | `0.2` | Faible : on veut de la constance |
| `LYNCEUS_CONTENU_MAX_CARS` | `60000` | Garde-fou taille (≈ tokens × 4) |
| `LYNCEUS_RATE_LIMIT` | `10/minute` | Par IP, sur `/v1/analyses` |

## Sécurité, abus, vie privée

- **Rate limiting** sur `/v1/analyses` (le lookup est bon marché, l'analyse non). Clés API optionnelles pour instances publiques.
- **Pas de journalisation IP + URL** sur `/v1/lookup` (voir [ETHIQUE.md](ETHIQUE.md) §4) ; phase 3 : lookup k-anonyme par préfixe de hash (modèle HaveIBeenPwned).
- Contenu soumis = donnée non fiable : jamais interprété comme instruction (le prompt le délimite explicitement), taille bornée, HTML refusé (Markdown uniquement).
- CORS restreint à l'extension + configurable par instance.

## Fédération (phase 4 — esquisse)

- Chaque instance expose `/v1/meta` + un flux d'export signé de ses cartes (JSONL, clé d'instance).
- Synchronisation **pull** entre instances de confiance (liste de pairs configurée) ; les cartes importées gardent leur provenance (`instance_origine`) et restent re-vérifiables localement.
- Pas de consensus global : un réseau de confiance à la petits-pas (modèle relais Mastodon plutôt que blockchain — simple, auditable, révocable).

## Arborescence cible du dépôt

```
Project-Lynceus/
├── api/          # FastAPI + moteur d'analyse + CLI + Docker Compose (phase 1)
├── extension/    # Extension Chrome MV3, TypeScript (phase 2)
├── schema/       # JSON Schema de la carte + exemples (source de vérité partagée)
├── prompts/      # Prompts d'analyse versionnés
├── corpus/       # Corpus de calibration
└── docs/         # ETHIQUE, METHODOLOGIE, TAXONOMIE, ARCHITECTURE
```
