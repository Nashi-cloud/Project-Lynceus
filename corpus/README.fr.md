# Corpus de calibration

<!-- traduit-de: corpus/README.md sha256:91cc04b933f92f7b -->

[English](README.md) · **Français**

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
lynceus calibrer corpus/corpus.yaml                      # rapport en console
lynceus calibrer corpus/corpus.yaml --json rapport.json  # + rapport détaillé
lynceus calibrer corpus/corpus.yaml --filtre satire      # un sous-ensemble
lynceus calibrer corpus/corpus.yaml --parallele 12       # plus vite sur votre propre instance
```

Les cas sont analysés **de front** (4 à la fois par défaut), ce qui divise l'attente d'autant : mesuré sur 12 cas à 3 s l'analyse, 37 s en séquentiel contre 9,6 s à 4 en parallèle, et 4,2 s à 12. Le défaut reste modeste par courtoisie envers une instance partagée — monter à 12 est justifié sur votre propre instance. Un dépassement de la limite de débit n'échoue pas : la demande patiente et reprend.

Les écarts sont classés : catégorie erronée, technique attendue manquante ou faux positif sur une technique interdite sont des **échecs graves** (code de sortie 1) ; un grade à un cran de la fourchette est un **écart mineur**.

## Cas sentinelles obligatoires

1. **Satire** → jamais classée trompeuse.
2. **Éditorial de qualité** → jamais pénalisé pour sa position.
3. **Pseudo-médecine marchande** → conflit d'intérêt détecté.
4. **Article factuel de référence** → grade A/B, peu ou pas de techniques.
5. **Contenu confessionnel non manipulateur** → la foi n'est pas notée.

Deux pièges complètent le socle : le **faux équilibre** (ton neutre, procédé trompeur — doit être détecté) et la **vulgarisation scientifique dense** (vocabulaire technique légitime — ne doit PAS déclencher `jargon_pseudo_scientifique`).

## Enrichir le corpus

### Spécimens fictifs

Socle stable, écrits pour porter un procédé précis, versionnés dans le dépôt. Voir [specimens/README.fr.md](specimens/README.fr.md).

### Pages réelles capturées

Elles ancrent la mesure dans le monde réel — un spécimen écrit pour illustrer une technique la contient forcément ; une vraie page, non.

**Les captures ne sont pas versionnées.** Reproduire des articles entiers dans un dépôt public poserait un problème de droit d'auteur, y compris pour un usage de calibration. Le dépôt ne contient que le **manifeste** : URL, date de capture, empreinte du contenu et attentes. Chacun recrée les captures localement ; l'empreinte `content_hash` garantit que tout le monde mesure exactement le même texte.

Conséquences pratiques :

- une capture **absente** → le cas est ignoré, jamais compté comme un échec (un dépôt fraîchement cloné ne doit pas paraître rouge) ;
- une capture **divergente** → signalée explicitement : la page a changé, il faut recapturer et réexaminer les attentes, pas les ajuster à l'aveugle.

**Ajouter une page :**

```bash
# 1. Récupérer le texte de la page (extension, copier-coller, ou trafilatura)
# 2. L'enregistrer comme capture — la commande affiche l'entrée à coller
lynceus capturer article.md --url https://exemple.fr/article --titre "…"

# 3. L'ANALYSER avant de fixer quoi que ce soit
lynceus analyser corpus/captures/article.md

# 4. Examiner le résultat, puis compléter l'entrée dans corpus.yaml
```

L'ordre compte : fixer une attente avant d'avoir vu le résultat revient à inventer une vérité de référence. Fixer l'attente après examen, c'est constater ce qui est défendable — et ne l'inscrire que si ça l'est.

**Choisir les techniques attendues.** Les modèles varient dans leurs détections : n'exiger que les marqueurs **stables**, ceux que plusieurs modèles relèvent. Le cas SOTT du corpus n'exige qu'une seule technique (`verite_cachee`), la seule commune aux deux modèles testés — le reste variait.

## Résultats

Voir [RESULTATS.md](RESULTATS.md) — dernière passe : trois passes avec `z-ai/glm-5.2` et le prompt v0.1.2 à température 0, soit 13/13, 10/13 et 11/12 conformes.

> Un corpus qu'on ajuste jusqu'à ce que tout passe ne mesure plus rien. Chaque assouplissement d'attente doit être justifié par un examen du cas — et jamais porter sur les techniques attendues ou interdites, qui sont le cœur du test.
