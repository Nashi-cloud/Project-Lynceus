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
     main                     (stable — c'est ce que les instances déploient)
```

- **`main`** : stable uniquement. Ne reçoit que des merges depuis `next`, chaque release est taguée.
- **`next`** : pré-production. Reçoit `dev` quand un ensemble cohérent est prêt ; on y stabilise.
- **`dev`** : branche d'intégration. Toutes les branches spécifiques en partent et y reviennent.
- **Branches spécifiques** : `feat/<sujet>`, `fix/<sujet>`, `docs/<sujet>` — courtes, focalisées, mergées dans `dev` via PR.

## Conventions

- **Commits** : style Conventional Commits, en français — `feat: …`, `fix: …`, `docs: …`, `chore: …`, `test: …`.
- **Prompts et méthodologie** : toute modification de `prompts/`, `docs/METHODOLOGIE.md` ou `docs/TAXONOMIE.md` incrémente `prompt_version` (semver) et doit passer la calibration sur `corpus/` (dès qu'il est constitué).
- **Ids de taxonomie** : stables et définitifs, jamais renommés (l'annuaire les référence).
- **Charte** : toute PR doit être compatible avec [docs/ETHIQUE.md](docs/ETHIQUE.md) — c'est le critère de revue numéro un.

## Développement local

Voir [api/README.md](api/README.md) (serveur + CLI) et [extension/README.md](extension/README.md).

## Licence

Le projet est sous **AGPL-3.0** : en contribuant, vous acceptez que votre contribution soit publiée sous cette licence.
