"""L'annuaire : résolution cache/dédup et profils de domaines (cf. docs/ARCHITECTURE.md)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .modeles import Analyse, Domaine, Page


def chercher_analyse(session: Session, content_hash: str, prompt_version: str) -> Analyse | None:
    """Cas 1 et 3 de la résolution : même contenu (quelle que soit l'URL) déjà analysé avec ce prompt."""
    return session.scalar(
        select(Analyse).where(Analyse.content_hash == content_hash, Analyse.prompt_version == prompt_version)
    )


def chercher_page(session: Session, url_hash: str) -> Page | None:
    return session.scalar(select(Page).where(Page.url_hash == url_hash))


def lier_page(session: Session, *, url: str, url_normalisee: str, url_hash: str, domaine: str, analyse: Analyse) -> Page:
    """Crée ou met à jour la page et la pointe vers son analyse courante."""
    page = chercher_page(session, url_hash)
    maintenant = datetime.now(timezone.utc)
    if page is None:
        page = Page(url=url, url_normalisee=url_normalisee, url_hash=url_hash, domaine=domaine)
        session.add(page)
    page.analyse_courante_id = analyse.id
    page.derniere_vue = maintenant
    session.flush()
    recalculer_domaine(session, domaine)
    return page


def recalculer_domaine(session: Session, domaine: str) -> None:
    """Agrégat sur les analyses COURANTES des pages du domaine."""
    lignes = session.execute(
        select(Analyse.grade, func.count(Analyse.id), func.avg(Analyse.score))
        .join(Page, Page.analyse_courante_id == Analyse.id)
        .where(Page.domaine == domaine)
        .group_by(Analyse.grade)
    ).all()
    nb = sum(l[1] for l in lignes)
    if nb == 0:
        return
    score_moyen = sum(l[1] * l[2] for l in lignes) / nb
    distribution = {grade: compte for grade, compte, _ in lignes}

    profil = session.get(Domaine, domaine)
    if profil is None:
        profil = Domaine(domaine=domaine)
        session.add(profil)
    profil.nb_analyses = nb
    profil.score_moyen = round(float(score_moyen), 1)
    profil.distribution_grades = distribution
    profil.maj_le = datetime.now(timezone.utc)
    session.flush()


def profil_domaine(session: Session, domaine: str) -> dict | None:
    profil = session.get(Domaine, domaine)
    if profil is None:
        return None
    return {
        "domaine": profil.domaine,
        "nb_analyses": profil.nb_analyses,
        "score_moyen": profil.score_moyen,
        "distribution_grades": profil.distribution_grades,
        "maj_le": profil.maj_le.isoformat(),
    }
