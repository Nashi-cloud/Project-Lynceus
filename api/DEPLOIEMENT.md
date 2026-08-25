# Déployer une instance Lynceus

Pour héberger une instance destinée à d'autres personnes : vos proches, un groupe, ou à terme le public.

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

L'image est construite une fois et déployée telle quelle, sans compilation sur l'hôte :

```bash
# Depuis la racine du dépôt
REGISTRE=votre-registre.exemple/lynceus-api      # votre registre d'images

docker build -f api/Dockerfile -t $REGISTRE:v0.3.0 .
docker tag  $REGISTRE:v0.3.0 $REGISTRE:latest
docker push $REGISTRE:v0.3.0
docker push $REGISTRE:latest
```

L'étiquette de version permet de revenir en arrière : `LYNCEUS_IMAGE=…:v0.2.0` puis `docker compose up -d`.

## 3. Démarrer

```bash
cd api
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml logs -f api
```

Le schéma de base est créé et migré automatiquement au démarrage (Alembic). Aucune commande à lancer.

Vérifier :

```bash
curl http://127.0.0.1:8000/sante     # {"statut":"ok",…}
curl http://127.0.0.1:8000/v1/meta   # doit indiquer "cle_requise": true
```

## 4. Exposer en HTTPS

L'API parle en HTTP simple : le chiffrement est délégué à la couche d'exposition.

### Cloudflare Tunnel (recommandé)

Le conteneur `cloudflared` établit une connexion **sortante** vers Cloudflare : aucun port entrant à ouvrir, aucune adresse publique à exposer, certificat TLS géré par Cloudflare.

1. Dans **Cloudflare Zero Trust → Networks → Tunnels**, créez un tunnel et notez son jeton.
2. Ajoutez un *public hostname* pointant vers `http://api:8000`. C'est le nom du service dans le réseau Docker, pas une adresse de l'hôte.
3. Placez le jeton dans `.env` :

```ini
CLOUDFLARE_TUNNEL_TOKEN=eyJ…
# Cloudflare transmet l'adresse du visiteur dans cet en-tête. Sans lui, toutes les
# requêtes porteraient l'adresse du tunnel et un seul visiteur épuiserait la limite
# de débit de tout le monde.
LYNCEUS_ENTETE_IP_REELLE=CF-Connecting-IP
```

4. Démarrez avec le profil :

```bash
docker compose -f docker-compose.prod.yml --profile tunnel up -d
```

> **`LYNCEUS_ENTETE_IP_REELLE` ne doit être défini que si l'instance est joignable *uniquement* par le tunnel.** Un en-tête HTTP se falsifie : si l'API reste accessible en direct, n'importe qui contournerait la limite de débit en annonçant une adresse différente à chaque requête. Gardez `LYNCEUS_BIND=127.0.0.1` (le défaut), ou mieux, supprimez la section `ports:` du service `api` : le tunnel le joint par le réseau interne.

### Autres options

**Tailscale Serve** : accès réservé à votre tailnet, sans compte tiers :

```bash
sudo tailscale serve --bg 8000     # tailnet seulement
sudo tailscale funnel --bg 8000    # exposé à Internet
```

Un reverse proxy classique (Caddy, nginx) fonctionne également ; renseignez alors `LYNCEUS_ENTETE_IP_REELLE=X-Real-IP` (ou l'en-tête que votre proxy utilise).

Quelle que soit l'option, l'adresse obtenue est celle que les utilisateurs saisissent dans les réglages de l'extension.

## 5. Distribuer les clés

Depuis une machine détenant la clé privée, pas le serveur :

```bash
export LYNCEUS_CLE_PRIVEE=…
lynceus cle-emettre --jours 365 --quota 50 --nombre 5
```

Chaque personne colle sa clé dans les réglages de l'extension, avec l'adresse de l'instance. Une clé ne contient **aucune information sur son porteur** : ni nom, ni adresse, ni identifiant. Vous ne saurez pas qui analyse quoi, et c'est voulu.

Le quota est journalier et ne compte que les **analyses réelles** : une page déjà présente dans l'annuaire est resservie gratuitement, sans l'entamer.

Cette distribution à la main convient à quelques proches. Au-delà, le **portail** délivre les clés tout seul (section suivante).

## 6. Le portail public

Le portail est le site : le récit, la méthodologie, le référentiel des procédés, l'annuaire consultable, le téléchargement de l'extension et l'inscription en un clic. C'est un second point d'entrée de la **même image**, déployé séparément.

### Pourquoi séparément

| | Instance | Portail |
|---|---|---|
| Détient | la clé **publique** | la clé **privée** |
| Stocke | analyses, pages, contestations | **rien** |
| Parle à | un fournisseur de modèle (facturé) | l'instance, par son API publique |
| Si elle est compromise | les analyses sont exposées | **on peut forger des clés à volonté** |

La clé privée est le secret le plus sensible du projet : elle permet d'émettre des clés valables sur votre instance, donc de dépenser votre budget de modèle. La poser sur la machine qui parle à Internet, qui exécute des analyses et qui tient une base de données, c'est la mettre là où il y a le plus à compromettre.

Le portail, lui, n'a **pas de base de données** et ne conserve rien : ni les clés délivrées, ni les recherches, ni les contestations, qu'il transmet à l'instance. Un conteneur suffit, sur la plus petite machine disponible, et le perdre ne perd aucune donnée.

Les réunir sur un seul hôte fonctionne et reste défendable pour démarrer. Mais c'est un choix à faire les yeux ouverts, pas un défaut de configuration.

### Démarrer

```bash
# Sur la machine qui héberge le portail (idéalement pas celle de l'instance)
cp .env.portail.example .env    # y placer LYNCEUS_PORTAIL_CLE_PRIVEE et l'adresse publique de l'instance
mkdir -p paquets
docker compose -f docker-compose.portail.yml --profile tunnel up -d
```

Le hostname Cloudflare du portail doit pointer vers `http://portail:8080`.

### L'extension est déjà dans l'image

L'image contient l'archive de l'extension : elle est construite dans un étage Node du `Dockerfile`, dont rien d'autre ne subsiste. Un portail fraîchement déployé distribue donc l'extension sans qu'on ait à copier quoi que ce soit sur l'hôte.

Ce paquet embarqué est **neutre** : aucune adresse de portail n'y est inscrite, faute de quoi il faudrait une image par portail. L'adresse est ajoutée **au moment du téléchargement**, dans un fichier `portail.json` glissé dans l'archive servie. L'extension l'y lit et propose « Obtenir une clé » sans que personne ait à recopier une adresse. Renseignez `LYNCEUS_PORTAIL_ADRESSE` : sans elle, l'adresse est déduite de la requête, ce qui se trompe de schéma derrière un proxy qui ne transmet pas `X-Forwarded-Proto`.

### Le lien à transmettre

`https://votre-portail/telecharger` sert **toujours la version la plus haute** publiée par ce portail. C'est une adresse stable : elle ne change pas d'une version à l'autre, et le lien figure dans le pied de page de chaque page du site, avec le numéro de version et le poids de l'archive.

L'archive servie est configurée à la volée pour ce portail, si bien qu'un lien envoyé par message suffit : la personne télécharge, charge l'extension dans Chrome, et le bouton « Obtenir une clé » sait déjà à qui s'adresser.

### Publier une version sans reconstruire l'image

Déposez un zip de version plus haute dans `./paquets` :

```bash
cd extension && npm run paquet
scp lynceus-extension-v*.zip serveur:/chemin/vers/api/paquets/
```

Le portail relit le dossier à chaque requête : la nouvelle version est proposée **immédiatement**, sans redémarrage. Le départage se fait sur le **numéro de version**, jamais sur la date du fichier ni sur l'ordre des dossiers, si bien que restaurer une sauvegarde ou déposer un zip plus ancien ne fait pas régresser ce qui est distribué. Retirez le zip du volume et le paquet de l'image reprend la main.

### Ce qui redémarre, et ce qui ne redémarre pas

Trois conteneurs, trois cycles de vie indépendants. Mettre l'un à jour n'interrompt pas les autres.

| Ce que vous changez | Ce qu'il faut faire | Ce qui s'interrompt |
|---|---|---|
| Une version de l'extension | déposer le zip dans `./paquets` | **rien** |
| Le site (textes, mise en page) | `pull` puis `up -d` du compose portail | le site, quelques secondes |
| L'API (moteur, annuaire, schéma) | `pull` puis `up -d` du compose instance | les analyses, quelques secondes |

Le site et l'API partagent la même image mais pas le même conteneur : redéployer le portail laisse l'API analyser sans s'en apercevoir, et inversement. Pendant un redémarrage de l'instance, le portail continue de servir ses pages et signale simplement l'annuaire comme injoignable.

> **Une extension installée ne se met pas à jour toute seule.** Chargée en mode développeur, elle reste à sa version tant que la personne ne la recharge pas. Publier un nouveau zip met la nouvelle version à disposition, cela ne l'installe chez personne.

### Ce que l'inscription délivre, et ce qu'elle ne retient pas

`POST /v1/inscription` renvoie un billet : l'adresse de l'instance, une clé signée, son quota et son échéance. Aucun compte n'est créé, aucune adresse électronique n'est demandée, et **rien n'est enregistré** : interrogé, le portail serait incapable de dire qui a obtenu quoi.

L'inscription est **libre par défaut** (`LYNCEUS_PORTAIL_CLES_PAR_IP_JOUR=0`). Ce choix a une contrepartie qu'il faut connaître : rien n'empêche un script de demander mille clés, et chaque clé donne droit à des analyses facturées. Trois leviers, du plus doux au plus ferme :

1. **Le quota par clé** (`LYNCEUS_PORTAIL_QUOTA_JOUR`) : déjà actif, il borne ce qu'une clé peut coûter.
2. **Le plafond par adresse** (`LYNCEUS_PORTAIL_CLES_PAR_IP_JOUR`) : passer à 2 ou 3 suffit à décourager le scriptage ordinaire. Compteur en mémoire, remis à zéro au redémarrage : un frein, pas une barrière, et inopérant derrière un rotateur d'adresses.
3. **La révocation** (`LYNCEUS_CLES_REVOQUEES` sur l'instance) : l'identifiant d'une clé abusive est visible en base, dans `consommations_cles`.

Surveillez le nombre d'analyses **réelles** (section « Surveiller les coûts ») plutôt que le nombre de clés : mille clés inutilisées ne coûtent rien.

### Obligations légales d'une instance ouverte au public

Dès que le portail est accessible à d'autres que vous, trois pages deviennent nécessaires,
et le portail les sert : `/mentions-legales`, `/confidentialite` et `/conditions`.

Leur contenu vient de la configuration, pas du code, parce que chaque instance a son propre
exploitant :

```ini
LYNCEUS_PORTAIL_EDITEUR_NOM=…
LYNCEUS_PORTAIL_EDITEUR_STATUT=…
LYNCEUS_PORTAIL_EDITEUR_ADRESSE=…
LYNCEUS_PORTAIL_EDITEUR_IDENTIFIANT=…     # SIREN ou équivalent
LYNCEUS_PORTAIL_EDITEUR_DIRECTEUR=…
LYNCEUS_PORTAIL_EDITEUR_CONTACT=…
LYNCEUS_PORTAIL_HEBERGEUR_NOM=…
LYNCEUS_PORTAIL_HEBERGEUR_ADRESSE=…
LYNCEUS_PORTAIL_DROIT_APPLICABLE=…
```

Non renseignées, les pages **indiquent qu'elles ne le sont pas** au lieu d'afficher des
mentions inventées, et le portail l'écrit sur la sortie d'erreur au démarrage. Un usage
strictement personnel n'a rien à remplir.

> **Le point à ne pas manquer.** La politique de confidentialité annonce en tête que le
> texte des pages analysées est transmis au fournisseur de modèle, qui peut être hors de
> l'Union européenne. Elle **nomme le fournisseur réellement configuré**, lu dans
> `/v1/meta` de l'instance : changer de fournisseur met la page à jour toute seule, ce qui
> évite qu'elle devienne fausse sans que personne s'en aperçoive. Si ce transfert pose
> problème dans votre cas, choisissez un fournisseur établi dans l'Union, ou un modèle
> local via Ollama : le texte ne sort alors pas de la machine.

L'analyse complète, avec les traitements, les bases légales retenues et les durées de
conservation, est dans [docs/CONFORMITE.md](../docs/CONFORMITE.md).

### Le portail sans clé privée

Laisser `LYNCEUS_PORTAIL_CLE_PRIVEE` vide est un mode valide : les pages restent servies, l'annuaire reste consultable, et l'inscription répond `503` en expliquant qu'aucune clé n'est délivrée ici. C'est ce qu'il faut pour une vitrine, ou pour un portail qui ne distribue que la documentation.

## 7. Exploitation courante

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

Si une clé est utilisée abusivement, ajoutez son identifiant à `LYNCEUS_CLES_REVOQUEES` (visible dans la sortie de `cle-emettre`, ou en base) et redémarrez. La liste ne contient que les clés écartées, ce n'est pas un annuaire.

## Les trois garde-fous

Ils se cumulent, et **aucun ne s'applique à une page déjà présente dans l'annuaire** : la resservir ne coûte rien, donc n'est ni limitée ni décomptée.

| Garde-fou | Compté par | Fenêtre | Où | Réglage |
|---|---|---|---|---|
| Débit | adresse du visiteur | 60 s glissantes | mémoire | `LYNCEUS_RATE_LIMIT_ANALYSES` (10/min) |
| Quota | identifiant de clé | jour calendaire (UTC) | base | porté par chaque clé (`--quota`) |
| Taille | aucune | par requête | aucun | `LYNCEUS_CONTENU_MAX_CARS` (60 000) |

Le débit arrête les rafales (un script qui boucle) ; le quota protège le budget sur la durée (quelqu'un qui analyserait tranquillement des milliers de pages dans la journée).

> **Un seul processus.** Le compteur de débit vit dans la mémoire du processus : servir l'application avec plusieurs workers multiplierait la limite réelle par leur nombre, silencieusement. L'image lance donc un unique processus. Si le trafic l'exigeait un jour, il faudrait d'abord déplacer ce compteur dans un stockage partagé (Redis ou équivalent), avant d'ajouter des workers et non après.

## Capacité et montée en charge

Une analyse mobilise un thread pendant tout l'appel au modèle (10 à 60 s selon le modèle et la longueur de la page). Sans plafond, quelques dizaines d'analyses suffiraient à saturer le serveur, et les consultations d'annuaire, normalement instantanées, attendraient derrière elles.

`LYNCEUS_ANALYSES_SIMULTANEES` (12 par défaut) borne les analyses menées de front. Les demandes au-delà **patientent sans consommer de thread** : elles aboutissent, simplement plus tard.

Mesures sur un serveur réel, modèle simulé à 3 s par analyse :

| Analyses lancées d'un coup | Toutes abouties | Pire latence d'un lookup | Médiane |
|---|---|---|---|
| 40 | 40/40 | 0,22 s | 2 ms |
| 60 | 60/60 | 0,21 s | 2 ms |
| 200 | 200/200 | 2,2 s | 2 ms |

Avant ce plafond, 40 analyses simultanées suffisaient à faire attendre un lookup **6,2 secondes**. Le badge passif reste désormais réactif sous une charge que votre instance ne connaîtra probablement jamais.

**Débit soutenu** : environ `analyses_simultanees / durée_d_une_analyse`. Avec 12 places et un modèle à 15 s, comptez ~48 analyses par minute, bien au-delà de ce qu'un cercle familial ou associatif produit, d'autant que les pages déjà connues sont resservies **sans analyse**.

Si le trafic l'exigeait vraiment :

1. **augmentez `LYNCEUS_ANALYSES_SIMULTANEES`** : c'est le levier direct, tant que le fournisseur de modèle suit (attention à ses propres limites de débit) ;
2. **puis seulement**, envisagez plusieurs processus, mais il faudra d'abord déplacer le compteur de débit dans un stockage partagé (voir l'avertissement plus haut).

Une file de tâches (Celery, RQ) n'apporterait rien ici : elle imposerait Redis et un worker séparé, et obligerait les clients à interroger périodiquement l'état de leur analyse au lieu de recevoir directement leur carte. Le plafond de concurrence résout le même problème sans rien de tout cela.

## Monter à plusieurs milliers d'utilisateurs

Ce qui cède en premier, dans l'ordre, et ce qui est déjà traité.

### Déjà en place

**L'index de recherche par préfixe.** Le lookup k-anonyme (`LIKE 'abcde%'`) est la requête la plus fréquente : une par page visitée, badge activé. PostgreSQL n'utilise un index B-tree ordinaire pour ce filtre que si la collation est `C`. Sans opérateur adapté, la requête balaie toute la table. Mesuré : **22 ms sur 500 000 pages**, contre **0,08 ms** avec l'index `varchar_pattern_ops`, et **0,25 ms sur 5 millions**. La migration le crée automatiquement.

**Le pool de connexions.** Le défaut de SQLAlchemy (5 + 10) était inférieur au nombre de threads du serveur : sous charge, des requêtes auraient attendu une connexion libre sans que la base soit en cause. Porté à 20 + 20, avec `pool_pre_ping` (écarte les connexions coupées par un pare-feu) et recyclage à 30 minutes.

**Le démarrage simultané de plusieurs répliques.** Sans coordination, elles appliqueraient les mêmes migrations de front, avec des erreurs, voire un schéma à moitié migré. Un verrou consultatif PostgreSQL sérialise l'opération : vérifié avec 6 répliques lancées ensemble sur une base vierge, une seule migre, les autres attendent puis constatent qu'il n'y a rien à faire.

**Le plafond d'analyses simultanées**, qui préserve la réactivité des consultations (section précédente).

### Ce qu'il faudra faire pour aller plus loin

Deux verrous empêchent aujourd'hui d'ajouter des répliques, et ils doivent être levés **avant**, pas après :

1. **Le compteur de débit vit en mémoire.** Avec N processus, la limite réelle est multipliée par N. Il faut le déplacer dans un stockage partagé (Redis). Le quota par clé, lui, est déjà en base et se comporte correctement en multi-instances.
2. **Le plafond de concurrence est également par processus.** Même remarque : N répliques enverraient N × 12 analyses simultanées au fournisseur de modèle, avec ses propres limites de débit à la clé.

### Le vrai plafond n'est pas technique

Le débit d'analyses est borné par le fournisseur de modèle et par le budget, pas par ce serveur. Deux effets jouent en votre faveur :

- **le cache est mutualisé** : plus il y a d'utilisateurs, plus la proportion de pages déjà connues augmente, et une page connue ne coûte rien ;
- **les consultations sont quasi gratuites** : 0,25 ms sur 5 millions de pages, sans appel au modèle.

Autrement dit, un millier d'utilisateurs qui lisent les mêmes sites d'actualité coûtent bien moins qu'un millier d'utilisateurs qui exploreraient chacun des pages inédites. Surveillez le nombre d'analyses **réelles** (section suivante), pas le nombre de requêtes.

## Surveiller les coûts

Le vrai risque d'une instance exposée n'est pas l'intrusion, c'est la facture. Trois garde-fous se cumulent : quota par clé, limite de débit par IP, et taille maximale du contenu. Pour estimer la dépense :

```bash
docker exec lynceus-db psql -U lynceus -c \
  "SELECT DATE(cree_le) jour, COUNT(*) analyses FROM analyses GROUP BY 1 ORDER BY 1 DESC LIMIT 7;"
```

Multipliez par le tarif de votre modèle. Rappel utile : **une page n'est analysée qu'une fois** pour tous les utilisateurs, donc le coût décroît naturellement à mesure que l'annuaire se remplit.
