"""Modèle de données de l'annuaire (cf. docs/ARCHITECTURE.md)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

TypeJSON = JSON().with_variant(JSONB(), "postgresql")


def _maintenant() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Analyse(Base):
    """Une carte d'analyse — attachée à un contenu (content_hash), pas à une URL :
    le même contenu copié sous plusieurs URL partage la même analyse."""

    __tablename__ = "analyses"
    __table_args__ = (UniqueConstraint("content_hash", "prompt_version", name="uq_contenu_prompt"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    prompt_version: Mapped[str] = mapped_column(String(20))
    schema_version: Mapped[str] = mapped_column(String(20))
    carte: Mapped[dict] = mapped_column(TypeJSON)
    categorie: Mapped[str] = mapped_column(String(40))
    score: Mapped[int] = mapped_column(Integer)
    grade: Mapped[str] = mapped_column(String(1))
    confiance: Mapped[float] = mapped_column(Float)
    modele: Mapped[str] = mapped_column(String(120))
    fournisseur: Mapped[str] = mapped_column(String(120))
    duree_ms: Mapped[int] = mapped_column(Integer, default=0)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_maintenant)


class Page(Base):
    """Une URL connue de l'annuaire, pointant vers son analyse courante."""

    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(Text)
    url_normalisee: Mapped[str] = mapped_column(Text)
    url_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    domaine: Mapped[str] = mapped_column(String(255), index=True)
    analyse_courante_id: Mapped[int | None] = mapped_column(ForeignKey("analyses.id"), nullable=True)
    premiere_vue: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_maintenant)
    derniere_vue: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_maintenant)


class Signalement(Base):
    """Contestation d'une analyse — par un lecteur ou par l'éditeur du site (charte §6).

    Aucune donnée personnelle n'est requise : un signalement est anonyme par défaut.
    Le champ `contact` reste facultatif, pour un éditeur qui souhaite une réponse."""

    __tablename__ = "signalements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analyse_id: Mapped[int] = mapped_column(ForeignKey("analyses.id"), index=True)
    motif: Mapped[str] = mapped_column(String(40))
    message: Mapped[str] = mapped_column(Text)
    contact: Mapped[str | None] = mapped_column(String(320), nullable=True)
    statut: Mapped[str] = mapped_column(String(20), default="nouveau", index=True)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_maintenant)


class Domaine(Base):
    """Profil agrégé d'un domaine, recalculé à chaque nouvelle analyse."""

    __tablename__ = "domaines"

    domaine: Mapped[str] = mapped_column(String(255), primary_key=True)
    nb_analyses: Mapped[int] = mapped_column(Integer, default=0)
    score_moyen: Mapped[float] = mapped_column(Float, default=0.0)
    distribution_grades: Mapped[dict] = mapped_column(TypeJSON, default=dict)
    maj_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_maintenant)
