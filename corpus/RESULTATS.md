# Résultats de calibration

Dernière passe : **2026-08-24** · modèle `z-ai/glm-5.2` (via OpenRouter) · prompt **v0.1.1**

**10/10 conformes** — 0 écart mineur, 0 échec grave.

| Cas | Catégorie | Grade | Techniques détectées |
|---|---|---|---|
| Le conseil municipal vote à l'unanimité contre l'una | satire | **B** (68) | — |
| Pourquoi je pense que notre commune se trompe sur le | opinion | **A** (84) | — |
| La racine oubliée que les laboratoires préfèrent vou | publicite_sponsorise | **E** (6) | `verite_cachee`, `autorite_anonyme`, `eux_contre_nous`, `preuve_anecdotique`, `solution_miracle`, `appel_a_la_nature`, `conflit_interet_commercial`, `urgence_artificielle` |
| Le pont de la Vieille-Écluse fermé pour travaux du 3 | information | **A** (85) | — |
| Méditation de l'Avent : l'attente comme chemin | contenu_confessionnel | **A** (89) | — |
| Coupure électrique de novembre : trois questions qui | theorie_du_complot | **E** (8) | `je_pose_des_questions`, `eux_contre_nous`, `verite_cachee`, `heros_persecute`, `hyper_intentionnalisme`, `correlation_causation`, `absence_de_sources` |
| Cinq habitudes du soir pour mieux dormir | publicite_sponsorise | **C** (52) | `autorite_anonyme`, `conflit_interet_commercial` |
| Fluoration de l'eau : le débat reste ouvert | information | **D** (39) | `faux_equilibre`, `attentes_impossibles`, `je_pose_des_questions` |
| Pourquoi le ciel est bleu, et pourquoi cette explica | analyse_expertise | **B** (71) | — |
| Ce que trois ans d'errance médicale m'ont appris | temoignage | **B** (74) | — |

## Lecture

Les cinq sentinelles de [docs/METHODOLOGIE.md](../docs/METHODOLOGIE.md) §7 passent :

- **Satire** classée `satire`, jamais comme désinformation.
- **Opinion argumentée** non pénalisée pour sa position (grade A).
- **Pseudo-médecine marchande** : grade E et conflit d'intérêt commercial détecté.
- **Information factuelle** bien notée, sans détection de complaisance.
- **Contenu confessionnel** : aucune technique relevée, la foi n'est pas notée.

Deux pièges plus difficiles sont également réussis :

- le **faux équilibre** (ton posé, apparence neutre) est classé D malgré sa forme journalistique ;
- la **vulgarisation scientifique** dense n'écope d'aucun faux positif `jargon_pseudo_scientifique`.

## Historique des ajustements du corpus

Première passe (même modèle, même prompt) : 7/10, dont un échec sur la catégorie de la
pseudo-médecine marchande, classée `publicite_sponsorise` au lieu de `pseudo_science`.
Après examen, l'analyse était défendable — le texte est simultanément les deux — et c'est
l'attente du corpus qui était trop rigide. Le format accepte désormais
`categories_acceptables` pour les contenus hybrides ; les exigences sur les techniques et
les grades sont restées inchangées. Les deux écarts mineurs (grade A obtenu là où B–C
était attendu, sur des textes irréprochables) ont conduit à élargir ces fourchettes.

> Un corpus qu'on ajuste jusqu'à ce que tout passe ne mesure plus rien. Chaque
> assouplissement doit être justifié par un examen du cas, et jamais porter sur les
> techniques attendues ou interdites — le cœur du test.
