"""Tests du CLI — surtout la logique de calibration, qui est l'outil de non-régression
du projet : si elle se trompe, toutes les mesures de qualité deviennent fausses."""

import json

import pytest
from typer.testing import CliRunner

from lynceus.cli import CaptureManquante, _comparer, _corps_demande, _erreur_http, app
from lynceus.normalisation import hacher_contenu

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


# ---------- captures de pages réelles ----------

def _capture(tmp_path, contenu="Contenu capturé d'une page réelle, assez long pour être analysé."):
    (tmp_path / "captures").mkdir(exist_ok=True)
    (tmp_path / "captures" / "page.md").write_text(contenu, encoding="utf-8")
    return contenu


def test_capture_lue_avec_empreinte_conforme(tmp_path):
    contenu = _capture(tmp_path)
    corps = _corps_demande(
        {"capture": "captures/page.md", "url": "https://exemple.fr/a", "content_hash": hacher_contenu(contenu)},
        tmp_path,
    )
    assert corps["contenu_markdown"] == contenu
    assert corps["url"] == "https://exemple.fr/a"


def test_capture_absente_signalee_clairement(tmp_path):
    """Cas du contributeur qui clone le dépôt : les captures ne sont pas versionnées."""
    with pytest.raises(CaptureManquante) as exc:
        _corps_demande({"capture": "captures/absente.md", "url": "https://exemple.fr/a"}, tmp_path)
    assert "recréer" in str(exc.value)


def test_capture_divergente_refusee(tmp_path):
    """Une page qui a changé doit être signalée, jamais mesurée en silence : sinon on
    comparerait des résultats obtenus sur des contenus différents."""
    _capture(tmp_path)
    with pytest.raises(CaptureManquante) as exc:
        _corps_demande(
            {"capture": "captures/page.md", "content_hash": "0" * 64},
            tmp_path,
        )
    assert "divergente" in str(exc.value)
    assert "recapturer" in str(exc.value)


def test_capture_sans_empreinte_acceptee(tmp_path):
    """L'empreinte est recommandée mais pas obligatoire (capture en cours de constitution)."""
    contenu = _capture(tmp_path)
    corps = _corps_demande({"capture": "captures/page.md"}, tmp_path)
    assert corps["contenu_markdown"] == contenu


def test_calibrer_ignore_les_captures_absentes(tmp_path, monkeypatch):
    """Un cas non mesurable ne doit pas compter comme un échec : le contributeur qui n'a
    pas recréé les captures verrait sinon un corpus artificiellement rouge."""
    (tmp_path / "corpus.yaml").write_text(
        "- capture: captures/absente.md\n"
        "  titre: Page non capturée\n"
        "  url: https://exemple.fr/a\n"
        "  categorie_attendue: information\n",
        encoding="utf-8",
    )
    resultat = runner.invoke(app, ["calibrer", str(tmp_path / "corpus.yaml")])
    assert resultat.exit_code == 0, "une capture absente ne doit pas faire échouer la calibration"
    assert "ignoré" in resultat.stdout


def test_capturer_ecrit_et_affiche_l_entree(tmp_path):
    source = tmp_path / "source.md"
    source.write_text("Un contenu de page suffisamment long pour passer le seuil minimal. " * 5, encoding="utf-8")
    resultat = runner.invoke(app, [
        "capturer", str(source), "--url", "https://exemple.fr/article",
        "--vers", str(tmp_path / "captures"), "--nom", "test",
    ])
    assert resultat.exit_code == 0
    assert (tmp_path / "captures" / "test.md").is_file()
    assert "content_hash:" in resultat.stdout
    assert "capture: captures/test.md" in resultat.stdout


def test_capturer_refuse_un_contenu_trop_court(tmp_path):
    source = tmp_path / "source.md"
    source.write_text("trop court", encoding="utf-8")
    resultat = runner.invoke(app, ["capturer", str(source), "--url", "https://exemple.fr/a",
                                   "--vers", str(tmp_path / "captures")])
    assert resultat.exit_code == 2


# ---------- lynceus env : variables d'un déploiement ----------

def _variables(sortie: str) -> dict[str, str]:
    """Les lignes NOM=valeur de la sortie, commentaires et cadres ignorés."""
    valeurs = {}
    for ligne in sortie.splitlines():
        ligne = ligne.strip()
        if ligne.startswith("#") or "=" not in ligne or " " in ligne.split("=", 1)[0]:
            continue
        nom, valeur = ligne.split("=", 1)
        if nom.isupper():
            valeurs[nom] = valeur
    return valeurs


def test_env_production_apparie_les_deux_machines():
    """Le piège du déploiement : lancer cles-paire deux fois et déployer un portail qui
    signe avec une clé que l'instance ne reconnaît pas. Les deux blocs doivent venir
    d'une seule paire, ce qui se vérifie par la cryptographie, pas par la mise en page."""
    from lynceus.cles import publique_de

    resultat = runner.invoke(app, ["env", "production"])
    assert resultat.exit_code == 0
    variables = _variables(resultat.stdout)

    publique = variables["LYNCEUS_CLE_PUBLIQUE"]
    privee = variables["LYNCEUS_PORTAIL_CLE_PRIVEE"]
    assert publique and privee
    assert publique_de(privee) == publique


def test_env_recette_apparie_aussi():
    from lynceus.cles import publique_de

    variables = _variables(runner.invoke(app, ["env", "recette"]).stdout)
    assert publique_de(variables["LYNCEUS_PORTAIL_CLE_PRIVEE"]) == variables["LYNCEUS_CLE_PUBLIQUE"]


def test_env_engendre_des_secrets_differents_a_chaque_appel():
    un = _variables(runner.invoke(app, ["env", "production"]).stdout)
    deux = _variables(runner.invoke(app, ["env", "production"]).stdout)
    for nom in ("POSTGRES_PASSWORD", "LYNCEUS_ADMIN_TOKEN", "LYNCEUS_PORTAIL_CLE_PRIVEE"):
        assert un[nom] != deux[nom], f"{nom} est identique d'un appel à l'autre"
        assert len(un[nom]) >= 20


def test_env_reutilise_une_paire_existante():
    """Reconfigurer une seule machine ne doit pas obliger à tout réémettre."""
    from lynceus.cles import generer_paire

    privee, publique = generer_paire()
    variables = _variables(runner.invoke(app, ["env", "production", "--cle-privee", privee]).stdout)
    assert variables["LYNCEUS_PORTAIL_CLE_PRIVEE"] == privee
    assert variables["LYNCEUS_CLE_PUBLIQUE"] == publique


def test_env_refuse_une_cle_privee_illisible():
    resultat = runner.invoke(app, ["env", "production", "--cle-privee", "pas-une-cle"])
    assert resultat.exit_code == 1
    # Sur la sortie d'erreur, comme tout ce qui n'est pas une variable exploitable.
    assert "illisible" in resultat.stderr
    assert resultat.stdout.strip() == "", "aucune variable ne doit sortir en cas d'échec"


def test_env_laisse_vide_ce_que_lui_seul_ne_peut_pas_savoir():
    """Un exemple plausible démarrerait et échouerait plus tard, à la première analyse.
    Vide, Compose refuse de démarrer et dit laquelle manque."""
    variables = _variables(runner.invoke(app, ["env", "production"]).stdout)
    for nom in ("LYNCEUS_IMAGE", "LYNCEUS_LLM_API_KEY", "LYNCEUS_PORTAIL_INSTANCE",
                "LYNCEUS_PORTAIL_EDITEUR_NOM", "CLOUDFLARE_TUNNEL_TOKEN"):
        assert variables[nom] == "", f"{nom} devrait être vide"


def test_env_recette_ne_renseigne_pas_didentite_legale():
    """Une recette ne doit pas pouvoir passer pour un service ouvert au public."""
    variables = _variables(runner.invoke(app, ["env", "recette"]).stdout)
    assert not any(nom.startswith("LYNCEUS_PORTAIL_EDITEUR") for nom in variables)
    assert variables["LYNCEUS_SUFFIXE"] == "-staging"


def test_env_sortie_standard_directement_utilisable_comme_fichier():
    """« lynceus env recette > .env » doit produire un fichier valide, pas un fichier à
    nettoyer. Titres, avertissement et explications partent donc sur la sortie d'erreur :
    Compose refuse un fichier dont une ligne n'est pas NOM=valeur, et l'erreur qu'il
    donne alors (« key cannot contain a space ») n'aide personne."""
    resultat = runner.invoke(app, ["env", "recette"])

    for numero, ligne in enumerate(resultat.stdout.splitlines(), start=1):
        if not ligne.strip() or ligne.lstrip().startswith("#"):
            continue
        nom = ligne.split("=", 1)[0]
        assert "=" in ligne and nom.isupper() and " " not in nom, (
            f"ligne {numero} inexploitable dans un .env : {ligne!r}"
        )

    # Les explications existent toujours, ailleurs.
    assert "Recette" in resultat.stderr
    assert "trousseau" in resultat.stderr


def test_env_sans_tiret_cadratin():
    for cible in ("production", "recette"):
        assert "—" not in runner.invoke(app, ["env", cible]).stdout
