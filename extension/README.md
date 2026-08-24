# Lynceus Extension — client Chrome (MV3)

TypeScript, Manifest V3, zéro framework. L'extraction du contenu se fait **localement dans le navigateur** (Readability + Turndown) : paywalls et protections anti-robots déjà franchis par l'utilisateur, et rien ne part sans son geste.

## Construire et installer

```bash
cd extension
npm install
npm run build          # → dist/
```

Puis dans Chrome : `chrome://extensions` → activer le **Mode développeur** → **Charger l'extension non empaquetée** → choisir le dossier `extension/dist`.

> **Chrome sur le poste local, API sur une VM de dev distante (Tailscale) :** rapatriez `dist/` en local (`rsync -a vm:…/extension/dist/ ~/lynceus-extension/`), puis dans les réglages de l'extension mettez l'instance sur l'**adresse Tailscale de la VM** (ex. `http://100.x.y.z:8000`, visible avec `tailscale status` sur la VM) — pas de tunnel SSH nécessaire, le tailnet est déjà chiffré et le pare-feu de la VM n'autorise que `tailscale0`. Sur la VM, lancez uvicorn en écoutant sur toutes les interfaces pour que le tailnet y accède : `uvicorn lynceus.main:creer_application --factory --host 0.0.0.0`. **Ne jamais exposer l'API sur une IP publique** : elle n'a pas d'authentification et porte une clé LLM facturée à l'usage.

## Utilisation

1. **Analyser** : clic droit sur une page → « 🔭 Analyser cette page avec Lynceus » (ou clic sur l'icône puis bouton). Le panneau latéral affiche la carte : indice A–E, catégorie, techniques relevées avec extraits, points positifs, questions à se poser.
2. **Badge passif** (optionnel, désactivé par défaut) : à activer dans les réglages. Quand une page visitée est déjà dans l'annuaire, sa note s'affiche sur l'icône — seul un hash SHA-256 de l'URL normalisée est envoyé, jamais l'URL ni le contenu.
3. **Réglages** : adresse de l'instance (auto-hébergement de premier ordre), test de connexion affichant la transparence de l'instance (modèle, version du prompt, taille du référentiel).
4. **Contour de page** : après une analyse explicite jugée D ou E, un contour discret (couleur reprise de la pastille — orange sourd/rouge sourd, pas de rouge criard) signale visuellement la page. Retiré automatiquement à la navigation ou si une ré-analyse donne un meilleur grade. Ne s'applique jamais aux pages reconnues seulement par le badge passif (cela demanderait un accès à toutes les pages, hors du périmètre de permissions actuel).

## Permissions — philosophie

| Permission | Pourquoi | Quand |
|---|---|---|
| `activeTab` + `scripting` | extraire le contenu de la page analysée | uniquement sur geste explicite |
| `sidePanel`, `contextMenus` | l'interface | — |
| `storage` | les réglages | — |
| `tabs` | **optionnelle** — connaître l'URL des pages pour le badge passif | demandée seulement si le badge est activé, rendue s'il est désactivé |

Aucune `host_permission` : les appels à l'instance passent par le CORS de l'API. Le panneau ne s'ouvre jamais tout seul (charte §3), le rendu passe intégralement par `textContent` (aucune injection possible depuis le contenu analysé).

## Structure

```
src/
├── fond.ts               # service worker : menu contextuel, orchestration, badge, états par onglet
├── extracteur.ts         # injecté à la demande : Readability → Turndown → Markdown
├── commun/
│   ├── types.ts          # miroir TS de schema/carte-analyse.schema.json
│   ├── hachage.ts        # normalisation d'URL + SHA-256 — MIROIR EXACT du Python
│   ├── api.ts            # client de l'instance (lookup, analyses)
│   └── reglages.ts       # storage.sync, badge OFF par défaut
├── panneau/              # side panel (carte d'analyse)
└── options/              # réglages
test/parite_normalisation.mjs  # garantit hash TS == hash Python (12 URL de référence)
```

## Vérifications

```bash
npm run verifier   # tsc --noEmit
npm test           # parité de normalisation TypeScript ↔ Python
```
