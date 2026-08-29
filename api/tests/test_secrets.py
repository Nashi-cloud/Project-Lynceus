"""Le détecteur de secrets, éprouvé dans les deux sens.

Un détecteur qui ne trouve rien rassure à tort ; un détecteur qui crie pour rien finit
désactivé, et un garde-fou désactivé ne garde rien. Ces tests tiennent les deux bouts."""

import subprocess
import sys

import pytest

from lynceus.config import trouver_racine

OUTIL = trouver_racine() / "outils" / "chercher-secrets.py"


def inspecter(tmp_path, contenu: str) -> subprocess.CompletedProcess:
    fichier = tmp_path / "essai.env"
    fichier.write_text(contenu, encoding="utf-8")
    return subprocess.run([sys.executable, str(OUTIL), str(fichier)],
                          capture_output=True, text=True)


# Les appâts sont assemblés au lieu d'être écrits d'un tenant, et ce n'est pas de la
# coquetterie. Un dépôt public est passé au crible par des détecteurs qui ne savent pas
# qu'une clé est fabriquée : la première version de ce fichier a déclenché une alerte
# « Tailscale API Key » sur GitHub, à traiter à la main pour rien. Découpé, le littéral
# n'existe nulle part dans les sources, mais il est bien reconstitué avant d'être écrit
# dans le fichier que le détecteur inspecte : l'épreuve reste entière.
FAUX = {
    "tailscale": "tskey-" + "auth-" + "kM3xQp7ZrT1a9vNb2LcYwHs4dEgFj6Uk",
    "openrouter": "sk-" + "or-v1-" + "3f8a2c91d47e05b6a8c3f10e29d7b4a6c85f1e0d93b2",
    "anthropic": "sk-" + "ant-api03-" + "Zx7Kq2mR9tLp4vN8wYbC1eGh5JdF0sAu",
    "github": "ghp_" + "9mK2xQ7pR4tV8nL3wYbC5eGh1JdF0sAu6Zx",
}


@pytest.mark.parametrize("ligne, attendu", [
    (f"TS_AUTHKEY={FAUX['tailscale']}", "Tailscale"),
    (f"LYNCEUS_LLM_API_KEY={FAUX['openrouter']}", "OpenRouter"),
    (f"CLE={FAUX['anthropic']}", "Anthropic"),
    (f"JETON={FAUX['github']}", "GitHub"),
    ("LYNCEUS_PORTAIL_CLE_PRIVEE=MC4CAQAwBQYDK2VwBCIEIKx9Qw2mF7bT3nR8vHc1LpYs", "privée"),
    ("W=https://h.example/api/stacks/webhooks/5104de32-d68f-4e8b-b314-46d3c0b15dbb", "Portainer"),
    ("A=https://une-machine.tailabcd.ts.net/", "tailnet"),
    ("A=http://100.127.0.1:8000", "tailnet"),
    ("-----BEGIN OPENSSH PRIVATE KEY-----", "clé privée"),
])
def test_un_vrai_secret_est_repere(tmp_path, ligne, attendu):
    resultat = inspecter(tmp_path, ligne + "\n")
    assert resultat.returncode == 1, f"non repéré : {ligne}"
    assert attendu in resultat.stderr


@pytest.mark.parametrize("ligne", [
    "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}",
    "LYNCEUS_LLM_API_KEY=sk-or-xxxxxxxxxxxx",
    "LYNCEUS_ADMIN_TOKEN=<votre jeton>",
    "LYNCEUS_PORTAIL_CLE_PRIVEE=",
    "LYNCEUS_LLM_API_KEY=${LYNCEUS_LLM_API_KEY:?clé du fournisseur LLM requise}",
    "adresse : https://lynceus-staging.<votre-tailnet>.ts.net",
])
def test_un_gabarit_ne_declenche_rien(tmp_path, ligne):
    """La documentation montre la forme des secrets pour l'expliquer. Elle ne doit pas
    devenir sa propre suspecte, sans quoi l'étape passe au rouge en permanence et finit
    par être retirée du verifier."""
    resultat = inspecter(tmp_path, ligne + "\n")
    assert resultat.returncode == 0, f"fausse alerte sur : {ligne}\n{resultat.stderr}"


def test_le_depot_entier_est_propre():
    """Ce que `verifier.sh` exécute, rejoué ici : le dépôt ne doit rien contenir."""
    resultat = subprocess.run([sys.executable, str(OUTIL)],
                              capture_output=True, text=True, cwd=trouver_racine())
    assert resultat.returncode == 0, resultat.stderr


def test_le_crochet_pre_commit_est_versionne_et_executable():
    """Un crochet qui n'est pas dans le dépôt ne protège que celui qui l'a écrit."""
    crochet = trouver_racine() / ".githooks" / "pre-commit"
    assert crochet.is_file()
    assert crochet.stat().st_mode & 0o111, "le crochet doit être exécutable"
    assert "--indexe" in crochet.read_text(encoding="utf-8")
