# Déployer une instance Lynceus

Pour héberger une instance destinée à d'autres personnes — vos proches, un groupe, ou à terme le public.

> Pour un usage strictement personnel, [INSTALLATION.md](INSTALLATION.md) suffit : pas besoin de tout ceci.

## Ce qui change dès qu'une instance est exposée

| | Usage personnel | Instance exposée |
|---|---|---|
| Base de données | SQLite | PostgreSQL |
| Accès | ouvert | **clés d'accès obligatoires** |
| Chiffrement | inutile (localhost) | **HTTPS obligatoire** |
| Redémarrage | manuel | automatique |

La règle non négociable : **votre clé LLM est facturée à l'usage**. Une instance exposée sans clés d'accès permet à n'importe qui de dépenser votre argent. Le compose de production refuse d'ailleurs de démarrer sans `LYNCEUS_CLE_PUBLIQUE`.

## 1. Préparer les secrets

```bash
cd api
cp .env.prod.example .env

python3 -c "import secrets; print(secrets.token_urlsafe(24))"   # POSTGRES_PASSWORD
python3 -c "import secrets; print(secrets.token_urlsafe(32))"   # LYNCEUS_ADMIN_TOKEN
lynceus cles-paire                                              # LYNCEUS_CLE_PUBLIQUE
```

Gardez la **clé privée** hors de la machine qui héberge l'instance : c'est elle qui permet d'émettre des clés, et l'instance n'en a pas besoin. Si le serveur est compromis, personne ne pourra émettre de clés en votre nom.

## 2. Publier l'image

L'image est construite une fois et déployée telle quelle — pas de compilation sur l'hôte :

```bash
# Depuis la racine du dépôt
docker build -f api/Dockerfile -t votre-registre.exemple/lynceus-api:v0.3.0 .
docker tag  votre-registre.exemple/lynceus-api:v0.3.0 \
            votre-registre.exemple/lynceus-api:latest
docker push votre-registre.exemple/lynceus-api:v0.3.0
docker push votre-registre.exemple/lynceus-api:latest
```

L'étiquette de version permet de revenir en arrière : `LYNCEUS_IMAGE=…:v0.2.0` puis `docker compose up -d`.

## 3. Démarrer

```bash
cd api
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml logs -f api
```

Le schéma de base est créé et migré automatiquement au démarrage (Alembic) — aucune commande à lancer.

Vérifier :

```bash
curl http://127.0.0.1:8000/sante     # {"statut":"ok",…}
curl http://127.0.0.1:8000/v1/meta   # doit indiquer "cle_requise": true
```

## 4. Exposer en HTTPS

L'API parle en HTTP simple : le chiffrement est délégué. **Tailscale Serve** est le plus simple — certificat automatique, aucun port ouvert sur Internet :

```bash
# Accessible depuis votre tailnet uniquement
sudo tailscale serve --bg 8000

# Accessible depuis Internet (nécessaire si vos utilisateurs ne sont pas sur le tailnet)
sudo tailscale funnel --bg 8000
```

L'adresse devient `https://<machine>.tailnet.exemple`. C'est elle que les utilisateurs mettent dans les réglages de l'extension.

> **Funnel expose l'instance à Internet.** Les clés d'accès deviennent alors votre seule protection : vérifiez que `cle_requise` vaut bien `true` avant d'activer.

Un reverse proxy classique (Caddy, nginx) fonctionne évidemment aussi ; l'API n'attend rien de particulier.

## 5. Distribuer les clés

Depuis une machine détenant la clé privée — pas le serveur :

```bash
export LYNCEUS_CLE_PRIVEE=…
lynceus cle-emettre --jours 365 --quota 50 --nombre 5
```

Chaque personne colle sa clé dans les réglages de l'extension, avec l'adresse de l'instance. Une clé ne contient **aucune information sur son porteur** : ni nom, ni adresse, ni identifiant. Vous ne saurez pas qui analyse quoi — c'est voulu.

Le quota est journalier et ne compte que les **analyses réelles** : une page déjà présente dans l'annuaire est resservie gratuitement, sans l'entamer.

## 6. Exploitation courante

```bash
# Contestations reçues (charte §6)
export LYNCEUS_ADMIN_TOKEN=…
lynceus signalements --statut nouveau
lynceus traiter 3 --statut examine --decision "…"

# Mise à jour
docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d

# Sauvegarde de l'annuaire
docker exec lynceus-db pg_dump -U lynceus lynceus | gzip > lynceus-$(date +%F).sql.gz
```

L'annuaire est le patrimoine de l'instance : chaque analyse a coûté un appel au modèle. **Sauvegardez-le régulièrement.**

## Révoquer une clé

Si une clé est utilisée abusivement, ajoutez son identifiant à `LYNCEUS_CLES_REVOQUEES` (visible dans la sortie de `cle-emettre`, ou en base) et redémarrez. La liste ne contient que les clés écartées — ce n'est pas un annuaire.

## Surveiller les coûts

Le vrai risque d'une instance exposée n'est pas l'intrusion, c'est la facture. Trois garde-fous se cumulent : quota par clé, limite de débit par IP, et taille maximale du contenu. Pour estimer la dépense :

```bash
docker exec lynceus-db psql -U lynceus -c \
  "SELECT DATE(cree_le) jour, COUNT(*) analyses FROM analyses GROUP BY 1 ORDER BY 1 DESC LIMIT 7;"
```

Multipliez par le tarif de votre modèle. Rappel utile : **une page n'est analysée qu'une fois** pour tous les utilisateurs — le coût décroît naturellement à mesure que l'annuaire se remplit.
