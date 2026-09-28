# Résultats de calibration

<!-- calibration:début (engendré par « lynceus calibrer --ecrire », ne pas modifier à la main) -->

Dernière passe : **2026-09-28** · modèle `z-ai/glm-5.3` (via openrouter.ai) · prompt **v0.1.8** · température **0** · raisonnement **low** · hébergeur **mistral**

**3 passes** enregistrées sur cette version du prompt : **13/15, 13/15, 12/15** conformes. Une passe unique ne dirait rien de solide, puisque le modèle ne rend pas deux fois la même analyse du même texte.

| Cas | Catégorie | Grade | Score | Écarts relevés |
|---|---|---|---|---|
| Le conseil municipal vote à l'unanimité contre l'unanimité | satire | A | 90 | — |
| Pourquoi je pense que notre commune se trompe sur le stationnement payant | opinion | A | 86 à 89 | — |
| La racine oubliée que les laboratoires préfèrent vous cacher | publicite_sponsorise | E | 14 à 16 | technique manquante : `solution_miracle` (1 passe(s) sur 3) |
| Le pont de la Vieille-Écluse fermé pour travaux du 3 au 28 mars | information | A | 80 à 82 | — |
| Méditation de l'Avent : l'attente comme chemin | contenu_confessionnel | A | 89 | — |
| Coupure électrique de novembre : trois questions qui dérangent | theorie_du_complot | E | 10 à 11 | — |
| What They Won't Tell You About the New Water Treatment Plant | theorie_du_complot | E | 19 à 20 | — |
| Cinq habitudes du soir pour mieux dormir | publicite_sponsorise | C | 56 à 58 | — |
| Fluoration de l'eau : le débat reste ouvert | information | C | 60 à 64 | — |
| Pourquoi le ciel est bleu, et pourquoi cette explication est incomplète | analyse_expertise | A B B | 74 à 80 | — |
| Ce que trois ans d'errance médicale m'ont appris | temoignage | A | 82 à 86 | grade A hors de la fourchette B, C, D ; technique manquante : `preuve_anecdotique` |
| Biais de confirmation — Wikipédia | analyse_expertise | A | 89 | — |
| Résumé SOTT des changements terrestres - Juin 2026 | pseudo_science / opinion | D | 34 à 40 | technique manquante : `verite_cachee` ; catégorie `opinion` au lieu de theorie_du_complot, pseudo_science (1 passe(s) sur 3) |
| Atelier du Guidon, réparation de vélos | publicite_sponsorise | A | 92 | — |
| La Gazette de Saint-Aubin, page d'accueil | autre | A | 80 à 84 | — |

<!-- calibration:fin -->

## Lecture

### GLM-5.3 en raisonnement « low », servi par Mistral (2026-09-28)

Même prompt v0.1.8, mêmes quinze cas, autre modèle et autre réglage : GLM-5.3 au lieu de GLM-5.2, raisonnement réglé sur « low » au lieu du défaut du fournisseur, et un hébergeur imposé sans repli, au lieu de celui que le routeur choisit à chaque appel. Le tableau ci-dessus porte sur ces trois passes ; celles de GLM-5.2, décrites plus bas, restent au journal.

**La conformité ne bouge pas**, 13/15, 13/15, 12/15 contre 12/15, 11/15, 13/15 : à cette taille de corpus, la différence ne se lit pas. La page en anglais est rendue en anglais aux trois passes.

**La stabilité, elle, progresse nettement.** Mesurée entre les passes avec `lynceus mesurer`, sur 45 comparaisons :

| Entre deux passes | GLM-5.2, défauts | GLM-5.3 « low », Mistral |
|---|---|---|
| Même catégorie | 87 % | 96 % |
| Même grade | 82 % | 96 % |
| Techniques en commun (Jaccard) | 0,87 | 0,92 |
| Écart de score moyen | 3,8 points | 1,6 point |
| Écart de score maximal | 10 points | 6 points |

Le raisonnement « low » y est sans doute pour beaucoup : un modèle qui pense peu dévie peu. L'hébergeur imposé aussi, puisque le routeur servait auparavant le même modèle en fp8 ou en fp4 selon l'appel.

**Le coût baisse d'environ 70 %.** Les trois passes ont coûté 0,18 $, soit 0,4 centime par analyse, le prompt système étant relu depuis le cache de l'hébergeur. Mesurées sur trois spécimens avec les réglages précédents, les analyses coûtaient de 0,9 à 2,2 centimes.

**Pourquoi Mistral.** L'hébergeur officiel du modèle, Z.AI, a été essayé d'abord : il refuse la capture SOTT et rend une réponse vide, raison « sensitive », aux six passes où il l'a reçue. Un hébergeur qui filtre des contenus ne convient pas à un outil qui doit pouvoir les analyser tous. Neuf autres hébergeurs ont analysé la même page. Mistral a été retenu parce que c'est une entreprise européenne, sans conservation des données sur ce point d'accès. Cela ne supprime pas le transfert que [docs/ETHIQUE.md](../docs/ETHIQUE.md) oblige à nommer : le texte passe toujours par OpenRouter, établi aux États-Unis, avant d'arriver chez Mistral. Seul un appel direct à un hébergeur européen le supprimerait. Son prix de base est parmi les plus élevés, mais son cache le rend parmi les moins chers à l'usage.

**Ce qui reste.** Le témoignage manque toujours `preuve_anecdotique` et sort en A, comme sous GLM-5.2. Le résumé SOTT manque `verite_cachee` aux trois passes, et sort une fois en `opinion`. La sentinelle pseudo-médicale détecte le conflit d'intérêt aux trois passes, mais manque `solution_miracle` une fois.

### Le prompt v0.1.8 sous GLM-5.2

Trois passes indépendantes sur analyses neuves, sur les **quinze cas** de la version précédente, attentes inchangées.

Les sentinelles de [docs/METHODOLOGIE.md](../docs/METHODOLOGIE.md) §7 tiennent aux trois passes, catégorie et fourchette, **sauf une** : la page en anglais a reçu deux fois sur trois une analyse rédigée en français. Ce n'était jamais arrivé dans aucune passe enregistrée. Quatre tirages de contrôle faits aussitôt sur ce seul cas l'ont rendue en anglais aux trois tirages aboutis, le quatrième ayant échoué au transport, et quatre tirages sous v0.1.7 aussi. Rien dans le v0.1.8 ne touche à la langue. L'écart reste consigné tel quel : c'est à la prochaine mesure de dire s'il revient.

Un remède a été essayé puis écarté. Le prompt et le cadre du message sont en français, seule la page est en anglais : une ligne rappelant la langue de rédaction, placée après le contenu, a rendu l'analyse en anglais aux six tirages, mais la catégorie est passée à `opinion` cinq fois sur six. Cinq tirages sous v0.1.8 le même jour donnaient `theorie_du_complot` et l'anglais aux cinq. Une variante plus discrète, la langue de rédaction dans l'en-tête, donnait encore `opinion` deux fois sur cinq. Le rappel corrigeait un écart qui ne se reproduisait pas au prix d'un écart qui se reproduisait : il n'a pas été retenu. L'essai est gardé sur la branche `feat/prompt-0.1.9`.

### Vendre n'est pas un procédé (v0.1.8)

La définition de `conflit_interet_commercial` ne couvrait qu'un « discours alarmiste ou miraculeux » dont l'auteur tire profit. Le spécimen 08, des conseils de sommeil qui débouchent sur un matelas avec lien partenaire signalé, n'a rien d'alarmiste : le modèle le détectait en débordant la définition, **onze fois sur dix-huit** depuis le v0.1.3, et rien ne lui disait où s'arrêter.

La définition a d'abord été réécrite seule, pour nommer les deux cas, le déguisement et la peur ou le miracle qui poussent à l'achat. Mesurée sur treize tirages du spécimen 08, elle a fait **pire** : quatre détections sur treize, et la catégorie retombait en `information` ou `opinion` une fois sur deux. La justification du modèle disait pourquoi : le partenariat étant « explicitement signalé, ce qui est louable », il n'y avait selon lui plus rien à signaler. Un cas particulier du prompt dit donc en toutes lettres que **la mention du partenariat modère la gravité sans retirer la détection**, et que le procédé s'extrait du passage qui recommande le produit.

Résultat sur six tirages ciblés : détection cinq fois sur six, `publicite_sponsorise` six fois sur six, grade C à chaque fois, soit dans la fourchette C à D que le cas attendait et qu'il manquait en v0.1.7. Puis aux trois passes complètes : détection trois fois sur trois. La contre-épreuve tient : le commerce honnête (spécimen 12), qui s'annonce comme commercial et ne fait que décrire ses services, ne reçoit la détection à aucun des six tirages où il a été mesuré.

Les totaux, 12/15, 11/15, 13/15 contre 12/15, 11/15, 12/15, ne se distinguent pas, et il ne faut pas leur faire dire plus. Ce qui se lit est le cas visé.

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
| 2026-09-28 | v0.1.8 | 0 | 13/15, 13/15, 12/15 ; GLM-5.3 « low » servi par Mistral, bien plus stable entre passes, 70 % moins cher |
| 2026-09-25 | v0.1.8 | 0 | 12/15, 11/15, 13/15 ; conseil sponsorisé détecté aux trois passes, page anglaise rendue deux fois en français |
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
