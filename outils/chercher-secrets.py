#!/usr/bin/env python3
"""Cherche des secrets avant qu'ils n'entrent dans un commit.

La détection de GitHub ne suffit pas ici, et il faut le dire clairement. Elle reconnaît les
jetons de fournisseurs connus, à leur préfixe : une clé Tailscale, un jeton GitHub, une clé
d'API d'un service partenaire. Elle ne reconnaîtra jamais les trois secrets propres à ce
projet, qui n'ont aucune forme remarquable :

  · la clé privée Ed25519 qui signe les accès, une simple chaîne en base64 ;
  · les URL de webhook Portainer, qui sont des jetons de déploiement déguisés ;
  · les noms de machines du tailnet et leurs adresses en 100.64.0.0/10.

Les motifs personnalisés de GitHub demandent Advanced Security, qui ne vient pas avec un
dépôt public gratuit. D'où ce script, qui tourne dans `verifier.sh` et dans un crochet
pre-commit : c'est la seule couche qui protège ce que ce projet a de particulier.

    outils/chercher-secrets.py            # l'arbre de travail suivi par git
    outils/chercher-secrets.py --indexe   # seulement ce qui est indexé (crochet pre-commit)
    outils/chercher-secrets.py fichier…   # des fichiers précis
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Un motif nomme ce qu'il cherche : le message doit dire quoi faire, pas seulement qu'il y a
# un problème. Le groupe capturant, quand il existe, isole la valeur suspecte pour que les
# gabarits (« … », « xxx », « <à remplir> ») ne déclenchent pas d'alerte.
MOTIFS: list[tuple[str, str, str]] = [
    (r"tskey-(?:auth|api|client)-([A-Za-z0-9]{10,})",
     "clé Tailscale",
     "révoquer la clé dans la console Tailscale, elle est compromise"),
    (r"sk-or-v1-([A-Za-z0-9]{20,})",
     "clé OpenRouter",
     "révoquer la clé sur openrouter.ai, elle est compromise"),
    (r"sk-ant-[A-Za-z0-9-]*-([A-Za-z0-9_-]{20,})",
     "clé Anthropic",
     "révoquer la clé dans la console Anthropic"),
    (r"(?:ghp|gho|ghs|ghu)_([A-Za-z0-9]{20,})|github_pat_([A-Za-z0-9_]{20,})",
     "jeton GitHub",
     "révoquer le jeton dans les réglages GitHub"),
    (r"-----BEGIN (?:OPENSSH|RSA|EC|DSA|PGP|)\s*PRIVATE KEY-----",
     "clé privée en clair",
     "retirer le fichier et engendrer une nouvelle paire"),
    (r"(?:LYNCEUS_(?:PORTAIL_)?)?CLE_PRIVEE\s*[:=]\s*([A-Za-z0-9+/=]{16,})",
     "clé privée Lynceus",
     "elle seule émet les clés d'accès : engendrer une nouvelle paire (lynceus cles-paire)"),
    (r"PRIVATE_KEY\s*[:=]\s*([A-Za-z0-9+/=]{16,})",
     "clé privée",
     "engendrer une nouvelle paire"),
    (r"/api/stacks/webhooks/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
     "webhook Portainer",
     "c'est un jeton de déploiement : régénérer le webhook dans Portainer"),
    (r"\b([a-z0-9-]+\.tail[0-9a-f]{4,}\.ts\.net)\b",
     "nom de machine du tailnet",
     "le remplacer par un gabarit ; le tailnet n'a rien à faire dans un dépôt public"),
    (r"\b(100\.(?:6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.[0-9]{1,3}\.[0-9]{1,3})\b",
     "adresse du tailnet (100.64.0.0/10)",
     "la remplacer par un gabarit"),
    (r"(?:POSTGRES_PASSWORD|LYNCEUS_ADMIN_TOKEN|LYNCEUS_LLM_API_KEY)\s*[:=]\s*(\S{8,})",
     "secret d'exploitation renseigné",
     "les fichiers d'exemple se livrent avec des valeurs vides"),
]

# Une alerte qui crie pour rien finit désactivée, et un garde-fou désactivé ne garde rien.
# D'où ce filtre, écrit en clair plutôt qu'en une expression illisible : il reconnaît ce qui
# est manifestement un gabarit, et rien d'autre.
MOTS_GABARIT = ("votre", "your", "exemple", "example", "test", "factice", "placeholder",
                "validation", "changeme", "remplacer", "adresse", "mot de passe")


def est_un_gabarit(valeur: str) -> bool:
    """Vrai si la valeur est une illustration et non un secret.

    Trois formes couvrent tout ce que ce dépôt contient légitimement : la substitution de
    Compose et du shell (`${POSTGRES_PASSWORD}`), le gabarit entre chevrons (`<votre clé>`),
    et la valeur tronquée par des points ou des x (`sk-or-xxxx`, `sk-or-...`)."""
    valeur = valeur.strip()
    if not valeur or valeur[0] in "$<{":
        return True
    if any(marque in valeur.lower() for marque in ("xxx", "...", "…")):
        return True
    if valeur.lower().startswith(MOTS_GABARIT):
        return True
    return all(caractere in " .…<>xX*$?{}[]()/-_" for caractere in valeur)

# Deux fichiers contiennent des secrets pour de bonnes raisons : celui-ci, qui décrit les
# motifs qu'il cherche, et celui qui l'éprouve. Les écarter est nécessaire, mais ce sont
# aussi les deux seuls endroits du dépôt où un vrai secret pourrait dormir sans être vu :
# leurs valeurs sont fabriquées de toutes pièces, et doivent le rester.
IGNORES = {"outils/chercher-secrets.py", "api/tests/test_secrets.py"}

BINAIRES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2",
            ".ttf", ".otf", ".zip", ".gz", ".pdf", ".sqlite3"}


def fichiers_a_lire(arguments: list[str]) -> list[str]:
    if arguments and arguments[0] == "--indexe":
        commande = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"]
    elif arguments:
        return arguments
    else:
        commande = ["git", "ls-files"]
    sortie = subprocess.run(commande, capture_output=True, text=True, check=True).stdout
    return [ligne for ligne in sortie.splitlines() if ligne]


def trouvailles(chemin: str) -> list[tuple[int, str, str, str]]:
    fichier = Path(chemin)
    if chemin in IGNORES or fichier.suffix.lower() in BINAIRES or not fichier.is_file():
        return []
    try:
        lignes = fichier.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, OSError):
        return []

    trouve = []
    for numero, ligne in enumerate(lignes, 1):
        for motif, quoi, remede in MOTIFS:
            for correspondance in re.finditer(motif, ligne):
                valeur = next((g for g in correspondance.groups() if g), correspondance.group(0))
                if est_un_gabarit(valeur):
                    continue
                trouve.append((numero, quoi, remede, valeur[:8] + "…"))
    return trouve


def main() -> int:
    lus = 0
    alertes = []
    for chemin in fichiers_a_lire(sys.argv[1:]):
        lus += 1
        for numero, quoi, remede, extrait in trouvailles(chemin):
            alertes.append(f"  {chemin}:{numero}  {quoi} ({extrait})\n      → {remede}")

    if alertes:
        print(f"{len(alertes)} secret(s) probable(s) :\n", file=sys.stderr)
        print("\n".join(alertes), file=sys.stderr)
        print("\nUn secret poussé est un secret compromis, même retiré au commit suivant :\n"
              "l'historique le garde. Le révoquer passe avant le nettoyage.", file=sys.stderr)
        return 1

    print(f"{lus} fichier(s) inspecté(s), aucun secret repéré.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
