# Journal des versions — extension Lynceus

Le numéro de version se voit dans `chrome://extensions` (mode développeur) et en bas de la page **Réglages** de l'extension — utile pour vérifier qu'un rebuild a bien été rechargé.

## 0.3.0 — 2026-08-24

- **fix** : le titre affiché pouvait rester celui de la page précédente sur un site à navigation interne (SPA — YouTube…), le contenu du corps de page et le `<title>` du document n'étant pas mis à jour au même instant par le site. L'extraction attend désormais que le titre se stabilise avant de lire la page.
- **feat** : permission d'hôte optionnelle (`http://*/*`, `https://*/*`), demandée avec `tabs` uniquement si le badge passif est activé. Corrige trois limites liées : le contour de page ne s'appliquait qu'après une analyse explicite, les sites à navigation interne (YouTube) n'étaient pas détectés en cas de changement de contenu sans rechargement, et le bouton « Analyser cette page » du panneau perdait l'accès à la page après une navigation (l'accès accordé par le clic droit est ponctuel).

## 0.2.0 — 2026-08-24

- **feat** : contour discret autour de la page pour les analyses jugées D ou E (couleur reprise de la pastille de note — pas de rouge criard), retiré automatiquement à la navigation ou si une ré-analyse donne un meilleur grade.
- **fix** : le panneau restait figé sur l'ancienne carte en changeant de page dans le même onglet — le rafraîchissement ne dépendait que du changement d'onglet, jamais de la navigation elle-même, et l'état n'était jamais explicitement repoussé au panneau.

## 0.1.1 — 2026-08-24

- **fix** : le lookup passif (badge sur l'icône) fonctionnait, mais n'alimentait jamais l'état lu par le panneau — ouvrir le panneau sur une page déjà connue de l'annuaire affichait quand même l'écran « Analyser cette page ? ». Le panneau affiche désormais directement la carte, sans déclencher d'analyse.

## 0.1.0 — 2026-08-24

Version initiale : extraction locale (Readability + Turndown), side panel, menu contextuel, badge passif opt-in (permission `tabs` optionnelle), réglages avec instance configurable.
