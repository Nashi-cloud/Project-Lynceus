"""Le tableau publié de la calibration, et sa provenance.

Le portail publie des scores. Tant qu'ils s'écrivaient à la main, la seule chose vérifiée
était que la version de prompt annoncée corresponde aux fichiers : rien n'empêchait donc
d'avancer l'estampille sans avoir relancé une seule analyse. Ces tests verrouillent la règle
inverse : un chiffre publié vient d'une passe enregistrée, ou la construction échoue."""

import json

import pytest
from typer.testing import CliRunner

from lynceus import calibration
from lynceus.cli import app

runner = CliRunner()


def passe(**surcharges) -> dict:
    base = {
        "date": "2026-08-27",
        "modele": "test/modele",
        "fournisseur": "essai.test",
        "temperature": 0,
        "prompt_version": "0.1.2",
        "corpus": "0" * 16,
        "conformes": 1,
        "mesures": 1,
        "depuis_cache": 0,
        "cas": [{
            "id": "specimens/cas.md",
            "titre": "Cas de test",
            "titre_en": "Test case",
            "categorie": "satire",
            "grade": "A",
            "score": 94,
            "ecarts": [],
        }],
    }
    return {**base, **surcharges}


# ---------- engendrement du bloc ----------

def test_une_passe_donne_un_tableau_lisible():
    rendu = calibration.bloc([passe()])
    assert "Dernière passe : **2026-08-27**" in rendu
    assert "`test/modele` (via essai.test)" in rendu
    assert "prompt **v0.1.2**" in rendu
    assert "température **0**" in rendu
    assert "**Une passe**" in rendu
    assert "| Cas de test | satire | A | 94 | — |" in rendu


def test_plusieurs_passes_donnent_l_intervalle_et_la_suite_des_grades():
    """Une note qui bouge d'une passe à l'autre doit se voir, pas se moyenner.

    C'est la dispersion qui informe le lecteur : un score unique laisserait croire à une
    reproductibilité que le modèle n'a pas."""
    def cas(grade, score):
        return [{"id": "specimens/cas.md", "titre": "Cas de test", "titre_en": "Test case",
                 "categorie": "satire", "grade": grade, "score": score, "ecarts": []}]

    rendu = calibration.bloc([
        passe(cas=cas("A", 91), conformes=1),
        passe(cas=cas("B", 79), conformes=0),
        passe(cas=cas("A", 98), conformes=1),
    ])
    assert "**3 passes**" in rendu
    assert "**1/1, 0/1, 1/1** conformes" in rendu
    assert "| Cas de test | satire | A B A | 79 à 98 | — |" in rendu


def test_un_ecart_qui_n_apparait_pas_partout_annonce_son_taux():
    ecart = [{"gravite": "grave", "type": "categorie", "obtenu": "opinion", "attendu": "satire"}]
    rendu = calibration.bloc([
        passe(),
        passe(cas=[{**passe()["cas"][0], "categorie": "opinion", "ecarts": ecart}]),
    ])
    assert "catégorie `opinion` au lieu de satire (1 passe(s) sur 2)" in rendu
    assert "satire / opinion" in rendu


def test_un_cas_non_mesure_reste_au_tableau():
    """L'effacer donnerait un corpus qui rétrécit sans qu'on sache pourquoi."""
    absent = [{"gravite": "grave", "type": "non_mesure", "detail": "capture absente"}]
    rendu = calibration.bloc([passe(cas=[{"id": "x", "titre": "Page réelle", "titre_en": "Real page",
                                          "ecarts": absent}])])
    assert "cas non mesuré : capture absente" in rendu


def test_le_bloc_anglais_prend_le_titre_anglais_et_ses_phrases():
    rendu = calibration.bloc([passe()], langue="en")
    assert "Latest run: **2026-08-27**" in rendu
    assert "| Test case | satire | A | 94 | — |" in rendu
    assert "**One run**" in rendu
    assert "Cas de test" not in rendu


def test_les_categories_ne_sont_pas_traduites():
    """Un id de catégorie est ce que l'instance attend, pas un libellé d'affichage."""
    assert "satire" in calibration.bloc([passe()], langue="en")


# ---------- journal ----------

def test_le_journal_ne_fait_que_croitre(tmp_path):
    journal = tmp_path / "passes.jsonl"
    calibration.enregistrer(journal, passe())
    calibration.enregistrer(journal, passe(date="2026-08-28"))
    assert len(calibration.passes(journal)) == 2


def test_le_journal_se_filtre_sur_la_version_de_prompt(tmp_path):
    """Une passe menée sous une version antérieure ne mesure pas ce qui s'applique."""
    journal = tmp_path / "passes.jsonl"
    calibration.enregistrer(journal, passe(prompt_version="0.1.1"))
    calibration.enregistrer(journal, passe(prompt_version="0.1.2"))
    assert len(calibration.passes(journal, "0.1.2")) == 1
    assert calibration.passes(tmp_path / "absent.jsonl") == []


# ---------- insertion dans le document ----------

def test_le_bloc_remplace_sans_toucher_au_reste(tmp_path):
    """La lecture des résultats est écrite à la main : une machine ne peut pas dire ce
    qu'un écart signifie. Elle doit survivre à chaque réengendrement."""
    fichier = tmp_path / "RESULTATS.md"
    fichier.write_text(
        "# Résultats\n\n"
        f"{calibration.MARQUE_DEBUT}\nancien tableau\n{calibration.MARQUE_FIN}\n\n"
        "## Lecture\n\nCe que ces chiffres veulent dire.\n",
        encoding="utf-8",
    )
    assert calibration.remplacer_bloc(fichier, calibration.bloc([passe()]))
    texte = fichier.read_text(encoding="utf-8")
    assert "ancien tableau" not in texte
    assert "Ce que ces chiffres veulent dire." in texte
    assert texte.startswith("# Résultats")


def test_reengendrer_a_l_identique_ne_touche_pas_au_fichier(tmp_path):
    fichier = tmp_path / "RESULTATS.md"
    fichier.write_text(f"# R\n\n{calibration.bloc([passe()])}\n", encoding="utf-8")
    assert calibration.remplacer_bloc(fichier, calibration.bloc([passe()])) is False


def test_le_bloc_publie_se_relit(tmp_path):
    fichier = tmp_path / "RESULTATS.md"
    rendu = calibration.bloc([passe()])
    fichier.write_text(f"# R\n\n{rendu}\n\n## Suite\n", encoding="utf-8")
    assert calibration.bloc_publie(fichier) == rendu
    (tmp_path / "sans.md").write_text("# R\n", encoding="utf-8")
    assert calibration.bloc_publie(tmp_path / "sans.md") == ""


# ---------- la commande de contrôle ----------

@pytest.fixture
def corpus_publie(tmp_path, monkeypatch):
    """Un corpus minimal avec son rapport publié, dans les deux langues."""
    (tmp_path / "specimens").mkdir()
    (tmp_path / "specimens" / "cas.md").write_text(
        "---\nsource: fictif\n---\n\nContenu du spécimen.", encoding="utf-8")
    (tmp_path / "corpus.yaml").write_text(
        "- fichier: specimens/cas.md\n"
        "  titre: Cas de test\n"
        "  titre_en: Test case\n"
        "  categorie_attendue: satire\n"
        "  grade_attendu: [A, B]\n",
        encoding="utf-8",
    )
    (tmp_path / "RESULTATS.md").write_text("# Résultats de calibration\n\n## Lecture\n", encoding="utf-8")
    (tmp_path / "en").mkdir()
    (tmp_path / "en" / "RESULTATS.md").write_text(
        "# Calibration results\n\n<!-- traduit-de: corpus/RESULTATS.md sha256:0000000000000000 -->\n\n## How to read it\n",
        encoding="utf-8")
    return tmp_path


def test_sans_passe_enregistree_le_controle_echoue(corpus_publie):
    """Le cœur du garde-fou : des chiffres sans mesure ne passent pas."""
    resultat = runner.invoke(app, ["calibration", "--corpus", str(corpus_publie / "corpus.yaml")])
    assert resultat.exit_code == 1
    assert "Aucune passe enregistrée" in resultat.stdout


def test_un_tableau_retouche_a_la_main_est_detecte(corpus_publie):
    """Avancer un chiffre sans relancer la mesure devient un échec, pas un détail."""
    from lynceus.moteur import prompt as moteur_prompt

    version = moteur_prompt.versions_disponibles()[-1]
    journal = corpus_publie / "passes.jsonl"
    # L'empreinte du corpus réel, pas celle du gabarit : le contrôle ne retient que les
    # passes mesurées contre les attentes en vigueur.
    calibration.enregistrer(journal, passe(
        prompt_version=version, corpus=calibration.empreinte(corpus_publie / "corpus.yaml")))
    for chemin, langue in (("RESULTATS.md", "fr"), ("en/RESULTATS.md", "en")):
        fichier = corpus_publie / chemin
        calibration.remplacer_bloc(
            fichier, calibration.bloc(calibration.passes(journal, version), langue))

    argv = ["calibration", "--corpus", str(corpus_publie / "corpus.yaml")]
    assert runner.invoke(app, argv).exit_code == 0

    fichier = corpus_publie / "RESULTATS.md"
    fichier.write_text(fichier.read_text(encoding="utf-8").replace("| 94 |", "| 99 |"),
                       encoding="utf-8")
    retouche = runner.invoke(app, argv)
    assert retouche.exit_code == 1
    assert "ne correspond pas au journal" in retouche.stdout


def test_une_passe_resservie_depuis_le_cache_le_dit():
    """Sans cette mention, une relecture de l'annuaire passerait pour une mesure neuve.

    C'est l'écueil rencontré à la première passe enregistrée : les treize cas étaient déjà
    en base, aucun appel au modèle n'a eu lieu, et le tableau annonçait pourtant « une
    passe » comme s'il s'agissait d'un tirage indépendant."""
    rendu = calibration.bloc([passe(depuis_cache=1, mesures=1)])
    assert "**1/1\\*** conformes" in rendu
    assert "astérisque" in rendu

    neuve = calibration.bloc([passe(depuis_cache=0, mesures=1)])
    assert "\\*" not in neuve and "astérisque" not in neuve


def test_le_tableau_ne_melange_pas_deux_corpus(tmp_path):
    """Modifier une attente change ce que « conforme » veut dire.

    Agréger des passes mesurées contre des attentes différentes donnerait un total qui ne
    correspond à aucun corpus réel. Le filtre n'existait pas : le cas ne s'était jamais
    présenté parce qu'un changement de corpus avait toujours accompagné un changement de
    version de prompt, qui excluait les anciennes passes par un autre chemin."""
    journal = tmp_path / "passes.jsonl"
    calibration.enregistrer(journal, passe(corpus="a" * 16, conformes=1))
    calibration.enregistrer(journal, passe(corpus="b" * 16, conformes=0))

    courantes = calibration.passes_courantes(journal, "0.1.2", "b" * 16)
    assert [p["corpus"] for p in courantes] == ["b" * 16]


def test_sans_empreinte_de_corpus_toutes_les_passes_comptent(tmp_path):
    """Le filtre est explicite : un appel qui ne le demande pas garde l'ancien comportement,
    ce qui laisse lisibles les journaux antérieurs au champ."""
    journal = tmp_path / "passes.jsonl"
    calibration.enregistrer(journal, passe(corpus="a" * 16))
    calibration.enregistrer(journal, passe(corpus="b" * 16))
    assert len(calibration.passes_courantes(journal, "0.1.2")) == 2


def test_un_corpus_modifie_ne_laisse_aucune_passe_courante(tmp_path):
    """Le cas qui compte : après modification d'une attente, plus rien ne doit compter.
    Le tableau ne peut alors plus être engendré, et la mesure redevient obligatoire."""
    journal = tmp_path / "passes.jsonl"
    calibration.enregistrer(journal, passe(corpus="a" * 16))
    assert calibration.passes_courantes(journal, "0.1.2", "c" * 16) == []


def test_le_tableau_ne_melange_pas_deux_modeles(tmp_path):
    """Deux modèles ne donnent pas les mêmes notes sur le même texte.

    Un tableau qui mélangerait leurs passes afficherait des intervalles de score mesurant
    l'écart entre deux modèles, pas la variabilité de celui que l'instance emploie."""
    journal = tmp_path / "passes.jsonl"
    calibration.enregistrer(journal, passe(modele="ancien/modele"))
    calibration.enregistrer(journal, passe(modele="nouveau/modele"))
    calibration.enregistrer(journal, passe(modele="nouveau/modele", date="2026-08-28"))

    courantes = calibration.passes_courantes(journal, "0.1.2")
    assert [p["modele"] for p in courantes] == ["nouveau/modele"] * 2
    assert "ancien/modele" not in calibration.bloc(courantes)
