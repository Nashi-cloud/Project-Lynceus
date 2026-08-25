# Projet Lynceus 🔭

> **La vigie de l'information.** Lyncée, vigie des Argonautes, voyait à travers les coques des navires et la terre elle-même. Une vigie prévient l'équipage ; elle ne prend jamais la barre.

Lynceus analyse le contenu d'une page web et explique à son lecteur, **sans le juger**, les techniques de persuasion et de manipulation qu'elle emploie : sources absentes, appel à la peur, rhétorique du secret, faux experts, conflits d'intérêt commerciaux… Le tout résumé par un indice de confiance façon **Nutri-Score de l'information** (A → E), avec le détail pédagogique à portée de clic.

**Projet à but humanitaire, 100 % libre (AGPL-3.0), gratuit, auto-hébergeable.**

## Installer

**[→ Guide d'installation pas à pas](INSTALLATION.md)** : extension seule ou kit complet (serveur + extension), avec ou sans Docker.

## Pourquoi ?

Nous avons toutes et tous dans notre entourage des personnes exposées à la désinformation : pseudo-médecine, théories du complot, manipulation sectaire, articles fabriqués. Les contredire frontalement ne fonctionne pas, et la recherche montre même que cela renforce les croyances (réactance).

Ce qui fonctionne, c'est **l'inoculation** : apprendre à reconnaître les *techniques* de manipulation, indépendamment du sujet. Lynceus n'est pas un ministère de la vérité ; c'est un outil d'éducation aux médias qui montre les procédés, cite les extraits, et laisse le lecteur conclure.

## Comment ça marche ?

```
┌─ Navigateur ────────────────────┐        ┌─ Instance Lynceus (auto-hébergeable) ┐
│ Extension Chrome (MV3)          │        │  API annuaire (FastAPI)              │
│  · badge passif ────────────────┼─GET──▶ │  /lookup (hash URL) ──▶ Annuaire     │
│  · clic droit « Analyser »      │        │                         (PostgreSQL) │
│  · extraction LOCALE            │        │  /v1/analyses                        │
│    Readability.js → Markdown ───┼─POST─▶ │    │ si absent de l'annuaire         │
│  · side panel (carte) ◀─────────┼─JSON── │    ▼                                 │
└───────────┬─────────────────────┘        │  Moteur d'analyse (LLM configurable) │
            │                              │  endpoint compatible OpenAI :        │
            │ « Obtenir une clé »          │  OpenRouter │ Ollama │ vLLM │ etc.   │
            ▼                              └───────────────▲──────────────────────┘
┌─ Portail (site public) ─────────┐                        │
│  récit · méthodologie · procédés│──── annuaire, ─────────┘
│  annuaire · téléchargement      │     contestations
│  /v1/inscription → clé signée   │
│  détient la clé PRIVÉE          │   sans base de données : il ne conserve rien
└─────────────────────────────────┘
```

1. **Badge passif** : à chaque page, l'extension interroge l'annuaire (hash de l'URL, aucun contenu envoyé). Page déjà analysée → la note s'affiche sur l'icône. Désactivable.
2. **Analyse volontaire** : clic droit → « Analyser cette page ». Le texte est extrait *localement* (Readability), converti en Markdown et envoyé à l'API. Le panneau latéral affiche la carte d'analyse.
3. **Annuaire mutualisé** : chaque page n'est analysée qu'une fois pour tout le monde. Le même contenu copié-collé sur un autre site est reconnu (hash de contenu). Domaine par domaine, un profil de fiabilité se construit.
4. **Portail** : le site public. Il présente le projet, publie la méthodologie, laisse consulter l'annuaire sans rien installer, distribue l'extension, et délivre une clé d'accès en un clic, sans compte ni adresse électronique. C'est un service **séparé de l'instance** : lui seul détient la clé privée qui signe les clés, si bien qu'une instance compromise ne permet pas d'en forger.

## La carte d'analyse

Chaque analyse produit une carte JSON ([schéma](schema/carte-analyse.schema.json), [exemple](schema/exemples/pseudo-science.json)) :

- **Catégorie** du contenu : information, opinion, satire, pseudo-science, contenu confessionnel…
- **Note globale A–E** calculée par le serveur à partir de 4 dimensions transparentes : sources, factualité, ton, transparence.
- **Techniques détectées** : chacune avec l'extrait *verbatim* de la page et une explication pédagogique ([taxonomie complète](docs/TAXONOMIE.md)).
- **Points positifs** : toujours recherchés : l'équité est une condition de la crédibilité.
- **Questions à se poser** : socratiques, pour rendre le lecteur acteur.

## Principes non négociables

Résumé de la [charte éthique](docs/ETHIQUE.md) :

1. **Une vigie, pas un juge** : on décrit des méthodes, on ne juge pas des croyances.
2. **Transparence radicale** : prompts, méthodologie, pondérations et code publics et versionnés.
3. **Scan volontaire** : jamais d'analyse à l'insu de l'utilisateur.
4. **Vie privée** : pas d'historique de navigation stocké, pas de compte requis, lookup par hash.
5. **Équité** : satire ≠ désinformation, opinion assumée ≠ manipulation, points positifs systématiques.
6. **Faillibilité assumée** : l'analyse est produite par une IA, l'indice de confiance est affiché, toute analyse est contestable.

## Documentation

| Document | Contenu |
|---|---|
| [docs/ETHIQUE.md](docs/ETHIQUE.md) | La charte : posture, vie privée, équité, limites |
| [docs/METHODOLOGIE.md](docs/METHODOLOGIE.md) | Catégories, dimensions, barème, calcul de la note, cas particuliers |
| [docs/TAXONOMIE.md](docs/TAXONOMIE.md) | Les 31 techniques détectées, documentées et sourcées |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | API, modèle de données, déduplication, couche LLM, fédération |
| [prompts/](prompts/) | Prompts d'analyse versionnés (publics, comme tout le reste) |
| [corpus/](corpus/) | Corpus de calibration des prompts |
| [api/DEPLOIEMENT.md](api/DEPLOIEMENT.md) | Héberger une instance et un portail : secrets, exposition, clés, coûts, montée en charge |

## Stack

- **API / serveur** : Python, FastAPI, PostgreSQL. Le « kit » auto-hébergeable (Docker Compose).
- **Extension** : TypeScript, Manifest V3, side panel Chrome, extraction Readability.js.
- **Portail** : le même paquet Python, second point d'entrée (`lynceus.portail`). Jinja2 et htmx,, aucune ressource chargée depuis un tiers, lisible sans JavaScript.
- **LLM** : tout endpoint compatible OpenAI (`/chat/completions`) : OpenRouter, Ollama en local, vLLM… Modèle et fournisseur configurables par instance.

## Vérifier le projet

```bash
./verifier.sh              # tests API + extension, typage, build, cohérence des versions
./verifier.sh --calibrer   # + calibration du corpus (serveur requis)
```

97 tests au total : 65 côté API (pytest, couverture 84 %) et 32 côté extension (`node --test`), plus un test de parité garantissant que l'extension et le serveur calculent les mêmes empreintes d'URL.

## Feuille de route

- [x] **Phase 0, fondations** : charte, méthodologie, taxonomie, schéma de la carte, prompt v0.1
- [x] **Phase 1, API MVP** : `/lookup` + `/analyses`, SQLite/PostgreSQL, adapter LLM compatible OpenAI, CLI, Docker Compose
- [x] **Phase 2, extension Chrome** : side panel, menu contextuel, badge passif opt-in, extraction locale Readability
- [x] **Phase 3, annuaire public** : lookup k-anonyme (technique HaveIBeenPwned), contestation d'analyses et droit de réponse, profils de domaines
- [x] **Publication** : guide d'installation, empaquetage de l'extension, migrations Alembic
- [x] **Phase 3b, portail public** : site (récit, méthodologie, référentiel, annuaire consultable), distribution de l'extension, inscription en un clic sans compte
- [ ] **Phase 3c** : instance et portail de référence hébergés publiquement
- [ ] **Phase 4, réseau** : fédération d'annuaires entre instances, i18n, portage Firefox

## Contribuer

Le projet vise un réseau mondial et bénévole de vérification. Toute contribution est bienvenue : code, taxonomie, corpus de calibration, traductions, hébergement d'instances. Licence **AGPL-3.0** : toute instance publique modifiée doit publier ses sources, car la transparence de l'analyseur est le cœur de sa légitimité.

---

*English summary: Lynceus is a free-software (AGPL-3.0) media-literacy stack (a Chrome extension plus a self-hostable directory API) that analyzes web pages with a configurable LLM and explains, without preaching, the manipulation techniques they use (missing sources, fear appeals, fake experts…), summarized as an A–E trust index. Every analysis is cached in a shared directory so each page is only ever analyzed once. Documentation is currently in French; translations welcome.*
