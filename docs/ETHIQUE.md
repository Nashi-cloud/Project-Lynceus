# Charte éthique de Lynceus

Cette charte est contraignante : toute fonctionnalité, tout prompt, toute décision de conception doit pouvoir s'y référer. Elle est versionnée avec le code — la modifier est un acte public.

## 1. Une vigie, pas un juge

Lynceus **décrit des méthodes**, il ne juge pas des personnes ni des croyances.

- On signale « ce texte emploie l'appel à la peur, voici l'extrait » — jamais « ce site ment » ni « vous avez tort d'y croire ».
- La **foi religieuse et les convictions personnelles ne sont pas notées**. Sont évaluées : les affirmations factuelles vérifiables (« ce remède guérit le cancer ») et les techniques de manipulation (peur, urgence, isolement « eux contre nous »), quelle que soit la tradition ou l'idéologie qui les emploie.
- Le lecteur tire ses conclusions lui-même. L'objectif est l'autonomie intellectuelle (théorie de l'inoculation), pas l'adhésion à un verdict.

## 2. Transparence radicale

On ne peut pas dénoncer l'opacité en étant opaque.

- Les **prompts d'analyse sont publics et versionnés** dans ce dépôt ([prompts/](../prompts/)).
- La **méthodologie, les pondérations et le barème** sont publiés ([METHODOLOGIE.md](METHODOLOGIE.md)).
- Chaque carte d'analyse indique le modèle utilisé, la version du prompt et l'indice de confiance.
- Licence AGPL-3.0 : toute instance publique modifiée doit publier ses sources.

## 3. Le scan est volontaire

- **Aucune page n'est analysée à l'insu de l'utilisateur.** L'analyse (envoi du contenu) est toujours déclenchée par un geste explicite.
- Le badge passif (consultation de l'annuaire) n'envoie qu'un hash d'URL, jamais de contenu, et **peut être désactivé** dans les réglages.
- Le panneau latéral ne s'ouvre jamais tout seul. Aucune notification anxiogène, aucun blocage de page : Lynceus informe, il n'empêche rien.

## 4. Vie privée

- **Le serveur ne stocke aucun historique de navigation.** Les lookups ne sont pas journalisés avec des identifiants (pas de couple IP + URL conservé).
- Pas de compte requis, pas de traceur, pas de télémétrie cachée.
- Le lookup passif fonctionne **en k-anonymat** (technique HaveIBeenPwned) : seuls les 5 premiers caractères du hash d'URL sont envoyés, et la correspondance finale est faite dans le navigateur. Le serveur ne peut pas déterminer quelle page est consultée. Le mode historique (hash complet) ne subsiste que pour les instances qui n'annoncent pas cette capacité.
- L'auto-hébergement complet est un droit de premier ordre : le « kit » serveur est un livrable du projet, pas une option de second rang.

## 5. Équité de l'analyse

- **La satire n'est pas de la désinformation.** Un contenu satirique est catégorisé comme tel, avec un simple avertissement de second degré. (Le crash-test permanent : ne jamais classer un site parodique en « fake news ».)
- **Une opinion assumée n'est pas une manipulation.** Un éditorial est évalué sur son honnêteté argumentative et sa transparence, pas sur sa position.
- **Les points positifs sont systématiquement recherchés** et affichés. Une analyse qui ne saurait dire que du mal perd toute crédibilité auprès de ceux qu'elle veut aider.
- Les extraits cités sont **verbatim** : aucune technique n'est rapportée sans citation exacte de la page.

## 6. Faillibilité assumée

- L'analyse est produite par un modèle de langage : **elle peut se tromper**. Chaque carte affiche un indice de confiance et cet avertissement.
- Toute analyse est **contestable** depuis le panneau ou l'API (`POST /v1/signalements`), y compris par les éditeurs des sites analysés (motif `droit_de_reponse`). Un signalement est anonyme par défaut : aucune donnée personnelle n'est exigée. Le nombre de contestations est public sur chaque analyse.
- Les analyses sont datées et re-générables : un site qui s'améliore verra sa carte évoluer.

## 7. Pédagogie plutôt que verdict

- Vocabulaire descriptif (« signaux de prudence », « techniques relevées ») — jamais de « FAKE NEWS », d'emoji poubelle, de rouge criard accusateur.
- Chaque technique détectée est accompagnée d'une **explication du mécanisme psychologique** : c'est l'apprentissage du procédé qui immunise, pas l'étiquette.
- Des **« questions à se poser »** accompagnent chaque carte : le lecteur reste l'enquêteur.

## 8. Indépendance

- Pas de publicité, pas de vente de données, jamais.
- Financement (hébergement de l'instance de référence, coûts d'inférence) transparent et publié.
- Aucun traitement de faveur : la méthodologie s'applique identiquement à tous les contenus, quelle que soit leur orientation.

## 9. Cadre juridique

Lynceus publie des **évaluations méthodologiquement fondées de contenus publics** — le terrain établi des initiatives d'éducation aux médias (Décodex, NewsGuard, fact-checkers IFCN). Trois garde-fous : méthodologie publiée, extraits cités verbatim, droit de réponse. Les cartes portent sur des contenus et des procédés, pas sur des personnes.

## Références

- *The Debunking Handbook 2020* — Lewandowsky, Cook et al.
- Sander van der Linden, *Foolproof* (2023) — théorie de l'inoculation / prebunking.
- John Cook — taxonomie FLICC (Fake experts, Logical fallacies, Impossible expectations, Cherry picking, Conspiracy theories).
- First Draft — typologie des désordres de l'information (Wardle & Derakhshan).
