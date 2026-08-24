"""Environnement Alembic — la base de données est celle configurée par l'instance
(LYNCEUS_DATABASE_URL), jamais une URL codée en dur dans alembic.ini."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from lynceus.config import parametres
from lynceus.modeles import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# L'appelant (lynceus/migrations.py) fournit déjà l'URL du moteur de l'application : ne
# JAMAIS l'écraser, sinon les migrations viseraient une autre base que celle demandée.
# On ne retombe sur la configuration de l'instance que pour un appel direct à la commande
# `alembic`, où aucune URL n'a été passée.
if not config.get_main_option("sqlalchemy.url", None):
    config.set_main_option("sqlalchemy.url", parametres().database_url.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # SQLite ne sait pas modifier une colonne en place : le mode « batch » recrée la
        # table proprement. Sans effet sur PostgreSQL.
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
