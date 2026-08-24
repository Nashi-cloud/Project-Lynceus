"""Migrations de schéma (Alembic).

Le projet est auto-hébergeable : une instance déjà déployée ne doit ni casser ni perdre ses
données quand le schéma évolue. Trois situations sont couvertes — base neuve, instance
antérieure à Alembic (tables créées par create_all), instance déjà suivie."""

import sqlite3

import pytest
from sqlalchemy import create_engine, inspect, text

from lynceus.migrations import appliquer
from lynceus.modeles import Base


@pytest.fixture
def chemin_base(tmp_path):
    return tmp_path / "instance.sqlite3"


def _moteur(chemin):
    return create_engine(f"sqlite:///{chemin}")


def _tables(chemin) -> set[str]:
    with sqlite3.connect(chemin) as connexion:
        return {r[0] for r in connexion.execute("SELECT name FROM sqlite_master WHERE type='table'")}


# ---------- base neuve ----------

def test_base_neuve_creee_par_alembic(chemin_base):
    resultat = appliquer(_moteur(chemin_base))
    assert resultat == "creee"
    assert {"analyses", "pages", "domaines", "signalements", "alembic_version"} <= _tables(chemin_base)


def test_base_neuve_est_suivie(chemin_base):
    """La base doit être versionnée, sinon les migrations suivantes ne s'appliqueraient pas."""
    appliquer(_moteur(chemin_base))
    with sqlite3.connect(chemin_base) as connexion:
        assert connexion.execute("SELECT version_num FROM alembic_version").fetchone() is not None


# ---------- instance antérieure à Alembic ----------

def test_instance_existante_adoptee(chemin_base):
    """Cas rencontré en production : tables créées par create_all(), sans suivi Alembic.
    Alembic doit les adopter, pas tenter de les recréer."""
    Base.metadata.create_all(_moteur(chemin_base))  # ancienne méthode de création
    assert "alembic_version" not in _tables(chemin_base)

    resultat = appliquer(_moteur(chemin_base))
    assert resultat == "estampillee_puis_migree"
    assert "alembic_version" in _tables(chemin_base)


def test_donnees_preservees_lors_de_l_adoption(chemin_base):
    """Une migration ne doit JAMAIS perdre de données existantes."""
    moteur = _moteur(chemin_base)
    Base.metadata.create_all(moteur)
    with moteur.begin() as connexion:
        connexion.execute(text(
            "INSERT INTO analyses (content_hash, prompt_version, schema_version, carte, "
            "categorie, score, grade, confiance, modele, fournisseur, duree_ms, cree_le) "
            "VALUES ('abc', '0.1.1', '0.1.0', '{}', 'information', 80, 'A', 0.9, "
            "'test/modele', 'test', 100, '2026-01-01')"
        ))

    appliquer(moteur)

    with moteur.begin() as connexion:
        ligne = connexion.execute(text("SELECT content_hash, grade FROM analyses")).one()
    assert ligne[0] == "abc"
    assert ligne[1] == "A"


# ---------- idempotence ----------

def test_relance_sans_effet(chemin_base):
    """Les migrations tournent à chaque démarrage : relancer ne doit rien casser."""
    moteur = _moteur(chemin_base)
    assert appliquer(moteur) == "creee"
    assert appliquer(moteur) == "migree"
    assert appliquer(moteur) == "migree"


def test_schema_conforme_aux_modeles(chemin_base):
    """Le schéma produit par Alembic doit correspondre aux modèles : sinon la migration
    initiale a divergé des déclarations SQLAlchemy."""
    moteur = _moteur(chemin_base)
    appliquer(moteur)
    inspecteur = inspect(moteur)

    for table in Base.metadata.sorted_tables:
        colonnes_reelles = {c["name"] for c in inspecteur.get_columns(table.name)}
        colonnes_attendues = {c.name for c in table.columns}
        assert colonnes_attendues == colonnes_reelles, f"divergence sur la table {table.name}"
