# Journal des versions de l'extension Lynceus

Le numéro de version se voit dans `chrome://extensions` (mode développeur) et en bas de la page **Réglages** de l'extension : utile pour vérifier qu'un rebuild a bien été rechargé.

## 0.9.3 (2026-08-25)

- **docs** : la page d'accueil et les réglages annoncent désormais que le texte d'une page analysée est transmis par l'instance au fournisseur de modèle de langage qu'elle utilise, parfois hors de l'Union européenne. L'extension promettait la vie privée sans mentionner le seul transfert que son utilisateur ne peut pas éviter. Le remède est indiqué dans la même phrase : une instance auto-hébergée avec un modèle local n'envoie rien au dehors.

## 0.9.2 (2026-08-25)

- **feat** : l'extension lit l'adresse du portail dans `portail.json`, fichier que le portail glisse dans l'archive au moment du téléchargement. Une extension téléchargée depuis un portail propose donc « Obtenir une clé » sans qu'on ait rien à saisir, alors même que le paquet publié est neutre et valable pour n'importe quel portail. L'option de compilation `--portail=` reste prioritaire, pour un paquet qu'on construit soi-même.
- **security** : l'adresse lue dans l'archive est validée comme n'importe quelle donnée reçue d'un serveur. Une adresse qui n'est pas en http(s) est ignorée plutôt que proposée.

## 0.9.1 (2026-08-25)

- **docs** : suppression des tirets cadratins dans tous les textes visibles de l'extension (page d'accueil, réglages, panneau, messages d'erreur), reformulés plutôt que substitués. Demande explicite de l'utilisateur.

## 0.9.0 (2026-08-25)

- **feat** : **inscription en un clic**. Un bouton « Obtenir une clé d'accès » interroge un portail Lynceus, qui renvoie une clé *et* l'adresse de l'instance à laquelle elle donne accès : l'extension se configure seule. Aucun compte, aucune adresse électronique, aucun identifiant : la clé ne porte qu'une date d'expiration et un quota. Proposé sur la page d'accueil dès l'installation, et disponible à tout moment dans les réglages.
- **feat** : nouveau réglage « portail », distinct de l'instance. Le portail délivre les clés, l'instance analyse ; un auto-hébergeur n'a besoin d'aucun portail.
- **feat** : un paquet peut être construit avec l'adresse de son portail (`node build.mjs --paquet --portail=https://…`), si bien qu'une extension téléchargée depuis un portail arrive déjà configurée sur lui.
- **security** : la réponse d'un portail est vérifiée avant d'être appliquée, car c'est elle qui décide de l'instance vers laquelle partiront les pages analysées. Une clé mal formée ou une instance dont l'adresse n'est pas en http(s) est refusée, et l'interface affiche l'instance retenue au lieu de la configurer en silence.

## 0.8.0 (2026-08-24)

- **feat** : réglage d'une clé d'accès, pour les instances qui en demandent une. La clé accompagne les analyses ; les consultations d'annuaire restent libres. Une clé Lynceus n'est pas un compte : elle ne contient aucune information sur son porteur, seulement une date d'expiration et un quota journalier.
- **feat** : le test de connexion indique si l'instance exige une clé, et un refus explique quoi faire plutôt que d'afficher un code d'erreur.

## 0.7.0 (2026-08-24)

- **feat** : sur une page pas encore analysée, le panneau affiche ce que l'annuaire sait déjà **du site** : nombre de pages analysées, indice moyen, répartition des notes. L'information est immédiate et ne coûte rien. Formulation volontairement prudente : elle décrit d'autres pages du site, jamais celle qu'on lit, dont le contenu n'a pas été examiné.
- **feat** : les articles dépassant la taille analysable de l'instance sont désormais raccourcis (à une frontière de paragraphe quand c'est possible) au lieu d'être refusés. La carte porte la mention que seul le début a été examiné : elle est mise en cache et resservie à d'autres lecteurs, elle doit donc le dire.
- **refactor** : logique de raccourcissement extraite dans `commun/troncature.ts`, testable sans navigateur.

## 0.6.0 (2026-08-24)

- **feat** : consultation d'annuaire en **k-anonymat** (technique HaveIBeenPwned). Seuls les 5 premiers caractères de l'empreinte d'URL sont envoyés, soit un seau partagé par plus d'un million d'adresses possibles, et la correspondance finale se fait dans le navigateur. L'instance ne peut plus déterminer quelle page est consultée. Activé automatiquement quand l'instance l'annonce, avec repli sur le mode historique sinon.
- **feat** : la carte complète n'est chargée que si le panneau est réellement ouvert ; un badge se contente du résumé reçu avec le préfixe. Moins d'informations transmises, et moins de requêtes.
- **feat** : contestation d'une analyse depuis le panneau (« Contester cette analyse ») avec sept motifs, dont un droit de réponse pour les éditeurs des sites analysés. Le nombre de contestations déjà enregistrées est affiché.

## 0.5.1 (2026-08-24)

- **fix** : chaque requête réussie laissait un minuteur armé jusqu'à son échéance (jusqu'à 5 minutes), maintenant le service worker éveillé sans raison. Le minuteur est désormais libéré dans tous les cas, succès compris. Défaut révélé par les nouveaux tests, dont le processus refusait de se terminer.
- **test** : 32 tests unitaires ajoutés (lanceur natif `node --test`) couvrant la normalisation d'URL, les réglages, le client API (délai, annulation, messages d'erreur) et le suivi des analyses en vol.
- **refactor** : la logique d'annulation par génération quitte `fond.ts` pour `commun/generations.ts` (`SuiviAnalyses`), testable sans navigateur.

## 0.5.0 (2026-08-24)

- **feat** : page d'accueil à l'installation, proposant explicitement la reconnaissance automatique (badge, panneau pré-rempli, contour) avec un bouton d'activation. Jusqu'ici il fallait deviner l'existence des réglages et y cocher une case. Chrome exige qu'une demande de permission parte d'un clic réel : l'activation reste donc un geste, mais elle est désormais proposée au bon moment.
- **feat** : invitation discrète dans le panneau (écran « Analyser cette page ? ») pour activer la reconnaissance automatique, affichée uniquement si la permission n'est pas déjà accordée.
- **feat** : le réglage suit désormais les permissions accordées ou retirées depuis Chrome lui-même (`permissions.onAdded` et `onRemoved`) : plus de désynchronisation entre l'état réel et la case des réglages.

## 0.4.0 (2026-08-24)

- **fix** : aucun délai limite sur l'appel réseau d'une analyse. Une connexion bloquée faisait tourner le panneau indéfiniment, sans retour ni moyen d'agir. Signalé après un cas réel sur YouTube.
- **feat** : délai configurable dans les réglages (défaut 300 s, filet de sécurité, le serveur ayant son propre plafond à 360 s au pire avec retry), au-delà duquel une analyse bloquée est abandonnée automatiquement avec un message explicite.
- **feat** : chronomètre visible dans le panneau pendant l'extraction et l'analyse, et bouton « Annuler » à tout moment : plus besoin d'attendre en aveugle.
- Aucun risque de coût incontrôlé côté fournisseur LLM : le serveur ne retente jamais plus d'une fois une analyse (180 s × 2 maximum), documenté dans `api/.env.example` (`LYNCEUS_LLM_TIMEOUT_S`).

## 0.3.0 (2026-08-24)

- **fix** : le titre affiché pouvait rester celui de la page précédente sur un site à navigation interne (SPA comme YouTube), le contenu du corps de page et le `<title>` du document n'étant pas mis à jour au même instant par le site. L'extraction attend désormais que le titre se stabilise avant de lire la page.
- **feat** : permission d'hôte optionnelle (`http://*/*`, `https://*/*`), demandée avec `tabs` uniquement si le badge passif est activé. Corrige trois limites liées : le contour de page ne s'appliquait qu'après une analyse explicite, les sites à navigation interne (YouTube) n'étaient pas détectés en cas de changement de contenu sans rechargement, et le bouton « Analyser cette page » du panneau perdait l'accès à la page après une navigation (l'accès accordé par le clic droit est ponctuel).

## 0.2.0 (2026-08-24)

- **feat** : contour discret autour de la page pour les analyses jugées D ou E (couleur reprise de la pastille de note, pas de rouge criard), retiré automatiquement à la navigation ou si une ré-analyse donne un meilleur grade.
- **fix** : le panneau restait figé sur l'ancienne carte en changeant de page dans le même onglet : le rafraîchissement ne dépendait que du changement d'onglet, jamais de la navigation elle-même, et l'état n'était jamais explicitement repoussé au panneau.

## 0.1.1 (2026-08-24)

- **fix** : le lookup passif (badge sur l'icône) fonctionnait, mais n'alimentait jamais l'état lu par le panneau. Ouvrir le panneau sur une page déjà connue de l'annuaire affichait quand même l'écran « Analyser cette page ? ». Le panneau affiche désormais directement la carte, sans déclencher d'analyse.

## 0.1.0 (2026-08-24)

Version initiale : extraction locale (Readability + Turndown), side panel, menu contextuel, badge passif opt-in (permission `tabs` optionnelle), réglages avec instance configurable.
