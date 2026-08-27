# Résultats de calibration

<!-- calibration:début (engendré par « lynceus calibrer --ecrire », ne pas modifier à la main) -->

Dernière passe : **2026-08-27** · modèle `z-ai/glm-5.2` (via openrouter.ai) · prompt **v0.1.2** · température **0**

**Une passe** enregistrée sur cette version du prompt : **11/13\*** conformes. Une passe unique ne dit rien de solide, puisque le modèle ne rend pas deux fois la même analyse du même texte.

Les passes marquées d'une astérisque ont été intégralement resservies depuis l'annuaire : elles rejouent une mesure déjà enregistrée au lieu d'en produire une nouvelle. Pour un tirage réellement indépendant, il faut une base vierge.

| Cas | Catégorie | Grade | Score | Écarts relevés |
|---|---|---|---|---|
| Le conseil municipal vote à l'unanimité contre l'unanimité | satire | A | 88 | — |
| Pourquoi je pense que notre commune se trompe sur le stationnement payant | opinion | A | 84 | — |
| La racine oubliée que les laboratoires préfèrent vous cacher | publicite_sponsorise | E | 7 | — |
| Le pont de la Vieille-Écluse fermé pour travaux du 3 au 28 mars | information | A | 84 | — |
| Méditation de l'Avent : l'attente comme chemin | contenu_confessionnel | C | 57 | — |
| Coupure électrique de novembre : trois questions qui dérangent | theorie_du_complot | E | 9 | — |
| What They Won't Tell You About the New Water Treatment Plant | theorie_du_complot | E | 2 | — |
| Cinq habitudes du soir pour mieux dormir | publicite_sponsorise | B | 66 | grade B hors de la fourchette C, D |
| Fluoration de l'eau : le débat reste ouvert | opinion | D | 40 | — |
| Pourquoi le ciel est bleu, et pourquoi cette explication est incomplète | information | B | 70 | catégorie `information` au lieu de analyse_expertise |
| Ce que trois ans d'errance médicale m'ont appris | temoignage | C | 60 | — |
| Biais de confirmation — Wikipédia | information | A | 92 | — |
| Résumé SOTT des changements terrestres - Juin 2026 | pseudo_science | D | 30 | — |

<!-- calibration:fin -->

## Lecture

Une seule passe est enregistrée sur cette version du prompt, et elle a été resservie depuis l'annuaire. Elle dit donc ce que l'instance rend aujourd'hui, pas ce qu'un nouveau tirage donnerait. Les passes menées avant que le journal existe figurent dans l'historique, en fin de page, avec leurs chiffres tels qu'ils avaient été relevés.

Les cinq sentinelles de [docs/METHODOLOGIE.md](../docs/METHODOLOGIE.md) §7 tiennent : la satire reste classée `satire`, l'opinion argumentée n'est pas pénalisée pour sa position, la pseudo-médecine marchande sort en E, l'information factuelle en A, et le contenu confessionnel reste dans sa catégorie sans qu'aucune des techniques interdites soit relevée. Le spécimen anglais est analysé en anglais, ce que le corpus vérifie explicitement par `langue_attendue`.

Deux écarts sur treize cas :

- **Vulgarisation scientifique** classée `information` au lieu de `analyse_expertise`. La frontière est mince, un article qui explique un phénomène en citant l'état des connaissances relève des deux lectures. C'est néanmoins un échec grave au sens du corpus, parce que la catégorie y est une attente exacte et non une appréciation.
- **Publicité déguisée** notée B alors que la fourchette attendue est C à D. Un cran au-dessus : le procédé est vu, sa gravité est jugée plus faible. Écart mineur.

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
| 2026-08-27 | v0.1.2 | 0 | 11/13, première passe enregistrée au journal (resservie depuis l'annuaire) |
| 2026-08-27 | v0.1.2 | 0 | 13/13, 10/13, 11/12 sur trois passes |
| 2026-08-27 | v0.1.2 | 0,2 | 11/13 sur une passe, puis 9, 11, 9 sur trois passes de contrôle |
| 2026-08-24 | v0.1.1 | 0,2 | 12/12 conformes (passe unique, 12 cas) |
