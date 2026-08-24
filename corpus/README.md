# Corpus de calibration

Pages de référence servant à évaluer chaque évolution des prompts et de la méthodologie (aucune régression silencieuse — cf. docs/METHODOLOGIE.md §7).

## Format (`corpus.yaml`)

Chaque entrée porte **soit** `fichier` (spécimen figé du dépôt), **soit** `url` (page réelle) :

```yaml
- fichier: specimens/04-fictif-satire.md
  titre: Le conseil municipal vote à l'unanimité contre l'unanimité
  categorie_attendue: satire            # ou categories_acceptables: [a, b]
  grade_attendu: [A, B, C]              # fourchette acceptable
  techniques_attendues: []              # ids qui DOIVENT être détectés
  techniques_interdites: [verite_cachee]  # détections qui seraient des faux positifs graves
  confiance_min: 0.5                    # plancher optionnel
  notes: Crash-test satire — ne doit JAMAIS sortir en pseudo_science
```

Le socle est **local par choix** : un corpus d'URL casse dès qu'une page est modifiée et échoue sur les sites protégés contre le téléchargement automatique. Les entrées `url` restent possibles pour ancrer la calibration dans le monde réel, en complément.

`categories_acceptables` sert aux contenus légitimement hybrides (un article pseudo-médical qui vend un produit est aussi une publicité déguisée) : exiger une étiquette unique testerait un arbitrage arbitraire plutôt que la qualité de l'analyse.

## Lancer une calibration

```bash
lynceus calibrer corpus/corpus.yaml                    # rapport en console
lynceus calibrer corpus/corpus.yaml --json rapport.json  # + rapport détaillé
lynceus calibrer corpus/corpus.yaml --filtre satire      # un sous-ensemble
```

Les écarts sont classés : catégorie erronée, technique attendue manquante ou faux positif sur une technique interdite sont des **échecs graves** (code de sortie 1) ; un grade à un cran de la fourchette est un **écart mineur**.

## Cas sentinelles obligatoires

1. **Satire** → jamais classée trompeuse.
2. **Éditorial de qualité** → jamais pénalisé pour sa position.
3. **Pseudo-médecine marchande** → conflit d'intérêt détecté.
4. **Article factuel de référence** → grade A/B, peu ou pas de techniques.
5. **Contenu confessionnel non manipulateur** → la foi n'est pas notée.

Deux pièges complètent le socle : le **faux équilibre** (ton neutre, procédé trompeur — doit être détecté) et la **vulgarisation scientifique dense** (vocabulaire technique légitime — ne doit PAS déclencher `jargon_pseudo_scientifique`).

## Résultats

Voir [RESULTATS.md](RESULTATS.md) — dernière passe : 10/10 avec `z-ai/glm-5.2` et le prompt v0.1.1.

## Enrichir le corpus

- **Spécimens fictifs** : socle stable, écrits pour porter un procédé précis. Voir [specimens/README.md](specimens/README.md).
- **Pages réelles** : ajouter une entrée `url`, de préférence vers une capture archivée (Wayback Machine) pour la stabilité. Les analyser d'abord manuellement, et ne fixer l'attente qu'après examen du résultat.

> Un corpus qu'on ajuste jusqu'à ce que tout passe ne mesure plus rien. Chaque assouplissement d'attente doit être justifié par un examen du cas — et jamais porter sur les techniques attendues ou interdites, qui sont le cœur du test.
