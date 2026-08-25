# Contribuer à Lynceus

Merci de vouloir aider ! Toute contribution compte : code, taxonomie, corpus de calibration, traductions, hébergement d'instances.

## Modèle de branches

```
feat/*  fix/*  docs/*        (branches spécifiques, depuis dev)
      │
      ▼  PR + revue
     dev                      (intégration continue du développement)
      │
      ▼  lot jugé stable
     next                     (pré-production : stabilisation, tests d'instance)
      │
      ▼  release taguée (vX.Y.Z)
     main                     (stable : c'est ce que les instances déploient)
```

- **`main`** : stable uniquement. Ne reçoit que des merges depuis `next`, chaque release est taguée.
- **`next`** : pré-production. Reçoit `dev` quand un ensemble cohérent est prêt ; on y stabilise.
- **`dev`** : branche d'intégration. Toutes les branches spécifiques en partent et y reviennent.
- **Branches spécifiques** : `feat/<sujet>`, `fix/<sujet>`, `docs/<sujet>` : courtes, focalisées, mergées dans `dev` via PR.

## Routine de vérification

**Avant tout merge dans `dev`** :

```bash
./verifier.sh              # tests API + extension, typage, build, cohérence des versions
./verifier.sh --calibrer   # + passe de calibration (serveur requis, consomme des tokens)
```

Le script échoue si un test tombe, si le typage strict n'est pas respecté, ou si les versions de l'extension divergent entre `manifest.json`, `package.json` et `CHANGELOG.md`.

Détail des étapes, si besoin de les lancer séparément :

| Étape | Commande | Quand |
|---|---|---|
| Tests API | `cd api && .venv/bin/python -m pytest` | toute modification de `api/` |
| Typage extension | `cd extension && npm run verifier` | toute modification de `extension/` |
| Tests extension | `cd extension && npm test` | toute modification de `extension/` |
| Build extension | `cd extension && npm run build` | avant de recharger dans Chrome |
| Calibration | `lynceus calibrer corpus/corpus.yaml` | **obligatoire** si `prompts/`, `docs/METHODOLOGIE.md`, `docs/TAXONOMIE.md` ou le modèle changent |

## Conventions

- **Commits** : style Conventional Commits, en français : `feat: …`, `fix: …`, `docs: …`, `chore: …`, `test: …`.
- **Une branche par sujet**, mergée dans `dev` avec `--no-ff` (l'historique garde la trace du regroupement).
- **Tests obligatoires** pour toute correction de bug : le test doit échouer avant le correctif. Pour une fonctionnalité, tester au moins la logique métier isolable des API du navigateur.
- **Versions de l'extension** : toute modification de `extension/` incrémente la version dans `manifest.json` **et** `package.json`, avec une entrée dans `extension/CHANGELOG.md` (patch pour un correctif, mineure pour une fonctionnalité). Sans ça, impossible de savoir quel build est chargé dans Chrome.
- **Prompts et méthodologie** : toute modification de `prompts/`, `docs/METHODOLOGIE.md` ou `docs/TAXONOMIE.md` incrémente `prompt_version` (semver) et doit passer la calibration sur `corpus/`. Reporter le résultat dans [corpus/RESULTATS.md](corpus/RESULTATS.md).
- **Corpus** : ne jamais assouplir une attente pour faire passer un test sans avoir examiné le cas, et jamais sur `techniques_attendues` / `techniques_interdites`, qui sont le cœur de la mesure.
- **Ids de taxonomie** : stables et définitifs, jamais renommés (l'annuaire les référence).
- **Charte** : toute PR doit être compatible avec [docs/ETHIQUE.md](docs/ETHIQUE.md) : c'est le critère de revue numéro un.

## Développement local

Voir [api/README.md](api/README.md) (serveur + CLI) et [extension/README.md](extension/README.md).

## Licence

Le projet est sous **AGPL-3.0** : en contribuant, vous acceptez que votre contribution soit publiée sous cette licence.
