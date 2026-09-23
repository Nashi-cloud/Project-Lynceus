"""Les mesures de l'étape zéro (docs/ARCHITECTURE-CIBLE.md §8).

Tout ce qui sera dit un jour d'un encodeur comparé à la chaîne actuelle passera par ces
fonctions. Une erreur ici ne se verrait pas à l'usage : elle déplacerait silencieusement le
chiffre publié. D'où des tests sur des cas calculables à la main."""

import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from lynceus import mesure
from lynceus.cli import app
from lynceus.mesure import Intervalle
from lynceus.moteur.prompt import charger_taxonomie
from lynceus.normalisation import hacher_contenu

runner = CliRunner()
RACINE = Path(__file__).resolve().parents[2]
TECHNIQUES = set(charger_taxonomie())
CATEGORIES = {"information", "opinion", "theorie_du_complot", "satire"}


# ---------- positions ----------

def test_localiser_compte_sur_le_texte_normalise():
    reference = mesure.texte_de_reference("Un  texte\n\navec   des espaces.")
    assert reference == "Un texte avec des espaces."
    debut, fin = mesure.localiser("texte\navec", reference)
    assert reference[debut:fin] == "texte avec"


def test_localiser_retire_l_habillage_comme_la_validation():
    reference = "Il dit que tout est caché."
    debut, fin = mesure.localiser("« …tout est caché »", reference)
    assert reference[debut:fin] == "tout est caché"


def test_localiser_choisit_l_occurrence_demandee():
    reference = "vite, vite, vite"
    assert mesure.localiser("vite", reference, occurrence=2) == (6, 10)
    with pytest.raises(mesure.ExtraitIntrouvable):
        mesure.localiser("vite", reference, occurrence=4)


def test_carte_avec_extrait_inventé_compte_comme_perdu():
    carte = {"techniques_detectees": [
        {"id": "verite_cachee", "extrait": "on vous cache tout"},
        {"id": "ad_hominem", "extrait": "phrase que la page ne contient pas"},
    ]}
    trouves, perdus = mesure.intervalles_de_carte(carte, "Ici, on vous cache tout.")
    assert trouves == [Intervalle(5, 23, "verite_cachee")]
    assert perdus == 1


def test_carte_qui_porte_deja_ses_positions_n_est_pas_relocalisee():
    """La carte 0.2.0 portera `debut` et `fin` : ils font foi, sans recherche de texte."""
    carte = {"techniques_detectees": [{"id": "ad_hominem", "debut": 2, "fin": 9}]}
    assert mesure.intervalles_de_carte(carte, "peu importe")[0] == [Intervalle(2, 9, "ad_hominem")]


# ---------- recouvrement partiel ----------

def test_intervalles_identiques_donnent_un():
    a = [Intervalle(0, 10, "ad_hominem")]
    assert mesure.comptes_intervalles(a, a).f1 == 1.0


def test_recouvrement_partiel_rapporte_au_prorata():
    """Prédit [0, 10), référence [5, 25) : la moitié du prédit est juste, le quart de la
    référence est trouvé. P = 0,5, R = 0,25, F1 = 1/3."""
    comptes = mesure.comptes_intervalles([Intervalle(0, 10, "x")], [Intervalle(5, 25, "x")])
    assert comptes.precision == 0.5
    assert comptes.rappel == 0.25
    assert comptes.f1 == pytest.approx(1 / 3)


def test_la_technique_doit_coincider():
    comptes = mesure.comptes_intervalles([Intervalle(0, 10, "x")], [Intervalle(0, 10, "y")])
    assert comptes.f1 == 0.0


def test_le_credit_d_un_intervalle_est_plafonne():
    """Un intervalle large qui couvre deux références ne vaut pas deux réussites."""
    comptes = mesure.comptes_intervalles(
        [Intervalle(0, 10, "x")],
        [Intervalle(0, 10, "x"), Intervalle(0, 10, "x")])
    assert comptes.precision == 1.0


def test_rien_a_trouver_et_rien_de_trouve_n_est_pas_un_score():
    comptes = mesure.comptes_intervalles([], [])
    assert comptes.f1 is None and comptes.precision is None


def test_rien_de_trouve_quand_il_fallait_trouver_vaut_zero():
    comptes = mesure.comptes_intervalles([], [Intervalle(0, 5, "x")])
    assert comptes.precision is None
    assert comptes.rappel == 0.0
    assert comptes.f1 == 0.0


def test_les_comptes_s_additionnent_en_moyenne_micro():
    total = (mesure.comptes_techniques({"a"}, {"a"})
             + mesure.comptes_techniques({"b", "c"}, {"b"}))
    assert (total.precision, total.rappel) == (2 / 3, 1.0)


# ---------- accords ----------

def test_kappa_parfait_et_indefini():
    assert mesure.kappa_cohen(["a", "b"], ["a", "b"]) == 1.0
    assert mesure.kappa_cohen(["a", "a"], ["a", "a"]) is None
    assert mesure.kappa_cohen(["a"], ["a"]) is None


def test_kappa_corrige_le_hasard():
    # Accord observé 0,5 ; attendu 0,5 : pas mieux que le hasard.
    assert mesure.kappa_cohen(["a", "a", "b", "b"], ["a", "b", "a", "b"]) == 0.0


def test_ecart_nul_entre_deux_passes_identiques():
    cas = {"id": "c1", "categorie": "satire", "grade": "A", "score": 90, "techniques": ["x"]}
    ecart = mesure.ecart_entre_passes([{"cas": [cas]}, {"cas": [dict(cas)]}])
    assert ecart["meme_categorie"] == 1.0
    assert ecart["techniques_jaccard"] == 1.0
    assert ecart["ecart_score_max"] == 0
    assert ecart["cas_instables"] == []


def test_ecart_entre_passes_releve_ce_qui_bouge():
    a = {"cas": [{"id": "c1", "categorie": "opinion", "grade": "B", "score": 70, "techniques": ["x", "y"]},
                 {"id": "c2", "categorie": "satire", "grade": "A", "score": 90, "techniques": []}]}
    b = {"cas": [{"id": "c1", "categorie": "opinion", "grade": "C", "score": 58, "techniques": ["x"]},
                 {"id": "c2", "categorie": "satire", "grade": "A", "score": 90, "techniques": []},
                 {"id": "c3", "categorie": "satire", "grade": "A", "score": 90}]}
    ecart = mesure.ecart_entre_passes([a, b])
    assert ecart["comparaisons"] == 2  # c3 n'est pas dans les deux passes
    assert ecart["meme_grade"] == 0.5
    assert ecart["techniques_jaccard"] == 0.75
    assert ecart["ecart_score_max"] == 12
    assert ecart["cas_instables"] == ["c1"]


def test_un_cas_non_mesure_n_entre_pas_dans_l_ecart():
    a = {"cas": [{"id": "c1", "ecarts": [{"type": "non_mesure"}]}]}
    b = {"cas": [{"id": "c1", "categorie": "satire", "grade": "A", "score": 90}]}
    assert mesure.ecart_entre_passes([a, b])["comparaisons"] == 0


# ---------- annotations ----------

PAGE = "Coïncidence ? Je ne crois pas. Les élites savent tout et vous cachent la vérité."


def annotation(**surcharges):
    base = {
        "_fichier": "a.yaml",
        "cas": "specimens/x.md",
        "annotateur": "une",
        "content_hash": hacher_contenu(PAGE),
        "categorie": "theorie_du_complot",
        "grade": ["D", "E"],
        "intervalles": [{"extrait": "Les élites savent tout", "technique": "eux_contre_nous"}],
    }
    return {**base, **surcharges}


def test_annotation_valide_rend_ses_intervalles():
    intervalles = mesure.verifier_annotation(annotation(), PAGE, TECHNIQUES, CATEGORIES)
    assert [PAGE[i.debut:i.fin] for i in intervalles] == ["Les élites savent tout"]


@pytest.mark.parametrize("surcharge, motif", [
    ({"content_hash": "0" * 64}, "empreinte"),
    ({"categorie": "rumeur"}, "catégorie inconnue"),
    ({"grade": ["F"]}, "grade inconnu"),
    ({"annotateur": ""}, "annotateur"),
    ({"intervalles": [{"extrait": "Les élites savent tout", "technique": "inventee"}]}, "hors référentiel"),
    ({"intervalles": [{"extrait": "absent de la page", "technique": "ad_hominem"}]}, "absent"),
])
def test_annotation_fautive_est_refusee(surcharge, motif):
    with pytest.raises(mesure.AnnotationInvalide, match=motif):
        mesure.verifier_annotation(annotation(**surcharge), PAGE, TECHNIQUES, CATEGORIES)


def page_annotee(*annotations_brutes, carte=None):
    annotations = [{**a, "intervalles": mesure.verifier_annotation(a, PAGE, TECHNIQUES, CATEGORIES)}
                   for a in annotations_brutes]
    page = {"reference": PAGE, "annotations": annotations}
    if carte is not None:
        page["carte"] = carte
    return page


def test_chaine_contre_annotations():
    carte = {
        "categorie": "theorie_du_complot",
        "note": {"grade": "C"},
        "techniques_detectees": [
            {"id": "eux_contre_nous", "extrait": "Les élites savent tout et vous cachent la vérité"},
            {"id": "hyper_intentionnalisme", "extrait": "Coïncidence ? Je ne crois pas."},
        ],
    }
    resultat = mesure.mesurer_contre_annotations([page_annotee(annotation(), carte=carte)])
    assert resultat["categorie"] == 1.0
    assert resultat["grade_dans_la_fourchette"] == 0.0
    assert resultat["grade_a_un_cran"] == 1.0
    assert resultat["techniques"]["precision"] == 0.5
    assert resultat["techniques"]["rappel"] == 1.0
    assert resultat["intervalles"]["rappel"] == 1.0
    assert resultat["extraits_verbatim"] == 1.0


def test_accord_entre_deux_annotateurs():
    autre = annotation(annotateur="deux", categorie="opinion", intervalles=[
        {"extrait": "Coïncidence ? Je ne crois pas.", "technique": "hyper_intentionnalisme"}])
    accord = mesure.accord_annotateurs([page_annotee(annotation(), autre)])
    assert accord["paires"] == 1
    assert accord["categorie_accord"] == 0.0
    assert accord["techniques_f1"] == 0.0


# ---------- correspondances publiées ----------

TABLES = RACINE / "corpus" / "correspondances"

SEMEVAL_2023 = [
    "Appeal_to_Authority", "Appeal_to_Popularity", "Appeal_to_Values", "Appeal_to_Fear-Prejudice",
    "Flag_Waving", "Causal_Oversimplification", "False_Dilemma-No_Choice",
    "Consequential_Oversimplification", "Straw_Man", "Red_Herring", "Whataboutism", "Slogans",
    "Appeal_to_Time", "Conversation_Killer", "Loaded_Language", "Repetition",
    "Exaggeration-Minimisation", "Obfuscation-Vagueness-Confusion", "Name_Calling-Labeling",
    "Doubt", "Guilt_by_Association", "Appeal_to_Hypocrisy", "Questioning_the_Reputation",
]

FLICC = [
    "ad hominem", "anecdote", "cherry picking", "conspiracy theory", "fake experts",
    "false choice", "false equivalence", "impossible expectations", "misrepresentation",
    "oversimplification", "single cause", "slothful induction",
]


@pytest.mark.parametrize("fichier, etiquettes", [
    ("semeval2023-t3.yaml", SEMEVAL_2023),
    ("flicc.yaml", FLICC),
])
def test_chaque_table_couvre_tout_l_inventaire_et_vise_le_referentiel(fichier, etiquettes):
    """Une étiquette oubliée ferait échouer une conversion au milieu d'un jeu de données ;
    une cible renommée dans la taxonomie déplacerait des intervalles vers le vide."""
    table = mesure.charger_correspondance(TABLES / fichier, TECHNIQUES)
    assert len(table) == len(etiquettes)
    for etiquette in etiquettes:
        mesure.convertir(etiquette, table)


def test_la_table_de_correspondance_suit_la_version_du_referentiel():
    version = (RACINE / "docs" / "TAXONOMIE.md").read_text(encoding="utf-8").split("**")[1]
    for chemin in TABLES.glob("*.yaml"):
        assert yaml.safe_load(chemin.read_text(encoding="utf-8"))["referentiel"] == version, chemin.name


def test_les_etiquettes_se_comparent_sans_la_typographie():
    table = mesure.charger_correspondance(TABLES / "semeval2023-t3.yaml", TECHNIQUES)
    assert mesure.convertir("straw man", table)["cibles"] == ["epouvantail"]
    with pytest.raises(KeyError):
        mesure.convertir("Bandwagon", table)


@pytest.mark.parametrize("regle, motif", [
    ({"lien": "exact", "vers": None}, "exactement une cible"),
    ({"lien": "aucun", "vers": "ad_hominem"}, "pas avoir de cible"),
    ({"lien": "revue", "vers": []}, "candidates"),
    ({"lien": "proche", "vers": "ad_hominem"}, "lien inconnu"),
    ({"lien": "exact", "vers": "inexistante"}, "hors référentiel"),
])
def test_une_table_mal_formee_est_refusee(tmp_path, regle, motif):
    chemin = tmp_path / "t.yaml"
    chemin.write_text(yaml.safe_dump({"correspondances": {"X": regle}}), encoding="utf-8")
    with pytest.raises(ValueError, match=motif):
        mesure.charger_correspondance(chemin, TECHNIQUES)


def test_les_annotations_versionnees_sont_valides():
    """Une annotation fautive fausse toutes les mesures qui la suivent : la construction
    échoue plutôt que de les laisser passer."""
    resultat = runner.invoke(app, ["mesurer", str(RACINE / "corpus" / "corpus.yaml")])
    assert resultat.exit_code == 0, resultat.output


# ---------- la commande ----------

def test_commande_mesurer_de_bout_en_bout(tmp_path):
    (tmp_path / "specimens").mkdir()
    (tmp_path / "specimens" / "x.md").write_text(PAGE, encoding="utf-8")
    (tmp_path / "corpus.yaml").write_text(yaml.safe_dump([{"fichier": "specimens/x.md"}]),
                                          encoding="utf-8")
    dossier = tmp_path / "annotations" / "une"
    dossier.mkdir(parents=True)
    brute = {k: v for k, v in annotation().items() if k != "_fichier"}
    (dossier / "x.yaml").write_text(yaml.safe_dump(brute, allow_unicode=True), encoding="utf-8")
    rapport = tmp_path / "rapport.json"
    rapport.write_text(json.dumps([{"id": "specimens/x.md", "carte": {
        "categorie": "theorie_du_complot", "note": {"grade": "D"},
        "techniques_detectees": [{"id": "eux_contre_nous", "extrait": "Les élites savent tout"}],
    }}]), encoding="utf-8")
    sortie = tmp_path / "mesures.json"

    resultat = runner.invoke(app, ["mesurer", str(tmp_path / "corpus.yaml"),
                                   "--rapport", str(rapport), "--json", str(sortie)])

    assert resultat.exit_code == 0, resultat.output
    mesures = json.loads(sortie.read_text(encoding="utf-8"))
    assert mesures["contre_annotations"]["intervalles"]["f1"] == 1.0
    assert mesures["contre_annotations"]["grade_dans_la_fourchette"] == 1.0


def test_commande_mesurer_echoue_sur_une_annotation_fautive(tmp_path):
    (tmp_path / "x.md").write_text(PAGE, encoding="utf-8")
    (tmp_path / "corpus.yaml").write_text(yaml.safe_dump([{"fichier": "x.md"}]), encoding="utf-8")
    (tmp_path / "annotations").mkdir()
    brute = {k: v for k, v in annotation(cas="x.md", content_hash="0" * 64).items() if k != "_fichier"}
    (tmp_path / "annotations" / "x.yaml").write_text(yaml.safe_dump(brute), encoding="utf-8")

    resultat = runner.invoke(app, ["mesurer", str(tmp_path / "corpus.yaml")])

    assert resultat.exit_code == 1
    assert "empreinte" in resultat.output


def test_le_squelette_d_annotation_porte_la_bonne_empreinte(tmp_path):
    """L'en-tête d'un spécimen ne fait pas partie du texte analysé : l'empreinte du squelette
    doit être celle que la vérification recalculera, sinon toute annotation naîtrait fautive."""
    (tmp_path / "x.md").write_text("---\ntitre: essai\n---\n\n" + PAGE, encoding="utf-8")
    (tmp_path / "corpus.yaml").write_text(yaml.safe_dump([{"fichier": "x.md"}]), encoding="utf-8")

    resultat = runner.invoke(app, ["annoter", "x.md", "--annotateur", "une",
                                   "--corpus", str(tmp_path / "corpus.yaml")])

    assert resultat.exit_code == 0, resultat.output
    squelette = yaml.safe_load(resultat.output)
    assert squelette["content_hash"] == hacher_contenu(PAGE)
    assert squelette["annotateur"] == "une"
    assert squelette["guide"] == mesure.GUIDE_ANNOTATION


# ---------- arbitrage et catégories hybrides ----------

def test_deux_lectures_divergentes_demandent_un_arbitre():
    autre = annotation(annotateur="deux", categorie="opinion")
    page = {**page_annotee(annotation(), autre), "cas": "specimens/x.md"}
    assert mesure.a_arbitrer([page]) == ["specimens/x.md"]


def test_un_passage_delimite_autrement_ne_demande_pas_d_arbitre():
    """Même technique, bornes différentes : le recouvrement partiel le mesure déjà."""
    autre = annotation(annotateur="deux", intervalles=[
        {"extrait": "Les élites savent tout et vous cachent", "technique": "eux_contre_nous"}])
    page = {**page_annotee(annotation(), autre), "cas": "specimens/x.md"}
    assert mesure.a_arbitrer([page]) == []


def test_l_arbitrage_devient_la_reference_et_sort_de_l_accord():
    autre = annotation(annotateur="deux", categorie="opinion")
    arbitre = annotation(annotateur="trois", role="arbitrage")
    page = {**page_annotee(annotation(), autre, arbitre), "cas": "specimens/x.md"}
    assert mesure.a_arbitrer([page]) == []
    assert mesure.accord_annotateurs([page])["paires"] == 1
    carte = {"categorie": "theorie_du_complot", "note": {"grade": "D"}, "techniques_detectees": []}
    resultat = mesure.mesurer_contre_annotations([{**page, "carte": carte}])
    assert resultat["categorie"] == 1.0  # mesurée contre l'arbitre seul, pas contre « opinion »


def test_une_categorie_acceptable_compte_comme_juste_sans_changer_l_accord():
    hybride = annotation(categories_acceptables=["opinion"])
    carte = {"categorie": "opinion", "note": {"grade": "D"}, "techniques_detectees": []}
    resultat = mesure.mesurer_contre_annotations([page_annotee(hybride, carte=carte)])
    assert resultat["categorie"] == 1.0


@pytest.mark.parametrize("surcharge, motif", [
    ({"role": "correction"}, "rôle inconnu"),
    ({"categories_acceptables": ["rumeur"]}, "catégorie inconnue"),
])
def test_role_et_categories_acceptables_sont_controles(surcharge, motif):
    with pytest.raises(mesure.AnnotationInvalide, match=motif):
        mesure.verifier_annotation(annotation(**surcharge), PAGE, TECHNIQUES, CATEGORIES)


def test_une_annotation_du_jeu_d_evaluation_est_reconnue(tmp_path):
    """Les annotations se partagent entre les deux manifestes : mesurer le corpus de
    calibration ne doit pas déclarer inconnu un cas du jeu d'évaluation."""
    (tmp_path / "x.md").write_text(PAGE, encoding="utf-8")
    (tmp_path / "corpus.yaml").write_text("[]", encoding="utf-8")
    (tmp_path / "evaluation.yaml").write_text(yaml.safe_dump([{"fichier": "x.md"}]), encoding="utf-8")
    (tmp_path / "annotations").mkdir()
    brute = {k: v for k, v in annotation(cas="x.md").items() if k != "_fichier"}
    (tmp_path / "annotations" / "x.yaml").write_text(yaml.safe_dump(brute), encoding="utf-8")

    resultat = runner.invoke(app, ["mesurer", str(tmp_path / "corpus.yaml")])

    assert resultat.exit_code == 0, resultat.output
    assert "1 annotation(s)" in resultat.output


def test_ecrire_est_refuse_hors_du_corpus_de_calibration(tmp_path):
    (tmp_path / "evaluation.yaml").write_text("[]", encoding="utf-8")
    resultat = runner.invoke(app, ["calibrer", str(tmp_path / "evaluation.yaml"), "--ecrire"])
    assert resultat.exit_code == 2
    assert "refusé" in resultat.output


def test_un_extrait_trop_long_est_refuse():
    """Un extrait de plus de 600 caractères n'est plus une citation courte (guide, règle 5)."""
    longue = "mot " * 200
    brute = annotation(content_hash=hacher_contenu(longue),
                       intervalles=[{"extrait": longue, "technique": "ad_hominem"}])
    with pytest.raises(mesure.AnnotationInvalide, match="600"):
        mesure.verifier_annotation(brute, mesure.texte_de_reference(longue), TECHNIQUES, CATEGORIES)


def test_la_version_du_guide_suit_le_document():
    texte = (RACINE / "docs" / "ANNOTATION.md").read_text(encoding="utf-8")
    assert f"Version du guide : **{mesure.GUIDE_ANNOTATION}**" in texte
    assert f"## 5. Le guide d'annotation, version {mesure.GUIDE_ANNOTATION}" in texte
    assert f'guide: "{mesure.GUIDE_ANNOTATION}"' in texte


# ---------- phase de démarrage : un seul annotateur ----------

def test_la_relecture_mesure_la_constance_et_n_est_jamais_une_reference():
    relue = annotation(role="relecture", categorie="opinion")
    page = {**page_annotee(annotation(), relue), "cas": "specimens/x.md"}
    intra = mesure.accord_intra([page])
    assert intra["paires"] == 1
    assert intra["categorie_accord"] == 0.0
    assert intra["techniques_f1"] == 1.0
    # Ni arbitrage demandé, ni accord entre annotateurs : il n'y a qu'une personne.
    assert mesure.a_arbitrer([page]) == []
    assert mesure.accord_annotateurs([page])["paires"] == 0
    carte = {"categorie": "theorie_du_complot", "note": {"grade": "D"}, "techniques_detectees": []}
    assert mesure.mesurer_contre_annotations([{**page, "carte": carte}])["categorie"] == 1.0


def test_les_lectures_en_cours_se_mesurent_sans_etre_publiees(tmp_path):
    """Une page pas encore close vit dans annotations-en-cours/, que git ignore : elle doit
    quand même compter pour la coordination qui la mesure."""
    (tmp_path / "x.md").write_text(PAGE, encoding="utf-8")
    (tmp_path / "corpus.yaml").write_text(yaml.safe_dump([{"fichier": "x.md"}]), encoding="utf-8")
    brute = {k: v for k, v in annotation(cas="x.md").items() if k != "_fichier"}
    (tmp_path / "annotations-en-cours" / "une").mkdir(parents=True)
    (tmp_path / "annotations-en-cours" / "une" / "x.yaml").write_text(yaml.safe_dump(brute), encoding="utf-8")

    resultat = runner.invoke(app, ["mesurer", str(tmp_path / "corpus.yaml")])

    assert resultat.exit_code == 0, resultat.output
    assert "1 annotation(s)" in resultat.output
    assert "qu'une lecture" in resultat.output


def test_le_dossier_des_lectures_en_cours_n_est_pas_versionne():
    ignores = (RACINE / ".gitignore").read_text(encoding="utf-8")
    assert "corpus/annotations-en-cours/" in ignores


# ---------- le jeu argent reste hors du jeu de test ----------

def deja_vus(tmp_path, *lignes):
    chemin = tmp_path / "deja-vus.txt"
    chemin.write_text("# Pages du jeu argent\n" + "".join(l + "\n" for l in lignes), encoding="utf-8")
    return chemin


def test_une_page_du_jeu_argent_se_reconnait_par_contenu_ou_par_adresse(tmp_path):
    vus = mesure.charger_deja_vus(deja_vus(tmp_path, f"{hacher_contenu(PAGE)} https://exemple.fr/a"))
    assert vus.motif(empreinte=hacher_contenu(PAGE)) is not None
    # L'adresse se compare normalisée : casse de l'hôte, traceurs, slash final.
    assert vus.motif(url="https://EXEMPLE.fr/a/?utm_source=x") is not None
    assert vus.motif(empreinte="0" * 64, url="https://exemple.fr/b") is None


def test_un_fichier_deja_vus_illisible_est_refuse(tmp_path):
    with pytest.raises(ValueError, match="ligne 2"):
        mesure.charger_deja_vus(deja_vus(tmp_path, "pas-une-empreinte https://exemple.fr"))


def test_capturer_refuse_une_page_du_jeu_argent(tmp_path):
    texte = "Un texte assez long pour être capturé. " * 10
    source = tmp_path / "page.md"
    source.write_text(texte, encoding="utf-8")
    liste = deja_vus(tmp_path, f"{hacher_contenu(texte.strip())} https://ailleurs.fr/x")

    resultat = runner.invoke(app, ["capturer", str(source), "--url", "https://exemple.fr/page",
                                   "--vers", str(tmp_path / "captures"), "--deja-vus", str(liste)])

    assert resultat.exit_code == 2
    assert "jeu argent" in resultat.output
    assert not (tmp_path / "captures").exists()


def test_mesurer_signale_un_jeu_de_test_contamine(tmp_path):
    (tmp_path / "corpus.yaml").write_text("[]", encoding="utf-8")
    (tmp_path / "evaluation.yaml").write_text(yaml.safe_dump([
        {"capture": "captures/a.md", "url": "https://exemple.fr/a", "content_hash": "1" * 64},
        {"capture": "captures/b.md", "url": "https://exemple.fr/b", "content_hash": "2" * 64},
    ]), encoding="utf-8")
    liste = deja_vus(tmp_path, f"{'9' * 64} https://exemple.fr/b")

    resultat = runner.invoke(app, ["mesurer", str(tmp_path / "corpus.yaml"), "--deja-vus", str(liste)])

    assert resultat.exit_code == 1
    assert "captures/b.md" in resultat.output
    assert "captures/a.md" not in resultat.output
