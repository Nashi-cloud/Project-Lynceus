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
      ▼  PR validée sur GitHub, puis tag (vX.Y.Z)
     main                     (stable : c'est ce que les instances déploient)
```

- **`main`** : stable uniquement. Ne reçoit que des merges depuis `next`, par une pull request que le mainteneur valide sur GitHub, et chaque release y est taguée.
- **`next`** : pré-production. Reçoit `dev` quand un ensemble cohérent est prêt ; on y stabilise.
- **`dev`** : branche d'intégration. Toutes les branches spécifiques en partent et y reviennent.
- **Branches spécifiques** : `feat/<sujet>`, `fix/<sujet>`, `docs/<sujet>` : courtes, focalisées, mergées dans `dev` via PR.

### La promotion, dans l'ordre

1. **Développer** sur une branche spécifique partie de `dev`.
2. **Fusionner dans `dev`** une fois `./verifier.sh` passé, avec `--no-ff`. La chaîne rejoue les tests et publie `:dev`.
3. **Fusionner `dev` dans `next`** quand le lot tient debout. La chaîne publie `:next` et déploie sur staging : c'est là qu'on éprouve la mise à jour sur une vraie instance, migrations comprises.
4. **Ouvrir une PR `next` → `main`** sur GitHub, que le mainteneur valide lui-même. Le merge déclenche la publication de `:latest` et `:v<VERSION>`, et le déploiement en production.
5. **Poser le tag annoté** `vX.Y.Z` sur le commit de fusion, en accord avec le fichier `VERSION`.

Une étape ne se saute pas : rien n'arrive dans `main` qui ne soit passé par staging.

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

`verifier.sh` refuse aussi un décalage entre la version la plus haute de `prompts/analyse/`, les estampilles de `docs/METHODOLOGIE.md` et `docs/TAXONOMIE.md`, et la version sur laquelle porte `corpus/RESULTATS.md`. Ces quatre-là partagent un seul compteur, `prompt_version`, celui que chaque analyse annonce.

## Ce que déclenche une poussée

Le dépôt est bâti pour une forge dotée d'un runner auto-hébergé (voir [api/DEPLOIEMENT.md](api/DEPLOIEMENT.md)). Les tests y rejouent ce que `verifier.sh` fait en local, dans des conteneurs jetables.

| Branche | Tests | Image publiée | Déploiement |
|---|---|---|---|
| `feat/*`, `fix/*`, `docs/*` | oui | aucune | aucun |
| `dev` | oui | `:dev` | aucun |
| `next` | oui | `:next` | staging |
| `main` | oui | `:latest` et `:v<VERSION>` | production |

La chaîne ne remplace pas `./verifier.sh` avant de fusionner : elle constate, elle ne relit pas. Et elle ne s'exécute pas pour une proposition venue d'un fork, un runner auto-hébergé exécutant le code qu'on lui confie.

**Version de l'API** : le fichier `VERSION` à la racine fait foi, et doit s'accorder avec `api/pyproject.toml` et `api/lynceus/__init__.py`. C'est lui que la chaîne lit pour étiqueter l'image publiée depuis `main`, donc pour rendre un retour arrière possible. `verifier.sh` refuse un décalage.

## Conventions

- **Commits** : style Conventional Commits, en français : `feat: …`, `fix: …`, `docs: …`, `chore: …`, `test: …`.
- **Une branche par sujet**, mergée dans `dev` avec `--no-ff` (l'historique garde la trace du regroupement).
- **Fusions de promotion** : `dev` → `next` et `next` → `main` en `--no-ff` également. Ces deux branches ne divergent jamais, donc un fast-forward passerait, mais on y perdrait le commit `merge: next → main (vX.Y.Z)` qui rend le graphe lisible et donne un point de retour arrière évident. Le fast-forward reste acceptable pour rattraper `next` sur `dev` quand il n'y a rien à marquer.
- **Tests obligatoires** pour toute correction de bug : le test doit échouer avant le correctif. Pour une fonctionnalité, tester au moins la logique métier isolable des API du navigateur.
- **Versions de l'extension** : toute modification de `extension/` incrémente la version dans `manifest.json` **et** `package.json`, avec une entrée dans `extension/CHANGELOG.md` (patch pour un correctif, mineure pour une fonctionnalité). Sans ça, impossible de savoir quel build est chargé dans Chrome.
- **Prompts et méthodologie** : toute modification de `prompts/`, `docs/METHODOLOGIE.md` ou `docs/TAXONOMIE.md` incrémente `prompt_version` (semver) et doit passer la calibration sur `corpus/`. Reporter le résultat dans [corpus/RESULTATS.md](corpus/RESULTATS.md).
- **Corpus** : ne jamais assouplir une attente pour faire passer un test sans avoir examiné le cas, et jamais sur `techniques_attendues` / `techniques_interdites`, qui sont le cœur de la mesure.
- **Ids de taxonomie** : stables et définitifs, jamais renommés (l'annuaire les référence).
- **Charte** : toute PR doit être compatible avec [docs/ETHIQUE.md](docs/ETHIQUE.md) : c'est le critère de revue numéro un.
- **IA générative** : une contribution substantiellement produite par un assistant le déclare, avec les lignes `Assisted-by:` et `Prompt:` en fin de message de commit, contiguës à `Signed-off-by:`. Voir [docs/IA-GENERATIVE.md](docs/IA-GENERATIVE.md). Une contribution que son auteur ne sait pas expliquer en revue est refusée, assistant ou pas.

## Droits sur les contributions

Le projet applique le **Developer Certificate of Origin** ([DCO.txt](DCO.txt)), le même
mécanisme que le noyau Linux et Git. Rien à signer, rien à renvoyer : vous ajoutez une
ligne à chaque commit.

```bash
git commit -s -m "feat: ..."      # -s ajoute la ligne Signed-off-by
```

```
Signed-off-by: Prénom Nom <adresse@exemple.fr>
```

Par cette ligne, vous certifiez avoir le droit d'apporter ce code sous licence AGPL-3.0.
Vous **conservez vos droits d'auteur** sur votre contribution : le projet ne vous demande
aucune cession.

Conséquence assumée : le projet ne pourra jamais être relicencié sans l'accord de chaque
contributeur, et ne pourra donc pas vendre d'exceptions à l'AGPL. C'est le prix d'une
contribution sans paperasse, et le choix a été fait en connaissance de cause. Ajoutez-vous
à [AUTHORS.md](AUTHORS.md) lors de votre première contribution.

## Développement local

Voir [api/README.md](api/README.md) (serveur + CLI) et [extension/README.md](extension/README.md).

## Licence

Le projet est sous **AGPL-3.0** : en contribuant, vous acceptez que votre contribution soit publiée sous cette licence.
