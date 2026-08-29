# Contribuer à Lynceus

<!-- traduit-de: CONTRIBUTING.md sha256:6360358fa1690fa0 -->

[English](CONTRIBUTING.md) · **Français**

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
| Calibration | `lynceus calibrer corpus/corpus.yaml --ecrire` | **obligatoire** si `prompts/`, `docs/METHODOLOGIE.md`, `docs/TAXONOMIE.md` ou le modèle changent |

`verifier.sh` refuse aussi un décalage entre la version la plus haute de `prompts/analyse/`, les estampilles de `docs/METHODOLOGIE.md` et `docs/TAXONOMIE.md`, et la version sur laquelle porte `corpus/RESULTATS.md`. Ces quatre-là partagent un seul compteur, `prompt_version`, celui que chaque analyse annonce.

## Ce que déclenche une poussée

Les tests tournent sur des machines fournies par GitHub, gratuites et sans plafond sur un dépôt public. Ils rejouent ce que `verifier.sh` fait en local.

| Branche | Tests | Image publiée sur GHCR |
|---|---|---|
| `feat/*`, `fix/*`, `docs/*` | oui | aucune |
| `dev` | oui | `:dev` |
| `next` | oui | `:next` |
| `main` | oui | `:latest` et `:v<VERSION>` |

**Une proposition venue d'un fork est vérifiée comme les autres.** Ça n'a pas toujours été le cas : les tests tournaient sur un runner auto-hébergé, qui exécute le code qu'on lui donne, et les forks en étaient exclus. La proposition d'un inconnu ne déclenchait alors rien, son auteur n'avait aucun retour et le mainteneur relisait à l'aveugle. Une machine jetable règle le problème.

La chaîne ne remplace pas `./verifier.sh` avant de fusionner : elle constate, elle ne relit pas.

**Le déploiement ne figure plus dans la chaîne.** Il se faisait par webhook, depuis le runner auto-hébergé, seul capable de joindre le réseau privé de l'exploitant. Une URL de webhook étant un jeton de déploiement déguisé, le sens est inversé : les instances vont chercher l'image sur GHCR, et plus rien n'entre chez elles. Voir [api/DEPLOIEMENT.fr.md](api/DEPLOIEMENT.fr.md).

**Version de l'API** : le fichier `VERSION` à la racine fait foi, et doit s'accorder avec `api/pyproject.toml` et `api/lynceus/__init__.py`. C'est lui que la chaîne lit pour étiqueter l'image publiée depuis `main`, donc pour rendre un retour arrière possible. `verifier.sh` refuse un décalage.

## Conventions

- **Commits** : style Conventional Commits, en français : `feat: …`, `fix: …`, `docs: …`, `chore: …`, `test: …`.
- **Une branche par sujet**, mergée dans `dev` avec `--no-ff` (l'historique garde la trace du regroupement).
- **Fusions de promotion** : `dev` → `next` et `next` → `main` en `--no-ff` également. Ces deux branches ne divergent jamais, donc un fast-forward passerait, mais on y perdrait le commit `merge: next → main (vX.Y.Z)` qui rend le graphe lisible et donne un point de retour arrière évident. Le fast-forward reste acceptable pour rattraper `next` sur `dev` quand il n'y a rien à marquer.
- **Tests obligatoires** pour toute correction de bug : le test doit échouer avant le correctif. Pour une fonctionnalité, tester au moins la logique métier isolable des API du navigateur.
- **Versions de l'extension** : toute modification de `extension/` incrémente la version dans `manifest.json` **et** `package.json`, avec une entrée dans `extension/CHANGELOG.md` (patch pour un correctif, mineure pour une fonctionnalité). Sans ça, impossible de savoir quel build est chargé dans Chrome.
- **Prompts et méthodologie** : toute modification de `prompts/`, `docs/METHODOLOGIE.md` ou `docs/TAXONOMIE.md` incrémente `prompt_version` (semver) et doit passer la calibration sur `corpus/`. Le résultat ne se recopie pas à la main : `lynceus calibrer corpus/corpus.yaml --ecrire` enregistre la passe dans `corpus/passes.jsonl` et réengendre le tableau de [corpus/RESULTATS.md](corpus/RESULTATS.md) dans les deux langues. `verifier.sh` réengendre ce tableau pour le comparer, et refuse une version de prompt pour laquelle aucune passe n'a été enregistrée : un chiffre publié vient d'une mesure, ou la construction échoue.
- **Corpus** : ne jamais assouplir une attente pour faire passer un test sans avoir examiné le cas, et jamais sur `techniques_attendues` / `techniques_interdites`, qui sont le cœur de la mesure.
- **Ids de taxonomie** : stables et définitifs, jamais renommés (l'annuaire les référence).
- **Charte** : toute PR doit être compatible avec [docs/ETHIQUE.md](docs/ETHIQUE.md) : c'est le critère de revue numéro un.
- **Langue du code et des documents** : le code, ses commentaires et les messages de commit sont en français, et cela ne changera pas. La documentation d'accueil (`README`, `CONTRIBUTING`, `INSTALLATION`, les `README` de sous-dossiers) est en anglais à son chemin canonique, avec le français à côté en `*.fr.md`. Les textes qui engagent le projet (`docs/`, `prompts/`, `corpus/RESULTATS.md`) gardent le français à leur chemin canonique, avec la traduction sous `en/`. La règle tient en une phrase : **là où un fichier est une porte, l'anglais est à la porte ; là où un fichier fait loi, le français reste l'original.**
- **Traductions** : le portail est bilingue. Une phrase d'interface vit dans les catalogues (`api/lynceus/portail/traductions/*.po` pour le site, `extension/src/_locales/*/messages.json` pour l'extension) et les tests refusent une phrase employée sans traduction. Un document du dépôt publié par le portail se traduit dans un sous-dossier de langue : `docs/ETHIQUE.md` devient `docs/en/ETHIQUE.md`. Le fichier traduit porte en deuxième ligne l'empreinte de la version qu'il traduit :

  ```
  <!-- traduit-de: docs/ETHIQUE.md sha256:8aa471a51c89 -->
  ```

  `lynceus traductions` dit où en est chaque document, et `verifier.sh` échoue si une traduction est en retard sur son original. **Modifier un document traduit suppose donc de revoir sa traduction et de mettre à jour cette ligne** : sans ça, le portail publierait deux textes qui ne disent plus la même chose, sans que rien ne le signale.
- **Secrets** : `verifier.sh` inspecte le dépôt avant chaque fusion, et un crochet `pre-commit` inspecte ce qui est indexé. À activer une fois par clone :

  ```bash
  git config core.hooksPath .githooks
  ```

  La détection de GitHub ne suffit pas ici, et il faut le dire : elle reconnaît les jetons de fournisseurs connus à leur préfixe, jamais les trois secrets propres à ce projet, qui n'ont aucune forme remarquable. La clé privée Ed25519 qui signe les accès est une simple chaîne en base64 ; une URL de webhook Portainer est un jeton de déploiement déguisé ; un nom de machine du tailnet n'a rien à faire dans un dépôt public. Les motifs personnalisés de GitHub demandent Advanced Security, absent d'un dépôt public gratuit. `outils/chercher-secrets.py` est donc la seule couche qui les couvre.

  Un secret poussé est un secret compromis, même retiré au commit suivant : l'historique le garde. Le révoquer passe avant le nettoyage.
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
à [AUTHORS.md](AUTHORS.fr.md) lors de votre première contribution.

## Développement local

Voir [api/README.md](api/README.fr.md) (serveur + CLI) et [extension/README.md](extension/README.fr.md).

## Licence

Le projet est sous **AGPL-3.0** : en contribuant, vous acceptez que votre contribution soit publiée sous cette licence.
