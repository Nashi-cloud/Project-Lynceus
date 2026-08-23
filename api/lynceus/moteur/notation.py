"""Notation — calculée par le SERVEUR, jamais par le LLM (cf. docs/METHODOLOGIE.md §5).
Pondérations et seuils publiés : déterminisme et auditabilité."""

from __future__ import annotations

POIDS = {"sources": 0.30, "factualite": 0.30, "ton": 0.20, "transparence": 0.20}
SEUILS = [(80, "A"), (65, "B"), (50, "C"), (30, "D")]


def calculer_score(dimensions: dict) -> int:
    return round(sum(poids * dimensions[nom]["score"] for nom, poids in POIDS.items()))


def calculer_grade(score: int) -> str:
    for seuil, grade in SEUILS:
        if score >= seuil:
            return grade
    return "E"
