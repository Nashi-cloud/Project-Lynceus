# Résultats de calibration

<!-- calibration:début (engendré par « lynceus calibrer --ecrire », ne pas modifier à la main) -->

Dernière passe : **2026-09-05** · modèle `z-ai/glm-5.2` (via openrouter.ai) · prompt **v0.1.7** · température **0**

**3 passes** enregistrées sur cette version du prompt : **10/15, 13/15, 13/15** conformes. Une passe unique ne dirait rien de solide, puisque le modèle ne rend pas deux fois la même analyse du même texte.

| Cas | Catégorie | Grade | Score | Écarts relevés |
|---|---|---|---|---|
| Le conseil municipal vote à l'unanimité contre l'unanimité | satire | A | 84 à 92 | — |
| Pourquoi je pense que notre commune se trompe sur le stationnement payant | opinion | A | 82 à 84 | — |
| La racine oubliée que les laboratoires préfèrent vous cacher | publicite_sponsorise | E | 7 à 10 | — |
| Le pont de la Vieille-Écluse fermé pour travaux du 3 au 28 mars | information | A B A | 72 à 82 | — |
| Méditation de l'Avent : l'attente comme chemin | contenu_confessionnel | A | 94 à 99 | — |
| Coupure électrique de novembre : trois questions qui dérangent | theorie_du_complot | E | 4 à 6 | technique manquante : `hyper_intentionnalisme` (1 passe(s) sur 3) |
| What They Won't Tell You About the New Water Treatment Plant | opinion / theorie_du_complot | E | 2 à 18 | catégorie `opinion` au lieu de theorie_du_complot (1 passe(s) sur 3) ; technique manquante : `autorite_anonyme` (1 passe(s) sur 3) |
| Cinq habitudes du soir pour mieux dormir | publicite_sponsorise | B C C | 64 à 65 | grade B hors de la fourchette C, D (1 passe(s) sur 3) |
| Fluoration de l'eau : le débat reste ouvert | information / opinion | D | 38 à 46 | — |
| Pourquoi le ciel est bleu, et pourquoi cette explication est incomplète | analyse_expertise | B A B | 72 à 80 | — |
| Ce que trois ans d'errance médicale m'ont appris | temoignage | A B A | 78 à 87 | grade A hors de la fourchette B, C, D (2 passe(s) sur 3) ; technique manquante : `preuve_anecdotique` |
| Biais de confirmation — Wikipédia | analyse_expertise / information | A | 88 à 90 | — |
| Résumé SOTT des changements terrestres - Juin 2026 | opinion | D | 32 à 38 | catégorie `opinion` au lieu de theorie_du_complot, pseudo_science ; technique manquante : `verite_cachee` (1 passe(s) sur 3) |
| Atelier du Guidon, réparation de vélos | autre | A | 94 à 100 | — |
| La Gazette de Saint-Aubin, page d'accueil | autre | A A B | 73 à 100 | — |

<!-- calibration:fin -->

## Lecture

Trois passes indépendantes sur analyses neuves, sur un corpus de **quinze cas** dont une attente a été corrigée.

Les cinq sentinelles de [docs/METHODOLOGIE.md](../docs/METHODOLOGIE.md) §7 tiennent aux trois passes, catégorie et fourchette.

### Un sommaire n'est pas un article

Cas rapporté par un utilisateur : sur une page d'accueil, l'analyse « part dans tous les sens ». Le spécimen 13 met la chose sous mesure, une page d'accueil de journal local, titres et liens, aucun texte suivi.

Sous le prompt v0.1.6, trois passes donnaient `information`, `information`, `autre` : **le même sommaire classé deux fois sur trois comme un article**. Pris pour un article, il est noté sur des attentes qui n'ont aucun sens pour lui, ce qui explique le désordre rapporté.

La règle existait pourtant, mais énoncée dans des termes que le modèle ne peut pas rapprocher de ce qu'il reçoit : « page non textuelle (boutique, accueil, forum) ». Or la page d'accueil d'un journal est parfaitement textuelle. C'est la quatrième fois de suite que le défaut est là : **le corpus sanctionnait une frontière que le prompt ne traçait nulle part**. Le v0.1.7 décrit le sommaire par sa forme, une suite de titres annonçant des contenus absents, et interdit de noter ce qui n'a pas été lu.

Résultat : `autre` aux trois passes, et encore aux trois passes de la mesure suivante, soit six sur six.

### L'encyclopédie, ou une frontière que la méthode ne trace pas

L'attente sur l'article de Wikipédia exigeait `information`. Le cas échouait deux passes sur trois en v0.1.6, puis les trois en v0.1.7.

Le premier réflexe était d'exiger `analyse_expertise`, puisque c'est ce que le modèle rendait. Ce serait refaire la même erreur : le prompt définit `information` comme du « contenu journalistique factuel (qui, quoi, où, quand) » et `analyse_expertise` comme une « analyse approfondie, vulgarisation scientifique », et **aucune des deux définitions ne parle d'encyclopédie**. Les deux catégories sont donc acceptées.

La mesure a tranché mieux que le raisonnement : les trois passes donnent `analyse_expertise`, `information`, `analyse_expertise`. Exiger l'une des deux aurait produit un échec sur trois, sur une page dont rien ne justifie qu'elle échoue.

Aucune exigence de qualité n'a été relâchée. Le prompt dit lui-même que la catégorie est « la nature dominante du contenu, **pas sa qualité** » : ce qui juge cette page reste sa fourchette `[A, B]` et ses trois techniques interdites, tenues aux trois passes.

### Le résultat le plus instructif de la journée

Le résumé SOTT, capture figée dont l'empreinte de contenu est vérifiée à chaque passe, sortait `pseudo_science` ou `theorie_du_complot` aux **trois** passes de la mesure précédente, sans un écart. Il sort `opinion` aux **trois** passes de celle-ci.

Même capture, même prompt, même modèle, même température, une heure d'intervalle. Rien dans le dépôt n'a changé entre les deux mesures pour ce cas. La seule explication compatible avec les faits est une variation du côté du fournisseur, que rien ici ne permet d'observer.

Trois passes ne suffisaient déjà pas à distinguer une amélioration d'un match nul. Cette page peut désormais dire mieux : **six tirages du même texte se répartissent trois contre trois entre deux verdicts opposés.** C'est la meilleure justification qui soit d'un corpus annoté à une autre échelle, et d'un modèle entraîné pour cette tâche plutôt que loué à l'appel.

### Deux garde-fous, nés de deux erreurs du même jour

Le vidage du cache entre deux passes visait une colonne inexistante. Il a échoué en silence, et deux passes ont été resservies intégralement depuis l'annuaire : trois totaux identiques, à un cheveu d'être publiés comme trois mesures. Le champ `depuis_cache` existait déjà, avec le bon raisonnement en commentaire ; le garde-fou n'avait jamais été construit. `--ecrire` refuse désormais une passe entièrement resservie.

Puis le plafond de débit de l'instance a laissé cinq cas sans analyse sur trois passes. Ils comptent comme écarts graves, si bien qu'un « 11/15 » lisait comme une mesure là où c'était une file d'attente. `--ecrire` refuse désormais une passe amputée, en nommant les cas et en conseillant de baisser `--parallele`.

S'y ajoute un défaut latent que la correction de l'attente a exposé : l'agrégation ne filtrait pas sur le corpus. Modifier une attente change ce que « conforme » veut dire, et rien n'empêchait de mélanger des passes mesurées contre des attentes différentes. Le cas ne s'était jamais présenté par coïncidence, chaque changement de corpus ayant jusqu'ici accompagné un changement de version de prompt.

Le point commun des trois : le raisonnement juste existait, dans un commentaire ou dans un README, et rien ne l'appliquait.

### Le reste

Le témoignage échoue toujours sa technique attendue aux trois passes, et son grade à deux sur trois. C'est voulu : l'attente a été **durcie** en v0.1.6 plutôt qu'élargie, pour nommer un vrai défaut, l'outil ne voyant pas la généralisation d'un cas unique à un conseil. Elle est publiée en échec tant que le défaut dure.

Totaux : 10, 13 et 13 sur 15. L'écart de trois conformités entre la première passe et les deux autres est du même ordre que la dispersion décrite plus haut, et ne se lit pas.

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
| 2026-09-05 | v0.1.7 | 0 | 10/15, 13/15, 13/15 ; attente encyclopédique corrigée, le résumé SOTT bascule en `opinion` aux trois passes |
| 2026-09-05 | v0.1.7 | 0 | 12/15, 11/15, 12/15 ; corpus à 15 cas, sommaire ajouté et corrigé aux trois passes |
| 2026-09-02 | v0.1.6 | 0 | 13/14, 12/14, 11/14 ; corpus à 14 cas, sentinelle commerce honnête ajouté |
| 2026-09-02 | v0.1.5 | 0 | 9/13, 10/13, 12/13 ; spécimen satirique stabilisé, témoignage reparti en A |
| 2026-09-01 | v0.1.4 | 0 | 11/13, 10/13, 10/13 sur trois passes ; témoignage corrigé, spécimen satirique déstabilisé |
| 2026-08-31 | v0.1.3 | 0 | 11/13, 9/13, 12/13 sur trois passes neuves ; la vulgarisation corrigée aux trois |
| 2026-08-27 | v0.1.2 | 0 | 11/13, première passe enregistrée au journal (resservie depuis l'annuaire) |
| 2026-08-27 | v0.1.2 | 0 | 13/13, 10/13, 11/12 sur trois passes |
| 2026-08-27 | v0.1.2 | 0,2 | 11/13 sur une passe, puis 9, 11, 9 sur trois passes de contrôle |
| 2026-08-24 | v0.1.1 | 0,2 | 12/12 conformes (passe unique, 12 cas) |
