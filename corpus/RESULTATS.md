# Résultats de calibration

Dernière passe : **2026-08-27** · modèle `z-ai/glm-5.2` (via OpenRouter) · prompt **v0.1.2**

**11/13 conformes** — 1 écart mineur, 1 échec grave. Dont **2 pages réelles capturées** et **1 spécimen en anglais** ; les 10 autres sont des spécimens écrits pour l'exercice.

| Cas | Catégorie | Grade | Techniques détectées |
|---|---|---|---|
| Le conseil municipal vote à l'unanimité contre l'una | satire | **A** (88) | — |
| Pourquoi je pense que notre commune se trompe sur le | opinion | **A** (84) | — |
| La racine oubliée que les laboratoires préfèrent vou | publicite_sponsorise | **E** (7) | `verite_cachee`, `eux_contre_nous`, `autorite_anonyme`, `preuve_anecdotique`, `solution_miracle`, `proces_d_intention`, `conflit_interet_commercial`, `urgence_artificielle` |
| Le pont de la Vieille-Écluse fermé pour travaux du 3 | information | **A** (84) | — |
| Méditation de l'Avent : l'attente comme chemin | contenu_confessionnel | **C** (57) | — |
| Coupure électrique de novembre : trois questions qui | theorie_du_complot | **E** (9) | `je_pose_des_questions`, `correlation_causation`, `hyper_intentionnalisme`, `eux_contre_nous`, `verite_cachee`, `heros_persecute`, `urgence_artificielle` |
| *What They Won't Tell You About the New Water Treatment Plant* (anglais) | theorie_du_complot | **E** (2) | `verite_cachee`, `autorite_anonyme`, `je_pose_des_questions`, `eux_contre_nous`, `heros_persecute`, `urgence_artificielle` |
| Cinq habitudes du soir pour mieux dormir | publicite_sponsorise | **B** (66) | `conflit_interet_commercial` |
| Fluoration de l'eau : le débat reste ouvert | opinion | **D** (40) | `faux_equilibre`, `attentes_impossibles`, `je_pose_des_questions`, `absence_de_sources` |
| Pourquoi le ciel est bleu, et pourquoi cette explica | information | **B** (70) | — |
| Ce que trois ans d'errance médicale m'ont appris | temoignage | **C** (60) | — |
| *Wikipédia — Biais de confirmation* (réel) | information | **A** (92) | — |
| *SOTT — Changements terrestres* (réel) | pseudo_science | **D** (30) | `cherry_picking`, `eux_contre_nous`, `verite_cachee`, `millefeuille_argumentatif`, `absence_de_sources`, `proces_d_intention`, `conflit_interet_commercial`, `appel_a_la_peur` |

## Lecture

Les six sentinelles de [docs/METHODOLOGIE.md](../docs/METHODOLOGIE.md) §7 passent :

- **Satire** classée `satire`, jamais comme désinformation.
- **Opinion argumentée** non pénalisée pour sa position (grade A).
- **Pseudo-médecine marchande** : grade E et conflit d'intérêt commercial détecté.
- **Information factuelle** bien notée, sans détection de complaisance.
- **Contenu confessionnel** : aucune technique relevée, la foi n'est pas notée.
- **Page en anglais** : analyse rédigée en anglais, mêmes procédés détectés que sur le spécimen français équivalent.

## Les deux écarts

**Échec grave.** « Pourquoi le ciel est bleu » classé `information` au lieu de `analyse_expertise`. La catégorie attendue n'est pas arbitraire : le texte est une vulgarisation qui expose ses limites, ce qui est le propre de l'analyse experte.

**Écart mineur.** « Cinq habitudes du soir » noté B (66) alors qu'un publireportage doit tomber en C ou D.

Ces deux cas ont été rejoués, et c'est ce qui les rend intéressants :

| Cas | Prompt v0.1.1 (passe du 24 août) | v0.1.2, passe complète | v0.1.2, rejoué sur base neuve |
|---|---|---|---|
| Le ciel est bleu | `analyse_expertise` B (71) | `information` B (70) | `analyse_expertise` B |
| Cinq habitudes | `publicite_sponsorise` C (52) | B (66), technique détectée | B (73), technique **non** détectée |

Aucun des deux n'est stable d'une passe à l'autre. Le modèle est interrogé à température 0,2 : deux analyses du même texte ne sont pas identiques, et ces deux cas sont proches d'une frontière (vulgarisation ou analyse experte ; publireportage assumé ou conseil pratique). L'écart ne s'explique donc pas par le passage à v0.1.2.

Ce n'est pas une raison de le classer sans suite. Deux choses en découlent, et elles sont ouvertes :

1. **Mesurer l'instabilité plutôt que la subir** : rejouer le corpus plusieurs fois et publier la dispersion, pas seulement un tirage. Une note qui change d'un cran d'une analyse à l'autre est une information que l'utilisateur mérite.
2. **Abaisser la température à 0** rendrait les analyses plus reproductibles, au prix d'une éventuelle rigidité. Le paramètre existe déjà par instance (`LYNCEUS_LLM_TEMPERATURE`), le défaut n'est pas tranché.

Conformément à la règle du corpus, aucune attente n'a été assouplie pour faire passer ces deux cas.

## Historique

| Date | Prompt | Résultat |
|---|---|---|
| 2026-08-27 | v0.1.2 | 11/13 conformes, 1 mineur, 1 grave (13 cas, dont un en anglais) |
| 2026-08-24 | v0.1.1 | 12/12 conformes |
