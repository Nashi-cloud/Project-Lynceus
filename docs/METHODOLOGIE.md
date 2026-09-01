# Méthodologie d'analyse

Version : **0.1.4**. Toute modification de ce document ou des prompts incrémente `prompt_version` (semver) et déclenche une passe sur le [corpus de calibration](../corpus/).

## Vue d'ensemble

```
Contenu (Markdown) ──▶ 1. Catégorisation ──▶ 2. Dimensions (4 scores) ──▶ 3. Techniques (extraits verbatim)
                                                                              │
Carte finale ◀── 6. Assemblage serveur ◀── 5. Note globale (calcul serveur) ◀─┤
(JSON validé)       (note + méta)           pondérations publiées             └▶ 4. Points positifs + questions
```

Le LLM produit la matière (catégorie, dimensions, techniques, textes) ; **la note globale est calculée par le serveur** à partir des dimensions, avec les pondérations publiées ci-dessous. Déterminisme et auditabilité : deux instances avec les mêmes dimensions produisent la même note.

## 1. Catégorisation du contenu

La catégorie décrit la **nature dominante** du contenu, pas sa qualité :

| Catégorie | Description |
|---|---|
| `information` | Contenu journalistique factuel (qui, quoi, où, quand) |
| `opinion` | Éditorial, tribune, billet assumé comme point de vue |
| `analyse_expertise` | Analyse approfondie, vulgarisation scientifique |
| `satire` | Contenu parodique ou humoristique |
| `publicite_sponsorise` | Contenu commercial, advertorial, page de vente |
| `temoignage` | Récit personnel, expérience vécue |
| `contenu_confessionnel` | Contenu religieux ou spirituel assumé comme tel |
| `pseudo_science` | Discours à apparence scientifique sans méthode scientifique |
| `theorie_du_complot` | Récit d'intention cachée coordonnée, présenté comme information |
| `autre` | Tout le reste (page d'accueil, boutique, forum…) |

La catégorie conditionne la lecture de la note (voir « Cas particuliers »).

## 2. Les quatre dimensions (0–100 chacune)

### `sources` : qualité du sourçage (pondération : 30 %)
- Les affirmations importantes sont-elles sourcées ? Sources primaires identifiables et vérifiables ?
- Liens réels vers les sources, ou simples affirmations (« des études montrent ») ?
- Les sources citées disent-elles vraiment ce qu'on leur fait dire (si vérifiable dans le texte) ?

### `factualite` : rigueur factuelle (pondération : 30 %)
- Affirmations extraordinaires → preuves extraordinaires ?
- Contradictions avec des faits établis ou le consensus scientifique (dans les limites de ce que le modèle sait, avec prudence) ?
- Distinction faits / interprétations ? Chiffres et dates cohérents ?

### `ton` : registre et procédés rhétoriques (pondération : 20 %)
- Registre dominant : factuel ou émotionnel (peur, indignation, urgence) ?
- Densité de techniques de manipulation détectées (voir [TAXONOMIE.md](TAXONOMIE.md)) ?
- Titre cohérent avec le contenu, ou piège à clic ?

### `transparence` : transparence de l'éditeur (pondération : 20 %)
- Auteur identifiable ? Mentions légales, entité éditrice ?
- Conflits d'intérêt visibles dans le texte (vente de produits liés aux affirmations) ?
- Opinion présentée comme information, publicité déguisée ?

## 3. Détection des techniques

- Uniquement des techniques **du référentiel** [TAXONOMIE.md](TAXONOMIE.md) (ids validés par le serveur).
- Chaque détection exige un **extrait verbatim** de la page. Pas de citation exacte → pas de détection.
- Chaque détection porte une gravité (`faible` / `moyenne` / `haute`) et une explication pédagogique du mécanisme.
- **Le contrôle verbatim ne s'arrête pas aux détections.** Toute citation entre guillemets, où qu'elle apparaisse dans les textes rendus, est vérifiée contre la page et signalée si elle ne s'y trouve pas. Le texte reste affiché : ce n'est pas une détection écartée, c'est une mesure du comportement du modèle, et le taux est observable.
- **Ce que cette barrière ne couvre pas, et il faut le dire.** Une affirmation sans guillemets échappe au contrôle. Un texte libre peut encore prêter au contenu une propriété qu'il ne revendique pas, sans le citer. Le prompt l'interdit, mais rien ne le rend impossible et **rien ne le mesure** : une attente de corpus a été essayée, listant des termes que l'analyse ne devait pas employer, et elle a été retirée parce qu'elle ne distingue pas « le produit est-il certifié ? », question légitime sur n'importe quelle page, de « comment cette certification est-elle obtenue ? », qui présuppose. Une garantie déterministe sur du texte libre n'existe pas, et prétendre le contraire serait plus grave que de l'écrire ici. Ce qui rattrape ce cas est la relecture humaine et la contestation.

## 4. Points positifs et questions

- **Points positifs** : toujours en chercher (dates exactes, source correcte, auteur identifié…). En trouver zéro doit rester exceptionnel et justifié.
- **Questions à se poser** : 2 à 4 questions socratiques, applicables par le lecteur lui-même (« Qui finance ce site ? », « Pourquoi aucune source n'est-elle liée ? »).
- **Une question ne présuppose pas.** « Le site précise-t-il si les données sont anonymisées ? » se pose sur n'importe quelle page ; « comment s'opère l'anonymisation ? » suppose acquis que la page l'annonce. Présupposer, c'est affirmer sous forme interrogative, et le faire au nom de l'outil sur une page tierce est le pire mode de défaillance possible pour un outil d'éducation aux médias.

## 5. Note globale (calcul serveur)

```
score = 0,30·sources + 0,30·factualite + 0,20·ton + 0,20·transparence
```

| Grade | Score | Lecture |
|---|---|---|
| **A** | ≥ 80 | Bonnes pratiques d'information |
| **B** | 65–79 | Globalement fiable, quelques réserves |
| **C** | 50–64 | Prudence, vérifier avant de partager |
| **D** | 30–49 | Forte prudence, signaux sérieux |
| **E** | < 30 | Signaux critiques nombreux |

L'**indice de confiance** (0–1, fourni par le LLM) est affiché séparément : il qualifie l'analyse, pas le contenu.

## 6. Cas particuliers

- **Satire** : la note évalue la *transparence de la satire* (un site parodique assumé note bien). La carte porte l'avertissement « contenu satirique, second degré ». Jamais traitée comme désinformation.
- **Opinion / éditorial** : évalué sur l'honnêteté argumentative (sources des faits invoqués, absence de techniques déloyales), **jamais sur la position défendue**.
- **Contenu confessionnel** : la foi n'est pas notée. Seules le sont les affirmations factuelles (santé, science, histoire) et les techniques de manipulation éventuelles (peur, urgence, isolement).
- **Contenu court ou tronqué** (paywall, extrait) : indice de confiance abaissé + avertissement explicite.
- **Langue étrangère** : analyse dans la langue du contenu si le modèle le permet, sinon avertissement.

## 7. Calibration

- Le [corpus](../corpus/) contient des pages de référence avec catégorie et fourchette de grade attendues.
- Toute évolution de prompt ou de méthodologie est évaluée contre le corpus avant merge : pas de régression silencieuse.
- Cas sentinelles obligatoires : un site satirique (jamais « désinformation »), un éditorial de qualité (jamais pénalisé pour sa position), un site pseudo-médical marchand (le conflit d'intérêt doit être détecté), et une page en anglais (l'analyse doit être rédigée dans la langue de la page).
- Le modèle n'est pas déterministe : deux passes sur le même contenu peuvent différer. Un écart isolé n'est donc pas une régression, et une régression se constate en rejouant le cas. Les écarts observés sont publiés avec leurs résultats plutôt que corrigés en assouplissant l'attente.

## Limites connues et assumées

1. Le modèle peut se tromper (hallucination, connaissance datée) → indice de confiance, contestation, ré-analyse.
2. L'analyse porte sur **une page**, pas sur la totalité d'un site → le profil de domaine n'est qu'un agrégat, présenté comme tel.
3. Les biais du modèle sous-jacent existent → prompts publics, corpus de calibration, choix du modèle par instance.
4. La factualité fine (fact-checking de chaque chiffre) n'est pas l'objet : Lynceus détecte des *méthodes*, les fact-checkers vérifient des *faits*. Les deux sont complémentaires.
5. La garantie « rien n'est inventé » est **complète sur les citations, partielle sur le reste**. Une citation est vérifiable mot pour mot, donc elle l'est. Une affirmation sans guillemets ne l'est pas, et aucun contrôle déterministe ne peut la vérifier sans juger le sens. Le prompt la contraint, la contestation la rattrape après coup, et le corpus n'y peut rien : distinguer une question qui présuppose d'une question qui interroge demande de juger le sens, ce qu'un contrôle déterministe ne fait pas.
