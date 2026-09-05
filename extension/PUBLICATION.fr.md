# Publier l'extension sur un magasin

<!-- traduit-de: extension/PUBLICATION.md sha256:973b0fa7b759b935 -->

Tout ce qu'il faut pour soumettre cette extension au Chrome Web Store, et les décisions qui
donnent sa forme à la soumission. Les étapes qui exigent un compte, un paiement ou une capture
d'écran se font à la main, et sont signalées comme telles.

## Les décisions, avant la paperasse

**Non répertorié d'abord.** La fiche est publiée mais n'apparaît pas dans les recherches : on y
accède par lien. C'est proportionné à un public d'une poignée de personnes et à un outil qui
n'a jamais été diffusé. La mise à jour automatique, qui est tout l'intérêt d'un magasin,
fonctionne exactement pareil pour une fiche non répertoriée. Passer en public plus tard tient
en un réglage.

**Le magasin s'ajoute, il ne remplace pas.** Un magasin est un goulot tenu par une seule
entreprise. Pour un outil qui note publiquement des pages, et commente donc des éditeurs, un
retrait n'est pas une hypothèse d'école et le recours n'existe pas vraiment. `/telecharger` sur
le portail reste la voie de secours documentée, et le kit d'auto-hébergement ne dépend jamais
d'un magasin.

**Une adresse de portail est inscrite en dur, et c'est une vraie concession.** L'image publiée
embarque un paquet *neutre*, et le portail qui le sert y glisse sa propre adresse dans
`portail.json` au moment du téléchargement. C'est ce qui permet à quiconque de déployer la même
image sans privilégier aucune instance. Un paquet de magasin ne peut pas faire cela : c'est un
fichier unique et immuable pour tous, il doit donc porter une adresse, et cette adresse est
`https://lynx.nashi.cloud`. Tout utilisateur qui ne change pas le réglage enverra donc le
contenu des pages à cette instance. C'est modifiable dans les réglages, le code est public, et
les auto-hébergeurs gardent la voie du portail. Cela reste une centralisation, elle est
délibérée, et elle est écrite ici pour qu'on ne la prenne pas pour un accident.

## D'où vient le paquet

**Le prendre sur la publication GitHub, pas d'une construction locale.** Pousser un tag
`vX.Y.Z` fait construire les deux paquets par la forge et les attache à la publication
(`.github/workflows/paquet.yml`) :

| Fichier | Ce qu'il contient |
|---|---|
| `lynceus-extension-vX.Y.Z.zip` | Neutre, aucune adresse de portail. C'est ce que l'image embarque, et ce que chaque portail sert après y avoir glissé sa propre adresse. |
| `lynceus-extension-vX.Y.Z-magasin.zip` | L'adresse compilée dedans, prise dans la variable de dépôt `PORTAIL_MAGASIN`. **C'est celui à déposer sur le magasin.** |

Un paquet construit sur le poste d'un mainteneur n'a aucune provenance, ce qui est une piètre
propriété pour un fichier qu'un magasin distribue ensuite à tous les utilisateurs. Le faire
construire par la forge lui donne la même provenance que l'image.

Les deux archives sont **reproductibles** : les horodatages sont figés, donc les mêmes sources
donnent un fichier identique à l'octet près, et `SHA256SUMS.txt` est attaché à côté.
`--portail=` fait partie des sources de ce point de vue : sans le même drapeau, l'empreinte
diffère légitimement. Pour vérifier le paquet de magasin à la main :

```bash
cd extension && npm ci
node build.mjs --paquet --portail=https://lynx.nashi.cloud
```

Reconstruire `dist/` sans le drapeau ensuite (`npm run build`), pour que l'extension chargée
localement revienne à ne proposer aucun portail.

## Champs de la fiche

Le nom et la description courte sont **déjà bilingues** et ne demandent aucune saisie : le
manifeste pointe vers `__MSG_nom_extension__` et `__MSG_description_extension__`, et le magasin
lit les catalogues de `src/_locales/`. Leur longueur est vérifiée par
`test/identite.test.mjs`, le magasin tronquant un nom au-delà de 75 caractères et refusant une
description au-delà de 132.

**Catégorie** : Éducation. L'outil apprend à lire une page, il ne filtre ni ne bloque.

**Objet unique**, à déclarer dans le formulaire :

> Analyser la page web que l'utilisateur soumet explicitement, noter sa fiabilité, et expliquer
> les procédés de persuasion qu'elle emploie.

**Description détaillée**, en français :

> Lynceus analyse la page web que vous lui demandez d'analyser, et explique les procédés de
> persuasion qu'elle emploie. Il décrit des méthodes, jamais des personnes ni des croyances, et
> il cite la page mot pour mot pour chaque procédé qu'il signale.
>
> C'est vous qui lancez l'analyse, par un clic droit puis « Analyser cette page avec Lynceus ».
> Rien n'est envoyé sans ce geste. La page est transformée en texte dans votre navigateur avant
> que quoi que ce soit en sorte : ce qui circule, c'est l'article, pas votre session.
>
> La carte d'analyse donne un indice de A à E, quatre scores (sources, factualité, ton,
> transparence), les procédés relevés avec la citation exacte qui les appuie, ce que la page
> fait bien, et des questions que vous pouvez vous poser sur n'importe quelle page.
>
> Tout est public et vérifiable : le prompt d'analyse, le référentiel des procédés, la
> méthodologie, et les chiffres de calibration avec leurs échecs, sont publiés sur le portail.
> Le code est libre sous AGPL-3.0, et l'ensemble s'auto-héberge, auquel cas l'extension parle à
> votre propre instance et aucune clé n'est nécessaire.
>
> Gratuit, sans compte, sans adresse électronique, sans publicité, sans pistage.

**URL de politique de confidentialité** : `https://lynx.nashi.cloud/confidentialite`

## Justification des permissions

Le formulaire demande une phrase par permission. Celles-ci sont exactes, ce qui compte plus que
d'être brèves : une justification qui en promet trop est ce qui fait refuser une soumission.

| Permission | Justification |
|---|---|
| `activeTab` | Lire la page courante uniquement au moment où l'utilisateur demande explicitement une analyse, depuis le menu contextuel ou le bouton du panneau. N'accorde rien avant ce geste, ni rien sur les autres onglets. |
| `scripting` | Injecter le script d'extraction dans la page analysée, qui la transforme en texte localement avec Readability, et poser un contour coloré sur une page notée D ou E. Tout le code injecté est livré dans le paquet. |
| `contextMenus` | Ajouter l'entrée « Analyser cette page avec Lynceus », qui est la façon principale de lancer une analyse. |
| `sidePanel` | Afficher la carte d'analyse. Le panneau ne s'ouvre jamais tout seul. |
| `storage` | Conserver les réglages : l'adresse de l'instance, la clé d'accès, et l'activation du badge passif. `storage.sync` pour que les réglages suivent le profil du navigateur. |
| `tabs` (optionnelle) | Lire l'adresse de l'onglet courant afin que le badge de la barre d'outils affiche un indice déjà connu pour cette page. Demandée seulement si l'utilisateur active le badge, refusable, et l'extension reste pleinement utilisable sans elle. |
| Permissions d'hôte (optionnelles) | Permettre au badge de voir l'adresse après une navigation interne, sans nouveau geste de l'utilisateur, et permettre de poser le contour. Désactivées par défaut, demandées avec le badge dans les réglages, révocables depuis Chrome. |

## Déclaration d'usage des données

Répondre honnêtement au formulaire. C'est la sous-déclaration qui fait retirer une extension.

- **Contenu de site web : oui.** Le texte d'une page est envoyé à l'instance configurée, en
  Markdown, et seulement après que l'utilisateur a explicitement demandé l'analyse de cette
  page.
- **Historique de navigation : oui.** Avec le badge passif activé, l'extension envoie une
  empreinte SHA-256 de l'adresse normalisée, ou seulement ses cinq premiers caractères quand
  l'instance sait faire le lookup k-anonyme, pour savoir si la page est déjà dans l'annuaire.
  L'adresse elle-même n'est jamais envoyée. Le déclarer est la lecture honnête, même si
  l'empreinte est conçue pour ne pas identifier la page.
- **Tout le reste : non.** Pas de nom, pas d'adresse électronique, pas de compte, pas de
  localisation, pas de donnée financière, pas de communication personnelle, pas de mesure
  d'audience, pas d'identifiant publicitaire. La clé d'accès est un jeton anonyme au porteur,
  ne porte aucune identité, et ne part que vers l'instance configurée par l'utilisateur.
- **Code distant : non.** Tout ce qui s'exécute est livré dans le paquet. Aucun CDN, aucun
  `eval`, aucun script téléchargé à l'exécution.

Les trois attestations se signent sans mentir : les données ne sont pas vendues à des tiers, ne
servent à aucune fin étrangère à l'objet unique ci-dessus, et ne servent ni à évaluer une
solvabilité ni à accorder un prêt.

## Ce qui se fait à la main

1. Un compte développeur au Chrome Web Store, avec ses frais d'inscription uniques. Ni le
   compte ni le moyen de paiement ne se délèguent.
2. Des **captures d'écran**, au moins une, en 1280x800 ou 640x400. Les utiles sont la carte
   d'analyse sur une vraie page, le badge passif dans la barre d'outils, et la page des
   réglages. Une vignette promotionnelle 440x280 est facultative pour une fiche non
   répertoriée.
3. Le dépôt du paquet et le remplissage du formulaire.
4. La revue, quelques jours en général. Une extension qui demande des permissions d'hôte, même
   optionnelles, est souvent regardée de plus près.

## Firefox, plus tard

`addons.mozilla.org` offre les mêmes mises à jour automatiques et sa revue est en général plus
rapide. Le manifeste est déjà en MV3, que Firefox prend en charge, mais le portage est le jalon
1 de la feuille de route et la suite de tests partagée vient avec. Rien de ce qui précède n'est
à refaire : mêmes justifications, mêmes déclarations, et AMO accepte en plus une archive des
sources pour la reproductibilité, ce à quoi ce paquet est construit.
