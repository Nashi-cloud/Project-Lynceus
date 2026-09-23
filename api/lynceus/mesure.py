"""Mesurer une chaîne d'analyse : l'étape zéro de docs/ARCHITECTURE-CIBLE.md §8.

La calibration dit si une carte respecte des attentes, cas par cas, en oui ou non. Elle ne dit
pas de combien une chaîne en vaut une autre, ni si deux passes de la même chaîne rendent la
même chose. Or c'est précisément ce qu'il faudra savoir pour comparer la chaîne actuelle à un
encodeur de repérage : sans métrique, une amélioration et un tirage chanceux se ressemblent.

Ce module ne fait que compter. Il ne lance aucune analyse et n'appelle aucun réseau : il prend
des cartes déjà rendues, des annotations humaines et le journal des passes, et en tire des
chiffres. Tout y est déterministe, ce qui permet de le tester entièrement.

**Les positions.** Un intervalle est un couple (début, fin) de caractères dans le **texte de
référence** d'une page : son Markdown normalisé par `normaliser_texte`, celui-là même dont on
calcule l'empreinte et dans lequel on vérifie les extraits. Les annotateurs n'écrivent pas de
positions, ce qui serait fragile et pénible : ils recopient l'extrait, et la position s'en
déduit. Une carte d'aujourd'hui ne porte que des extraits, et se localise de la même façon.

**Le recouvrement partiel.** Deux intervalles qui se chevauchent sans coïncider ne sont ni un
succès ni un échec complets. La mesure retenue est celle des campagnes SemEval 2020 tâche 11
et CheckThat! 2024 tâche 3 : chaque intervalle prédit rapporte la part de sa longueur couverte
par un intervalle de référence de même technique, et symétriquement pour le rappel. C'est ce
qui rendra nos chiffres comparables aux leurs.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

from .moteur.validation import _nettoyer_extrait
from .normalisation import hacher_contenu, normaliser_texte

GRADES = ("A", "B", "C", "D", "E")


# ---------------------------------------------------------------------------
# Intervalles
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Intervalle:
    debut: int
    fin: int
    technique: str

    @property
    def longueur(self) -> int:
        return max(0, self.fin - self.debut)


class ExtraitIntrouvable(ValueError):
    """Un extrait annoté ne figure pas dans le texte de référence, ou pas assez de fois."""


def texte_de_reference(contenu_markdown: str) -> str:
    """Le texte sur lequel toutes les positions se comptent. Voir la docstring du module."""
    return normaliser_texte(contenu_markdown)


def localiser(extrait: str, reference: str, occurrence: int = 1) -> tuple[int, int]:
    """La position de la n-ième occurrence d'un extrait dans le texte de référence.

    L'extrait est nettoyé comme le fait la validation des cartes (espaces, guillemets et
    points de suspension d'habillage) : une annotation et une carte qui recopient le même
    passage doivent tomber au même endroit."""
    cible = _nettoyer_extrait(extrait)
    if not cible:
        raise ExtraitIntrouvable("extrait vide")
    depart = -1
    for _ in range(max(1, occurrence)):
        depart = reference.find(cible, depart + 1)
        if depart == -1:
            raise ExtraitIntrouvable(
                f"extrait absent du texte (occurrence {occurrence}) : « {cible[:60]} »")
    return depart, depart + len(cible)


def intervalles_de_carte(carte: dict, reference: str) -> tuple[list[Intervalle], int]:
    """Les techniques d'une carte, localisées. Rend aussi le nombre d'extraits introuvables.

    Une carte validée par le serveur n'en a normalement aucun : c'est le garde-fou verbatim.
    Les compter quand même garde la mesure honnête le jour où une autre chaîne, un encodeur
    par exemple, fournira ses propres cartes sans passer par cette validation."""
    trouves, perdus = [], 0
    for technique in carte.get("techniques_detectees", []):
        if "debut" in technique and "fin" in technique:
            trouves.append(Intervalle(technique["debut"], technique["fin"], technique["id"]))
            continue
        try:
            debut, fin = localiser(technique.get("extrait", ""), reference)
        except ExtraitIntrouvable:
            perdus += 1
            continue
        trouves.append(Intervalle(debut, fin, technique["id"]))
    return trouves, perdus


def _chevauchement(a: Intervalle, b: Intervalle) -> int:
    if a.technique != b.technique:
        return 0
    return max(0, min(a.fin, b.fin) - max(a.debut, b.debut))


@dataclass
class Comptes:
    """Les sommes dont se déduisent précision, rappel et F1. Elles s'additionnent d'une page
    à l'autre, ce qui donne une moyenne micro sur le corpus plutôt qu'une moyenne de pages."""
    credit_precision: float = 0.0
    predits: int = 0
    credit_rappel: float = 0.0
    references: int = 0

    def __add__(self, autre: "Comptes") -> "Comptes":
        return Comptes(self.credit_precision + autre.credit_precision, self.predits + autre.predits,
                       self.credit_rappel + autre.credit_rappel, self.references + autre.references)

    @property
    def precision(self) -> float | None:
        """None quand rien n'a été prédit : une précision sans prédiction n'a pas de sens, et
        la fixer à 1 ou à 0 déciderait arbitrairement du chiffre publié."""
        return self.credit_precision / self.predits if self.predits else None

    @property
    def rappel(self) -> float | None:
        return self.credit_rappel / self.references if self.references else None

    @property
    def f1(self) -> float | None:
        if not self.predits and not self.references:
            return None  # rien à trouver et rien de trouvé : ni réussite ni échec à compter
        p, r = self.precision or 0.0, self.rappel or 0.0
        return 2 * p * r / (p + r) if p + r else 0.0

    def resume(self) -> dict:
        return {"precision": _arrondi(self.precision), "rappel": _arrondi(self.rappel),
                "f1": _arrondi(self.f1), "predits": self.predits, "references": self.references}


def comptes_intervalles(predits: list[Intervalle], references: list[Intervalle]) -> Comptes:
    """Le recouvrement partiel à la manière de SemEval 2020 tâche 11.

    Le crédit d'un intervalle est plafonné à 1 : un intervalle prédit qui couvre deux
    références de même technique ne vaut pas deux réussites."""
    comptes = Comptes(predits=len(predits), references=len(references))
    for p in predits:
        if p.longueur:
            comptes.credit_precision += min(1.0, sum(_chevauchement(p, r) for r in references) / p.longueur)
    for r in references:
        if r.longueur:
            comptes.credit_rappel += min(1.0, sum(_chevauchement(p, r) for p in predits) / r.longueur)
    return comptes


def comptes_techniques(predites: set[str], attendues: set[str]) -> Comptes:
    """La même mesure au niveau de la page : la technique est-elle relevée, où que ce soit.

    C'est la granularité de SemEval 2023 tâche 3, et celle que la calibration exige déjà
    avec `techniques_attendues` : plus indulgente, elle sépare « a vu le procédé » de « l'a
    situé au bon endroit »."""
    communes = len(predites & attendues)
    return Comptes(communes, len(predites), communes, len(attendues))


# ---------------------------------------------------------------------------
# Accords simples
# ---------------------------------------------------------------------------

def distance_grade(a: str, b: str) -> int:
    return abs(GRADES.index(a) - GRADES.index(b))


def distance_a_la_fourchette(grade: str, fourchette: list[str]) -> int:
    return min(distance_grade(grade, g) for g in fourchette)


def kappa_cohen(a: list[str], b: list[str]) -> float | None:
    """L'accord entre deux annotateurs, corrigé de celui que le hasard donnerait.

    None quand il n'est pas défini : moins de deux pages, ou un accord attendu total (les
    deux ont mis partout la même étiquette, il n'y a rien à corriger ni rien à apprendre)."""
    if len(a) != len(b) or len(a) < 2:
        return None
    n = len(a)
    observe = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    attendu = sum(ca[k] * cb[k] for k in ca) / (n * n)
    if attendu >= 1:
        return None
    return (observe - attendu) / (1 - attendu)


def _arrondi(valeur: float | None) -> float | None:
    return None if valeur is None else round(valeur, 3)


# ---------------------------------------------------------------------------
# Annotations
# ---------------------------------------------------------------------------

class AnnotationInvalide(ValueError):
    pass


def charger_annotations(dossier: Path) -> list[dict]:
    """Toutes les annotations d'un dossier, un fichier YAML par page et par annotateur."""
    import yaml

    if not dossier.is_dir():
        return []
    annotations = []
    for chemin in sorted(dossier.rglob("*.yaml")):
        donnees = yaml.safe_load(chemin.read_text(encoding="utf-8"))
        if isinstance(donnees, dict):
            annotations.append({**donnees, "_fichier": str(chemin)})
    return annotations


def verifier_annotation(annotation: dict, reference: str, techniques: set[str],
                        categories: set[str]) -> list[Intervalle]:
    """Contrôle une annotation contre la page qu'elle décrit, et rend ses intervalles.

    Une annotation est une vérité de référence : une faute y fausse toutes les mesures qui
    la suivent, sans que rien ne le montre. Mieux vaut donc refuser tôt et dire pourquoi."""
    fichier = annotation.get("_fichier", "(annotation)")
    for champ in ("cas", "annotateur", "content_hash", "categorie"):
        if not annotation.get(champ):
            raise AnnotationInvalide(f"{fichier} : champ `{champ}` manquant")
    if annotation["content_hash"] != hacher_contenu(reference):
        raise AnnotationInvalide(
            f"{fichier} : l'empreinte ne correspond plus au contenu du cas. La page a changé "
            "depuis l'annotation : il faut la relire, pas réestampiller.")
    if annotation["categorie"] not in categories:
        raise AnnotationInvalide(f"{fichier} : catégorie inconnue `{annotation['categorie']}`")
    for grade in annotation.get("grade") or []:
        if grade not in GRADES:
            raise AnnotationInvalide(f"{fichier} : grade inconnu `{grade}`")

    intervalles = []
    for n, entree in enumerate(annotation.get("intervalles") or [], start=1):
        technique = entree.get("technique")
        if technique not in techniques:
            raise AnnotationInvalide(f"{fichier}, intervalle {n} : technique hors référentiel `{technique}`")
        try:
            debut, fin = localiser(entree.get("extrait", ""), reference, entree.get("occurrence", 1))
        except ExtraitIntrouvable as exc:
            raise AnnotationInvalide(f"{fichier}, intervalle {n} : {exc}") from exc
        intervalles.append(Intervalle(debut, fin, technique))
    return intervalles


# ---------------------------------------------------------------------------
# Correspondances avec les corpus publics
# ---------------------------------------------------------------------------

LIENS = ("exact", "partiel", "revue", "aucun")


def _cle_etiquette(etiquette: str) -> str:
    return "".join(c for c in etiquette.lower() if c.isalnum())


def charger_correspondance(chemin: Path, techniques: set[str]) -> dict[str, dict]:
    """Une table de correspondance, contrôlée contre le référentiel, indexée par étiquette.

    Le contrôle est strict : une cible inconnue ou un lien mal formé lève. Une table fausse
    ne se voit pas à l'usage, elle déplace des milliers d'intervalles vers la mauvaise
    technique ; c'est à la lecture qu'il faut l'arrêter."""
    import yaml

    donnees = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
    table: dict[str, dict] = {}
    for etiquette, regle in (donnees.get("correspondances") or {}).items():
        lien, vers = regle.get("lien"), regle.get("vers")
        if lien not in LIENS:
            raise ValueError(f"{chemin.name}, {etiquette} : lien inconnu `{lien}`")
        cibles = [] if vers is None else ([vers] if isinstance(vers, str) else list(vers))
        if lien == "aucun" and cibles:
            raise ValueError(f"{chemin.name}, {etiquette} : un lien `aucun` ne peut pas avoir de cible")
        if lien in ("exact", "partiel") and len(cibles) != 1:
            raise ValueError(f"{chemin.name}, {etiquette} : un lien `{lien}` a exactement une cible")
        if lien == "revue" and not cibles:
            raise ValueError(f"{chemin.name}, {etiquette} : un lien `revue` liste ses candidates")
        inconnues = [c for c in cibles if c not in techniques]
        if inconnues:
            raise ValueError(f"{chemin.name}, {etiquette} : hors référentiel {inconnues}")
        cle = _cle_etiquette(etiquette)
        if cle in table:
            raise ValueError(f"{chemin.name} : étiquette en double `{etiquette}`")
        table[cle] = {"etiquette": etiquette, "lien": lien, "cibles": cibles}
    return table


def convertir(etiquette: str, table: dict[str, dict]) -> dict:
    """Ce qu'une étiquette étrangère devient chez nous.

    Rend le lien et les cibles. Une étiquette absente de la table lève : c'est le signe
    qu'un jeu de données n'a pas l'inventaire annoncé, et continuer compterait faux."""
    regle = table.get(_cle_etiquette(etiquette))
    if regle is None:
        raise KeyError(f"étiquette absente de la table : `{etiquette}`")
    return regle


# ---------------------------------------------------------------------------
# Les trois mesures publiables
# ---------------------------------------------------------------------------

def mesurer_contre_annotations(pages: list[dict]) -> dict:
    """Une chaîne comparée aux annotations humaines.

    Chaque page porte `reference` (le texte), `carte` (ce que la chaîne a rendu) et
    `annotations` (une ou plusieurs, déjà vérifiées, avec leurs `intervalles`). Quand deux
    annotateurs ont lu la même page, la chaîne est mesurée contre chacun et les comptes
    s'additionnent : on ne fabrique pas une référence moyenne que personne n'a écrite."""
    categories_justes = categories_total = 0
    grades_exacts = grades_proches = grades_total = 0
    intervalles, techniques = Comptes(), Comptes()
    extraits_perdus = extraits_total = 0

    for page in pages:
        carte = page["carte"]
        predits, perdus = intervalles_de_carte(carte, page["reference"])
        extraits_perdus += perdus
        extraits_total += len(carte.get("techniques_detectees", []))
        grade = carte.get("note", {}).get("grade")
        for annotation in page["annotations"]:
            categories_total += 1
            categories_justes += carte.get("categorie") == annotation["categorie"]
            if grade and annotation.get("grade"):
                grades_total += 1
                distance = distance_a_la_fourchette(grade, annotation["grade"])
                grades_exacts += distance == 0
                grades_proches += distance <= 1
            intervalles += comptes_intervalles(predits, annotation["intervalles"])
            techniques += comptes_techniques({p.technique for p in predits},
                                             {r.technique for r in annotation["intervalles"]})

    return {
        "pages": len(pages),
        "categorie": _taux(categories_justes, categories_total),
        "grade_dans_la_fourchette": _taux(grades_exacts, grades_total),
        "grade_a_un_cran": _taux(grades_proches, grades_total),
        "techniques": techniques.resume(),
        "intervalles": intervalles.resume(),
        "extraits_verbatim": _taux(extraits_total - extraits_perdus, extraits_total),
    }


def accord_annotateurs(pages: list[dict]) -> dict:
    """L'accord entre annotateurs, sur les pages lues par au moins deux d'entre eux.

    Ce chiffre est le plafond raisonnable de toute machine : exiger d'un modèle qu'il
    s'accorde avec un humain mieux que deux humains entre eux, c'est lui demander de deviner
    l'annotateur. Le F1 entre deux annotateurs est symétrique, ce qui permet de prendre l'un
    comme référence de l'autre sans choisir lequel."""
    cat_a, cat_b = [], []
    intervalles, techniques = Comptes(), Comptes()
    paires = 0
    for page in pages:
        for a, b in combinations(page["annotations"], 2):
            paires += 1
            cat_a.append(a["categorie"])
            cat_b.append(b["categorie"])
            intervalles += comptes_intervalles(a["intervalles"], b["intervalles"])
            techniques += comptes_techniques({i.technique for i in a["intervalles"]},
                                             {i.technique for i in b["intervalles"]})
    return {
        "paires": paires,
        "categorie_kappa": _arrondi(kappa_cohen(cat_a, cat_b)),
        "categorie_accord": _taux(sum(x == y for x, y in zip(cat_a, cat_b)), paires),
        "techniques_f1": _arrondi(techniques.f1),
        "intervalles_f1": _arrondi(intervalles.f1),
    }


def ecart_entre_passes(liste_passes: list[dict]) -> dict:
    """Ce que deux passes de la même chaîne sur le même corpus ont rendu de différent.

    Mesuré sur le journal des passes, donc sans rien relancer. Pour chaque paire de passes
    et chaque cas présent dans les deux : même catégorie, même grade, écart de score, et
    recouvrement des techniques relevées (indice de Jaccard). La cible de la chaîne composée
    est un écart nul ; la chaîne actuelle en est loin, et ce chiffre le rend visible."""
    comparaisons = memes_categories = memes_grades = 0
    jaccards, ecarts_score = [], []
    instables: Counter[str] = Counter()
    for a, b in combinations(liste_passes, 2):
        cas_b = {c["id"]: c for c in b.get("cas", [])}
        for cas in a.get("cas", []):
            autre = cas_b.get(cas["id"])
            if not autre or "categorie" not in cas or "categorie" not in autre:
                continue
            comparaisons += 1
            meme_categorie = cas["categorie"] == autre["categorie"]
            meme_grade = cas.get("grade") == autre.get("grade")
            memes_categories += meme_categorie
            memes_grades += meme_grade
            if cas.get("score") is not None and autre.get("score") is not None:
                ecarts_score.append(abs(cas["score"] - autre["score"]))
            ta, tb = set(cas.get("techniques") or []), set(autre.get("techniques") or [])
            jaccard = len(ta & tb) / len(ta | tb) if ta | tb else 1.0
            jaccards.append(jaccard)
            if not (meme_categorie and meme_grade and jaccard == 1.0):
                instables[cas["id"]] += 1
    return {
        "passes": len(liste_passes),
        "comparaisons": comparaisons,
        "meme_categorie": _taux(memes_categories, comparaisons),
        "meme_grade": _taux(memes_grades, comparaisons),
        "techniques_jaccard": _arrondi(sum(jaccards) / len(jaccards)) if jaccards else None,
        "ecart_score_moyen": _arrondi(sum(ecarts_score) / len(ecarts_score)) if ecarts_score else None,
        "ecart_score_max": max(ecarts_score) if ecarts_score else None,
        "cas_instables": sorted(instables),
    }


def _taux(reussites: int, total: int) -> float | None:
    return round(reussites / total, 3) if total else None
