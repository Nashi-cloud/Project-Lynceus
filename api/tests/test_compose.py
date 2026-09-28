"""Les fichiers compose transmettent-ils bien les réglages au conteneur ?

Ils listent les variables une à une. Une variable absente de la liste est ignorée sans
bruit : réglée dans Portainer, elle n'atteint jamais le conteneur, et l'instance tourne
avec le défaut du code. C'est arrivé : LYNCEUS_LLM_RAISONNEMENT existait depuis des
semaines sans qu'aucun compose ne la transmette."""

from pathlib import Path

import pytest
import yaml

from lynceus.config import Parametres

RACINE_API = Path(__file__).resolve().parents[1]

# Tout réglage qui change la note doit pouvoir être fixé en production.
QUI_CHANGENT_LA_NOTE = ["LYNCEUS_LLM_MODEL", "LYNCEUS_LLM_RAISONNEMENT", "LYNCEUS_LLM_HEBERGEURS",
                        "LYNCEUS_LLM_HEBERGEURS_REPLI", "LYNCEUS_LLM_CACHE_PROMPT"]


def _environnement_api(fichier: str) -> dict:
    compose = yaml.safe_load((RACINE_API / fichier).read_text(encoding="utf-8"))
    return compose["services"]["api"]["environment"]


@pytest.mark.parametrize("fichier", ["docker-compose.yml", "docker-compose.prod.yml",
                                     "docker-compose.staging.yml"])
def test_les_reglages_qui_changent_la_note_sont_transmis(fichier):
    environnement = _environnement_api(fichier)
    manquants = [v for v in QUI_CHANGENT_LA_NOTE if v not in environnement]
    assert not manquants, f"{fichier} ne transmet pas {manquants}"


def test_chaque_variable_transmise_est_lue_par_l_application():
    """L'inverse : une variable mal orthographiée dans le compose serait transmise, puis
    ignorée par l'application."""
    for variable in QUI_CHANGENT_LA_NOTE:
        assert variable.removeprefix("LYNCEUS_").lower() in Parametres.model_fields or any(
            variable in str(champ.validation_alias) for champ in Parametres.model_fields.values()
        ), variable
