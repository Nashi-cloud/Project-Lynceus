# Installing Lynceus

**English** · [Français](INSTALLATION.fr.md)

Two ways to use Lynceus, depending on what you are after.

| | **Extension only** | **Full kit** |
|---|---|---|
| What you install | the Chrome extension | the extension **and** your own server |
| What you need | the address of a Lynceus instance (`lynx.nashi.cloud`, or your own) | a machine (or a PC) and 20 minutes |
| Your data | goes through the instance you chose | never leaves your own machines |
| Cost | none | whatever the AI model you choose costs (or nothing, with a local model) |

> **A public reference instance is up: [lynx.nashi.cloud](https://lynx.nashi.cloud).** It issues an access key in one click, with no account and no email address. The full kit remains the option that respects your privacy most, since nothing then leaves your own machines.

---

## The full kit, step by step

### What you need

- A computer running Linux, macOS or Windows, switched on while you browse (a mini PC or a Raspberry Pi 4 is enough).
- **Python 3.11 or newer**: check with `python3 --version`.
- **Node.js 20 or newer**: check with `node --version`.
- Access to a language model. Two options:
  - **An online service** (OpenRouter, for instance): a few cents per analysis, nothing to install;
  - **A local model** with [Ollama](https://ollama.com): free and private, but it needs a beefy machine and gives coarser analyses.

### 1. Get Lynceus

```bash
git clone https://github.com/Nashi-cloud/Project-Lynceus.git Lynceus
cd Lynceus
```

### 2. Install the server

```bash
cd api
python3 -m venv .venv
.venv/bin/pip install -e .
```

### 3. Configure it

```bash
cp .env.example .env
```

Open `.env` in a text editor and fill in at least your key:

```ini
LYNCEUS_LLM_API_KEY=your-key-here
LYNCEUS_LLM_BASE_URL=https://openrouter.ai/api/v1
LYNCEUS_LLM_MODEL=z-ai/glm-5.2
```

*With Ollama instead:*

```ini
LYNCEUS_LLM_BASE_URL=http://localhost:11434/v1
LYNCEUS_LLM_MODEL=llama3.1
LYNCEUS_LLM_API_KEY=ollama
```

### 4. Start the server

```bash
.venv/bin/uvicorn lynceus.main:creer_application --factory
```

Leave that window open. To check everything is fine, open <http://localhost:8000/v1/meta> in your browser: you should see the name of the model you configured.

> **Is the browser on a different machine from the server?** Start with `--host 0.0.0.0` and put the machine's address in the extension settings. **Never expose the server on the open internet**: it has no authentication and your key is configured in it. A private network (VPN, [Tailscale](https://tailscale.com)) is the right answer.

### 5. Install the extension

In another terminal window:

```bash
cd Lynceus/extension
npm install
npm run build
```

Then in Chrome:

1. open `chrome://extensions`;
2. turn on **Developer mode** (the switch at the top right);
3. click **Load unpacked**;
4. choose the `Lynceus/extension/dist` folder.

A welcome page opens and offers to turn on automatic recognition. Up to you: without it, everything goes through the right-click menu.

### 6. Try it

Go to any article and **right click, then "🔭 Analyse this page with Lynceus"**. The panel opens on the right and the analysis arrives within seconds.

---

## With Docker (simpler if you already know it)

```bash
cd api
LYNCEUS_LLM_API_KEY=your-key docker compose up --build
```

The server and its PostgreSQL database start together. The extension is installed as above.

---

## Common questions

**How much does it cost?**
Each page is analysed only once: after that it is cached, free and instant, for every user of your instance. Reckon on a few cents per new analysis depending on the model you chose, or nothing at all with Ollama.

**Are the pages I visit sent anywhere?**
The content of a page is only transmitted when **you** ask for an analysis. If you turn on automatic recognition, only a partial digest of the address travels (five characters, shared by more than a million possible addresses): your instance cannot tell which page you are reading. Nothing is logged.

**"Lynceus instance unreachable"**
Is the server running? Does the address in the extension settings match? After editing `.env` you must **restart the server**: that file is only read at startup.

**Some sites refuse to be analysed**
Sites protected against robots (Cloudflare and the like) block the server, but not your browser. That is exactly why the extension extracts the content locally: use the right-click menu rather than the command line.

**I want to stop**
Remove the extension from `chrome://extensions`, stop the server (Ctrl+C) and delete the folder. Nothing survives anywhere else.

---

## Going further

- [Ethical charter](docs/en/ETHIQUE.md): what Lynceus forbids itself, and why
- [Methodology](docs/en/METHODOLOGIE.md): how the grade is computed
- [Taxonomy](docs/en/TAXONOMIE.md): the 31 techniques detected
- [Architecture](docs/en/ARCHITECTURE.md): for developers
- [Contributing](CONTRIBUTING.md): code, taxonomy, translations, hosting
