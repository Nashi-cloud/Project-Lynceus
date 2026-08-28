# Deploying a Lynceus instance

**English** · [Français](DEPLOIEMENT.fr.md)

For hosting an instance meant for other people: your family and friends, a group, or in time the public.

> For strictly personal use, [INSTALLATION.md](../INSTALLATION.md) is enough: none of this is needed.

## What changes the moment an instance is exposed

| | Personal use | Exposed instance |
|---|---|---|
| Database | SQLite | PostgreSQL |
| Access | open | **access keys mandatory** |
| Encryption | pointless (localhost) | **HTTPS mandatory** |
| Restart | manual | automatic |

The non-negotiable rule: **your LLM key is billed by usage**. An exposed instance without access keys lets anyone spend your money. The production compose file refuses to start without `LYNCEUS_CLE_PUBLIQUE`.

## 1. Preparing the secrets

One command asks the questions and generates every variable, secrets included:

```bash
lynceus env production     # two blocks: the instance, then the portal
lynceus env recette        # a single block, for the staging stack
```

In a terminal it asks for what it cannot guess: registry address, model provider key, public addresses, tunnel tokens, legal identity. Any answer may be left empty, in which case the variable stays to be filled in. Two questions deserve a pause:

- **the tunnel token is asked for twice** in production. Two machines, two tunnels, two tokens: copying the same one on both sides gives you a second tunnel that connects and serves the wrong service;
- **is the instance reachable only through the tunnel?** Answering yes enables `LYNCEUS_ENTETE_IP_REELLE`. A header can be forged: on an instance reachable directly, trusting it lets anyone bypass the rate limit by announcing whatever address they like.

Without a local installation, the same command lives in the image:

```bash
docker run --rm <registry>/lynceus-api:latest lynceus env production
```

What is generated is generated **once**: PostgreSQL password, admin token, and above all **a single key pair for both blocks**. The easiest mistake to make is calling `cles-paire` twice and deploying a portal that signs with a key the instance does not recognise; sign-up then answers correctly, and it is the instance that refuses the key, later, at the user's end.

What only you know stays **empty**: registry address, model provider key, tunnel token, public addresses, legal identity. That is deliberate. A sample value would let the stack start and fail on the first analysis; empty, Compose refuses to start and names the missing variable.

Explanations and questions go to standard error, variables to standard output, so the file can be written directly. Redirected, the command asks nothing and returns a template with blanks, which suits scripts.

```bash
lynceus env recette > .env      # a template to fill in
lynceus env recette | tee .env  # questions asked, file written
```

In production the output contains **two files**, one per machine, carrying the same variable names with different values. A comment marker separates the blocks: cut there. Pasting both into a single `.env` would let the second win with nothing to signal it.

To reconfigure a single machine later, without reissuing the keys already handed out:

```bash
lynceus env production --cle-privee <the existing private key>
```

The public key is derived from the private one, so there is only one secret to keep.

Keep the **private key** off the machine hosting the instance: it is what allows keys to be issued, and the instance does not need it. If the server is compromised, nobody will be able to issue keys in your name.

> The output contains secrets in the clear. It has no business in a ticket, a repository, or a conversation.

## Every variable has two names

The code of this project is in French and will stay that way. An environment variable,
though, is not code: it is the operator's door, the one they open with this guide beside
them. Each therefore answers to two names, one French, one English.

Nothing to change on an existing instance: the French name remains the canonical one, it is
what `lynceus env` generates, and it wins if both are set. Setting both to different values
raises a warning at startup, because a setting ignored in silence is the kind of failure
that costs an evening.

The last two lines are read by Compose rather than by the application: the substitution
there is nested, and the effect is the same.

| Canonical name | English alias |
|---|---|
| `LYNCEUS_ANALYSES_SIMULTANEES` | `LYNCEUS_CONCURRENT_ANALYSES` |
| `LYNCEUS_BDD_MAX_OVERFLOW` | `LYNCEUS_DB_MAX_OVERFLOW` |
| `LYNCEUS_BDD_POOL_RECYCLE_S` | `LYNCEUS_DB_POOL_RECYCLE_S` |
| `LYNCEUS_BDD_POOL_SIZE` | `LYNCEUS_DB_POOL_SIZE` |
| `LYNCEUS_CLES_REVOQUEES` | `LYNCEUS_REVOKED_KEYS` |
| `LYNCEUS_CLE_PUBLIQUE` | `LYNCEUS_PUBLIC_KEY` |
| `LYNCEUS_CONTENU_MAX_CARS` | `LYNCEUS_CONTENT_MAX_CHARS` |
| `LYNCEUS_CONTENU_MIN_CARS` | `LYNCEUS_CONTENT_MIN_CHARS` |
| `LYNCEUS_ENTETE_IP_REELLE` | `LYNCEUS_REAL_IP_HEADER` |
| `LYNCEUS_LLM_FOURNISSEUR` | `LYNCEUS_LLM_PROVIDER` |
| `LYNCEUS_LLM_RAISONNEMENT` | `LYNCEUS_LLM_REASONING` |
| `LYNCEUS_PORTAIL_ADRESSE` | `LYNCEUS_PORTAL_ADDRESS` |
| `LYNCEUS_PORTAIL_CLES_PAR_IP_JOUR` | `LYNCEUS_PORTAL_KEYS_PER_IP_DAY` |
| `LYNCEUS_PORTAIL_CLE_PRIVEE` | `LYNCEUS_PORTAL_PRIVATE_KEY` |
| `LYNCEUS_PORTAIL_CONTACT` | `LYNCEUS_PORTAL_CONTACT` |
| `LYNCEUS_PORTAIL_CORS_ORIGINS` | `LYNCEUS_PORTAL_CORS_ORIGINS` |
| `LYNCEUS_PORTAIL_DELAI_INSTANCE_S` | `LYNCEUS_PORTAL_INSTANCE_TIMEOUT_S` |
| `LYNCEUS_PORTAIL_DEPOT` | `LYNCEUS_PORTAL_REPOSITORY` |
| `LYNCEUS_PORTAIL_DEPOT_FICHIERS` | `LYNCEUS_PORTAL_REPOSITORY_FILES` |
| `LYNCEUS_PORTAIL_DROIT_APPLICABLE` | `LYNCEUS_PORTAL_GOVERNING_LAW` |
| `LYNCEUS_PORTAIL_EDITEUR_ADRESSE` | `LYNCEUS_PORTAL_PUBLISHER_ADDRESS` |
| `LYNCEUS_PORTAIL_EDITEUR_CONTACT` | `LYNCEUS_PORTAL_PUBLISHER_CONTACT` |
| `LYNCEUS_PORTAIL_EDITEUR_DIRECTEUR` | `LYNCEUS_PORTAL_PUBLISHER_DIRECTOR` |
| `LYNCEUS_PORTAIL_EDITEUR_IDENTIFIANT` | `LYNCEUS_PORTAL_PUBLISHER_ID` |
| `LYNCEUS_PORTAIL_EDITEUR_NOM` | `LYNCEUS_PORTAL_PUBLISHER_NAME` |
| `LYNCEUS_PORTAIL_EDITEUR_STATUT` | `LYNCEUS_PORTAL_PUBLISHER_STATUS` |
| `LYNCEUS_PORTAIL_ENTETE_IP_REELLE` | `LYNCEUS_PORTAL_REAL_IP_HEADER` |
| `LYNCEUS_PORTAIL_HEBERGEUR_ADRESSE` | `LYNCEUS_PORTAL_HOST_ADDRESS` |
| `LYNCEUS_PORTAIL_HEBERGEUR_NOM` | `LYNCEUS_PORTAL_HOST_NAME` |
| `LYNCEUS_PORTAIL_HEBERGEUR_SITE` | `LYNCEUS_PORTAL_HOST_SITE` |
| `LYNCEUS_PORTAIL_INSTANCE` | `LYNCEUS_PORTAL_INSTANCE` |
| `LYNCEUS_PORTAIL_INSTANCE_INTERNE` | `LYNCEUS_PORTAL_INTERNAL_INSTANCE` |
| `LYNCEUS_PORTAIL_NOM` | `LYNCEUS_PORTAL_NAME` |
| `LYNCEUS_PORTAIL_PAQUETS` | `LYNCEUS_PORTAL_PACKAGES` |
| `LYNCEUS_PORTAIL_QUOTA_JOUR` | `LYNCEUS_PORTAL_DAILY_QUOTA` |
| `LYNCEUS_PORTAIL_VALIDITE_JOURS` | `LYNCEUS_PORTAL_VALIDITY_DAYS` |
| `LYNCEUS_SUFFIXE` | `LYNCEUS_SUFFIX` |
| `LYNCEUS_PAQUETS` | `LYNCEUS_PACKAGES` |

## 2. Publishing the image

The image is built once and deployed as is, with no compilation on the host:

```bash
# From the root of the repository
REGISTRE=your-registry.example/lynceus-api      # your image registry

docker build -f api/Dockerfile -t $REGISTRE:v$(cat VERSION) .
docker tag  $REGISTRE:v$(cat VERSION) $REGISTRE:latest
docker push $REGISTRE:v$(cat VERSION)
docker push $REGISTRE:latest
```

The build context is the **root of the repository**, not `api/`: the image embeds `prompts/`, `docs/` and `schema/`, and its first stage builds the extension package from `extension/`. A single image serves both the instance and the portal, which are only two entry commands into it.

The version tag makes it possible to roll back: `LYNCEUS_IMAGE=…:v0.2.0` then `docker compose up -d`. It comes from the `VERSION` file, which `verifier.sh` checks against `pyproject.toml` and `__init__.py`. A mismatch would produce an instance announcing on `/v1/meta` a version nobody could redeploy.

### Automating it: the CI pipeline

The repository contains two GitHub Actions compatible workflows, designed for a **self-hosted runner** labelled `self-hosted, forge`:

| File | Trigger | Effect |
|---|---|---|
| `.github/workflows/tests.yml` | push to `main`, `next`, `dev`, `feat/**`, `fix/**`, `docs/**` | replays `pytest` and the extension suite in throwaway containers |
| `.github/workflows/build.yml` | push to `main`, `next`, `dev` | builds the image, publishes it, and triggers the redeployment |

How branches map to image tags:

| Branch | Tag | Redeployment |
|---|---|---|
| `dev` | `:dev` | none (build only) |
| `next` | `:next` | staging, by webhook |
| `main` | `:latest` and `:v<VERSION>` | production, by webhook |

To configure in the repository, on the forge side:

- variable `REGISTRE_FORGE`: the registry address **as seen from the runner**, `127.0.0.1:5000` by default. The deployment hosts reach that registry by its network name instead, set in each stack's `LYNCEUS_IMAGE`;
- secrets `WEBHOOK_STAGING_INSTANCE`, `WEBHOOK_STAGING_PORTAIL`, `WEBHOOK_PROD_INSTANCE`, `WEBHOOK_PROD_PORTAIL`: the redeployment URLs, one per stack. Two stacks pull the same image, the instance and the portal, hence two calls; the instance first, since it carries the schema migrations. A step with no secret passes with a warning rather than failing, so that a cloned repository can build its images without configuring anything.

Those URLs are not in the workflow files, and must not go in them: **a Portainer webhook URL is a deployment token in disguise**, enough for anyone who knows it to redeploy a stack. Since the repository is meant to become public, they stay secrets.

Two details that are expensive to discover in production:

- the webhook call uses `curl --fail`. Without that flag, `curl` exits 0 on an HTTP 404 and the step goes green while the call hit nothing. A stack deleted and recreated changes webhook id: that is exactly the case you want to see fail;
- test jobs do **not** run for a proposal coming from a fork. A self-hosted runner executes whatever code it is given: on a public repository, opening it to forks would amount to handing over the machine. Contributions are reviewed, and their author runs `./verifier.sh` at home.

### A staging instance, deployed from Portainer

`docker-compose.staging.yml` is meant for that: **a single stack**, database, instance and portal together, one set of variables, one redeployment webhook.

It is a knowing compromise, and it only holds for staging. In production the instance and the portal are two stacks on two machines: the portal holds the private key that signs access, the instance is the exposed surface, and separating them means a compromised instance still does not let anyone forge keys. In staging the aim is the opposite, checking the whole loop at once, so the portal reaches the instance over the stack's internal network and the staging private key lives next to it.

**The key pair must be specific to staging.** `lynceus cles-paire` generates one. Reusing the production public key would make production accept every key issued for testing.

Variables to fill in from the Portainer editor:

```ini
LYNCEUS_IMAGE=<registry>/lynceus-api:next
POSTGRES_PASSWORD=<specific to staging>
LYNCEUS_LLM_API_KEY=<your key>
LYNCEUS_CLE_PUBLIQUE=<staging pair>
LYNCEUS_PORTAIL_CLE_PRIVEE=<the private key of the SAME pair>
LYNCEUS_PORTAIL_INSTANCE=https://api-staging.example.org   # public address, not a service name
LYNCEUS_PORTAIL_ADRESSE=https://staging.example.org        # otherwise the downloaded archive may carry an http address
CLOUDFLARE_TUNNEL_TOKEN=<token>
COMPOSE_PROFILES=tunnel                                    # enables the tunnel service
```

A single tunnel is enough for both services: on the Cloudflare side, two *public hostnames*, one to `http://api:8000`, the other to `http://portail:8080`. Those are the service names inside the stack's network, not addresses on the host.

The legal identity is left empty **on purpose**: the legal pages then announce that they are not filled in, and the portal warns at startup. A staging deployment must never be able to pass for a service open to the public.

Three traps, all of them met in practice:

- **relative paths mean nothing in Portainer.** A `./paquets` resolves against the directory Compose is launched from, which is not this repository when Portainer is deploying. The mount therefore uses an absolute path, `LYNCEUS_PAQUETS`, whose default is fine. Docker creates the folder if it is missing;
- **the container suffix is not cosmetic.** Without `LYNCEUS_SUFFIXE`, two environments on the same machine fight over the name `lynceus-api` and the second refuses to start. The staging file suffixes `-staging` by default;
- **the webhook is a deployment token.** Whoever knows its URL can retrigger the stack. It goes in the repository secrets, never in a versioned file.

### Or two separate stacks, as in production

Nothing forces you to go through the staging file: `docker-compose.prod.yml` and `docker-compose.portail.yml` accept the same variables, with `LYNCEUS_IMAGE` on `:next` and `LYNCEUS_SUFFIXE=-staging`. That is the choice to make if staging is meant to reproduce the production topology rather than to be quick.

```bash
docker compose -p lynceus-staging -f docker-compose.prod.yml up -d
```

The suffix only affects container names; the volumes are already isolated by the Compose project name.

## 3. Starting up

```bash
cd api
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml logs -f api
```

The database schema is created and migrated automatically at startup (Alembic). There is no command to run.

To check:

```bash
curl http://127.0.0.1:8000/sante     # {"statut":"ok",…}
curl http://127.0.0.1:8000/v1/meta   # must show "cle_requise": true
```

## 4. Exposing over HTTPS

The API speaks plain HTTP: encryption is delegated to the exposure layer.

### Cloudflare Tunnel (recommended)

The `cloudflared` container establishes an **outbound** connection to Cloudflare: no inbound port to open, no public address to expose, TLS certificate handled by Cloudflare.

1. In **Cloudflare Zero Trust → Networks → Tunnels**, create a tunnel and note its token.
2. Add a *public hostname* pointing at `http://api:8000`. That is the service name inside the Docker network, not an address on the host.
3. Put the token in `.env`:

```ini
CLOUDFLARE_TUNNEL_TOKEN=eyJ…
# Cloudflare passes the visitor's address in this header. Without it, every request
# would carry the tunnel's address and a single visitor would exhaust everybody's
# rate limit.
LYNCEUS_ENTETE_IP_REELLE=CF-Connecting-IP
```

4. Start with the profile:

```bash
docker compose -f docker-compose.prod.yml --profile tunnel up -d
```

The tunnel service lives behind a **Compose profile**: without it, it does not exist, and nothing says so. That is disconcerting the first time: you deploy, everything works, and a container is missing.

From **Portainer** there is no flag to pass: add the variable to the stack's variables, and Compose reads it from the `.env` Portainer writes next to the file.

```ini
COMPOSE_PROFILES=tunnel
```

> **`LYNCEUS_ENTETE_IP_REELLE` must only be set if the instance is reachable *solely* through the tunnel.** An HTTP header can be forged: if the API remains directly accessible, anyone could bypass the rate limit by announcing a different address on every request. Keep `LYNCEUS_BIND=127.0.0.1` (the default), or better, remove the `ports:` section of the `api` service: the tunnel reaches it over the internal network.

### Other options

**Tailscale Serve**: access restricted to your tailnet, with no third-party account:

```bash
sudo tailscale serve --bg 8000     # tailnet only
sudo tailscale funnel --bg 8000    # exposed to the internet
```

A classic reverse proxy (Caddy, nginx) works as well; in that case set `LYNCEUS_ENTETE_IP_REELLE=X-Real-IP` (or whichever header your proxy uses).

Whichever option you choose, the resulting address is the one users type into the extension settings.

## 5. Handing out keys

From a machine holding the private key, not from the server:

```bash
export LYNCEUS_CLE_PRIVEE=…
lynceus cle-emettre --jours 365 --quota 50 --nombre 5
```

Each person pastes their key into the extension settings, along with the instance address. A key contains **no information about its holder**: no name, no address, no identifier. You will not know who analyses what, and that is by design.

The quota is daily and counts only **real analyses**: a page already present in the directory is served again for free, without eating into it.

Handing keys out by hand suits a few people you know. Beyond that, the **portal** issues keys on its own (next section).

## 6. The public portal

The portal is the website: the story, the methodology, the reference list of techniques, the browsable directory, the extension download and one-click sign-up. It is a second entry point into the **same image**, deployed separately.

### Why separately

| | Instance | Portal |
|---|---|---|
| Holds | the **public** key | the **private** key |
| Stores | analyses, pages, disputes | **nothing** |
| Talks to | a model provider (billed) | the instance, through its public API |
| If compromised | the analyses are exposed | **keys can be forged at will** |

The private key is the most sensitive secret in the project: it makes it possible to issue keys valid on your instance, and therefore to spend your model budget. Putting it on the machine that talks to the internet, runs analyses and keeps a database is putting it where there is the most to compromise.

The portal, for its part, has **no database** and keeps nothing: not the keys it issues, not the searches, not the disputes, which it forwards to the instance. One container is enough, on the smallest machine available, and losing it loses no data.

Putting them on a single host works and remains defensible to get started. But it is a choice to make with open eyes, not a misconfiguration.

### Starting it

```bash
# On the machine hosting the portal (ideally not the instance's)
cp .env.portail.example .env    # put LYNCEUS_PORTAIL_CLE_PRIVEE and the instance's public address in it
mkdir -p paquets
docker compose -f docker-compose.portail.yml --profile tunnel up -d
```

From Portainer, the `COMPOSE_PROFILES=tunnel` variable replaces the flag.

The portal's Cloudflare hostname must point at `http://portail:8080`.

### The extension is already in the image

The image contains the extension archive: it is built in a Node stage of the `Dockerfile`, of which nothing else survives. A freshly deployed portal therefore distributes the extension without anything having to be copied onto the host.

That embedded package is **neutral**: no portal address is written into it, since otherwise there would have to be one image per portal. The address is added **at download time**, in a `portail.json` file slipped into the archive that is served. The extension reads it there and offers "Get a key" without anyone having to copy an address. Set `LYNCEUS_PORTAIL_ADRESSE`: without it the address is inferred from the request, which gets the scheme wrong behind a proxy that does not forward `X-Forwarded-Proto`.

### The link to pass around

`https://your-portal/telecharger` always serves **the highest version** published by that portal. It is a stable address: it does not change from one version to the next, and the link appears in the footer of every page of the site, with the version number and the size of the archive.

The archive served is configured on the fly for that portal, so a link sent in a message is enough: the person downloads it, loads the extension into Chrome, and the "Get a key" button already knows who to talk to.

### Publishing a version without rebuilding the image

Drop a zip with a higher version into `./paquets`:

```bash
cd extension && npm run paquet
scp lynceus-extension-v*.zip server:/path/to/api/paquets/
```

The portal re-reads the folder on every request: the new version is offered **immediately**, with no restart. The tie-break is on the **version number**, never on the file date nor on folder order, so restoring a backup or dropping in an older zip does not roll back what is distributed. Remove the zip from the volume and the package from the image takes over again.

### What restarts, and what does not

Three containers, three independent life cycles. Updating one does not interrupt the others.

| What you change | What to do | What is interrupted |
|---|---|---|
| An extension version | drop the zip into `./paquets` | **nothing** |
| The site (text, layout) | `pull` then `up -d` of the portal compose | the site, for a few seconds |
| The API (engine, directory, schema) | `pull` then `up -d` of the instance compose | analyses, for a few seconds |

The site and the API share the same image but not the same container: redeploying the portal leaves the API analysing without noticing, and the other way round. While the instance restarts, the portal keeps serving its pages and simply reports the directory as unreachable.

> **An installed extension does not update itself.** Loaded in developer mode, it stays at its version until the person reloads it. Publishing a new zip makes the new version available; it installs it on nobody.

### What sign-up issues, and what it does not keep

`POST /v1/inscription` returns a ticket: the instance address, a signed key, its quota and its expiry. No account is created, no email address is asked for, and **nothing is recorded**: if asked, the portal would be unable to say who obtained what.

Sign-up is **unrestricted by default** (`LYNCEUS_PORTAIL_CLES_PAR_IP_JOUR=0`). That choice has a downside worth knowing: nothing stops a script from asking for a thousand keys, and every key grants billed analyses. Three levers, from gentlest to firmest:

1. **The per-key quota** (`LYNCEUS_PORTAIL_QUOTA_JOUR`): already active, it bounds what one key can cost.
2. **The per-address ceiling** (`LYNCEUS_PORTAIL_CLES_PAR_IP_JOUR`): setting it to 2 or 3 is enough to discourage ordinary scripting. The counter lives in memory and resets on restart: a brake, not a barrier, and useless behind an address rotator.
3. **Revocation** (`LYNCEUS_CLES_REVOQUEES` on the instance): the id of an abusive key is visible in the database, in `consommations_cles`.

Watch the number of **real** analyses (the "Watching the costs" section) rather than the number of keys: a thousand unused keys cost nothing.

### Legal obligations of an instance open to the public

As soon as the portal is reachable by anyone but you, three pages become necessary, and the
portal serves them: `/mentions-legales`, `/confidentialite` and `/conditions`.

To those is added an obligation that comes not from the law but from the licence. The
AGPL-3.0 requires (article 13) that the corresponding source be offered to people who **use
the service remotely**, modifications included. Serving Lynceus without publishing the code
you are running is not compliant. Two variables are enough:

```ini
LYNCEUS_PORTAIL_DEPOT=https://github.com/Nashi-cloud/Project-Lynceus
LYNCEUS_PORTAIL_DEPOT_FICHIERS=https://github.com/Nashi-cloud/Project-Lynceus/blob/main
```

Those are the defaults: an instance running the published code as is has nothing to change,
and the address announced is accurate. **As soon as you modify the code, put your own
repository there**: it is your version that must be offered, not ours.

The first feeds the "source code" links in the footer and in the documents. The second is
used to point at a specific file, and its shape depends on the forge: `/blob/main` on GitHub
and GitLab, `/src/branch/main` on Forgejo. Left empty, the pages talk about the repository
without being able to link to it, and the portal says so at startup.

Their content comes from the configuration, not from the code, because every instance has
its own operator:

```ini
LYNCEUS_PORTAIL_EDITEUR_NOM=…
LYNCEUS_PORTAIL_EDITEUR_STATUT=…
LYNCEUS_PORTAIL_EDITEUR_ADRESSE=…
LYNCEUS_PORTAIL_EDITEUR_IDENTIFIANT=…     # company number or equivalent
LYNCEUS_PORTAIL_EDITEUR_DIRECTEUR=…
LYNCEUS_PORTAIL_EDITEUR_CONTACT=…
LYNCEUS_PORTAIL_HEBERGEUR_NOM=…
LYNCEUS_PORTAIL_HEBERGEUR_ADRESSE=…
LYNCEUS_PORTAIL_DROIT_APPLICABLE=…
```

Left unset, the pages **say that they are unset** instead of displaying invented details,
and the portal writes it to standard error at startup. Strictly personal use has nothing to
fill in.

> **The point not to miss.** The privacy policy states at the top that the text of analysed
> pages is transmitted to the model provider, which may be outside the European Union. It
> **names the provider actually configured**, read from the instance's `/v1/meta`: changing
> provider updates the page by itself, which stops it becoming false without anyone
> noticing. If that transfer is a problem in your case, choose a provider established in
> the Union, or a local model through Ollama: the text then never leaves the machine.

The full analysis, with the processing operations, the legal bases relied on and the
retention periods, is in [docs/en/CONFORMITE.md](../docs/en/CONFORMITE.md).

### The portal without a private key

Leaving `LYNCEUS_PORTAIL_CLE_PRIVEE` empty is a valid mode: the pages are still served, the directory is still browsable, and sign-up answers `503` explaining that no key is issued here. That is what you want for a showcase, or for a portal that only distributes the documentation.

## 7. Day-to-day operation

```bash
# Disputes received (charter §6)
export LYNCEUS_ADMIN_TOKEN=…
lynceus signalements --statut nouveau
lynceus traiter 3 --statut examine --decision "…"

# Update
docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d

# Backing up the directory
docker exec lynceus-db pg_dump -U lynceus lynceus | gzip > lynceus-$(date +%F).sql.gz
```

The directory is the instance's capital: every analysis cost a call to the model. **Back it up regularly.**

## Revoking a key

If a key is being abused, add its id to `LYNCEUS_CLES_REVOQUEES` (visible in the output of `cle-emettre`, or in the database) and restart. The list contains only the keys that have been set aside; it is not a directory.

## The three guardrails

They stack, and **none of them applies to a page already present in the directory**: serving it again costs nothing, so it is neither limited nor counted.

| Guardrail | Counted per | Window | Where | Setting |
|---|---|---|---|---|
| Rate | visitor address | 60 s sliding | memory | `LYNCEUS_RATE_LIMIT_ANALYSES` (10/min) |
| Quota | key id | calendar day (UTC) | database | carried by each key (`--quota`) |
| Size | nothing | per request | nothing | `LYNCEUS_CONTENU_MAX_CARS` (60,000) |

The rate limit stops bursts (a looping script); the quota protects the budget over time (someone quietly analysing thousands of pages in a day).

> **A single process.** The rate counter lives in the process's memory: serving the application with several workers would multiply the real limit by their number, silently. The image therefore starts a single process. Should traffic ever demand it, that counter would first have to move to shared storage (Redis or equivalent), before adding workers and not after.

## Capacity and scaling

An analysis ties up a thread for the whole call to the model (10 to 60 s depending on the model and the length of the page). With no ceiling, a few dozen analyses would be enough to saturate the server, and directory lookups, normally instant, would queue behind them.

`LYNCEUS_ANALYSES_SIMULTANEES` (12 by default) bounds the analyses run concurrently. Requests beyond that **wait without consuming a thread**: they do complete, just later.

Measurements on a real server, with a simulated model at 3 s per analysis:

| Analyses started at once | All completed | Worst lookup latency | Median |
|---|---|---|---|
| 40 | 40/40 | 0.22 s | 2 ms |
| 60 | 60/60 | 0.21 s | 2 ms |
| 200 | 200/200 | 2.2 s | 2 ms |

Before that ceiling, 40 simultaneous analyses were enough to make a lookup wait **6.2 seconds**. The passive badge now stays responsive under a load your instance will most likely never see.

**Sustained throughput**: roughly `simultaneous_analyses / duration_of_one_analysis`. With 12 slots and a model at 15 s, reckon on about 48 analyses a minute, well beyond what a family or a small association produces, all the more so since already known pages are served **without an analysis**.

If traffic really demanded it:

1. **raise `LYNCEUS_ANALYSES_SIMULTANEES`**: that is the direct lever, as long as the model provider keeps up (mind its own rate limits);
2. **only then**, consider several processes, but the rate counter must first move to shared storage (see the warning above).

A task queue (Celery, RQ) would bring nothing here: it would impose Redis and a separate worker, and would force clients to poll for the state of their analysis instead of receiving their card directly. The concurrency ceiling solves the same problem without any of that.

## Scaling to several thousand users

What gives way first, in order, and what is already handled.

### Already in place

**The prefix search index.** The k-anonymous lookup (`LIKE 'abcde%'`) is the most frequent query: one per page visited, with the badge on. PostgreSQL only uses an ordinary B-tree index for that filter if the collation is `C`. Without a suitable operator class, the query scans the whole table. Measured: **22 ms over 500,000 pages**, against **0.08 ms** with the `varchar_pattern_ops` index, and **0.25 ms over 5 million**. The migration creates it automatically.

**The connection pool.** SQLAlchemy's default (5 + 10) was lower than the server's thread count: under load, requests would have waited for a free connection with the database not to blame. Raised to 20 + 20, with `pool_pre_ping` (which drops connections cut by a firewall) and recycling at 30 minutes.

**Several replicas starting at once.** Without coordination they would apply the same migrations concurrently, with errors, or even a half-migrated schema. A PostgreSQL advisory lock serialises the operation: verified with 6 replicas started together against a blank database, one migrates and the others wait and then find there is nothing to do.

**The ceiling on simultaneous analyses**, which preserves the responsiveness of lookups (previous section).

### What will have to be done to go further

Two locks currently prevent adding replicas, and they must be lifted **before**, not after:

1. **The rate counter lives in memory.** With N processes, the real limit is multiplied by N. It has to move to shared storage (Redis). The per-key quota, on the other hand, is already in the database and behaves correctly across instances.
2. **The concurrency ceiling is also per process.** Same remark: N replicas would send N × 12 simultaneous analyses to the model provider, which has its own per-key rate limits.

### The real ceiling is not technical

Analysis throughput is bounded by the model provider and by the budget, not by this server. Two effects work in your favour:

- **the cache is shared**: the more users there are, the higher the proportion of pages already known, and a known page costs nothing;
- **lookups are nearly free**: 0.25 ms over 5 million pages, with no call to the model.

In other words, a thousand users reading the same news sites cost far less than a thousand users each exploring pages nobody has seen. Watch the number of **real** analyses (next section), not the number of requests.

## Watching the costs

The real risk of an exposed instance is not intrusion, it is the bill. Three guardrails stack: per-key quota, per-IP rate limit, and maximum content size. To estimate the spend:

```bash
docker exec lynceus-db psql -U lynceus -c \
  "SELECT DATE(cree_le) jour, COUNT(*) analyses FROM analyses GROUP BY 1 ORDER BY 1 DESC LIMIT 7;"
```

Multiply by your model's rate. A useful reminder: **a page is only analysed once** for all users, so the cost naturally falls as the directory fills up.
