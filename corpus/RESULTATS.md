# Résultats de calibration

<!-- calibration:début (engendré par « lynceus calibrer --ecrire », ne pas modifier à la main) -->

Dernière passe : **2026-09-01** · modèle `z-ai/glm-5.2` (via openrouter.ai) · prompt **v0.1.4** · température **0**

**3 passes** enregistrées sur cette version du prompt : **11/13, 10/13, 10/13** conformes. Une passe unique ne dirait rien de solide, puisque le modèle ne rend pas deux fois la même analyse du même texte.

| Cas | Catégorie | Grade | Score | Écarts relevés |
|---|---|---|---|---|
| Le conseil municipal vote à l'unanimité contre l'unanimité | satire | B D A | 38 à 85 | grade D hors de la fourchette A, B, C (1 passe(s) sur 3) |
| Pourquoi je pense que notre commune se trompe sur le stationnement payant | opinion | A | 80 à 83 | — |
| La racine oubliée que les laboratoires préfèrent vous cacher | publicite_sponsorise | E | 9 à 16 | cas non mesuré : HTTP 500 : Internal Server Error (1 passe(s) sur 3) |
| Le pont de la Vieille-Écluse fermé pour travaux du 3 au 28 mars | information | A B A | 79 à 84 | — |
| Méditation de l'Avent : l'attente comme chemin | contenu_confessionnel | B A A | 78 à 84 | — |
| Coupure électrique de novembre : trois questions qui dérangent | theorie_du_complot | E | 8 à 9 | technique manquante : `hyper_intentionnalisme` (1 passe(s) sur 3) |
| What They Won't Tell You About the New Water Treatment Plant | theorie_du_complot | E | 10 à 14 | — |
| Cinq habitudes du soir pour mieux dormir | publicite_sponsorise | C D C | 48 à 64 | technique manquante : `conflit_interet_commercial` (2 passe(s) sur 3) |
| Fluoration de l'eau : le débat reste ouvert | opinion | D | 42 à 46 | — |
| Pourquoi le ciel est bleu, et pourquoi cette explication est incomplète | analyse_expertise | B | 68 à 76 | — |
| Ce que trois ans d'errance médicale m'ont appris | temoignage | B | 66 à 74 | — |
| Biais de confirmation — Wikipédia | analyse_expertise / information | A | 90 | catégorie `analyse_expertise` au lieu de information (2 passe(s) sur 3) |
| Résumé SOTT des changements terrestres - Juin 2026 | theorie_du_complot / opinion | D D E | 29 à 40 | catégorie `opinion` au lieu de theorie_du_complot, pseudo_science (1 passe(s) sur 3) |

<!-- calibration:fin -->

## Lecture

Trois passes indépendantes sont enregistrées sur cette version du prompt, sur des analyses neuves : la mise en cache est indexée sur le couple contenu et version de prompt, et les analyses de la version en cours ont été retirées de la base entre chaque passe.

Les cinq sentinelles de [docs/METHODOLOGIE.md](../docs/METHODOLOGIE.md) §7 tiennent quant à la **catégorie** : la satire reste classée `satire`, l'opinion argumentée n'est pas pénalisée pour sa position, la pseudo-médecine marchande sort en E, l'information factuelle en A, et le contenu confessionnel reste dans sa catégorie. Le spécimen anglais est analysé en anglais.

### Ce que le prompt v0.1.4 a corrigé

Le v0.1.4 interdit à une question de présupposer, et étend la règle d'attribution à tous les textes rendus. Deux écarts installés en v0.1.3 disparaissent.

**Le témoignage rentre dans sa fourchette.** Il sortait en A deux passes sur trois, un cran trop haut ; il sort désormais en B aux trois passes, entre 66 et 74, sans aucun écart. C'est le plus net des changements, et il va dans le sens attendu : une question qui ne présuppose plus cesse d'ajouter du crédit au texte.

**La page complotiste réelle revient dans sa catégorie** deux passes sur trois, contre `opinion` deux passes sur trois en v0.1.3.

### Ce qu'il a dégradé, et qu'il faut dire aussi

**Le spécimen satirique s'est déstabilisé.** Il tenait en A entre 85 et 100 sous v0.1.3 ; il oscille maintenant entre 38 et 85 et sort en D une passe sur trois. La catégorie tient, donc la sentinelle du §7 n'est pas en cause, mais un texte parodique noté D est une erreur qu'un lecteur voit immédiatement. C'est le point à surveiller en priorité sur la prochaine version.

**La publicité déguisée ne fait plus détecter `conflit_interet_commercial`** deux passes sur trois, alors que c'est la technique attendue et le trait définitoire du cas. **L'article encyclopédique bascule en `analyse_expertise`** deux passes sur trois au lieu d'une.

### Ce que trois passes n'établissent toujours pas

Les totaux sont 11, 10 et 10 sur 13, contre 11, 9 et 12 en v0.1.3. Indiscernables. La conclusion tirée la dernière fois vaut telle quelle : à treize cas et à cette dispersion, une différence de deux conformités n'est pas un signal. Ce qui se lit, ce sont les cas pris un par un, et l'accord ou non des trois passes sur chacun.

Une passe a rendu une erreur HTTP 500 sur un cas, marqué « non mesuré » plutôt que compté conforme, ce qui est le bon comportement. L'erreur n'a pas été reproduite. L'hypothèse la plus probable est un verrou SQLite sous quatre analyses simultanées, la base de développement étant en SQLite alors que la production tourne sur PostgreSQL ; elle n'est pas vérifiée.

### Une barrière ajoutée, et une mesure qui a échoué

Le serveur vérifie désormais **toute citation entre guillemets**, où qu'elle apparaisse, et plus seulement dans une détection. Les champs libres échappaient à tout contrôle. Le rapport de calibration ne compte pas encore ces rejets, donc leur taux reste à mesurer sur des pages réelles.

Une attente de corpus a été essayée pour mesurer ce que la barrière ne couvre pas, une liste de termes que l'analyse ne devait pas employer parce que le spécimen ne les emploie pas. Elle a été **retirée après une passe**, où elle a signalé « Le produit est-il évalué ou certifié par des autorités de santé compétentes ? » sur la page de pseudo-médecine. C'est une bonne question socratique, générique, qui n'affirme rien. Un contrôle lexical ne distingue pas une question qui interroge d'une question qui présuppose, et garder une attente fausse aurait été pire que de n'en avoir aucune. La règle d'attribution reste donc contrainte par le prompt et non mesurée, ce que [docs/METHODOLOGIE.md](../docs/METHODOLOGIE.md) §3 dit désormais explicitement.

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
| 2026-09-01 | v0.1.4 | 0 | 11/13, 10/13, 10/13 sur trois passes ; témoignage corrigé, spécimen satirique déstabilisé |
| 2026-08-31 | v0.1.3 | 0 | 11/13, 9/13, 12/13 sur trois passes neuves ; la vulgarisation corrigée aux trois |
| 2026-08-27 | v0.1.2 | 0 | 11/13, première passe enregistrée au journal (resservie depuis l'annuaire) |
| 2026-08-27 | v0.1.2 | 0 | 13/13, 10/13, 11/12 sur trois passes |
| 2026-08-27 | v0.1.2 | 0,2 | 11/13 sur une passe, puis 9, 11, 9 sur trois passes de contrôle |
| 2026-08-24 | v0.1.1 | 0,2 | 12/12 conformes (passe unique, 12 cas) |
