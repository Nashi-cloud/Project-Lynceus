# Résultats de calibration

<!-- calibration:début (engendré par « lynceus calibrer --ecrire », ne pas modifier à la main) -->

Dernière passe : **2026-09-02** · modèle `z-ai/glm-5.2` (via openrouter.ai) · prompt **v0.1.6** · température **0**

**3 passes** enregistrées sur cette version du prompt : **13/14, 12/14, 11/14** conformes. Une passe unique ne dirait rien de solide, puisque le modèle ne rend pas deux fois la même analyse du même texte.

| Cas | Catégorie | Grade | Score | Écarts relevés |
|---|---|---|---|---|
| Le conseil municipal vote à l'unanimité contre l'unanimité | satire | A | 87 à 92 | — |
| Pourquoi je pense que notre commune se trompe sur le stationnement payant | opinion | A | 80 à 86 | — |
| La racine oubliée que les laboratoires préfèrent vous cacher | publicite_sponsorise | E | 10 à 17 | — |
| Le pont de la Vieille-Écluse fermé pour travaux du 3 au 28 mars | information | A B A | 77 à 81 | — |
| Méditation de l'Avent : l'attente comme chemin | contenu_confessionnel | A | 86 à 94 | — |
| Coupure électrique de novembre : trois questions qui dérangent | theorie_du_complot | E | 10 à 12 | — |
| What They Won't Tell You About the New Water Treatment Plant | theorie_du_complot | E | 11 à 14 | — |
| Cinq habitudes du soir pour mieux dormir | publicite_sponsorise / information | C | 58 à 62 | catégorie `information` au lieu de publicite_sponsorise (1 passe(s) sur 3) ; technique manquante : `conflit_interet_commercial` (1 passe(s) sur 3) |
| Fluoration de l'eau : le débat reste ouvert | opinion | D | 40 à 46 | — |
| Pourquoi le ciel est bleu, et pourquoi cette explication est incomplète | analyse_expertise | B A B | 74 à 84 | — |
| Ce que trois ans d'errance médicale m'ont appris | temoignage | A | 80 à 82 | grade A hors de la fourchette B, C, D ; technique manquante : `preuve_anecdotique` |
| Biais de confirmation — Wikipédia | information / analyse_expertise | A | 86 à 88 | catégorie `analyse_expertise` au lieu de information (2 passe(s) sur 3) |
| Résumé SOTT des changements terrestres - Juin 2026 | theorie_du_complot / pseudo_science | D | 30 à 36 | — |
| Atelier du Guidon, réparation de vélos | autre | A | 93 à 100 | — |

<!-- calibration:fin -->

## Lecture

Trois passes indépendantes sur analyses neuves, sur un corpus passé à **quatorze cas**.

Les cinq sentinelles de [docs/METHODOLOGIE.md](../docs/METHODOLOGIE.md) §7 tiennent aux trois passes, catégorie et fourchette.

### Un contrôle négatif qui manquait

Le §7 imposait un sentinelle « site pseudo-médical marchand » dont le conflit d'intérêt doit être détecté, sans aucun cas symétrique. Les deux spécimens commerciaux du corpus étaient l'un et l'autre malhonnêtes, si bien que **rien n'aurait échoué si l'outil s'était mis à pénaliser le commerce en tant que tel**. Le spécimen 12 comble ce trou : page commerciale assumée, tarifs publiés, exploitante nommée, limites de l'activité énoncées, et qui renvoie vers des ateliers associatifs gratuits.

Il sort en `autre`, **A entre 93 et 100 aux trois passes, sans un écart**. La pseudo-médecine marchande reste en E entre 10 et 17. L'outil distingue donc le commerce honnête du commerce trompeur, ce qu'aucune mesure ne disait jusqu'ici.

### La dimension `sources` dit enfin ce qu'elle note

Signalé depuis le dépôt nashi.cloud : une page qui décrit ses propres services ne peut structurellement citer personne, et perdait 30 % de sa note pour une attente qui ne s'appliquait pas, la justification du modèle le reconnaissant parfois elle-même.

La règle ajoutée ne dépend **pas de la catégorie** mais de ce que le texte affirme : pas d'affirmation demandant un appui extérieur, pas de pénalité ; des affirmations de fait, il faut les étayer, page commerciale comprise. C'est ce qui permet au spécimen 12 de sortir en A sans que le spécimen 01 cesse de sortir en E.

Une repondération par catégorie avait été envisagée. Elle est inutile : énoncer la règle dans le prompt donne le même résultat sans toucher à l'arithmétique, et « mêmes dimensions, même note » reste vrai.

### Le témoignage, attente resserrée et non relâchée

Ce cas sortait en A, un cran au-dessus de sa fourchette, depuis trois versions. L'examen a montré que l'attente ne disait pas ce qu'elle voulait dire : l'en-tête du spécimen annonce une `preuve_anecdotique` de gravité faible à moyenne, et la fourchette `[B, C, D]` n'était qu'un **proxy** de cette détection, que le corpus n'exigeait nulle part. Le modèle ne détecte aucune technique et note A.

La fourchette n'a pas été élargie pour faire passer le test. La technique attendue a été ajoutée, ce qui **durcit** l'attente et nomme le vrai défaut : l'outil ne voit pas la généralisation d'un cas unique à un conseil. L'écart est désormais précis au lieu d'être flou, et il est publié.

### Le reste

La page complotiste réelle est **conforme aux trois passes** pour la première fois en quatre versions. L'article encyclopédique bascule toujours en `analyse_expertise` deux passes sur trois. La publicité déguisée passe une fois sur trois en `information`, ce qui est nouveau et à surveiller.

Totaux : 13, 12 et 11 sur 14. Ils ne se comparent pas à ceux des versions précédentes, le corpus ayant gagné un cas et une attente. Ce qui se lit reste le cas par cas.

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
| 2026-09-02 | v0.1.6 | 0 | 13/14, 12/14, 11/14 ; corpus à 14 cas, sentinelle commerce honnête ajouté |
| 2026-09-02 | v0.1.5 | 0 | 9/13, 10/13, 12/13 ; spécimen satirique stabilisé, témoignage reparti en A |
| 2026-09-01 | v0.1.4 | 0 | 11/13, 10/13, 10/13 sur trois passes ; témoignage corrigé, spécimen satirique déstabilisé |
| 2026-08-31 | v0.1.3 | 0 | 11/13, 9/13, 12/13 sur trois passes neuves ; la vulgarisation corrigée aux trois |
| 2026-08-27 | v0.1.2 | 0 | 11/13, première passe enregistrée au journal (resservie depuis l'annuaire) |
| 2026-08-27 | v0.1.2 | 0 | 13/13, 10/13, 11/12 sur trois passes |
| 2026-08-27 | v0.1.2 | 0,2 | 11/13 sur une passe, puis 9, 11, 9 sur trois passes de contrôle |
| 2026-08-24 | v0.1.1 | 0,2 | 12/12 conformes (passe unique, 12 cas) |
