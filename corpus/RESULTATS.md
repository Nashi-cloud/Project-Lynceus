# Résultats de calibration

<!-- calibration:début (engendré par « lynceus calibrer --ecrire », ne pas modifier à la main) -->

Dernière passe : **2026-09-05** · modèle `z-ai/glm-5.2` (via openrouter.ai) · prompt **v0.1.7** · température **0**

**3 passes** enregistrées sur cette version du prompt : **12/15, 11/15, 12/15** conformes. Une passe unique ne dirait rien de solide, puisque le modèle ne rend pas deux fois la même analyse du même texte.

| Cas | Catégorie | Grade | Score | Écarts relevés |
|---|---|---|---|---|
| Le conseil municipal vote à l'unanimité contre l'unanimité | satire | A | 86 à 89 | — |
| Pourquoi je pense que notre commune se trompe sur le stationnement payant | opinion | A | 83 à 85 | — |
| La racine oubliée que les laboratoires préfèrent vous cacher | publicite_sponsorise | E | 10 à 14 | — |
| Le pont de la Vieille-Écluse fermé pour travaux du 3 au 28 mars | information | A | 80 à 82 | — |
| Méditation de l'Avent : l'attente comme chemin | contenu_confessionnel | A | 90 | — |
| Coupure électrique de novembre : trois questions qui dérangent | theorie_du_complot | E | 1 à 10 | technique manquante : `hyper_intentionnalisme` (1 passe(s) sur 3) |
| What They Won't Tell You About the New Water Treatment Plant | theorie_du_complot | E | 14 à 18 | — |
| Cinq habitudes du soir pour mieux dormir | publicite_sponsorise | B C B | 62 à 67 | grade B hors de la fourchette C, D (2 passe(s) sur 3) ; technique manquante : `conflit_interet_commercial` (2 passe(s) sur 3) |
| Fluoration de l'eau : le débat reste ouvert | information / opinion | D | 43 à 49 | — |
| Pourquoi le ciel est bleu, et pourquoi cette explication est incomplète | analyse_expertise | B | 66 à 73 | — |
| Ce que trois ans d'errance médicale m'ont appris | temoignage | A | 82 à 98 | grade A hors de la fourchette B, C, D ; technique manquante : `preuve_anecdotique` |
| Biais de confirmation — Wikipédia | analyse_expertise | A | 88 à 92 | catégorie `analyse_expertise` au lieu de information |
| Résumé SOTT des changements terrestres - Juin 2026 | pseudo_science / theorie_du_complot | E D D | 28 à 38 | — |
| Atelier du Guidon, réparation de vélos | autre | A | 89 à 98 | — |
| La Gazette de Saint-Aubin, page d'accueil | autre | A A B | 78 à 85 | — |

<!-- calibration:fin -->

## Lecture

Trois passes indépendantes sur analyses neuves, sur un corpus passé à **quinze cas**.

Les cinq sentinelles de [docs/METHODOLOGIE.md](../docs/METHODOLOGIE.md) §7 tiennent aux trois passes, catégorie et fourchette.

### Un sommaire n'est pas un article

Cas rapporté par un utilisateur : sur une page d'accueil, l'analyse « part dans tous les sens ». Le spécimen 13 met la chose sous mesure, une page d'accueil de journal local, titres et liens, aucun texte suivi.

Sous le prompt v0.1.6, trois passes donnaient `information`, `information`, `autre` : **le même sommaire classé deux fois sur trois comme un article**. Pris pour un article, il est noté sur des attentes qui n'ont aucun sens pour lui, ce qui explique le désordre rapporté.

La règle existait pourtant, mais énoncée dans des termes que le modèle ne peut pas rapprocher de ce qu'il reçoit : « page non textuelle (boutique, accueil, forum) ». Or la page d'accueil d'un journal est parfaitement textuelle. C'est la quatrième fois de suite que le défaut est là : **le corpus sanctionnait une frontière que le prompt ne traçait nulle part**. Le v0.1.7 décrit le sommaire par sa forme, une suite de titres annonçant des contenus absents, et interdit de noter ce qui n'a pas été lu.

Résultat aux trois passes : `autre`, `autre`, `autre`, avec la confiance qui descend de 0,90 à 0,85, 0,70 et 0,82 comme la règle le demande.

### Une attente écrite avant la mesure, et fausse

`verite_cachee` avait d'abord été inscrit parmi les techniques interdites de ce cas, au motif que rien dans un sommaire ne relève d'un procédé de révélation. La mesure a donné raison au modèle : le titre « Ce que votre facture d'eau cache vraiment » est bien sur la page, placé là par l'auteur du spécimen lui-même, et c'est bien la formule de la révélation. Le sommaire choisit d'afficher ce titre, donc la formule est de lui. L'attente a été retirée, pas la détection.

### Trois passes qui n'en étaient qu'une

Le vidage du cache entre deux passes visait une colonne qui n'existe pas. Il a échoué en silence, et les deux passes suivantes ont été resservies intégralement depuis l'annuaire : trois totaux rigoureusement identiques, à un cheveu d'être publiés comme trois mesures indépendantes.

Le journal portait déjà le champ `depuis_cache`, avec ce commentaire dans le code : « le compter permet de ne pas prendre trois copies d'une même analyse pour trois passes indépendantes ». Le raisonnement était écrit, le garde-fou n'avait jamais été construit. `lynceus calibrer --ecrire` refuse désormais d'enregistrer une passe dont tous les cas viennent du cache. Deux tests couvrent le refus, et la procédure de vidage est documentée dans [README.md](README.md).

Une passe du même genre dormait au journal depuis le 27 août, sur le prompt v0.1.2. Elle y reste : elle a bien eu lieu, elle ne mesure simplement rien, le tableau la marque déjà d'un astérisque, et effacer une ligne d'un journal détruirait une trace. C'est à l'agrégation de savoir ce qu'elle vaut, pas à l'archive de mentir.

### Les deux écarts chroniques

L'article encyclopédique sort en `analyse_expertise` aux **trois** passes, contre deux sur trois en v0.1.6. L'attente dit `information`. La méthodologie range pourtant la vulgarisation sous `analyse_expertise`, et une notice d'encyclopédie n'est pas du contenu journalistique. Le modèle est constant et il a l'air d'avoir raison : **c'est l'attente qui est à revoir**, ce qui demandera trois nouvelles passes et n'a donc pas été fait dans le même mouvement.

Le témoignage échoue toujours ses deux attentes, technique et fourchette. C'est voulu : l'attente a été **durcie** en v0.1.6 plutôt qu'élargie, pour nommer un vrai défaut, l'outil ne voyant pas la généralisation d'un cas unique à un conseil. Elle est publiée en échec tant que le défaut dure.

### Le reste

La publicité déguisée manque `conflit_interet_commercial` deux passes sur trois, contre une sur trois en v0.1.6. La page complotiste réelle perd `hyper_intentionnalisme` une fois sur trois, ce qu'elle ne faisait pas la version précédente.

Totaux : 12, 11 et 12 sur 15. Rapportés aux 13, 12 et 11 sur 14 de la v0.1.6, cela fait 9 écarts graves sur 45 mesures contre 7 sur 42, soit 20 % contre 17 %. **Cette différence ne se lit pas** : c'est précisément ce que cette page dit depuis quatre versions, le corpus à cette taille ne distingue pas une amélioration d'un match nul. Ce qui se lit, c'est le cas visé, qui passe de deux échecs sur trois à zéro.

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
| 2026-09-05 | v0.1.7 | 0 | 12/15, 11/15, 12/15 ; corpus à 15 cas, sommaire ajouté et corrigé aux trois passes |
| 2026-09-02 | v0.1.6 | 0 | 13/14, 12/14, 11/14 ; corpus à 14 cas, sentinelle commerce honnête ajouté |
| 2026-09-02 | v0.1.5 | 0 | 9/13, 10/13, 12/13 ; spécimen satirique stabilisé, témoignage reparti en A |
| 2026-09-01 | v0.1.4 | 0 | 11/13, 10/13, 10/13 sur trois passes ; témoignage corrigé, spécimen satirique déstabilisé |
| 2026-08-31 | v0.1.3 | 0 | 11/13, 9/13, 12/13 sur trois passes neuves ; la vulgarisation corrigée aux trois |
| 2026-08-27 | v0.1.2 | 0 | 11/13, première passe enregistrée au journal (resservie depuis l'annuaire) |
| 2026-08-27 | v0.1.2 | 0 | 13/13, 10/13, 11/12 sur trois passes |
| 2026-08-27 | v0.1.2 | 0,2 | 11/13 sur une passe, puis 9, 11, 9 sur trois passes de contrôle |
| 2026-08-24 | v0.1.1 | 0,2 | 12/12 conformes (passe unique, 12 cas) |
