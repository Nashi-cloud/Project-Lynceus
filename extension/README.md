# Lynceus Extension — client Chrome (phase 2)

TypeScript, Manifest V3.

## Comportement

1. **Badge passif** (désactivable) : à la navigation, `GET /v1/lookup` avec le hash SHA-256 de l'URL normalisée — aucun contenu envoyé. Page connue → grade affiché en badge sur l'icône (couleurs sobres, style Nutri-Score). Domaine connu → indication du profil de domaine.
2. **Analyse volontaire** : menu contextuel « 🔭 Analyser cette page avec Lynceus » (ou clic sur l'icône) → extraction locale Readability.js → Markdown (Turndown) → `POST /v1/analyses` → carte affichée dans le **side panel**.
3. Le side panel ne s'ouvre **jamais** tout seul (cf. docs/ETHIQUE.md §3).

## UI du side panel

- En tête : grade A–E + catégorie + indice de confiance — lisible en 2 secondes.
- Dépliable : dimensions, puis techniques détectées (extrait surligné + explication), points positifs, questions à se poser.
- Pied : « analyse produite par une IA, contestable » + lien signalement + version du prompt (transparence).
- Registre visuel : neutre et pédagogique. Pas de rouge criard, pas d'icônes anxiogènes.

## Permissions (minimales)

`sidePanel`, `contextMenus`, `activeTab` (extraction au clic uniquement), `storage` (réglages : URL de l'instance, badge on/off). Pas de `tabs`/`<all_urls>` en lecture permanente si le badge passif est désactivé.

## Réglages

- URL de l'instance (défaut : instance de référence ; auto-hébergement possible).
- Badge passif : activé/désactivé.
- Langue de l'interface.
