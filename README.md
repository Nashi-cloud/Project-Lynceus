# Projet Lynceus 🔭

> **La vigie de l'information.** Lyncée, vigie des Argonautes, voyait à travers les coques des navires et la terre elle-même. Une vigie prévient l'équipage — elle ne prend jamais la barre.

Lynceus analyse le contenu d'une page web et explique à son lecteur, **sans le juger**, les techniques de persuasion et de manipulation qu'elle emploie : sources absentes, appel à la peur, rhétorique du secret, faux experts, conflits d'intérêt commerciaux… Le tout résumé par un indice de confiance façon **Nutri-Score de l'information** (A → E), avec le détail pédagogique à portée de clic.

**Projet à but humanitaire, 100 % libre (AGPL-3.0), gratuit, auto-hébergeable.**

## Pourquoi ?

Nous avons toutes et tous dans notre entourage des personnes exposées à la désinformation : pseudo-médecine, théories du complot, manipulation sectaire, articles fabriqués. Les contredire frontalement ne fonctionne pas — la recherche montre même que cela renforce les croyances (réactance).

Ce qui fonctionne, c'est **l'inoculation** : apprendre à reconnaître les *techniques* de manipulation, indépendamment du sujet. Lynceus n'est pas un ministère de la vérité ; c'est un outil d'éducation aux médias qui montre les procédés, cite les extraits, et laisse le lecteur conclure.

## Comment ça marche ?

```
┌─ Navigateur ────────────────────┐        ┌─ Serveur Lynceus (auto-hébergeable) ─┐
│ Extension Chrome (MV3)          │        │  API annuaire (FastAPI)              │
│  · badge passif ────────────────┼─GET──▶ │  /lookup (hash URL) ──▶ Annuaire     │
│  · clic droit « Analyser »      │        │                         (PostgreSQL) │
│  · extraction LOCALE            │        │  /analyze                            │
│    Readability.js → Markdown ───┼─POST─▶ │    │ si absent de l'annuaire         │
│  · side panel (carte) ◀─────────┼─JSON── │    ▼                                 │
└─────────────────────────────────┘        │  Moteur d'analyse (LLM configurable) │
              CLI ────────────────┼──────▶ │  endpoint compatible OpenAI :        │
                                           │  OpenRouter │ Ollama │ vLLM │ etc.   │
                                           └──────────────────────────────────────┘
```

1. **Badge passif** — à chaque page, l'extension interroge l'annuaire (hash de l'URL, aucun contenu envoyé). Page déjà analysée → la note s'affiche sur l'icône. Désactivable.
2. **Analyse volontaire** — clic droit → « Analyser cette page ». Le texte est extrait *localement* (Readability), converti en Markdown et envoyé à l'API. Le panneau latéral affiche la carte d'analyse.
3. **Annuaire mutualisé** — chaque page n'est analysée qu'une fois pour tout le monde. Le même contenu copié-collé sur un autre site est reconnu (hash de contenu). Domaine par domaine, un profil de fiabilité se construit.

## La carte d'analyse

Chaque analyse produit une carte JSON ([schéma](schema/carte-analyse.schema.json), [exemple](schema/exemples/pseudo-science.json)) :

- **Catégorie** du contenu : information, opinion, satire, pseudo-science, contenu confessionnel…
- **Note globale A–E** calculée par le serveur à partir de 4 dimensions transparentes : sources, factualité, ton, transparence.
- **Techniques détectées** — chacune avec l'extrait *verbatim* de la page et une explication pédagogique ([taxonomie complète](docs/TAXONOMIE.md)).
- **Points positifs** — toujours recherchés : l'équité est une condition de la crédibilité.
- **Questions à se poser** — socratiques, pour rendre le lecteur acteur.

## Principes non négociables

Résumé de la [charte éthique](docs/ETHIQUE.md) :

1. **Une vigie, pas un juge** — on décrit des méthodes, on ne juge pas des croyances.
2. **Transparence radicale** — prompts, méthodologie, pondérations et code publics et versionnés.
3. **Scan volontaire** — jamais d'analyse à l'insu de l'utilisateur.
4. **Vie privée** — pas d'historique de navigation stocké, pas de compte requis, lookup par hash.
5. **Équité** — satire ≠ désinformation, opinion assumée ≠ manipulation, points positifs systématiques.
6. **Faillibilité assumée** — l'analyse est produite par une IA, l'indice de confiance est affiché, toute analyse est contestable.

## Documentation

| Document | Contenu |
|---|---|
| [docs/ETHIQUE.md](docs/ETHIQUE.md) | La charte : posture, vie privée, équité, limites |
| [docs/METHODOLOGIE.md](docs/METHODOLOGIE.md) | Catégories, dimensions, barème, calcul de la note, cas particuliers |
| [docs/TAXONOMIE.md](docs/TAXONOMIE.md) | Les 31 techniques détectées, documentées et sourcées |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | API, modèle de données, déduplication, couche LLM, fédération |
| [prompts/](prompts/) | Prompts d'analyse versionnés (publics, comme tout le reste) |
| [corpus/](corpus/) | Corpus de calibration des prompts |

## Stack

- **API / serveur** : Python, FastAPI, PostgreSQL — le « kit » auto-hébergeable (Docker Compose).
- **Extension** : TypeScript, Manifest V3, side panel Chrome, extraction Readability.js.
- **LLM** : tout endpoint compatible OpenAI (`/chat/completions`) — OpenRouter, Ollama en local, vLLM… Modèle et fournisseur configurables par instance.

## Feuille de route

- [x] **Phase 0 — Fondations** : charte, méthodologie, taxonomie, schéma de la carte, prompt v0.1
- [x] **Phase 1 — API MVP** : `/lookup` + `/analyses`, SQLite/PostgreSQL, adapter LLM compatible OpenAI, CLI, Docker Compose
- [x] **Phase 2 — Extension Chrome** : side panel, menu contextuel, badge passif opt-in, extraction locale Readability
- [ ] **Phase 3 — Annuaire public** : instance de référence, profils de domaines, contestation d'analyses, lookup k-anonyme
- [ ] **Phase 4 — Réseau** : fédération d'annuaires entre instances, i18n, portage Firefox

## Contribuer

Le projet vise un réseau mondial et bénévole de vérification. Toute contribution est bienvenue : code, taxonomie, corpus de calibration, traductions, hébergement d'instances. Licence **AGPL-3.0** : toute instance publique modifiée doit publier ses sources — la transparence de l'analyseur est le cœur de sa légitimité.

---

*English summary: Lynceus is a free-software (AGPL-3.0) media-literacy stack — a Chrome extension plus a self-hostable directory API — that analyzes web pages with a configurable LLM and explains, without preaching, the manipulation techniques they use (missing sources, fear appeals, fake experts…), summarized as an A–E trust index. Every analysis is cached in a shared directory so each page is only ever analyzed once. Documentation is currently in French; translations welcome.*
