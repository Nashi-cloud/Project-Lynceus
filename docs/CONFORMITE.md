# Conformité réglementaire

Ce document décrit l'analyse de conformité du projet et de l'instance de référence. Il est
versionné avec le code, comme la charte : le modifier est un acte public.

> **Ce document n'est pas un avis juridique.** Il expose l'analyse du projet et les
> mesures effectivement implémentées, avec les points qui restent à valider par un
> professionnel. Les affirmations vérifiables par le code renvoient au fichier concerné.

## 1. Identification de l'éditeur

Tout service de communication au public en ligne doit identifier son éditeur. Lynceus
étant auto-hébergeable, cette identité **dépend de qui exploite l'instance** et ne peut
pas être codée en dur.

Elle est donc configurée (`LYNCEUS_PORTAIL_EDITEUR_*`, `LYNCEUS_PORTAIL_HEBERGEUR_*`) et
publiée sur `/mentions-legales`. Deux garde-fous :

- si l'identité est incomplète, la page **le dit** au lieu d'afficher des mentions
  inventées (`gabarits/_legal_incomplet.html`) ;
- le portail **avertit au démarrage** quand il déclare une instance publique sans identité
  complète (`portail/__init__.py`).

## 2. Données personnelles

### Ce qui est traité

| Traitement | Données | Base légale retenue | Conservation |
|---|---|---|---|
| Consultation de l'annuaire | préfixe d'empreinte d'URL, adresse IP le temps de la requête | intérêt légitime | aucune |
| Analyse d'une page | texte de la page, titre, URL, adresse IP | intérêt légitime | l'analyse, sans lien avec une personne |
| Limite de débit | adresse IP, compteur | intérêt légitime (protection du service) | fenêtre glissante d'une minute, en mémoire |
| Contestation | message, contact facultatif | intérêt légitime (droit de réponse) | tant que l'analyse est publiée |
| Délivrance d'une clé | aucune | sans objet | aucune |

### Le transfert qu'il ne faut pas taire

Analyser suppose de transmettre le texte de la page au **fournisseur de modèle de
langage** configuré, qui peut être établi hors de l'Union européenne. C'est le flux le
plus important du système.

Trois conséquences assumées :

1. la politique de confidentialité l'annonce **en tête de page**, pas en note ;
2. elle nomme le fournisseur **réellement configuré**, lu dans `/v1/meta` de l'instance
   plutôt qu'écrit à la main, pour qu'elle ne puisse pas devenir fausse en silence ;
3. le remède est un livrable du projet, pas une pirouette : une instance auto-hébergée
   avec un modèle local ne fait sortir aucun texte.

Une instance qui vise une conformité stricte au regard des transferts hors Union doit
choisir un fournisseur établi dans l'Union, ou un modèle local. Le projet ne verrouille
aucun fournisseur : c'est un adaptateur compatible OpenAI, changeable par configuration.

### Minimisation, par construction et non par promesse

- **k-anonymat** : la consultation n'envoie que les premiers caractères de l'empreinte
  d'URL, et la correspondance finale se fait chez le client. Un test dédié vérifie que le
  serveur ne renvoie jamais l'empreinte entière (`tests/test_phase3.py`,
  `tests/test_portail.py`).
- **Extraction locale** : le serveur ne visite jamais les pages à la place de
  l'utilisateur, et n'apprend donc rien de sa navigation.
- **Aucun compte** : les clés d'accès ne portent qu'une date d'expiration et un quota.
  Le portail ne conserve rien de ce qu'il délivre.
- **Aucun cookie, aucune ressource tierce** : polices, feuille de style et scripts sont
  servis par le portail lui-même. Aucun bandeau de consentement, parce qu'il n'y a rien à
  consentir.

### Limite honnête sur les droits des personnes

Ne rien rattacher à une personne a une conséquence désagréable : il n'existe en pratique
aucun moyen de retrouver « les données de quelqu'un ». Ce n'est pas une échappatoire, mais
il faut le dire plutôt que de promettre un droit d'accès inapplicable. Les contestations
déposées avec un contact sont, elles, identifiables et effaçables.

## 3. Transparence des systèmes d'IA

Le règlement européen sur l'intelligence artificielle impose d'informer les personnes
lorsqu'elles interagissent avec un système d'IA ou consultent un contenu qu'il a produit.

Mesures en place :

- chaque carte d'analyse porte un avertissement **ajouté par le serveur**, que le client
  ne peut pas retirer (`main.py`, constante `AVERTISSEMENT_IA`) ;
- l'indice de confiance du modèle est affiché ;
- le modèle et sa version de prompt sont publiés dans chaque analyse et dans `/v1/meta` ;
- la méthodologie, les pondérations et le référentiel de procédés sont publics et
  versionnés.

**Analyse du niveau de risque.** Le système décrit des procédés rhétoriques dans des
contenus publics et ne prend aucune décision produisant des effets juridiques sur les
personnes. Il ne relève d'aucun des usages listés comme à haut risque : il ne détermine
pas l'accès à une formation ni à un emploi, n'évalue pas des personnes, et n'est pas
destiné à influencer un scrutin. Les obligations retenues sont donc celles de
transparence. **Cette qualification reste à confirmer par un professionnel** avant toute
communication publique s'en prévalant.

## 4. Contenus analysés et droits des tiers

- Les analyses portent sur des **contenus accessibles publiquement** et citent des
  extraits courts à fin d'analyse et de commentaire, avec mention de la source. Le serveur
  refuse toute citation qui ne se retrouve pas **mot pour mot** dans la page, ce qui
  interdit d'attribuer à quelqu'un des propos qu'il n'a pas tenus (`moteur/validation.py`).
- Les analyses décrivent des **procédés**, jamais des personnes. La charte l'impose et le
  prompt le formule explicitement.
- Un **droit de réponse** est ouvert à tous, et en premier lieu aux éditeurs des sites
  analysés. Le nombre de contestations reçues est public avant même instruction, et toute
  décision de modération est justifiée et conservée.
- Le corpus de calibration ne **versionne pas** les captures de pages réelles, uniquement
  leur manifeste : URL, date, empreinte de contenu et attentes.

## 5. Licence et propriété intellectuelle

- Le projet est publié sous **AGPL-3.0**. Toute version modifiée mise à disposition par le
  réseau doit publier ses sources.
- Le titulaire des droits est indiqué dans [AUTHORS.md](../AUTHORS.md).
- Les contributions extérieures relèvent du **Developer Certificate of Origin** : chaque
  contributeur certifie avoir le droit d'apporter son code sous cette licence
  ([DCO.txt](../DCO.txt), voir [CONTRIBUTING.md](../CONTRIBUTING.md)).
- Les dépendances embarquées portent leur licence : htmx sous 0BSD, Fraunces et Newsreader
  sous SIL Open Font License, avec leurs notices dans `api/lynceus/portail/statique/`.

## 6. Ce qui reste à faire

- [ ] Faire relire les mentions légales, la politique de confidentialité et les conditions
      d'utilisation par un professionnel avant l'ouverture au public.
- [ ] Décider du fournisseur de modèle de l'instance de référence au regard des transferts
      hors Union, et le documenter.
- [ ] Tenir un registre des traitements si l'exploitant y est tenu.
- [ ] Vérifier la disponibilité du nom « Lynceus » à titre de marque avant toute
      communication d'ampleur.
