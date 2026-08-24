"""Tests du CLI — surtout la logique de calibration, qui est l'outil de non-régression
du projet : si elle se trompe, toutes les mesures de qualité deviennent fausses."""

import json

import pytest
from typer.testing import CliRunner

from lynceus.cli import _comparer, _corps_demande, _erreur_http, app

runner = CliRunner()


def carte(categorie="information", grade="B", score=70, confiance=0.9, techniques=()):
    return {
        "categorie": categorie,
        "note": {"grade": grade, "score": score, "confiance": confiance},
        "techniques_detectees": [{"id": t} for t in techniques],
    }


# ---------- _comparer : catégories ----------

def test_categorie_exacte_conforme():
    graves, mineurs = _comparer({"categorie_attendue": "satire"}, carte(categorie="satire"))
    assert graves == [] and mineurs == []


def test_categorie_exacte_erronee_est_grave():
    graves, _ = _comparer({"categorie_attendue": "satire"}, carte(categorie="pseudo_science"))
    assert len(graves) == 1 and "satire" in graves[0]


def test_categories_acceptables_pour_contenu_hybride():
    """Un article pseudo-médical qui vend un produit relève des deux catégories."""
    entree = {"categories_acceptables": ["pseudo_science", "publicite_sponsorise"]}
    for categorie in ("pseudo_science", "publicite_sponsorise"):
        graves, _ = _comparer(entree, carte(categorie=categorie))
        assert graves == []
    graves, _ = _comparer(entree, carte(categorie="satire"))
    assert len(graves) == 1


def test_categories_acceptables_prime_sur_categorie_attendue():
    entree = {"categorie_attendue": "satire", "categories_acceptables": ["information", "opinion"]}
    graves, _ = _comparer(entree, carte(categorie="opinion"))
    assert graves == []


# ---------- _comparer : grades (gravité selon la distance) ----------

def test_grade_dans_la_fourchette():
    graves, mineurs = _comparer({"grade_attendu": ["A", "B"]}, carte(grade="B"))
    assert graves == [] and mineurs == []


def test_grade_a_un_cran_est_mineur():
    graves, mineurs = _comparer({"grade_attendu": ["A", "B"]}, carte(grade="C"))
    assert graves == [] and len(mineurs) == 1


def test_grade_a_deux_crans_est_grave():
    """Un écart de deux crans (B attendu, D obtenu) fausserait le message à l'utilisateur."""
    graves, mineurs = _comparer({"grade_attendu": ["A", "B"]}, carte(grade="D"))
    assert len(graves) == 1 and mineurs == []


def test_grade_distance_calculee_depuis_le_plus_proche():
    """Fourchette [A, E] : un C est à deux crans de chaque borne -> grave."""
    graves, _ = _comparer({"grade_attendu": ["A", "E"]}, carte(grade="C"))
    assert len(graves) == 1


# ---------- _comparer : techniques (le cœur du test) ----------

def test_technique_attendue_manquante_est_grave():
    entree = {"techniques_attendues": ["conflit_interet_commercial", "solution_miracle"]}
    graves, _ = _comparer(entree, carte(techniques=["solution_miracle"]))
    assert len(graves) == 1 and "conflit_interet_commercial" in graves[0]


def test_faux_positif_sur_technique_interdite_est_grave():
    entree = {"techniques_interdites": ["verite_cachee"]}
    graves, _ = _comparer(entree, carte(techniques=["verite_cachee", "absence_de_sources"]))
    assert len(graves) == 1 and "faux positif" in graves[0]


def test_techniques_supplementaires_non_interdites_sont_tolerees():
    entree = {"techniques_attendues": ["solution_miracle"]}
    graves, mineurs = _comparer(entree, carte(techniques=["solution_miracle", "appel_a_la_peur"]))
    assert graves == [] and mineurs == []


def test_confiance_sous_le_plancher_est_mineure():
    graves, mineurs = _comparer({"confiance_min": 0.7}, carte(confiance=0.5))
    assert graves == [] and len(mineurs) == 1


def test_entree_sans_attente_ne_produit_aucun_ecart():
    graves, mineurs = _comparer({"notes": "juste documenté"}, carte())
    assert graves == [] and mineurs == []


def test_ecarts_multiples_cumules():
    entree = {
        "categorie_attendue": "satire",
        "grade_attendu": ["A"],
        "techniques_attendues": ["solution_miracle"],
        "techniques_interdites": ["verite_cachee"],
    }
    graves, _ = _comparer(entree, carte(categorie="pseudo_science", grade="E", techniques=["verite_cachee"]))
    assert len(graves) == 4  # catégorie + grade (4 crans) + manquante + faux positif


# ---------- _corps_demande ----------

def test_corps_depuis_specimen_local_retire_l_entete(tmp_path):
    """L'en-tête YAML documente le cas : il ne doit JAMAIS être envoyé à l'analyse,
    sinon il souffle la réponse attendue au modèle."""
    specimen = tmp_path / "cas.md"
    specimen.write_text(
        "---\nsource: fictif\nattendu: pseudo_science, grade E\n---\n\n# Titre réel\n\nContenu.",
        encoding="utf-8",
    )
    corps = _corps_demande({"fichier": "cas.md", "titre": "Titre réel"}, tmp_path)
    assert corps is not None
    assert "attendu:" not in corps["contenu_markdown"]
    assert "source: fictif" not in corps["contenu_markdown"]
    assert corps["contenu_markdown"].startswith("# Titre réel")
    assert corps["langue"] == "fr"


def test_corps_specimen_sans_entete_conserve_tout(tmp_path):
    specimen = tmp_path / "cas.md"
    specimen.write_text("# Sans en-tête\n\nContenu intégral.", encoding="utf-8")
    corps = _corps_demande({"fichier": "cas.md"}, tmp_path)
    assert corps["contenu_markdown"].startswith("# Sans en-tête")


def test_corps_depuis_url(tmp_path):
    corps = _corps_demande({"url": "https://exemple.fr/a", "titre": "T"}, tmp_path)
    assert corps == {"url": "https://exemple.fr/a", "titre": "T"}


def test_corps_entree_invalide(tmp_path):
    assert _corps_demande({"notes": "ni fichier ni url"}, tmp_path) is None


# ---------- _erreur_http ----------

def test_erreur_http_extrait_le_detail():
    class Reponse:
        text = '{"detail": "message lisible"}'

        def json(self):
            return {"detail": "message lisible"}

    assert _erreur_http(Reponse()) == "message lisible"


def test_erreur_http_corps_non_json():
    class Reponse:
        text = "<html>502 Bad Gateway</html>"

        def json(self):
            raise ValueError("pas du JSON")

    assert "502" in _erreur_http(Reponse())


# ---------- commande calibrer (bout en bout, API simulée) ----------

@pytest.fixture
def corpus(tmp_path):
    (tmp_path / "specimens").mkdir()
    (tmp_path / "specimens" / "cas.md").write_text("---\nsource: fictif\n---\n\nContenu du spécimen.", encoding="utf-8")
    (tmp_path / "corpus.yaml").write_text(
        "- fichier: specimens/cas.md\n"
        "  titre: Cas de test\n"
        "  categorie_attendue: satire\n"
        "  grade_attendu: [A, B]\n",
        encoding="utf-8",
    )
    return tmp_path / "corpus.yaml"


def _simuler_api(monkeypatch, carte_rendue):
    class Reponse:
        status_code = 200
        text = ""

        def json(self):
            return {"carte": carte_rendue, "en_cache": False}

    monkeypatch.setattr("httpx.post", lambda *a, **kw: Reponse())
    monkeypatch.setattr(
        "httpx.get",
        lambda *a, **kw: type("R", (), {"json": lambda self: {"modele": "test/modele", "prompt_version": "0.1.1"}})(),
    )


def test_calibrer_corpus_conforme(corpus, monkeypatch):
    _simuler_api(monkeypatch, carte(categorie="satire", grade="A"))
    resultat = runner.invoke(app, ["calibrer", str(corpus)])
    assert resultat.exit_code == 0
    assert "1/1 conformes" in resultat.stdout


def test_calibrer_sort_en_erreur_sur_echec_grave(corpus, monkeypatch):
    """Code de sortie 1 : indispensable pour un usage en intégration continue."""
    _simuler_api(monkeypatch, carte(categorie="pseudo_science", grade="A"))
    resultat = runner.invoke(app, ["calibrer", str(corpus)])
    assert resultat.exit_code == 1


def test_calibrer_ecart_mineur_ne_fait_pas_echouer(corpus, monkeypatch):
    _simuler_api(monkeypatch, carte(categorie="satire", grade="C"))  # un cran hors fourchette
    resultat = runner.invoke(app, ["calibrer", str(corpus)])
    assert resultat.exit_code == 0
    assert "mineur" in resultat.stdout


def test_calibrer_ecrit_le_rapport_json(corpus, monkeypatch, tmp_path):
    _simuler_api(monkeypatch, carte(categorie="satire", grade="A", techniques=["appel_a_la_peur"]))
    rapport = tmp_path / "rapport.json"
    resultat = runner.invoke(app, ["calibrer", str(corpus), "--json", str(rapport)])
    assert resultat.exit_code == 0
    donnees = json.loads(rapport.read_text(encoding="utf-8"))
    assert donnees[0]["cas"] == "Cas de test"
    assert donnees[0]["obtenu"]["techniques"] == ["appel_a_la_peur"]


def test_calibrer_filtre(corpus, monkeypatch):
    _simuler_api(monkeypatch, carte(categorie="satire", grade="A"))
    resultat = runner.invoke(app, ["calibrer", str(corpus), "--filtre", "inexistant"])
    assert "0/0 conformes" in resultat.stdout


def test_calibrer_refuse_un_corpus_mal_forme(tmp_path, monkeypatch):
    mauvais = tmp_path / "mauvais.yaml"
    mauvais.write_text("ceci: n'est pas une liste\n", encoding="utf-8")
    resultat = runner.invoke(app, ["calibrer", str(mauvais)])
    assert resultat.exit_code == 2
