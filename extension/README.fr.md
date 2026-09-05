# Lynceus Extension, client Chrome (MV3)

<!-- traduit-de: extension/README.md sha256:62dcfa5f06af760c -->

[English](README.md) · **Français**

TypeScript, Manifest V3, zéro framework. L'extraction du contenu se fait **localement dans le navigateur** (Readability + Turndown) : paywalls et protections anti-robots déjà franchis par l'utilisateur, et rien ne part sans son geste.

## Construire et installer

```bash
cd extension
npm install
npm run build          # → dist/
```

Puis dans Chrome : `chrome://extensions` → activer le **Mode développeur** → **Charger l'extension non empaquetée** → choisir le dossier `extension/dist`.

> **Chrome sur le poste local, API sur une VM de dev distante (Tailscale) :** rapatriez `dist/` en local (`rsync -a vm:…/extension/dist/ ~/lynceus-extension/`), puis dans les réglages de l'extension mettez l'instance sur l'**adresse Tailscale de la VM** (ex. `http://100.x.y.z:8000`, visible avec `tailscale status` sur la VM). Pas de tunnel SSH nécessaire : le tailnet est déjà chiffré et le pare-feu de la VM n'autorise que `tailscale0`. Sur la VM, lancez uvicorn en écoutant sur toutes les interfaces pour que le tailnet y accède : `uvicorn lynceus.main:creer_application --factory --host 0.0.0.0`. **Ne jamais exposer l'API sur une IP publique** : elle n'a pas d'authentification et porte une clé LLM facturée à l'usage.

## Premier lancement

À l'installation, une page d'accueil s'ouvre et propose d'activer la **reconnaissance automatique** (badge sur l'icône, panneau pré-rempli, contour sur les pages à risque). Refuser laisse l'extension au strict minimum : tout passe alors par le clic droit. Le choix reste modifiable à tout moment dans les réglages, et une invitation discrète est proposée dans le panneau tant que la permission n'est pas accordée.

> Chrome impose qu'une demande de permission parte d'un clic utilisateur : l'activation ne peut pas être automatique, seulement proposée clairement.

## Utilisation

1. **Analyser** : clic droit sur une page → « 🔭 Analyser cette page avec Lynceus » (ou clic sur l'icône puis bouton). Le panneau latéral affiche la carte : indice A–E, catégorie, techniques relevées avec extraits, points positifs, questions à se poser.
2. **Badge passif** (optionnel, désactivé par défaut) : à activer dans les réglages. Quand une page visitée est déjà dans l'annuaire, sa note s'affiche sur l'icône. Seul un hash SHA-256 de l'URL normalisée est envoyé, jamais l'URL ni le contenu.
3. **Réglages** : adresse de l'instance (auto-hébergement de premier ordre), test de connexion affichant la transparence de l'instance (modèle, version du prompt, taille du référentiel).
4. **Profil du site** : sur une page pas encore analysée, le panneau indique ce que l'annuaire sait déjà du domaine (nombre de pages analysées, indice moyen, répartition). L'information est gratuite et immédiate ; elle est présentée comme portant sur *le site*, jamais sur la page en cours, dont le contenu n'a pas été lu.
5. **Contour de page** : sur une page jugée D ou E (analysée explicitement, ou reconnue via le badge passif si activé), un contour discret (couleur reprise de la pastille : orange sourd ou rouge sourd, jamais de rouge criard) signale visuellement la page. Retiré automatiquement à la navigation ou si une ré-analyse donne un meilleur grade.

## Permissions, et pourquoi si peu

| Permission | Pourquoi | Quand |
|---|---|---|
| `activeTab` + `scripting` | extraire le contenu de la page analysée | uniquement sur geste explicite (menu contextuel) ; accès ponctuel, expire à la navigation |
| `sidePanel`, `contextMenus` | l'interface | toujours |
| `storage` | les réglages | toujours |
| `tabs` + `http://*/*`, `https://*/*` | **optionnelles, demandées ensemble** : connaître l'URL en continu (badge), poser/retirer le contour sur les pages reconnues passivement, fiabiliser le bouton « Analyser » du panneau après une navigation | uniquement si le badge passif est activé dans les réglages ; rendues si désactivé |

Sans le badge passif activé, aucune `host_permission` n'est détenue : les appels à l'instance passent par le CORS de l'API, et tout accès à une page reste ponctuel (geste explicite). Le panneau ne s'ouvre jamais tout seul (charte §3), le rendu passe intégralement par `textContent` (aucune injection possible depuis le contenu analysé).

**Limite connue sans le badge activé** : les sites à navigation interne (SPA : YouTube, X/Twitter, applications monopage) ne rechargent pas la page en changeant de contenu ; sans la permission d'hôte, l'extension ne peut pas détecter ce changement et le panneau peut afficher une carte périmée. Activer le badge passif corrige ce cas (l'adresse redevient visible en continu).

## Structure

```
src/
├── fond.ts               # service worker : menu contextuel, orchestration, badge, états par onglet
├── extracteur.ts         # injecté à la demande : Readability → Turndown → Markdown
├── commun/
│   ├── types.ts          # miroir TS de schema/carte-analyse.schema.json
│   ├── hachage.ts        # normalisation d'URL + SHA-256, MIROIR EXACT du Python
│   ├── api.ts            # client de l'instance (lookup, analyses)
│   ├── inscription.ts    # obtention d'une clé auprès d'un portail
│   ├── reglages.ts       # storage.sync, badge OFF par défaut
│   ├── i18n.ts           # chrome.i18n, catalogues français et anglais
│   ├── generations.ts    # analyses en vol : un résultat annulé n'atteint jamais le panneau
│   ├── troncature.ts     # raccourcit une page trop longue pour l'instance, et le signale
│   ├── veille.ts         # veille du panneau : distinguer « ça travaille » de « plus personne »
│   ├── logo.svg          # logotype, source unique (pages + icônes)
│   └── lynceus.css       # jetons et pièces d'interface, jumeaux de ceux du portail
├── _locales/             # catalogues fr et en, lus par Chrome lui-même
├── panneau/              # side panel (carte d'analyse)
├── options/              # réglages
└── accueil/              # page ouverte à l'installation
polices/                  # Fraunces + Newsreader (OFL), embarquées
icones/                   # PNG engendrés par `npm run icones`
test/parite_normalisation.mjs  # garantit hash TS == hash Python (12 URL de référence)
```

## Langues

L'extension parle français et anglais par le mécanisme natif de Chrome (`_locales/<langue>/messages.json`, `chrome.i18n`) : aucune bibliothèque embarquée, et pas de sélecteur, puisque le navigateur choisit d'après sa propre langue d'interface. Le français est la langue de repli, déclarée dans le manifeste (`default_locale`). Le nom, la description et l'entrée du menu contextuel suivent, puisqu'ils viennent du manifeste.

`test/traductions.test.mjs` refuse une phrase employée sans traduction, une phrase devenue inutile, et une substitution `$1` perdue d'une langue à l'autre. Chrome ne signale pas une clé absente, il affiche un blanc.

La langue de l'*analyse* est une autre affaire : elle suit la langue de la page analysée, pas celle du navigateur. Une analyse s'adresse d'abord à qui lit cette page-là.

## Identité visuelle

L'extension et le portail sont le même objet aux yeux de qui les utilise : même palette, même logotype, mêmes couleurs de grade, mêmes polices. Comme un `.zip` chargé dans Chrome n'a accès qu'à lui-même, et qu'aller chercher une feuille de style ou une police sur le réseau reviendrait à signaler chaque ouverture du panneau, tout est recopié dans le paquet. `test/identite.test.mjs` compare cette copie à l'original du portail et échoue à la moindre divergence.

```bash
npm run icones     # réengendre icones/*.png depuis src/commun/logo.svg
```

Les icônes ne sont pas dessinées à la main : elles sont calculées depuis le tracé du logotype, sans aucune dépendance (voir `icones.mjs`). Le rendu est plein plutôt qu'au trait, parce qu'un trait de 1,5 unité sur 32 devient un demi-pixel à 16x16, et le détail s'adapte à la taille : pas de pupille en dessous de 32 px, pas de graduations en dessous de 48.

## Distribuer l'extension

```bash
npm run paquet     # → lynceus-extension-v<version>.zip
```

Archive prête à être partagée ou soumise au Chrome Web Store. Elle est **reproductible** : deux constructions des mêmes sources produisent un fichier identique (horodatages fixés), ce qui permet de vérifier qu'un paquet distribué correspond bien au code publié.

## Vérifications

```bash
npm run verifier     # tsc --noEmit
npm test             # tests unitaires + parité de normalisation TypeScript ↔ Python
npm run test:parite  # uniquement la parité de hachage avec l'API Python
```

Les tests utilisent le lanceur natif de Node (`node --test`), sans dépendance supplémentaire. Ils couvrent la normalisation d'URL, les réglages (dont les défauts qui engagent la vie privée), le client API (délai, annulation, messages d'erreur), le suivi des analyses en vol et les catalogues de traduction. La logique dépendant des API Chrome reste hors couverture : elle se vérifie en usage réel.
