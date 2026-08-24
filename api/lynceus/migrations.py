"""Migrations légères de schéma.

Le projet est auto-hébergeable : une instance existante ne doit pas casser quand le schéma
évolue. `Base.metadata.create_all()` crée les tables manquantes mais ne touche jamais à
celles qui existent — d'où ce complément, qui ajoute les colonnes apparues depuis.

Portée volontairement limitée aux AJOUTS de colonnes, seul cas rencontré jusqu'ici et le
seul qui soit sûr sans outillage dédié. Tout changement plus lourd (renommage, changement
de type, contrainte) demandera Alembic — voir docs/ARCHITECTURE.md.
"""

from __future__ import annotations

import logging

from sqlalchemy import Engine, inspect, text

from .modeles import Base

logger = logging.getLogger(__name__)


def appliquer(moteur: Engine) -> list[str]:
    """Ajoute les colonnes déclarées dans les modèles mais absentes en base.

    Retourne la liste des modifications appliquées (vide si le schéma était à jour)."""
    inspecteur = inspect(moteur)
    tables_existantes = set(inspecteur.get_table_names())
    appliquees: list[str] = []

    for table in Base.metadata.sorted_tables:
        if table.name not in tables_existantes:
            continue  # create_all s'en charge
        colonnes_en_base = {c["name"] for c in inspecteur.get_columns(table.name)}
        for colonne in table.columns:
            if colonne.name in colonnes_en_base:
                continue
            if not colonne.nullable and colonne.default is None and colonne.server_default is None:
                # Ajouter une colonne obligatoire sans valeur par défaut échouerait sur une
                # table déjà peuplée : on le signale plutôt que de planter au premier accès.
                logger.warning(
                    "Colonne %s.%s obligatoire et sans défaut : migration manuelle requise.",
                    table.name, colonne.name,
                )
                continue
            type_sql = colonne.type.compile(moteur.dialect)
            with moteur.begin() as connexion:
                connexion.execute(text(f'ALTER TABLE {table.name} ADD COLUMN {colonne.name} {type_sql}'))
            appliquees.append(f"{table.name}.{colonne.name}")
            logger.info("Colonne ajoutée : %s.%s", table.name, colonne.name)

    return appliquees
