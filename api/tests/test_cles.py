"""Clés d'accès auto-validantes.

Ce qui compte ici : une clé forgée ou modifiée doit être refusée, et la validation ne doit
jamais dépendre d'un annuaire — c'est tout l'intérêt du mécanisme."""

import json
from datetime import date, timedelta

import pytest

from lynceus.cles import CleInvalide, Droits, emettre, generer_paire, valider


@pytest.fixture(scope="module")
def paire():
    return generer_paire()


# ---------- fonctionnement nominal ----------

def test_cle_emise_est_valide(paire):
    privee, publique = paire
    cle, droits = emettre(privee, jours=30, quota_jour=50)
    verifies = valider(cle, publique)
    assert verifies == droits


def test_droits_transportes_dans_la_cle(paire):
    """Le quota et l'expiration voyagent DANS la clé : aucune base n'est consultée."""
    privee, publique = paire
    cle, _ = emettre(privee, jours=7, quota_jour=123)
    droits = valider(cle, publique)
    assert droits.quota_jour == 123
    assert droits.expire_le == (date.today() + timedelta(days=7)).isoformat()


def test_chaque_cle_a_un_identifiant_distinct(paire):
    """Nécessaire pour révoquer une clé précise sans toucher aux autres."""
    privee, publique = paire
    identifiants = {valider(emettre(privee)[0], publique).identifiant for _ in range(20)}
    assert len(identifiants) == 20


# ---------- ce qui doit être refusé ----------

def test_signature_falsifiee_refusee(paire):
    """LA propriété de sécurité : sans la clé privée, on ne peut pas forger de clé."""
    privee, publique = paire
    _, autre_publique = generer_paire()
    cle, _ = emettre(privee)
    with pytest.raises(CleInvalide, match="Signature invalide"):
        valider(cle, autre_publique)  # clé émise par un autre émetteur


def test_charge_utile_modifiee_refusee(paire):
    """Élever son propre quota doit casser la signature."""
    import base64

    privee, publique = paire
    cle, _ = emettre(privee, quota_jour=10)
    prefixe, charge, signature = cle.split(".")

    donnees = json.loads(base64.urlsafe_b64decode(charge + "=" * (-len(charge) % 4)))
    donnees["q"] = 100_000  # quota gonflé
    trafiquee = base64.urlsafe_b64encode(
        json.dumps(donnees, separators=(",", ":"), sort_keys=True).encode()
    ).decode().rstrip("=")

    with pytest.raises(CleInvalide, match="Signature invalide"):
        valider(f"{prefixe}.{trafiquee}.{signature}", publique)


def test_cle_expiree_refusee(paire):
    privee, publique = paire
    cle, _ = emettre(privee, jours=-1)  # expirée hier
    with pytest.raises(CleInvalide, match="expirée"):
        valider(cle, publique)


def test_cle_revoquee_refusee(paire):
    privee, publique = paire
    cle, droits = emettre(privee)
    assert valider(cle, publique, revoquees=set())  # sans liste : acceptée
    with pytest.raises(CleInvalide, match="révoquée"):
        valider(cle, publique, revoquees={droits.identifiant})


def test_formats_invalides_refuses(paire):
    _, publique = paire
    for mauvaise in ("", "pas-une-cle", "LYNC1.trop-court", "AUTRE1.a.b", "LYNC1.!!!.???"):
        with pytest.raises(CleInvalide):
            valider(mauvaise, publique)


def test_cle_publique_invalide_signalee(paire):
    privee, _ = paire
    cle, _ = emettre(privee)
    with pytest.raises(CleInvalide, match="mal configurée"):
        valider(cle, "pas-une-cle-publique")


# ---------- expiration ----------

def test_droits_expiree():
    droits = Droits(identifiant="x", emise_le="2026-01-01", expire_le="2026-06-30", quota_jour=10)
    assert droits.expiree(date(2026, 7, 1)) is True
    assert droits.expiree(date(2026, 6, 30)) is False
    assert droits.expiree(date(2026, 1, 15)) is False
