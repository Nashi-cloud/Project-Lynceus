# Résultats de calibration

<!-- calibration:début (engendré par « lynceus calibrer --ecrire », ne pas modifier à la main) -->

Dernière passe : **2026-08-31** · modèle `z-ai/glm-5.2` (via openrouter.ai) · prompt **v0.1.3** · température **0**

**3 passes** enregistrées sur cette version du prompt : **11/13, 9/13, 12/13** conformes. Une passe unique ne dirait rien de solide, puisque le modèle ne rend pas deux fois la même analyse du même texte.

| Cas | Catégorie | Grade | Score | Écarts relevés |
|---|---|---|---|---|
| Le conseil municipal vote à l'unanimité contre l'unanimité | satire | A | 85 à 100 | — |
| Pourquoi je pense que notre commune se trompe sur le stationnement payant | opinion | A | 82 à 84 | — |
| La racine oubliée que les laboratoires préfèrent vous cacher | publicite_sponsorise | E | 7 à 16 | — |
| Le pont de la Vieille-Écluse fermé pour travaux du 3 au 28 mars | information | A B A | 79 à 82 | — |
| Méditation de l'Avent : l'attente comme chemin | contenu_confessionnel | A | 84 à 91 | — |
| Coupure électrique de novembre : trois questions qui dérangent | theorie_du_complot | E | 5 à 13 | — |
| What They Won't Tell You About the New Water Treatment Plant | theorie_du_complot | E | 10 à 14 | technique manquante : `autorite_anonyme` (1 passe(s) sur 3) |
| Cinq habitudes du soir pour mieux dormir | publicite_sponsorise | C B C | 50 à 66 | grade B hors de la fourchette C, D (1 passe(s) sur 3) |
| Fluoration de l'eau : le débat reste ouvert | information / opinion | D | 38 à 40 | — |
| Pourquoi le ciel est bleu, et pourquoi cette explication est incomplète | analyse_expertise | B | 70 à 74 | — |
| Ce que trois ans d'errance médicale m'ont appris | temoignage | A C A | 64 à 82 | grade A hors de la fourchette B, C, D (2 passe(s) sur 3) |
| Biais de confirmation — Wikipédia | information / analyse_expertise | A | 88 à 94 | catégorie `analyse_expertise` au lieu de information (1 passe(s) sur 3) |
| Résumé SOTT des changements terrestres - Juin 2026 | opinion / theorie_du_complot | D | 31 à 39 | catégorie `opinion` au lieu de theorie_du_complot, pseudo_science (2 passe(s) sur 3) |

<!-- calibration:fin -->

## Lecture

Trois passes indépendantes sont enregistrées sur cette version du prompt. Rien n'y a été resservi depuis l'annuaire : la mise en cache est indexée sur le couple contenu et version de prompt, et les analyses de la version en cours ont été retirées de la base entre chaque passe, si bien que les treize cas ont été réanalysés trois fois. Les passes menées avant que le journal existe figurent dans l'historique, en fin de page, avec leurs chiffres tels qu'ils avaient été relevés.

Les cinq sentinelles de [docs/METHODOLOGIE.md](../docs/METHODOLOGIE.md) §7 tiennent aux trois passes : la satire reste classée `satire`, l'opinion argumentée n'est pas pénalisée pour sa position, la pseudo-médecine marchande sort en E, l'information factuelle en A, et le contenu confessionnel reste dans sa catégorie sans qu'aucune des techniques interdites soit relevée. Le spécimen anglais est analysé en anglais, ce que le corpus vérifie explicitement par `langue_attendue`.

### Ce que le prompt v0.1.3 a changé

Le v0.1.3 donne aux dix catégories la définition que `docs/METHODOLOGIE.md` publiait déjà. Jusque-là elles n'étaient qu'une liste d'identifiants nus, et la calibration sanctionnait une frontière que le prompt ne traçait nulle part.

**La correction visée tient.** La vulgarisation scientifique sort en `analyse_expertise` aux trois passes, entre 70 et 74, sans un seul écart. C'est un effet causal de la définition ajoutée, et non un tirage favorable : c'était l'échec grave publié en v0.1.2, il a disparu.

**Le contenu confessionnel a durablement changé de note**, de C 57 en v0.1.2 à A aux trois passes, entre 84 et 91. La mention « la nature dominante du contenu, pas sa qualité » a vraisemblablement cessé de faire pénaliser un texte pour n'être pas du journalisme. Le cas reste conforme, sa fourchette allant de A à C, mais le déplacement est réel et reproductible.

### Ce que trois passes ne permettent pas de conclure

Les totaux sont **11, 9 et 12 sur 13**. Trois chiffres qui, sur treize cas, ne se distinguent pas du hasard : l'écart de score entre passes atteint 7,8 points en moyenne et 18 au maximum, et **3 cas sur 13 changent carrément de catégorie d'une passe à l'autre**. À cette dispersion, une différence de deux ou trois conformités n'est pas un signal. C'est une limite du corpus, pas du prompt, et c'est la raison pour laquelle l'agrandissement du corpus annoté passe avant toute autre optimisation : sans lui, on ne peut pas distinguer une amélioration d'un tirage.

Deux écarts reviennent en majorité des passes, et sont donc autre chose que du bruit :

- **La page complotiste réelle sort en `opinion` deux fois sur trois** au lieu de `theorie_du_complot` ou `pseudo_science`. Le grade reste D dans tous les cas, donc le jugement rendu au lecteur n'est pas inversé, mais la nature du contenu est mal nommée. On ne peut pas imputer cette bascule aux définitions avec certitude : la v0.1.2 n'a jamais été mesurée sur trois passes pour ce cas, sa seule passe enregistrée ayant été resservie depuis l'annuaire.
- **Le témoignage sort en A deux fois sur trois**, un cran au-dessus de sa fourchette, avec le plus grand écart de score du corpus, 18 points. Ce cas est sur une frontière, pas dans une catégorie.

Un écart nouveau, minoritaire mais éclairant : **l'article encyclopédique sur le biais de confirmation bascule en `analyse_expertise` une passe sur trois**, alors qu'on attend `information`. C'est l'image inverse du défaut corrigé. Donner une définition à `analyse_expertise` attire désormais vers elle un contenu explicatif de fond, ce qui est cohérent avec la définition publiée et pose la question de sa frontière avec `information` pour un article d'encyclopédie.

Aucune de ces attentes n'a été ajustée. Elles sont publiées telles quelles, avec le nombre de passes concernées.

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
| 2026-08-31 | v0.1.3 | 0 | 11/13, 9/13, 12/13 sur trois passes neuves ; la vulgarisation corrigée aux trois |
| 2026-08-27 | v0.1.2 | 0 | 11/13, première passe enregistrée au journal (resservie depuis l'annuaire) |
| 2026-08-27 | v0.1.2 | 0 | 13/13, 10/13, 11/12 sur trois passes |
| 2026-08-27 | v0.1.2 | 0,2 | 11/13 sur une passe, puis 9, 11, 9 sur trois passes de contrôle |
| 2026-08-24 | v0.1.1 | 0,2 | 12/12 conformes (passe unique, 12 cas) |
