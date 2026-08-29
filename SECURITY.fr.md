# Politique de sécurité

<!-- traduit-de: SECURITY.md sha256:bb2cfa2a50cc4477 -->

[English](SECURITY.md) · **Français**

## Signaler une vulnérabilité

Passez par le **[signalement privé de vulnérabilité](https://github.com/Nashi-cloud/Project-Lynceus/security/advisories/new)** de ce dépôt. Il ouvre un canal privé entre vous et le mainteneur, et c'est le bon endroit même si vous n'êtes pas certain que ce que vous avez trouvé en soit une.

Merci de ne pas ouvrir de ticket public pour un problème de sécurité, et de laisser au mainteneur le temps de corriger avant d'en parler publiquement. Il y a un seul mainteneur et aucun engagement de délai : comptez un accusé de réception en quelques jours, pas en quelques heures. Le dire franchement vaut mieux que d'annoncer un délai que personne ne pourrait tenir.

## Ce qui entre dans le périmètre

- **L'API d'annuaire** (`api/`) : vérification des clés d'accès, quota journalier, limite de débit, consultation k-anonyme, et tout ce qui permettrait de dépenser le budget de modèle d'un exploitant ou de lire ce qu'on ne devrait pas.
- **Le portail** (`lynceus.portail`) : délivrance et signature des clés. La clé privée Ed25519 est le secret le plus sensible du projet, puisqu'elle émet des clés valables sur une instance.
- **L'extension** : tout ce qui permettrait à une page analysée de sortir de son onglet, ou d'envoyer un contenu sans que l'utilisateur l'ait demandé.
- **Les promesses de vie privée**, qui sont des affirmations vérifiables et non des intentions : aucun historique de navigation stocké, aucun couple adresse IP et URL journalisé, la consultation par préfixe qui ne rend jamais l'empreinte entière. Démontrer que l'une d'elles est fausse, c'est une vulnérabilité.

## Ce qui n'en est pas une

**Une analyse que vous jugez fausse, injuste ou orientée.** La carte le dit elle-même : elle est produite par un modèle de langage et peut se tromper. C'est à cela que sert la contestation, `POST /v1/signalements` ou le lien « Contester cette analyse » présent sur chaque carte, y compris pour les éditeurs des sites analysés. Voir le §6 de la [charte éthique](docs/ETHIQUE.md).

**Le fait que le texte d'une page parvienne à un fournisseur de modèle.** C'est le flux le plus important du système, il est annoncé en tête de la politique de confidentialité de chaque instance, et le remède fait partie du livrable : auto-hébergez avec un modèle local et rien ne quitte votre machine. Voir [docs/CONFORMITE.md](docs/CONFORMITE.md).

**Une instance tierce mal configurée.** Lynceus est auto-hébergeable et sans autorité centrale. Une instance exposée sans clés d'accès, ou faisant tourner une version modifiée, relève de qui l'exploite. Signalez-le-lui. Si le défaut est dans ce que ce dépôt livre, alors il entre dans le périmètre et nous voulons le savoir.

## Versions suivies

La dernière publiée sur `main`. Les tags antérieurs ne reçoivent pas de correctif : les instances sont censées suivre, et se mettre à jour tient dans un `pull`.

## Si vous exploitez une instance

Les deux points à vérifier en premier, tous deux documentés dans [api/DEPLOIEMENT.fr.md](api/DEPLOIEMENT.fr.md) :

- la **clé privée ne doit pas vivre sur l'instance**. Elle appartient à qui émet les clés. Compromettre l'instance ne doit pas permettre d'en forger ;
- `LYNCEUS_ENTETE_IP_REELLE` ne doit être défini que si l'instance est joignable **uniquement** par votre proxy. Un en-tête HTTP se falsifie sans peine, et le poser sur une instance joignable en direct offre la limite de débit à n'importe qui.
