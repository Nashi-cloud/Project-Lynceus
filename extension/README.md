# Lynceus Extension, the Chrome client (MV3)

**English** · [Français](README.fr.md)

TypeScript, Manifest V3, zero framework. Content extraction happens **locally in the browser** (Readability plus Turndown): paywalls and anti-robot protections have already been cleared by the user, and nothing leaves without their say-so.

## Build and install

```bash
cd extension
npm install
npm run build          # → dist/
```

Then in Chrome: `chrome://extensions`, turn on **Developer mode**, click **Load unpacked**, choose the `extension/dist` folder.

> **Chrome on the local machine, API on a remote development VM (Tailscale):** copy `dist/` back locally (`rsync -a vm:…/extension/dist/ ~/lynceus-extension/`), then in the extension settings point the instance at the **Tailscale address of the VM** (for example `http://100.x.y.z:8000`, visible with `tailscale status` on the VM). No SSH tunnel is needed: the tailnet is already encrypted and the VM's firewall only allows `tailscale0`. On the VM, start uvicorn listening on every interface so the tailnet can reach it: `uvicorn lynceus.main:creer_application --factory --host 0.0.0.0`. **Never expose the API on a public IP**: it has no authentication and carries an LLM key billed by usage.

## First run

On installation a welcome page opens and offers to turn on **automatic recognition** (badge on the icon, pre-filled panel, border on risky pages). Declining leaves the extension at the strict minimum: everything then goes through the right-click menu. The choice can be changed at any time in the settings, and a discreet invitation appears in the panel as long as the permission has not been granted.

> Chrome requires a permission request to come from a user click: turning it on cannot be automatic, only clearly offered.

## Use

1. **Analyse**: right click on a page, then "🔭 Analyse this page with Lynceus" (or click the icon and then the button). The side panel displays the card: A to E index, category, techniques found with their quoted passages, positive points, questions to ask yourself.
2. **Passive badge** (optional, off by default): turn it on in the settings. When a page you visit is already in the directory, its grade appears on the icon. Only a SHA-256 hash of the normalised URL is sent, never the URL and never the content.
3. **Settings**: the instance address (self-hosting is a first-class citizen), and a connection test that displays what the instance discloses (model, prompt version, size of the reference list).
4. **Site profile**: on a page not yet analysed, the panel shows what the directory already knows about the domain (number of pages analysed, average index, distribution). The information is free and immediate, and it is presented as being about *the site*, never about the current page, whose content has not been read.
5. **Page border**: on a page graded D or E (analysed explicitly, or recognised through the passive badge if it is on), a discreet border (colour taken from the grade pill: muted orange or muted red, never a screaming red) marks the page visually. It is removed automatically on navigation, or if a re-analysis gives a better grade.

## Permissions, and why so few

| Permission | Why | When |
|---|---|---|
| `activeTab` and `scripting` | extract the content of the page being analysed | only on an explicit gesture (context menu); one-shot access, expires on navigation |
| `sidePanel`, `contextMenus` | the interface | always |
| `storage` | the settings | always |
| `tabs` plus `http://*/*`, `https://*/*` | **optional, requested together**: knowing the URL continuously (the badge), adding and removing the border on passively recognised pages, making the panel's "Analyse" button reliable after navigation | only if the passive badge is turned on in the settings; handed back if it is turned off |

Without the passive badge turned on, no `host_permission` is held: calls to the instance go through the API's CORS, and any access to a page stays one-shot (an explicit gesture). The panel never opens by itself (charter §3), and rendering goes entirely through `textContent` (no injection is possible from the analysed content).

**A known limit without the badge on**: sites with internal navigation (single-page apps: YouTube, X/Twitter and the like) do not reload the page when the content changes; without the host permission the extension cannot detect that change, and the panel may show a stale card. Turning on the passive badge fixes that case (the address becomes continuously visible again).

## Layout

```
src/
├── fond.ts               # service worker: context menu, orchestration, badge, per-tab state
├── extracteur.ts         # injected on demand: Readability → Turndown → Markdown
├── commun/
│   ├── types.ts          # TS mirror of schema/carte-analyse.schema.json
│   ├── hachage.ts        # URL normalisation and SHA-256, AN EXACT MIRROR of the Python
│   ├── api.ts            # client of the instance (lookup, analyses)
│   ├── inscription.ts    # obtaining a key from a portal
│   ├── reglages.ts       # storage.sync, badge OFF by default
│   ├── i18n.ts           # chrome.i18n, French and English catalogues
│   ├── generations.ts    # analyses in flight: a cancelled result never reaches the panel
│   ├── troncature.ts     # shortening a page too long for the instance, and saying so
│   ├── veille.ts         # the panel's watch: telling "still working" from "nobody left"
│   ├── logo.svg          # logotype, single source (pages and icons)
│   └── lynceus.css       # design tokens and interface parts, twins of the portal's
├── _locales/             # fr and en message catalogues, read by Chrome itself
├── panneau/              # side panel (the analysis card)
├── options/              # settings
└── accueil/              # page opened on installation
polices/                  # Fraunces and Newsreader (OFL), embedded
icones/                   # PNGs generated by `npm run icones`
test/parite_normalisation.mjs  # guarantees TS hash == Python hash (12 reference URLs)
```

## Languages

The extension speaks French and English through Chrome's own mechanism (`_locales/<lang>/messages.json`, `chrome.i18n`): no library is bundled, and there is no language picker, because the browser chooses from its own interface language. French is the fallback, declared in the manifest (`default_locale`). The name, the description and the context menu entry follow, since they come from the manifest.

`test/traductions.test.mjs` refuses a string used without a translation, a string that has become useless, and a `$1` substitution lost from one language to another. Chrome does not report a missing key, it displays a blank.

The language of the *analysis* is a different matter: it follows the language of the page analysed, not the language of the browser. An analysis speaks first to whoever reads that page.

## Visual identity

The extension and the portal are one and the same object to whoever uses them: same palette, same logotype, same grade colours, same fonts. Since a `.zip` loaded into Chrome only has access to itself, and since fetching a stylesheet or a font over the network would signal every opening of the panel, everything is copied into the package. `test/identite.test.mjs` compares that copy against the portal's original and fails on the slightest divergence.

```bash
npm run icones     # regenerates icones/*.png from src/commun/logo.svg
```

The icons are not drawn by hand: they are computed from the logotype's path, with no dependency at all (see `icones.mjs`). The rendering is solid rather than outlined, because a stroke of 1.5 units out of 32 becomes half a pixel at 16x16, and the detail adapts to the size: no pupil below 32 px, no graduations below 48.

## Distributing the extension

```bash
npm run paquet     # → lynceus-extension-v<version>.zip
```

An archive ready to be shared or submitted to the Chrome Web Store. It is **reproducible**: two builds from the same sources produce an identical file (timestamps are fixed), which makes it possible to check that a distributed package really matches the published code.

## Checks

```bash
npm run verifier     # tsc --noEmit
npm test             # unit tests plus TypeScript ↔ Python normalisation parity
npm run test:parite  # only the hash parity with the Python API
```

The tests use Node's native runner (`node --test`), with no extra dependency. They cover URL normalisation, the settings (including the defaults that carry a privacy commitment), the API client (timeout, cancellation, error messages), the tracking of in-flight analyses and the translation catalogues. Logic that depends on the Chrome APIs stays outside that coverage: it is verified in real use.
