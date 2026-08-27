# Résultats de calibration

Dernière passe : **2026-08-27** · modèle `z-ai/glm-5.2` (via OpenRouter) · prompt **v0.1.2** · température **0**

**Trois passes**, sur une base neuve à chaque fois pour contourner le cache : **13/13**, **10/13** et **11/12** conformes. Une passe unique ne dirait rien de solide, puisque le modèle ne rend pas deux fois la même analyse du même texte.

| Cas | Catégorie | Grade | Score | Écarts relevés |
|---|---|---|---|---|
| Le conseil municipal vote à l'unanimité contre l'unanimité | satire | A | 91 à 98 | — |
| Pourquoi je pense que notre commune se trompe | opinion | A | 82 à 87 | — |
| La racine oubliée que les laboratoires préfèrent vous cacher | publicite_sponsorise | E | 7 à 14 | — |
| Le pont de la Vieille-Écluse fermé pour travaux | information | A | 80 à 86 | — |
| Méditation de l'Avent : l'attente comme chemin | contenu_confessionnel | A | 82 à 89 | — |
| Coupure électrique de novembre : trois questions qui dérangent | theorie_du_complot | E | 8 à 12 | — |
| *What They Won't Tell You About the New Water Treatment Plant* (anglais) | opinion / theorie_du_complot | E | 10 à 11 | catégorie `opinion` sur une passe |
| Cinq habitudes du soir pour mieux dormir | publicite_sponsorise | C | 61 à 64 | technique manquante sur une passe : `conflit_interet_commercial` |
| Fluoration de l'eau : le débat reste ouvert | information / opinion | D D C | 46 à 52 | — |
| Pourquoi le ciel est bleu, et pourquoi cette explication est incomplète | analyse_expertise | B C B | 64 à 75 | grade C hors fourchette sur une passe |
| Ce que trois ans d'errance médicale m'ont appris | temoignage | C | 55 à 63 | — |
| *Wikipédia — Biais de confirmation* (réel) | information | A | 89 à 93 | — |
| *SOTT — Changements terrestres* (réel) | theorie_du_complot / opinion | D | 30 à 32 | catégorie `opinion` sur une passe ; page injoignable sur une autre |

## Lecture

Les six sentinelles de [docs/METHODOLOGIE.md](../docs/METHODOLOGIE.md) §7 passent sur les trois passes :

- **Satire** classée `satire`, jamais comme désinformation.
- **Opinion argumentée** non pénalisée pour sa position (grade A).
- **Pseudo-médecine marchande** : grade E et conflit d'intérêt commercial détecté.
- **Information factuelle** bien notée, sans détection de complaisance.
- **Contenu confessionnel** : aucune technique relevée, la foi n'est pas notée.
- **Page en anglais** : analyse rédigée en anglais, mêmes procédés détectés que sur le spécimen français équivalent.

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

| Date | Prompt | Température | Résultat |
|---|---|---|---|
| 2026-08-27 | v0.1.2 | 0 | 13/13, 10/13, 11/12 sur trois passes |
| 2026-08-27 | v0.1.2 | 0,2 | 11/13 sur une passe, puis 9, 11, 9 sur trois passes de contrôle |
| 2026-08-24 | v0.1.1 | 0,2 | 12/12 conformes (passe unique, 12 cas) |
