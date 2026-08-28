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

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings

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


class ReglagesTolerants(BaseSettings):
    """Réglages pour lesquels une variable vide vaut « non renseignée ».

    Un fichier .env s'écrit à la main, et il est normal d'y laisser une ligne vide en
    attendant de la remplir. `lynceus env` en engendre lui-même : `LYNCEUS_LLM_CACHE_PROMPT=`
    sort vide, parce qu'un défaut posé par le générateur serait un choix fait à la place de
    l'exploitant.

    Sans cette tolérance, une telle ligne fait échouer la validation d'un champ non textuel
    et l'instance refuse de démarrer, pour un réglage que personne n'a demandé. Le cas s'est
    produit en recette : l'API tombait au démarrage, le portail attendait une API saine qui
    ne venait jamais, et le proxy renvoyait 502 sans que rien ne nomme la cause.

    La tolérance ne vaut que pour les champs non textuels. Pour une chaîne, le vide est une
    valeur qui veut dire quelque chose : `LYNCEUS_LLM_FOURNISSEUR=` demande de déduire le
    nom du fournisseur de l'adresse, ce qui n'est pas la même chose que de ne rien dire."""

    @classmethod
    def _champ_designe(cls, cle: str):
        """Le champ visé par une clé, qu'elle soit son nom ou l'un de ses deux alias.

        À ce stade, une valeur venue de l'environnement porte encore le nom de la variable
        et non celui du champ : chercher seulement par nom de champ laisserait passer tous
        les réglages aliassés, c'est-à-dire précisément ceux que ce projet a ajoutés."""
        champ = cls.model_fields.get(cle)
        if champ is not None:
            return champ
        for candidat in cls.model_fields.values():
            alias = getattr(candidat, "validation_alias", None)
            if alias is not None and cle in getattr(alias, "choices", ()):
                return candidat
        return None

    @model_validator(mode="before")
    @classmethod
    def _une_valeur_vide_vaut_absente(cls, valeurs):
        if not isinstance(valeurs, dict):
            return valeurs
        gardees = {}
        for cle, valeur in valeurs.items():
            champ = cls._champ_designe(cle) if isinstance(valeur, str) and not valeur.strip() else None
            if champ is not None and champ.annotation is not str:
                continue
            gardees[cle] = valeur
        return gardees
