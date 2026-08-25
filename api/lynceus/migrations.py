"""Application des migrations de schéma au démarrage.

Le projet est auto-hébergeable : une instance ne doit ni casser quand le schéma évolue, ni
exiger une commande manuelle après chaque mise à jour. Alembic est appelé au démarrage et
gère trois situations :

1. **Base neuve** — toutes les migrations sont appliquées depuis le début.
2. **Instance antérieure à Alembic** (tables créées par `create_all()`) — la base est
   estampillée à la révision initiale sans rejouer sa migration, qui échouerait sur des
   tables déjà présentes ; les migrations suivantes s'appliquent normalement.
3. **Instance déjà suivie par Alembic** — seules les migrations en attente sont appliquées.

Pour créer une migration après avoir modifié `modeles.py` :

    cd api && .venv/bin/alembic revision --autogenerate -m "description"

Relire systématiquement le fichier généré : l'autogénération ne devine ni les renommages
(qu'elle traduit en suppression + création, donc en perte de données) ni les migrations de
contenu.
"""

from __future__ import annotations

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, inspect, text

from .modeles import Base

logger = logging.getLogger(__name__)

RACINE_API = Path(__file__).resolve().parent.parent
FICHIER_ALEMBIC = RACINE_API / "alembic.ini"

# Tables du schéma initial : leur présence signale une instance antérieure à Alembic.
TABLES_INITIALES = {"analyses", "pages", "domaines"}


def _configuration(url_base: str) -> Config:
    # Config() sans fichier reste valide : toutes les options utiles sont posées ci-dessous.
    config = Config(str(FICHIER_ALEMBIC) if FICHIER_ALEMBIC.is_file() else None)
    config.set_main_option("script_location", str(RACINE_API / "lynceus" / "migrations_alembic"))
    config.set_main_option("sqlalchemy.url", url_base.replace("%", "%%"))
    return config


# Identifiant du verrou consultatif PostgreSQL. Arbitraire mais stable : deux instances
# qui démarrent ensemble doivent choisir le MÊME verrou pour se coordonner.
VERROU_MIGRATION = 8_154_733_201


def appliquer(moteur: Engine) -> str:
    """Met le schéma à jour. Retourne un mot décrivant ce qui a été fait.

    Plusieurs répliques peuvent démarrer en même temps : sans coordination, elles
    appliqueraient les mêmes migrations de front, avec des erreurs (« table déjà
    existante ») ou, pire, des migrations partielles. Sur PostgreSQL, un verrou consultatif
    sérialise l'opération : la première réplique migre, les autres attendent puis
    constatent qu'il n'y a plus rien à faire. SQLite n'est pas concerné (mono-processus)."""
    config = _configuration(str(moteur.url.render_as_string(hide_password=False)))

    if moteur.dialect.name == "postgresql":
        # Le verrou est tenu par la connexion : on la garde ouverte pendant toute la
        # migration, et il se libère à sa fermeture, y compris si le processus meurt.
        with moteur.connect() as verrou:
            verrou.execute(text("SELECT pg_advisory_lock(:cle)"), {"cle": VERROU_MIGRATION})
            verrou.commit()
            try:
                return _appliquer_sans_verrou(moteur, config)
            finally:
                verrou.execute(text("SELECT pg_advisory_unlock(:cle)"), {"cle": VERROU_MIGRATION})
                verrou.commit()
    return _appliquer_sans_verrou(moteur, config)


def _appliquer_sans_verrou(moteur: Engine, config: Config) -> str:
    with moteur.connect() as connexion:
        revision_actuelle = MigrationContext.configure(connexion).get_current_revision()
        tables = set(inspect(connexion).get_table_names())

    if revision_actuelle is None and TABLES_INITIALES <= tables:
        # Instance d'avant Alembic : ses tables existent déjà, il faut l'adopter sans rejouer
        # les migrations qui les créeraient une seconde fois. Reste à savoir OÙ l'estampiller.
        attendues = {table.name for table in Base.metadata.sorted_tables}
        if attendues <= tables:
            # Toutes les tables des modèles sont là (base créée par create_all avec une
            # version récente) : le schéma est à jour, il lui manque seulement le suivi.
            command.stamp(config, "head")
            logger.info("Base complète adoptée : estampillée à head.")
            return "adoptee"
        # Schéma partiel : on repart de la révision initiale et on applique la suite.
        revision_initiale = ScriptDirectory.from_config(config).get_base()
        command.stamp(config, revision_initiale)
        logger.info(
            "Base antérieure estampillée à la révision initiale (%s) ; tables manquantes : %s.",
            revision_initiale, ", ".join(sorted(attendues - tables)),
        )
        command.upgrade(config, "head")
        return "estampillee_puis_migree"

    command.upgrade(config, "head")
    return "creee" if revision_actuelle is None else "migree"
