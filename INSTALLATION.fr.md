# Installer Lynceus

<!-- traduit-de: INSTALLATION.md sha256:7b538860179faf2d -->

[English](INSTALLATION.md) · **Français**

Deux façons d'utiliser Lynceus, selon ce que vous cherchez.

| | **Extension seule** | **Kit complet** |
|---|---|---|
| Ce que vous installez | l'extension Chrome | l'extension **et** votre propre serveur |
| Il vous faut | l'adresse d'une instance Lynceus (`lynx.nashi.cloud`, ou la vôtre) | une machine (ou un PC) et 20 minutes |
| Vos données | passent par l'instance choisie | ne quittent jamais vos machines |
| Coût | aucun | celui du modèle d'IA que vous choisissez (ou zéro avec un modèle local) |

> **Une instance publique de référence existe : [lynx.nashi.cloud](https://lynx.nashi.cloud).** Elle délivre une clé d'accès en un clic, sans compte ni adresse électronique. Le kit complet reste la voie la plus respectueuse de votre vie privée, puisque rien ne quitte alors vos machines.

---

## Le kit complet, pas à pas

### Ce qu'il vous faut

- Un ordinateur sous Linux, macOS ou Windows, allumé quand vous naviguez (un mini-PC ou un Raspberry Pi 4 suffisent).
- **Python 3.11 ou plus récent** : vérifiez avec `python3 --version`.
- **Node.js 20 ou plus récent** : vérifiez avec `node --version`.
- Un accès à un modèle de langage. Deux possibilités :
  - **Un service en ligne** (OpenRouter, par exemple) : quelques centimes par analyse, aucune installation ;
  - **Un modèle local** avec [Ollama](https://ollama.com) : gratuit et privé, mais demande une machine costaude et donne des analyses moins fines.

### 1. Récupérer Lynceus

```bash
git clone https://github.com/Nashi-cloud/Project-Lynceus.git Lynceus
cd Lynceus
```

### 2. Installer le serveur

```bash
cd api
python3 -m venv .venv
.venv/bin/pip install -e .
```

### 3. Le configurer

```bash
cp .env.example .env
```

Ouvrez `.env` dans un éditeur de texte et renseignez au minimum votre clé :

```ini
LYNCEUS_LLM_API_KEY=votre-clé-ici
LYNCEUS_LLM_BASE_URL=https://openrouter.ai/api/v1
LYNCEUS_LLM_MODEL=z-ai/glm-5.2
```

*Avec Ollama à la place :*

```ini
LYNCEUS_LLM_BASE_URL=http://localhost:11434/v1
LYNCEUS_LLM_MODEL=llama3.1
LYNCEUS_LLM_API_KEY=ollama
```

### 4. Démarrer le serveur

```bash
.venv/bin/uvicorn lynceus.main:creer_application --factory
```

Laissez cette fenêtre ouverte. Pour vérifier que tout va bien, ouvrez <http://localhost:8000/v1/meta> dans votre navigateur : vous devez voir apparaître le nom du modèle configuré.

> **Le navigateur est sur une autre machine que le serveur ?** Démarrez avec `--host 0.0.0.0` et indiquez l'adresse de la machine dans les réglages de l'extension. **N'exposez jamais le serveur sur Internet** : il n'a pas d'authentification et votre clé y est configurée. Un réseau privé (VPN, [Tailscale](https://tailscale.com)) est la bonne solution.

### 5. Installer l'extension

Dans une autre fenêtre de terminal :

```bash
cd Lynceus/extension
npm install
npm run build
```

Puis dans Chrome :

1. ouvrez `chrome://extensions` ;
2. activez le **Mode développeur** (interrupteur en haut à droite) ;
3. cliquez sur **Charger l'extension non empaquetée** ;
4. choisissez le dossier `Lynceus/extension/dist`.

Une page d'accueil s'ouvre et vous propose d'activer la reconnaissance automatique. À vous de voir : sans elle, tout passe par le clic droit.

### 6. Essayer

Allez sur n'importe quel article, faites un **clic droit → « 🔭 Analyser cette page avec Lynceus »**. Le panneau s'ouvre sur la droite et l'analyse arrive en quelques secondes.

---

## Avec Docker (plus simple si vous connaissez)

```bash
cd api
LYNCEUS_LLM_API_KEY=votre-clé docker compose up --build
```

Le serveur et sa base PostgreSQL démarrent ensemble. L'extension s'installe comme ci-dessus.

L'image est aussi **publiée**, si vous préférez ne rien construire :

```bash
LYNCEUS_IMAGE=ghcr.io/nashi-cloud/lynceus-api:latest \
LYNCEUS_LLM_API_KEY=votre-clé docker compose up --pull always --no-build
```

Le premier démarrage est alors immédiat plutôt que de quelques minutes. Construire reste la
voie à suivre si vous comptez modifier le code, ce que la licence vous encourage à faire.

---

## Questions courantes

**Combien ça coûte ?**
Chaque page n'est analysée qu'une seule fois : ensuite elle est en cache, gratuitement et instantanément, pour tous les utilisateurs de votre instance. Comptez quelques centimes par nouvelle analyse selon le modèle choisi, ou rien du tout avec Ollama.

**Mes pages visitées sont-elles envoyées quelque part ?**
Le contenu d'une page n'est transmis que lorsque **vous** demandez une analyse. Si vous activez la reconnaissance automatique, seule une empreinte partielle de l'adresse circule (cinq caractères, partagés par plus d'un million d'adresses possibles) : votre instance ne peut pas savoir quelle page vous consultez. Rien n'est journalisé.

**« Instance Lynceus injoignable »**
Le serveur est-il démarré ? L'adresse dans les réglages de l'extension correspond-elle ? Après avoir modifié `.env`, il faut **redémarrer le serveur** : ce fichier n'est lu qu'au démarrage.

**Certains sites refusent l'analyse**
Les sites protégés contre les robots (Cloudflare et autres) bloquent le serveur, mais pas votre navigateur. C'est justement pourquoi l'extension extrait le contenu localement : passez par le clic droit plutôt que par la ligne de commande.

**Je veux arrêter**
Retirez l'extension depuis `chrome://extensions`, arrêtez le serveur (Ctrl+C) et supprimez le dossier. Rien ne subsiste ailleurs.

---

## Aller plus loin

- [Charte éthique](docs/ETHIQUE.md) : ce que Lynceus s'interdit, et pourquoi
- [Méthodologie](docs/METHODOLOGIE.md) : comment la note est calculée
- [Taxonomie](docs/TAXONOMIE.md) : les 31 techniques détectées
- [Architecture](docs/ARCHITECTURE.md) : pour les développeurs
- [Contribuer](CONTRIBUTING.fr.md) : code, taxonomie, traductions, hébergement
