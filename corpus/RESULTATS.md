# Résultats de calibration

<!-- calibration:début (engendré par « lynceus calibrer --ecrire », ne pas modifier à la main) -->

Dernière passe : **2026-09-02** · modèle `z-ai/glm-5.2` (via openrouter.ai) · prompt **v0.1.5** · température **0**

**3 passes** enregistrées sur cette version du prompt : **9/13, 10/13, 12/13** conformes. Une passe unique ne dirait rien de solide, puisque le modèle ne rend pas deux fois la même analyse du même texte.

| Cas | Catégorie | Grade | Score | Écarts relevés |
|---|---|---|---|---|
| Le conseil municipal vote à l'unanimité contre l'unanimité | satire | A | 84 à 89 | — |
| Pourquoi je pense que notre commune se trompe sur le stationnement payant | opinion | A | 80 à 88 | — |
| La racine oubliée que les laboratoires préfèrent vous cacher | publicite_sponsorise | E | 10 à 16 | — |
| Le pont de la Vieille-Écluse fermé pour travaux du 3 au 28 mars | information | B A B | 75 à 80 | — |
| Méditation de l'Avent : l'attente comme chemin | contenu_confessionnel | A | 88 à 94 | — |
| Coupure électrique de novembre : trois questions qui dérangent | theorie_du_complot | E | 10 à 12 | — |
| What They Won't Tell You About the New Water Treatment Plant | theorie_du_complot | E | 16 à 21 | — |
| Cinq habitudes du soir pour mieux dormir | publicite_sponsorise | C | 52 à 64 | technique manquante : `conflit_interet_commercial` (1 passe(s) sur 3) |
| Fluoration de l'eau : le débat reste ouvert | opinion | D | 41 à 47 | technique manquante : `faux_equilibre` (1 passe(s) sur 3) |
| Pourquoi le ciel est bleu, et pourquoi cette explication est incomplète | analyse_expertise | B | 65 à 71 | — |
| Ce que trois ans d'errance médicale m'ont appris | temoignage | A | 82 à 84 | grade A hors de la fourchette B, C, D |
| Biais de confirmation — Wikipédia | analyse_expertise / information | A | 82 à 90 | catégorie `analyse_expertise` au lieu de information (2 passe(s) sur 3) |
| Résumé SOTT des changements terrestres - Juin 2026 | pseudo_science / opinion / theorie_du_complot | D | 33 à 37 | catégorie `opinion` au lieu de theorie_du_complot, pseudo_science (1 passe(s) sur 3) ; technique manquante : `verite_cachee` (1 passe(s) sur 3) |

<!-- calibration:fin -->

## Lecture

Trois passes indépendantes, sur analyses neuves : la mise en cache est indexée sur le couple contenu et version de prompt, et les analyses de la version en cours ont été retirées de la base entre chaque passe.

Les cinq sentinelles de [docs/METHODOLOGIE.md](../docs/METHODOLOGIE.md) §7 tiennent aux trois passes, catégorie **et** fourchette de grade.

### Ce que le prompt v0.1.5 corrige, et comment ça a été établi

Le v0.1.4 avait déstabilisé le spécimen satirique : de A stable, il était passé à un D une passe sur trois. Le diagnostic a été fait sur ce seul cas plutôt que sur le corpus entier, ce qui coûte une analyse au lieu de treize. Huit tirages du même texte, quatre sous v0.1.3 et quatre sous v0.1.4, ont montré un mode de défaillance net : sur un tirage, `sources` et `factualite` tombaient à **exactement 0** pendant que `ton` et `transparence` restaient à 90 et 95. Le modèle basculait de « c'est une parodie » à « ce texte n'a pas de sources et ses affirmations sont fausses ».

La cause n'était pas une régression du v0.1.4 mais une **lacune de spécification** que le v0.1.4 a rendue plus visible. La règle sur la satire ne disait comment noter que `transparence`, et laissait le modèle décider seul pour les deux autres. Il décidait différemment d'un tirage à l'autre.

Le v0.1.5 énonce la règle manquante : une parodie invente ses faits par construction et ne cite pas de sources, ce ne sont pas des défauts, et ces deux dimensions se notent sur la loyauté du procédé. Résultat : **onze tirages sans un seul effondrement**, huit en mesure ciblée et trois en passe complète, contre deux effondrements sur sept avant. Le spécimen sort en A aux trois passes, entre 84 et 89.

Le point de méthode, parce qu'il resservira : quand une attente du corpus n'est pas tenue de façon **instable**, chercher d'abord ce que la spécification laisse implicite. Un modèle qui doit trancher lui-même ne tranche pas deux fois pareil. C'est la deuxième fois en trois versions que le défaut est là, et non dans le modèle ni dans l'attente.

### Ce qui a bougé en sens inverse

**Le témoignage repart en A aux trois passes**, un cran au-dessus de sa fourchette, alors que le v0.1.4 l'avait ramené en B. Les deux mouvements sont probablement liés : dire qu'une dimension ne se lit pas au premier degré pour la satire semble se généraliser aux contenus qui n'ont structurellement pas de sources à citer, ce qu'un récit personnel est aussi. Ce cas a maintenant bougé trois versions de suite, et c'est **son attente qu'il faut examiner**, pas la faire plier.

Deux écarts restent minoritaires et connus : l'article encyclopédique bascule en `analyse_expertise` deux passes sur trois, la page complotiste en `opinion` une passe sur trois.

### Les totaux, toujours muets

9, 10 et 12 sur 13, contre 11, 10, 10 en v0.1.4 et 11, 9, 12 en v0.1.3. Trois versions, neuf passes, aucune différence lisible sur le total. Ce qui se lit reste le cas par cas et l'accord des passes entre elles. À treize cas, le corpus dit si un comportement est stable, jamais si une version est meilleure.

## La température, mesurée

Le 27 août, une passe avait révélé deux cas qui changeaient de verdict d'une exécution à l'autre. Plutôt que d'ajuster les attentes, la question a été posée à l'expérience : **le modèle est-il plus stable à température 0 ?**

Six passes complètes du corpus, trois à 0,2 et trois à 0,0, chacune sur une base de données neuve pour qu'aucune analyse ne soit resservie depuis le cache. Comparaison sur les 12 cas présents dans les six passes.

| | température 0,2 | température 0 |
|---|---|---|
| Conformes par passe | 9, 11, 9 | 12, 10, 11 |
| Catégorie qui change d'une passe à l'autre | 2 cas sur 12 | 2 cas sur 12 |
| Grade qui change | 3 cas sur 12 | 2 cas sur 12 |
| Techniques détectées qui changent | 4 cas sur 12 | 4 cas sur 12 |
| Écart de score entre passes | **10,8 en moyenne, 61 au maximum** | **5,8 en moyenne, 11 au maximum** |
| Cas rigoureusement identiques aux trois passes | 5 sur 12 | 7 sur 12 |

Le cas qui a emporté la décision est le spécimen satirique. À température 0,2, le même texte a obtenu **99, puis 79, puis 38 sur 100**, soit les grades A, B et D. Une note qui change de trois grades selon le tirage n'est pas une note. À 0, ce cas ne bouge plus (91 à 98, toujours A).

**Conséquence : la température par défaut passe à 0.** Le paramètre reste réglable par instance, la reproductibilité n'étant pas le seul critère qu'on puisse retenir.

## Ce que l'expérience ne dit pas

Elle ne rend pas le système déterministe, et il faut le dire clairement : **à température 0, 5 cas sur 12 varient encore** quelque part, catégorie, grade ou techniques relevées. Le fournisseur n'est pas déterministe même à 0, et deux cas du corpus sont proches d'une frontière de catégorie (vulgarisation ou analyse experte ; information ou opinion sur un sujet à controverse). Le spécimen anglais lui-même bascule une fois sur trois en `opinion`.

Trois passes ne suffisent pas non plus à distinguer un écart de 1 conformité d'un effet du hasard. Ce qui est solide ici, c'est la dispersion des scores, où l'écart est net et va dans le même sens sur tous les cas.

Une passe unique restera donc publiée avec ses écarts, jamais lissée.

## Historique

Les lignes antérieures au journal ont été relevées à la main, avant que `lynceus calibrer --ecrire` existe. Elles sont conservées telles quelles : les réécrire reviendrait à leur donner une garantie qu'elles n'ont pas.

| Date | Prompt | Température | Résultat |
|---|---|---|---|
| 2026-09-02 | v0.1.5 | 0 | 9/13, 10/13, 12/13 ; spécimen satirique stabilisé, témoignage reparti en A |
| 2026-09-01 | v0.1.4 | 0 | 11/13, 10/13, 10/13 sur trois passes ; témoignage corrigé, spécimen satirique déstabilisé |
| 2026-08-31 | v0.1.3 | 0 | 11/13, 9/13, 12/13 sur trois passes neuves ; la vulgarisation corrigée aux trois |
| 2026-08-27 | v0.1.2 | 0 | 11/13, première passe enregistrée au journal (resservie depuis l'annuaire) |
| 2026-08-27 | v0.1.2 | 0 | 13/13, 10/13, 11/12 sur trois passes |
| 2026-08-27 | v0.1.2 | 0,2 | 11/13 sur une passe, puis 9, 11, 9 sur trois passes de contrôle |
| 2026-08-24 | v0.1.1 | 0,2 | 12/12 conformes (passe unique, 12 cas) |
