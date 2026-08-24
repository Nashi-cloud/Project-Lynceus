"""Migrations légères — une instance déjà déployée ne doit pas casser quand le schéma évolue.

Ce cas s'est produit en conditions réelles : les colonnes `decision` et `traite_le` ajoutées
aux signalements manquaient sur une base existante, et toute lecture échouait en 500. Les
tests ne l'avaient pas vu parce qu'ils partent d'une base vierge."""

from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, inspect, text

from lynceus.migrations import appliquer
from lynceus.modeles import Base


def _moteur(tmp_path):
    return create_engine(f"sqlite:///{tmp_path}/migration.sqlite3")


def test_schema_a_jour_ne_change_rien(tmp_path):
    moteur = _moteur(tmp_path)
    Base.metadata.create_all(moteur)
    assert appliquer(moteur) == []


def test_colonne_manquante_ajoutee(tmp_path):
    """Reproduit le cas réel : table créée avant l'ajout de colonnes."""
    moteur = _moteur(tmp_path)
    # Table « signalements » dans son ancienne forme, sans decision ni traite_le.
    ancien = MetaData()
    Table(
        "signalements", ancien,
        Column("id", Integer, primary_key=True),
        Column("analyse_id", Integer),
        Column("motif", String(40)),
        Column("message", String),
        Column("contact", String(320)),
        Column("statut", String(20)),
        Column("cree_le", String),
    ).create(moteur)

    appliquees = appliquer(moteur)
    assert "signalements.decision" in appliquees
    assert "signalements.traite_le" in appliquees

    colonnes = {c["name"] for c in inspect(moteur).get_columns("signalements")}
    assert {"decision", "traite_le"} <= colonnes


def test_donnees_existantes_preservees(tmp_path):
    """Une migration ne doit jamais perdre de données."""
    moteur = _moteur(tmp_path)
    ancien = MetaData()
    Table(
        "signalements", ancien,
        Column("id", Integer, primary_key=True),
        Column("analyse_id", Integer),
        Column("motif", String(40)),
        Column("message", String),
        Column("contact", String(320)),
        Column("statut", String(20)),
        Column("cree_le", String),
    ).create(moteur)
    with moteur.begin() as connexion:
        connexion.execute(text(
            "INSERT INTO signalements (analyse_id, motif, message, statut, cree_le) "
            "VALUES (1, 'autre', 'contestation existante', 'nouveau', '2026-01-01')"
        ))

    appliquer(moteur)

    with moteur.begin() as connexion:
        ligne = connexion.execute(text("SELECT message, statut, decision FROM signalements")).one()
    assert ligne[0] == "contestation existante"
    assert ligne[1] == "nouveau"
    assert ligne[2] is None  # nouvelle colonne, vide pour les lignes anciennes


def test_migration_idempotente(tmp_path):
    """Relancer la migration ne doit rien casser — elle tourne à chaque démarrage."""
    moteur = _moteur(tmp_path)
    Base.metadata.create_all(moteur)
    assert appliquer(moteur) == []
    assert appliquer(moteur) == []


def test_table_absente_laissee_a_create_all(tmp_path):
    moteur = _moteur(tmp_path)  # base totalement vide
    assert appliquer(moteur) == []
