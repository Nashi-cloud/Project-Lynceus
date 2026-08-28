"""Les variables d'environnement répondent à deux noms, l'un français, l'autre anglais.

Le code de ce projet est en français et le restera. Mais les variables d'environnement ne
sont pas du code : ce sont la porte de l'exploitant, celle qu'il ouvre en montant son
instance, guide de déploiement en anglais à côté. Lui demander de deviner ce que veut dire
`CLES_REVOQUEES` reviendrait à écrire la documentation dans une langue et l'interface dans
une autre.

Les deux noms sont donc acceptés partout, et aucune instance existante n'a à bouger. Le nom
français reste le nom canonique, celui qu'engendre `lynceus env` : c'est lui qui figure dans
les fichiers déjà déployés, et le changer ne rendrait service à personne.

Une seule chose est refusée en silence : rien. Poser les deux noms avec des valeurs
différentes déclenche un avertissement au démarrage, parce qu'un réglage ignoré sans bruit
est exactement le genre de panne qui coûte une soirée.
"""

from __future__ import annotations

import os
import sys

from pydantic import AliasChoices, Field

# Français d'abord : c'est le nom canonique, et il l'emporte si les deux sont posés.
ALIAS: dict[str, str] = {}


def deux_noms(francais: str, anglais: str, defaut):
    """Déclare un réglage sous ses deux noms. Le français prime si les deux sont donnés."""
    ALIAS[francais] = anglais
    return Field(defaut, validation_alias=AliasChoices(francais, anglais))


def avertir_des_conflits(environnement: dict[str, str] | None = None) -> list[str]:
    """Nomme les réglages posés deux fois avec des valeurs différentes.

    L'un des deux serait appliqué et l'autre ignoré, sans que rien ne le dise. Retourne les
    messages plutôt que de seulement les écrire, pour que les tests puissent les lire."""
    env = os.environ if environnement is None else environnement
    conflits = []
    for francais, anglais in ALIAS.items():
        if francais in env and anglais in env and env[francais] != env[anglais]:
            conflits.append(
                f"{francais} et {anglais} sont posés avec des valeurs différentes : "
                f"c'est {francais} qui s'applique, l'autre est ignoré."
            )
    for message in conflits:
        print(f"[lynceus] {message}", file=sys.stderr)
    return conflits
