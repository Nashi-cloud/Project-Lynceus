"""Index de recherche par préfixe sur url_hash.

Le lookup k-anonyme filtre par préfixe (LIKE 'abcde%'). En PostgreSQL, un index B-tree
ordinaire n'est PAS utilisé pour ce type de filtre lorsque la collation de la base n'est
pas « C » : mesuré sur 500 000 pages, la requête tombait en balayage séquentiel à 22 ms,
contre 0,08 ms avec l'index ci-dessous — et 0,25 ms sur 5 millions de pages.

C'est la requête la plus fréquente de l'API (chaque page visitée, badge passif activé) :
sans cet index, elle devient le premier goulot d'étranglement à l'échelle.

SQLite ignore l'opérateur et n'a pas ce problème : l'index n'y est pas créé.

Revision ID: a1b2c3d4e5f6
Revises: 672b781b582c
"""
from typing import Sequence, Union

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "672b781b582c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NOM_INDEX = "ix_pages_url_hash_prefixe"


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return  # opérateur propre à PostgreSQL ; SQLite fait déjà le bon choix
    op.execute(f"CREATE INDEX IF NOT EXISTS {NOM_INDEX} ON pages (url_hash varchar_pattern_ops)")


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    op.execute(f"DROP INDEX IF EXISTS {NOM_INDEX}")
