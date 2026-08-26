"""Clés d'accès auto-validantes (Ed25519).

Une clé porte elle-même ses droits — date d'expiration et quota journalier — et une
signature. L'API vérifie la signature avec la clé publique de l'émetteur : **aucun annuaire
de clés n'est nécessaire**, ni consultation de base au moment de la validation.

    LYNC1.<charge_utile base64url>.<signature base64url>

Séparation émetteur / valideur : seul l'émetteur (le site qui distribue les clés) détient la
clé privée. L'API ne connaît que la publique, si bien que compromettre l'API ne permet pas
de forger des clés. C'est ce qui rendra possible un site d'inscription hébergé ailleurs.

**La génération doit rester côté serveur.** Placer la clé privée dans l'extension
reviendrait à la publier : n'importe qui pourrait alors émettre des clés à volonté.

Ce que ce mécanisme ne résout pas, et qui est traité ailleurs :
- une clé qui circule reste valide → le quota journalier limite les dégâts ;
- la révocation individuelle exige une liste, mais elle ne contient que les clés abusives
  (voir `cles_revoquees` dans la configuration), pas l'ensemble des clés émises.
"""

from __future__ import annotations

import base64
import json
import secrets
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

PREFIXE = "LYNC1"


class CleInvalide(Exception):
    """Clé mal formée, falsifiée, expirée ou révoquée."""


@dataclass(frozen=True)
class Droits:
    """Ce qu'une clé autorise. Voyage dans la clé elle-même, jamais en base."""

    identifiant: str          # aléatoire : sert à révoquer une clé précise si nécessaire
    emise_le: str             # AAAA-MM-JJ
    expire_le: str            # AAAA-MM-JJ
    quota_jour: int

    def expiree(self, aujourdhui: date | None = None) -> bool:
        return (aujourdhui or datetime.now(timezone.utc).date()).isoformat() > self.expire_le


def _encoder(donnees: bytes) -> str:
    return base64.urlsafe_b64encode(donnees).decode().rstrip("=")


def _decoder(texte: str) -> bytes:
    return base64.urlsafe_b64decode(texte + "=" * (-len(texte) % 4))


def generer_paire() -> tuple[str, str]:
    """Crée une paire de clés pour l'émetteur. Retourne (privée, publique) en base64url.

    La privée reste chez l'émetteur ; la publique se met dans la configuration de chaque
    instance qui doit accepter ses clés."""
    privee = Ed25519PrivateKey.generate()
    from cryptography.hazmat.primitives.serialization import (
        Encoding,
        NoEncryption,
        PrivateFormat,
        PublicFormat,
    )

    brut_prive = privee.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    brut_public = privee.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return _encoder(brut_prive), _encoder(brut_public)


def publique_de(cle_privee: str) -> str:
    """Retrouve la clé publique correspondant à une clé privée.

    Une clé publique Ed25519 se déduit de la privée : il n'y a donc rien à conserver de
    plus que la privée pour reconfigurer une instance, et rien à craindre de perdre la
    publique. L'inverse est évidemment faux."""
    try:
        privee = Ed25519PrivateKey.from_private_bytes(_decoder(cle_privee))
    except Exception as erreur:  # base64 invalide, longueur incorrecte
        raise CleInvalide(f"clé privée illisible : {erreur}") from erreur

    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

    return _encoder(privee.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw))


def emettre(cle_privee: str, *, jours: int = 365, quota_jour: int = 50) -> tuple[str, Droits]:
    """Émet une clé signée. À n'exécuter QUE côté émetteur (détenteur de la clé privée)."""
    aujourdhui = datetime.now(timezone.utc).date()
    droits = Droits(
        identifiant=secrets.token_urlsafe(9),
        emise_le=aujourdhui.isoformat(),
        expire_le=(aujourdhui + timedelta(days=jours)).isoformat(),
        quota_jour=quota_jour,
    )
    charge = json.dumps(
        {
            "id": droits.identifiant,
            "e": droits.emise_le,
            "x": droits.expire_le,
            "q": droits.quota_jour,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode()

    privee = Ed25519PrivateKey.from_private_bytes(_decoder(cle_privee))
    signature = privee.sign(charge)
    return f"{PREFIXE}.{_encoder(charge)}.{_encoder(signature)}", droits


def valider(cle: str, cle_publique: str, revoquees: set[str] | None = None) -> Droits:
    """Vérifie une clé et retourne ses droits. Lève CleInvalide sinon.

    Aucune lecture de base : tout est dans la clé et dans la signature."""
    morceaux = cle.strip().split(".")
    if len(morceaux) != 3 or morceaux[0] != PREFIXE:
        raise CleInvalide("Format de clé non reconnu.")

    _, charge_encodee, signature_encodee = morceaux
    try:
        charge = _decoder(charge_encodee)
        signature = _decoder(signature_encodee)
    except Exception as exc:
        raise CleInvalide("Clé illisible.") from exc

    try:
        publique = Ed25519PublicKey.from_public_bytes(_decoder(cle_publique))
        publique.verify(signature, charge)
    except InvalidSignature as exc:
        raise CleInvalide("Signature invalide : cette clé n'a pas été émise par cette instance.") from exc
    except Exception as exc:
        raise CleInvalide("Clé publique de l'instance mal configurée.") from exc

    try:
        donnees = json.loads(charge)
        droits = Droits(
            identifiant=donnees["id"],
            emise_le=donnees["e"],
            expire_le=donnees["x"],
            quota_jour=int(donnees["q"]),
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise CleInvalide("Contenu de clé inattendu.") from exc

    # Signature vérifiée d'abord : inutile d'examiner le contenu d'une clé falsifiée.
    if droits.expiree():
        raise CleInvalide(f"Clé expirée le {droits.expire_le}. Demandez-en une nouvelle.")
    if revoquees and droits.identifiant in revoquees:
        raise CleInvalide("Cette clé a été révoquée.")
    return droits
