"""L'annuaire : résolution cache/dédup et profils de domaines (cf. docs/ARCHITECTURE.md)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .modeles import Analyse, ConsommationCle, Domaine, Page, Signalement


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


# Longueur du préfixe pour le lookup k-anonyme (modèle HaveIBeenPwned) : le client
# n'envoie que ce préfixe et fait la correspondance finale localement, si bien que le
# serveur ne peut pas savoir quelle page exacte est consultée (cf. docs/ETHIQUE.md §4).
# 5 caractères hexadécimaux = 1 048 576 seaux : assez pour que le préfixe ne désigne
# aucune page en particulier, assez fin pour que la réponse reste légère.
LONGUEUR_PREFIXE = 5


def chercher_par_prefixe(session: Session, prefixe: str) -> list[dict]:
    """Toutes les pages connues dont le hash d'URL commence par ce préfixe.

    Retourne des couples (suffixe du hash, grade, catégorie) : de quoi afficher un badge
    sans que le serveur apprenne l'URL consultée. La carte complète nécessite un appel
    explicite à /v1/analyses/{id}."""
    prefixe = prefixe.lower()
    lignes = session.execute(
        select(Page.url_hash, Analyse.id, Analyse.grade, Analyse.categorie, Analyse.score)
        .join(Analyse, Page.analyse_courante_id == Analyse.id)
        .where(Page.url_hash.startswith(prefixe))
    ).all()
    return [
        {
            "suffixe": url_hash[LONGUEUR_PREFIXE:],
            "analyse_id": analyse_id,
            "grade": grade,
            "categorie": categorie,
            "score": score,
        }
        for url_hash, analyse_id, grade, categorie, score in lignes
    ]


def enregistrer_signalement(
    session: Session, *, analyse_id: int, motif: str, message: str, contact: str | None
) -> Signalement:
    signalement = Signalement(
        analyse_id=analyse_id, motif=motif, message=message, contact=contact
    )
    session.add(signalement)
    session.flush()
    return signalement


def consommer_quota(session: Session, identifiant_cle: str, quota_jour: int) -> tuple[bool, int]:
    """Incrémente la consommation du jour si le quota le permet.

    Retourne (autorisé, consommation après incrément). Le compteur est journalier : une
    nouvelle ligne apparaît chaque jour, les précédentes deviennent inutiles."""
    jour = datetime.now(timezone.utc).date().isoformat()
    ligne = session.scalar(
        select(ConsommationCle).where(
            ConsommationCle.identifiant_cle == identifiant_cle, ConsommationCle.jour == jour
        )
    )
    if ligne is None:
        ligne = ConsommationCle(identifiant_cle=identifiant_cle, jour=jour, analyses=0)
        session.add(ligne)
        session.flush()
    if ligne.analyses >= quota_jour:
        return False, ligne.analyses
    ligne.analyses += 1
    session.flush()
    return True, ligne.analyses


def purger_consommations(session: Session, avant_le: str) -> int:
    """Supprime les compteurs antérieurs à une date — ils ne servent plus à rien."""
    lignes = session.scalars(select(ConsommationCle).where(ConsommationCle.jour < avant_le)).all()
    for ligne in lignes:
        session.delete(ligne)
    session.flush()
    return len(lignes)


STATUTS_SIGNALEMENT = {"nouveau", "examine", "rejete", "sans_objet"}


def lister_signalements(
    session: Session, *, statut: str | None = None, limite: int = 50
) -> list[Signalement]:
    """Signalements les plus anciens d'abord : on traite dans l'ordre d'arrivée."""
    requete = select(Signalement).order_by(Signalement.cree_le)
    if statut:
        requete = requete.where(Signalement.statut == statut)
    return list(session.scalars(requete.limit(limite)))


def traiter_signalement(
    session: Session, signalement_id: int, *, statut: str, decision: str
) -> Signalement | None:
    """Enregistre la décision de l'opérateur. La justification est obligatoire : écarter une
    contestation sans motif reviendrait à l'opacité que Lynceus dénonce (charte §2)."""
    if statut not in STATUTS_SIGNALEMENT:
        raise ValueError(f"Statut inconnu : {statut} (attendus : {sorted(STATUTS_SIGNALEMENT)})")
    signalement = session.get(Signalement, signalement_id)
    if signalement is None:
        return None
    signalement.statut = statut
    signalement.decision = decision
    signalement.traite_le = datetime.now(timezone.utc)
    session.flush()
    return signalement


def compter_signalements(session: Session, analyse_id: int) -> int:
    return session.scalar(
        select(func.count(Signalement.id)).where(Signalement.analyse_id == analyse_id)
    ) or 0


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
