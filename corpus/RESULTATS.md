# Résultats de calibration

<!-- calibration:début (engendré par « lynceus calibrer --ecrire », ne pas modifier à la main) -->

Dernière passe : **2026-08-31** · modèle `z-ai/glm-5.2` (via openrouter.ai) · prompt **v0.1.3** · température **0**

**Une passe** enregistrée sur cette version du prompt : **11/13** conformes. Une passe unique ne dit rien de solide, puisque le modèle ne rend pas deux fois la même analyse du même texte.

| Cas | Catégorie | Grade | Score | Écarts relevés |
|---|---|---|---|---|
| Le conseil municipal vote à l'unanimité contre l'unanimité | satire | A | 85 | — |
| Pourquoi je pense que notre commune se trompe sur le stationnement payant | opinion | A | 82 | — |
| La racine oubliée que les laboratoires préfèrent vous cacher | publicite_sponsorise | E | 7 | — |
| Le pont de la Vieille-Écluse fermé pour travaux du 3 au 28 mars | information | A | 82 | — |
| Méditation de l'Avent : l'attente comme chemin | contenu_confessionnel | A | 89 | — |
| Coupure électrique de novembre : trois questions qui dérangent | theorie_du_complot | E | 8 | — |
| What They Won't Tell You About the New Water Treatment Plant | theorie_du_complot | E | 14 | — |
| Cinq habitudes du soir pour mieux dormir | publicite_sponsorise | C | 50 | — |
| Fluoration de l'eau : le débat reste ouvert | information | D | 38 | — |
| Pourquoi le ciel est bleu, et pourquoi cette explication est incomplète | analyse_expertise | B | 70 | — |
| Ce que trois ans d'errance médicale m'ont appris | temoignage | A | 81 | grade A hors de la fourchette B, C, D |
| Biais de confirmation — Wikipédia | information | A | 93 | — |
| Résumé SOTT des changements terrestres - Juin 2026 | opinion | D | 39 | catégorie `opinion` au lieu de theorie_du_complot, pseudo_science |

<!-- calibration:fin -->

## Lecture

Une seule passe est enregistrée sur cette version du prompt. Rien n'y a été resservi depuis l'annuaire : la mise en cache est indexée sur le couple contenu et version de prompt, si bien qu'un changement de prompt force une analyse neuve des treize cas. Elle dit donc ce qu'un tirage a rendu, pas ce que trois tirages rendraient. Les passes menées avant que le journal existe figurent dans l'historique, en fin de page, avec leurs chiffres tels qu'ils avaient été relevés.

Les cinq sentinelles de [docs/METHODOLOGIE.md](../docs/METHODOLOGIE.md) §7 tiennent : la satire reste classée `satire`, l'opinion argumentée n'est pas pénalisée pour sa position, la pseudo-médecine marchande sort en E, l'information factuelle en A, et le contenu confessionnel reste dans sa catégorie sans qu'aucune des techniques interdites soit relevée. Le spécimen anglais est analysé en anglais, ce que le corpus vérifie explicitement par `langue_attendue`.

Deux écarts sur treize cas :

- **Page réelle d'agrégation complotiste** classée `opinion` au lieu de `theorie_du_complot` ou `pseudo_science`. Échec grave : la catégorie est une attente exacte. Le grade reste D et le score 39, donc le jugement rendu au lecteur n'est pas inversé, mais la nature du contenu est mal nommée, et c'est précisément ce que l'outil prétend savoir faire.
- **Témoignage** noté A alors que la fourchette attendue est B à D. Un cran au-dessus. Écart mineur.

### Ce qu'a déplacé le passage de v0.1.2 à v0.1.3

Le prompt v0.1.3 donne aux dix catégories la définition que `docs/METHODOLOGIE.md` publiait déjà. Jusque-là elles n'étaient qu'une liste d'identifiants nus, et la calibration sanctionnait une frontière que le prompt ne traçait nulle part. Le total ne bouge pas, 11 sur 13 avant comme après, mais la composition change entièrement, et il faut le lire cas par cas plutôt que sur le total.

**Les deux écarts publiés en v0.1.2 ont disparu.** La vulgarisation scientifique sort désormais en `analyse_expertise`, ce que la définition ajoutée dit explicitement. La publicité déguisée revient à C, dans sa fourchette. Le premier est un effet causal, la définition tranche la frontière ; le second peut n'être qu'un tirage plus favorable.

**Deux écarts nouveaux apparaissent**, décrits ci-dessus.

**Deux cas conformes ont beaucoup bougé sans sortir de leur fourchette.** Le contenu confessionnel passe de C 57 à A 89, le témoignage de C 60 à A 81. Ces deux déplacements dépassent la dispersion mesurée à température 0, qui plafonnait à 11 points entre passes, donc ils viennent du prompt et non du tirage. L'explication plausible est que la mention « la nature dominante du contenu, **pas sa qualité** » a cessé de faire pénaliser un texte pour n'être pas du journalisme. Si elle est juste, c'est le comportement voulu, et ce sont alors les fourchettes attendues de ces deux cas qui portent l'ancien biais. Cela ne se tranche pas sur une passe, et surtout pas en assouplissant une attente pour faire passer un test.

**Deux questions restent donc ouvertes**, à trancher par des tirages indépendants sur base vierge et non par un ajustement du corpus : la bascule de la page complotiste en `opinion` est-elle un effet des définitions ou l'instabilité de catégorie déjà documentée plus bas, et la remontée des scores sur le témoignage et le contenu confessionnel est-elle la correction d'un biais ou une complaisance nouvelle.

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
| 2026-08-31 | v0.1.3 | 0 | 11/13, analyses neuves, les deux écarts de v0.1.2 corrigés et deux autres apparus |
| 2026-08-27 | v0.1.2 | 0 | 11/13, première passe enregistrée au journal (resservie depuis l'annuaire) |
| 2026-08-27 | v0.1.2 | 0 | 13/13, 10/13, 11/12 sur trois passes |
| 2026-08-27 | v0.1.2 | 0,2 | 11/13 sur une passe, puis 9, 11, 9 sur trois passes de contrôle |
| 2026-08-24 | v0.1.1 | 0,2 | 12/12 conformes (passe unique, 12 cas) |
