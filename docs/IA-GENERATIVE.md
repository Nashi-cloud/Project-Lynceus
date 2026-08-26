# Usage de l'IA générative dans Lynceus

Lynceus demande aux pages qu'il analyse d'être transparentes sur leurs procédés. Il serait
malvenu qu'il soit opaque sur les siens. Ce document dit comment l'IA générative est
utilisée pour **fabriquer** le projet, ce qui est une question distincte de l'IA générative
que le produit **emploie** au moment d'analyser une page.

Il vaut aussi politique pour les contributions, et réponse à la [politique de NLnet sur
l'usage de l'IA générative](https://nlnet.nl/foundation/policies/generativeAI/), applicable
aux travaux financés par ce bailleur.

## Deux choses à ne pas confondre

**L'IA dans le produit.** Lynceus envoie le texte d'une page à un modèle de langage pour en
décrire les procédés de persuasion. C'est le cœur du logiciel, c'est assumé et documenté
ailleurs : [ETHIQUE.md](ETHIQUE.md) pour la posture, [METHODOLOGIE.md](METHODOLOGIE.md)
pour ce que le modèle produit et ce que le serveur calcule sans lui,
[CONFORMITE.md](CONFORMITE.md) pour ce qui circule et vers qui. L'avertissement affiché à
l'utilisateur n'est pas retirable.

**L'IA dans l'atelier.** C'est l'objet de ce document : comment le code, les tests et la
documentation ont été écrits.

## Comment ce projet est développé

Le projet est développé par un porteur unique, avec l'assistance d'un modèle de langage
utilisé comme assistant de programmation, sur la quasi-totalité de la base de code : code
serveur et extension, tests, documentation, et une partie des textes du portail.

Ce que ça ne change pas :

- **La responsabilité.** Chaque décision d'architecture, chaque compromis, chaque ligne
  fusionnée est relue et assumée par un humain, qui doit pouvoir l'expliquer. Une réponse
  d'assistant qu'on ne comprend pas ne se fusionne pas.
- **La routine de vérification.** `./verifier.sh` doit passer avant toute fusion dans `dev`,
  quelle que soit l'origine du code. Un correctif de bug exige un test qui échoue avant lui.
  Ces règles ne connaissent pas la provenance et n'ont pas à la connaître.
- **La charte.** [ETHIQUE.md](ETHIQUE.md) reste le critère de revue numéro un.

Ce qui n'est **pas** délégué : la charte éthique, la taxonomie des procédés et sa
justification, les pondérations de la note, et les arbitrages de posture. Ce sont les
endroits où le projet engage une responsabilité vis-à-vis des personnes qu'il vise, et ils
se discutent, se sourcent et se signent.

## Provenance dans les commits

Un commit qui introduit une contribution substantiellement produite par un assistant porte
deux lignes de fin de message :

```
Assisted-by: <identifiant du modèle, version comprise>
Prompt: <la demande, ou son résumé fidèle si elle était longue>
```

Exemple :

```
feat(api): valider les extraits mot pour mot

Assisted-by: claude-opus-5
Prompt: rejeter toute détection dont l'extrait ne se retrouve pas dans le texte
  source, après normalisation des espaces, et renvoyer les rejets au client
Signed-off-by: Prénom Nom <adresse@exemple.fr>
```

Trois détails de forme, parce qu'il s'agit de vraies lignes de fin (*trailers*) et que
`git interpret-trailers` doit pouvoir les relire :

- les clés sont sans accent, git n'acceptant que lettres, chiffres et tirets ;
- le bloc est **contigu**, sans ligne vide avant `Signed-off-by`, sinon seul le dernier
  paragraphe est reconnu ;
- une valeur longue se poursuit sur la ligne suivante avec une indentation.

La ligne `Signed-off-by` du [DCO](../DCO.txt) reste due, et elle porte le nom d'un humain :
c'est cet humain qui certifie avoir le droit d'apporter cette contribution sous AGPL-3.0.

Un commit qui ne fait que corriger, adapter ou intégrer du code généré ne porte pas
`Assisted-by` : il est le travail humain, et c'est justement la distinction que la
convention sert à rendre lisible.

Pour la documentation et les tests seuls, la déclaration générale de cette page suffit ;
la provenance par commit reste préférable.

## Droit d'auteur et licence

Deux conséquences dont le projet tient compte.

**Ce qui est purement généré n'est pas protégé.** En droit de l'Union, une production
obtenue sans contribution intellectuelle humaine substantielle n'ouvre pas de droit
d'auteur. Elle ne peut donc pas être apportée sous AGPL comme si elle l'était, ni facturée
comme travail humain à un financeur.

**Ce qui est généré ne doit pas reproduire l'œuvre d'autrui.** Une sortie d'assistant peut
reconstituer du code sous licence incompatible. La vigilance porte d'abord sur les blocs
longs et idiomatiques, qui sont les plus susceptibles d'être reconstitués plutôt
qu'écrits.

## Ce qu'on demande aux contributions extérieures

Vous pouvez utiliser un assistant. On vous demande de :

1. **le dire**, avec la convention de commit ci-dessus ;
2. **comprendre ce que vous proposez**, et pouvoir l'expliquer en revue ;
3. **vérifier la licence** de ce que l'assistant vous rend, comme vous le feriez d'un extrait
   trouvé ailleurs ;
4. **signer** avec le DCO, ce qui reste un engagement personnel.

Une contribution qu'un contributeur ne sait pas expliquer est refusée, assistant ou pas.
C'était déjà vrai avant.

## Journaux détaillés

Les transcriptions complètes des séances de développement ne sont pas publiées : elles
contiennent des secrets d'infrastructure et des données personnelles. Elles sont conservées
par le porteur et communicables sur demande à un financeur, caviardées de ces éléments. Les
journaux de provenance établis pour une candidature suivent ce format.
