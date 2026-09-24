# Constituer le jeu d'évaluation annoté

Version du guide : **1.2**, septembre 2026.

Ce document dit comment se construit le jeu de pages annotées à la main contre lequel se
mesure toute chaîne d'analyse de Lynceus. C'est l'étape zéro de
[l'architecture cible](ARCHITECTURE-CIBLE.md) : tant que ce jeu n'existe pas, une
amélioration et un tirage chanceux se ressemblent. L'outillage est décrit dans
[corpus/README.fr.md](../corpus/README.fr.md) ; ce document-ci décrit le travail humain.

La section 5, le guide d'annotation proprement dit, est versionnée. Chaque annotation
porte la version du guide sous laquelle elle a été faite, et toute révision du guide
incrémente ce numéro.

## 1. Ce que ce jeu est, et ce qu'il n'est pas

- **Un instrument de mesure.** Il dit, en chiffres, ce qu'une chaîne trouve et ce qu'elle
  rate, et à quel point deux lecteurs humains s'accordent sur la même page.
- **Pas une vérité.** Deux annotateurs attentifs ne s'accordent pas toujours. Leur accord
  est publié avec le reste, et fixe le plafond raisonnable de toute machine.
- **Pas un jeu d'entraînement.** La partie `test` n'est jamais montrée à un modèle en
  cours d'apprentissage ni à une chaîne en cours de réglage. Un jeu appris ne mesure plus
  rien. Les données d'entraînement viennent d'ailleurs (section 9).
- **Pas le corpus de calibration.** Les quinze cas de `corpus.yaml` restent les
  sentinelles et les pièges, avec leurs attentes. Le jeu d'évaluation vit dans
  `corpus/evaluation.yaml`, sans attente : l'annotation en tient lieu.

## 2. Les rôles

| Rôle | Qui | Ce qu'il fait |
|---|---|---|
| Coordination | Une personne, le mainteneur par défaut | Sélectionne les pages, fait les captures, les distribue, rassemble les lectures, fait arbitrer, publie les lots. |
| Annotation | Au moins deux personnes, sous pseudonyme | Lisent chaque page indépendamment et produisent une lecture chacune. |
| Arbitrage | Une troisième personne, jamais l'un des deux annotateurs de la page | Tranche les pages dont les deux lectures divergent. |

Profils recherchés pour l'annotation : éducation aux médias, journalisme, vérification
des faits, enseignement, documentation. Aucune compétence technique n'est nécessaire.

### 2.1 La phase de démarrage : un seul annotateur

Au départ, le mainteneur coordonne et annote seul. Le travail n'attend pas les bénévoles,
mais il faut dire ce que cette phase mesure et ce qu'elle ne mesure pas.

- **Ce qui ne se mesure pas encore** : l'accord entre deux personnes, qui seul dit si le
  guide se lit d'une seule façon. `lynceus mesurer` signale les pages qui n'ont qu'une
  lecture, et tout chiffre publié sur elles le dit.
- **Ce qui le remplace en partie** : la relecture. Une page sur dix, tirée au sort, est
  relue par le même annotateur au moins quatre semaines plus tard, sans rouvrir sa
  première lecture (`lynceus annoter --relecture`). L'accord d'un annotateur avec
  lui-même est publié sous ce nom, jamais comme un accord entre annotateurs.
- **Sélectionner avant de lire.** Qui choisit les pages et les annote risque de choisir
  celles qu'il sait lire. Un lot se sélectionne donc en entier, selon les quotas, avant
  la première lecture, et le motif de chaque page s'écrit dans `notes`.
- **Garder les lectures pour les suivants.** Les lectures de la partie `test` restent dans
  `corpus/annotations-en-cours/`, que git ignore, jusqu'à ce qu'une seconde personne ait
  lu la page. Publiées plus tôt, elles seraient sous les yeux du second annotateur, et sa
  lecture ne serait plus indépendante. Les pages de la partie `reglage` peuvent être
  publiées dès leur première lecture.
- **Arbitrer sans tiers.** Quand un bénévole a fait la seconde lecture et qu'aucune
  troisième personne n'est disponible, les deux lecteurs arbitrent ensemble, en séance,
  et l'arbitrage le mentionne dans `notes`. C'est moins solide qu'un tiers, et cela se dit.

## 3. Les règles qui ne se discutent pas

1. **Annoter sans avoir vu de carte.** Ni celle de Lynceus, ni celle d'aucun autre outil,
   ni l'annotation du jeu silver (section 11), ni avant ni pendant la lecture. Une annotation faite avec la réponse sous les yeux
   mesure l'accord avec le modèle, pas avec la page.
2. **Annoter sans IA.** Aucun modèle de langage ne propose, ne complète ni ne relit une
   annotation. La [politique IA](IA-GENERATIVE.md) du projet s'applique ici sans exception,
   pour la même raison que la règle 1.
3. **Lire seul.** Pas de discussion d'une page entre annotateurs avant que les deux
   lectures soient remises. Les notes de l'autre ne se lisent qu'après.
4. **Pas de conflit d'intérêt.** Aucune page de nashi.cloud ni d'un site lié au projet.
   Un annotateur déclare les sites auxquels il est lié (employeur, collaboration,
   militantisme) et ne reçoit aucune de leurs pages.
5. **Les captures ne sont jamais versionnées.** Le dépôt ne contient que le manifeste et
   les annotations. Les annotations ne contiennent que des extraits courts, au plus
   600 caractères chacun, ce qui relève de la citation à fin d'analyse (voir
   [CONFORMITE.md](CONFORMITE.md) §4).
6. **Des procédés, pas des personnes.** On annote ce que fait un texte, jamais ce que
   serait son auteur. Les pages centrées sur un particulier sont écartées dès la sélection.

## 4. Composer le jeu

### 4.1 Taille et partage

| | Pages | Rôle |
|---|---|---|
| Partie `test` | 200 au moins | Le chiffre publié. Jamais vue en réglage. |
| Partie `reglage` | 40 environ, plus les pages du pilote | Autorisée pour ajuster des seuils. |

Deux cents pages est le seuil en dessous duquel une différence de quelques points reste
du bruit. La partie de chaque page est **tirée au sort** au moment de la sélection, à
raison d'une page sur six en `reglage` : la choisir après avoir vu un résultat biaiserait
tout.

### 4.2 Équilibre

- **Langues** : environ 60 % en français, 40 % en anglais.
- **Catégories** : au moins 12 pages par catégorie de [METHODOLOGIE.md](METHODOLOGIE.md) §1,
  8 pour `autre`. La catégorie visée à la sélection est une intention, pas une étiquette :
  seule l'annotation la fixe.
- **Sources** : au plus 3 pages par domaine. Un mélange de presse nationale et régionale,
  de blogs, de sites de santé alternative, de pages de vente, de forums, de sites
  institutionnels, de satire, de contenu religieux et de vulgarisation.
- **Des pages sans procédé.** Environ la moitié du jeu doit venir de sources où l'on
  n'attend pas de manipulation. Sans elles, les faux positifs ne se mesurent pas, et ce
  sont eux qui trahissent la charte.
- **Longueurs** : courtes (moins de 3 000 caractères), moyennes, longues. Les captures de
  plus de 60 000 caractères sont écartées, puisque l'extension tronque au-delà.
- **Dates** : des pages publiées sur plusieurs années, pas seulement l'actualité du mois.

### 4.3 Trouver des pages

Les pages problématiques se trouvent notamment dans les contenus déjà examinés par les
rubriques de vérification des rédactions, qui citent leurs sources. Les autres se
choisissent par source, selon les quotas, sans regarder leur contenu au préalable.

Aucune page ne se choisit après l'avoir soumise à Lynceus : on retiendrait sans le
vouloir celles qu'il traite bien ou mal. Le motif de sélection s'écrit dans `notes`.

Aucune page du jeu silver (section 11) n'entre non plus dans le jeu de test : des modèles
l'ont déjà lue, et un encodeur apprendra peut-être dessus. La liste de ces pages est
publiée par lynx-corpus dans `silver/deja-vus.txt`. Désignée par `LYNCEUS_DEJA_VUS`, elle
fait refuser une telle page par `lynceus capturer`, et signaler par `lynceus mesurer` toute
page du jeu de test qui y figurerait déjà :

```bash
export LYNCEUS_DEJA_VUS=../lynx-corpus/silver/deja-vus.txt
lynceus capturer page.md --url https://exemple.fr/article --vers corpus/captures
lynceus mesurer corpus/evaluation.yaml
```

## 5. Le guide d'annotation, version 1.2

<!-- Les titres 5.1 à 5.4 sont lus par lynx-corpus, qui en fait le prompt de son panel :
     les renommer casse cette chaîne, et un test de lynx-corpus le signale. -->

**Ce qui a changé en 1.2.** Révision tirée du premier lot audité sous 1.1 : pages
d'accueil (catégorie et titres), grade d'un contenu confessionnel, grade d'une page
commerciale. Elle résout un conflit entre deux règles de la 1.1 et un autre entre la 1.1
et la méthodologie.

**Ce qui a changé en 1.1.** Révision tirée du pilote et des premiers audits du jeu silver
(37 pages) : la thèse l'emporte sur la forme, frontière opinion et analyse, pages
d'accueil, titres d'autres pages, une occurrence par technique, `absence_de_sources`
resserrée, portée de la règle du doute. Les lectures faites en 1.0 restent valides mais se
relisent à la lumière de ces règles avant publication.

### 5.1 L'ordre de lecture

1. Lire la page entière une fois, sans rien marquer.
2. Fixer la catégorie.
3. Marquer les passages.
4. Fixer la fourchette de grade, en dernier, une fois les passages vus.
5. Écrire les notes : hésitations, choix, ce qui a failli être marqué.

Compter entre 15 et 30 minutes par page. Au-delà, noter pourquoi et passer à la suivante.

### 5.2 La catégorie

La **nature dominante** du contenu, selon [METHODOLOGIE.md](METHODOLOGIE.md) §1, pas sa
qualité. Quelques règles de départage :

- Un article qui débouche sur la vente de ce qu'il vante est `publicite_sponsorise`, même
  s'il se présente comme une information.
- `satire` seulement si la page ou le site s'annonce comme tel, ou si l'outrance rend
  l'intention parodique évidente à un lecteur attentif.
- **La thèse l'emporte sur la forme.** Un texte qui défend une thèse pseudo-scientifique
  ou complotiste est `pseudo_science` ou `theorie_du_complot`, même s'il se présente comme
  une opinion. `opinion` est pour un point de vue assumé dont la thèse n'est ni l'une ni
  l'autre.
- **Opinion ou analyse.** Un texte qui conclut sur une position à adopter est une
  `opinion`, même chiffré : tribune, note de think tank, plaidoyer. `analyse_expertise`
  est pour un texte qui examine une question sans plaider, avec une méthode visible, ou
  pour une vulgarisation. `information` est pour le compte rendu de faits.
- **Pages d'accueil et sommaires.** Une page faite surtout de liens et d'accroches vers
  d'autres pages est `autre`, quelle que soit la nature du site : on n'en a pas lu les
  articles, et lui donner la catégorie d'une thèse reviendrait à étiqueter le site entier.
  Quand tous les contenus visibles partagent une même nature, satire ou complot par
  exemple, cette catégorie entre dans `categories_acceptables`. C'est la seule exception à
  « la thèse l'emporte sur la forme ».

`categories_acceptables` sert aux vrais hybrides, où deux étiquettes sont également
défendables : l'exemple type est le discours pseudo-médical qui vend son remède. Il ne
sert pas à se couvrir en cas d'hésitation : dans ce cas, choisir et le noter.

### 5.3 Les passages

On marque un passage où **la page elle-même emploie** l'une des 31 techniques de
[TAXONOMIE.md](TAXONOMIE.md). Rien d'autre : pas de technique hors de la liste, pas de
jugement sur la véracité des faits.

**Délimiter.**

- Le plus petit passage qui suffit à reconnaître le procédé : en général une phrase,
  jamais plus d'un paragraphe, au plus 600 caractères.
- Recopier le texte exactement, sans points de suspension ni coupure. Si le procédé
  s'étend sur deux phrases éloignées, faire deux passages.
- Quand le même texte apparaît plusieurs fois dans la page, préciser `occurrence`.
- Un même passage peut porter deux techniques : on l'inscrit deux fois.
- **Une occurrence par technique** : la première qui est nette, en lisant la page dans
  l'ordre. Les suivantes ne se marquent pas, même plus nettes ; une note peut dire que
  le procédé revient.

**Ce qui ne se marque pas.**

- **Le procédé rapporté.** Une page qui cite un discours complotiste pour le démonter
  n'emploie pas la vérité cachée. Seul compte ce que la page fait, pas ce qu'elle décrit.
- **Le procédé parodié.** Dans une satire, les procédés moqués ne se marquent pas.
- **La foi.** Une affirmation de foi n'est pas un procédé (charte, [ETHIQUE.md](ETHIQUE.md)).
- **Le style.** Un ton vif ou un vocabulaire fort ne sont pas des techniques. Le lexique
  émotionnel relève d'un compte automatique, pas de l'annotation.
- **Les titres d'autres pages, dans une page qui a son propre texte.** Dans un article ou
  une lettre d'information, un titre cité dans un sommaire, une liste de liens ou un
  encadré « à lire aussi » appartient à l'autre page. Le titre et les intertitres de la
  page elle-même se marquent comme le reste du texte. Sur une page d'accueil ou un
  sommaire, en revanche, les titres sont le contenu propre de la page et se marquent : sa
  nature se lit dans les procédés de ses titres et dans son grade, pas dans sa catégorie.

**Les techniques d'absence.** `absence_de_sources` se marque **une fois au plus** par page,
sur l'affirmation la plus importante, et seulement si la page présente comme établis des
faits vérifiables qui portent sa conclusion. Elle ne se marque pas sur une opinion, un
témoignage ou une page commerciale ordinaire. Une source nommée est une source, même sans
lien : « selon l'Insee » est sourcé. `conflit_interet_commercial` se marque sur le passage
où apparaît la vente, l'affiliation ou l'appel au don lié au discours.

**Dans le doute, ne pas marquer.** Marquer ce qu'un lecteur attentif relèverait à coup
sûr. Un passage douteux va dans les notes, avec la technique envisagée. Une annotation
prudente et stable vaut mieux qu'une annotation exhaustive que personne ne reproduit.

Le doute porte sur un passage isolé, pas sur un procédé qui porte la page entière. Celui-là
se marque toujours, sur le passage qui le montre le mieux : la solution miracle d'une page
de vente, le témoignage qui sert de seule preuve.

La gravité n'est pas demandée dans cette version du guide.

### 5.4 La fourchette de grade

Une ou deux lettres **adjacentes**, jamais plus. Raisonner par les quatre dimensions de
[METHODOLOGIE.md](METHODOLOGIE.md) §2 : sources, factualité, ton, transparence. La
fourchette dit où l'on placerait la page, pas où l'on pense que Lynceus la placera.

- **Contenu confessionnel.** La foi ne pèse pas : ne pas la juger, c'est ne rien lui
  retirer. Une page de foi sans affirmation de fait ni procédé se place en A ou B. Seules
  font baisser les affirmations de fait (santé, science, histoire) et les procédés relevés.
- **Page commerciale.** Vendre ne fait pas baisser le grade. Seuls comptent le
  déguisement (publicité présentée comme information), les affirmations de fait sans
  appui et les procédés relevés. Une page de vente assumée qui source ce qu'elle affirme
  se place en haut de l'échelle.

### 5.5 Le fichier

`lynceus annoter` prépare le squelette, avec la bonne empreinte :

```bash
lynceus annoter captures/nom-de-la-page.md --annotateur mon-pseudonyme \
  > mon-pseudonyme-nom-de-la-page.yaml
```

```yaml
cas: captures/nom-de-la-page.md
annotateur: mon-pseudonyme
guide: "1.2"
content_hash: 5c1e…
categorie: pseudo_science
categories_acceptables: [publicite_sponsorise]   # seulement pour un vrai hybride
grade: [D, E]
intervalles:
  - extrait: "ce que les laboratoires ne veulent pas que vous sachiez"
    technique: verite_cachee
  - extrait: "Commandez avant la rupture de stock"
    technique: urgence_artificielle
notes: |
  Sélection : rubrique de vérification, lot 3.
  Hésité sur autorite_anonyme pour « des chercheurs américains », non marqué : l'étude est citée plus bas.
```

## 6. Le déroulé

### 6.1 Formation

Chaque annotateur lit [TAXONOMIE.md](TAXONOMIE.md), [METHODOLOGIE.md](METHODOLOGIE.md)
§1 et §2, et ce guide. Il annote ensuite cinq spécimens du corpus de calibration, puis
compare sa lecture aux attentes de `corpus.yaml` et en discute avec la coordination.

### 6.2 Pilote

Vingt pages, toutes lues par deux annotateurs. Chaque désaccord est discuté en séance,
et le guide est révisé en conséquence : c'est ce qui fait passer la version à 1.1. Les
pages du pilote vont en partie `reglage`, puisqu'elles ont été discutées.

En phase de démarrage, le pilote se fait seul : vingt pages lues, puis toutes relues
quatre semaines plus tard. Chaque écart entre les deux lectures pointe une règle du guide
à préciser. Chaque nouveau bénévole fait ensuite son propre pilote sur ces vingt pages,
dont les lectures sont publiées puisqu'elles sont en partie `reglage`, et compare après
coup.

### 6.3 Production, par lots de vingt pages

1. **Sélection et capture** par la coordination : chaque page est capturée avec
   `lynceus capturer`, qui calcule l'empreinte. La capture rejoint l'archive privée de
   la coordination, sauvegardée ailleurs : une capture perdue ne se recrée pas à
   l'identique, et ses annotations deviendraient inutilisables. L'entrée s'ajoute à
   `corpus/evaluation.yaml`, avec `lot` et `partie`.
2. **Distribution** des captures aux deux annotateurs de chaque page, hors du dépôt.
3. **Lecture** indépendante. Chaque annotateur remet ses fichiers à la coordination, hors
   du dépôt : une lecture publiée avant que l'autre soit faite serait visible de tous.
4. **Contrôle** : la coordination place les lectures du lot dans
   `corpus/annotations-en-cours/<pseudonyme>/`, que git ignore, et lance
   `lynceus mesurer corpus/evaluation.yaml`, qui lit les deux dossiers. Une annotation fautive (empreinte,
   technique, extrait introuvable) est renvoyée à son auteur. La commande liste les pages
   à arbitrer.
5. **Arbitrage** des pages listées : l'arbitre lit la page, puis les deux lectures, et
   écrit la sienne avec `lynceus annoter --arbitrage`. Il ne consulte aucune carte.
   Un désaccord de bornes sur la même technique ne demande pas d'arbitre : le recouvrement
   partiel en rend compte.
6. **Publication** du lot en une seule demande de fusion : les pages closes passent de
   `annotations-en-cours/` à `annotations/`, avec les entrées du manifeste et les
   arbitrages. Le message de commit donne l'accord entre annotateurs du lot, et crédite
   chaque bénévole par une ligne `Co-authored-by:` (section 10).

### 6.4 Surveillance de l'accord

Après chaque lot, `lynceus mesurer` donne l'accord entre annotateurs. Seuils de départ,
à revoir après le pilote :

| Mesure sur un lot | Seuil | En dessous |
|---|---|---|
| Kappa de la catégorie | 0,6 | Pause, séance de mise au point, révision du guide |
| F1 des techniques entre annotateurs | 0,5 | Même chose |

Un accord bas n'est pas une faute des annotateurs : c'est presque toujours une règle du
guide qui manque ou qui se lit de deux façons.

### 6.5 Gel et première mesure

Quand la partie `test` atteint 200 pages lues chacune par deux personnes :

1. Étiquette git `evaluation-v1` sur le commit qui contient le dernier lot.
2. Publication de l'accord entre annotateurs sur l'ensemble.
3. Première mesure de la chaîne actuelle :

```bash
lynceus calibrer corpus/evaluation.yaml --json evaluation-v1.json
lynceus mesurer corpus/evaluation.yaml --rapport evaluation-v1.json --json mesures-v1.json
```

Cette passe coûte une analyse par page, soit environ 240 appels au fournisseur de modèle.
Elle se fait sur une instance de développement, jamais sur la production.

## 7. Où vit chaque chose

| Quoi | Où | Public |
|---|---|---|
| Ce guide | `docs/ANNOTATION.md` | Oui |
| Manifeste du jeu | `corpus/evaluation.yaml` | Oui |
| Lectures et arbitrages publiés | `corpus/annotations/<pseudonyme>/` | Oui |
| Captures | Archive privée de la coordination, sauvegardée | Non |
| Lectures en cours | Chez l'annotateur, puis `corpus/annotations-en-cours/` chez la coordination | Non, jusqu'à ce que la page soit close |
| Liste des annotateurs et licence | `corpus/annotations/README.md` | Oui |
| Déclarations de liens des annotateurs | Coordination | Non |

## 8. Le temps nécessaire

Estimations à confirmer sur le pilote :

| Tâche | Unité | Volume | Total |
|---|---|---|---|
| Sélection et capture | 5 min par page | 240 pages | 20 h |
| Lecture | 20 min | 480 lectures | 160 h |
| Arbitrage | 10 min | environ 80 pages, une sur trois | 15 h |
| Coordination et séances | | | 15 h |

Soit de l'ordre de **210 heures**, dont les trois quarts en lecture. À deux annotateurs
réguliers et quatre heures par semaine chacun, cela fait environ cinq mois ; à quatre,
moins de trois.

## 9. Les corpus publics, une voie parallèle

Les jeux publics (SemEval 2023 tâche 3, CheckThat! 2024, FLICC, MAFALDA) se ramènent à
nos techniques par les tables de `corpus/correspondances/`. Ils servent à entraîner et à
dégrossir, et donnent une mesure secondaire. Ils **ne remplacent pas** le jeu annoté :
leurs consignes d'annotation ne sont pas les nôtres, et la plupart ne sont pas en
français.

L'outil de conversion reste à écrire. La licence de chaque jeu est vérifiée avant tout
import, et aucun de ces jeux n'entre dans le dépôt.

## 10. Licence, accord et crédit

**La licence.** Les annotations et le manifeste du jeu d'évaluation sont publiés sous
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.fr), et non sous
l'AGPL-3.0 du code, qui n'est pas faite pour des données. Chacun peut les réutiliser, y
compris pour entraîner un modèle, à condition de citer la source et de partager ses
propres annotations dérivées sous la même licence. La notice figure dans
`corpus/annotations/README.md`.

**L'accord de chaque annotateur.** Un bénévole rejoint le jeu par une première demande de
fusion, qui ajoute sa ligne à la liste des annotateurs de `corpus/annotations/README.md`.
Son commit porte son propre `Signed-off-by` : il certifie ainsi, selon le
[DCO](../DCO.txt), qu'il a le droit de publier ses lectures sous la licence indiquée dans
ce dossier. C'est son accord écrit, daté, public, et il ne dépend pas de la coordination.
Aucune de ses lectures n'est publiée avant.

**Le crédit.** Le pseudonyme d'annotateur est l'identifiant GitHub, et l'on sait qu'il
peut révéler un nom. Chaque commit qui publie des lectures d'un bénévole porte une ligne
`Co-authored-by:` à son nom, avec l'adresse de son commit d'entrée, ce qui l'inscrit comme
coauteur sur la forge. Toute réutilisation du jeu cite « Annotations Lynceus » et renvoie
à la liste des annotateurs.

**Reste ouvert** : le recrutement des bénévoles et d'un arbitre.

## 11. Le jeu silver, annoté par des modèles

Le jeu de test mesure ; il ne suffit pas à entraîner un encodeur, qui demande des
milliers d'exemples. Ceux-là viennent d'un second jeu, le **jeu silver**, annoté par un
panel de modèles de langage et construit dans un dépôt séparé,
[lynx-corpus](https://github.com/Nashi-cloud/lynx-corpus). Les deux jeux ne se mélangent
jamais.

Le nom vient du vocabulaire de l'apprentissage automatique, qui oppose le *gold standard*,
des données annotées par des humains et qui servent de référence, au *silver standard*,
des données annotées par des machines, plus abondantes et moins sûres. Le jeu de test est
notre étalon or ; le jeu silver n'en est que l'argent, utile mais jamais la référence.

| | Jeu de test | Jeu silver |
|---|---|---|
| Lu par | des humains, à l'aveugle, sans IA | deux modèles, et un troisième qui arbitre |
| Taille | 200 pages et plus | des milliers |
| Sert à | mesurer | entraîner |
| Où | `corpus/` de ce dépôt | lynx-corpus |

**Le panel.** Trois modèles à poids ouverts de trois fournisseurs différents : deux lisent
chaque page indépendamment, avec ce guide pour consigne, et le troisième tranche leurs
désaccords sans pouvoir ajouter de passage. Des poids ouverts par choix : plusieurs
fournisseurs de modèles fermés interdisent d'entraîner un modèle concurrent sur leurs
sorties. La licence de chaque modèle est vérifiée avant toute publication.

**Le même contrôle.** Chaque lecture du panel passe par la vérification que passent les
annotations humaines : technique du référentiel, extrait retrouvé mot pour mot, empreinte.

**Pourquoi il n'est jamais une référence.** Une référence écrite par des modèles rendrait
la mesure circulaire, puisque la chaîne mesurée est elle-même un modèle. Des fournisseurs
différents ne rendent pas les erreurs indépendantes : trois modèles d'accord peuvent se
tromper ensemble.

**Comment il est mesuré.** Par un audit à l'aveugle : une page sur dix, tirée au sort, est
relue par un humain qui ne voit rien de ce que le panel en a dit. Le panel se mesure
contre ces lectures comme une chaîne quelconque, avec les mesures de `lynceus mesurer`.
S'il approche l'accord entre deux humains, le jeu silver est utilisable ; sinon, on sait
de combien il est bruité.

**Les garde-fous.**

- Chaque annotation silver porte `origine: machine` et l'annotateur `panel-silver`, et
  n'entre jamais dans `corpus/annotations/`.
- Les pages du corpus de calibration et du jeu de test sont exclues du jeu silver, par
  adresse et par empreinte.
- Les pages du jeu silver sont exclues du jeu de test, par la liste `deja-vus.txt`
  (section 4.3).
- Aucune capture n'est versionnée, pas plus ici que là.

