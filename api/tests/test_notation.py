from lynceus.moteur.notation import POIDS, calculer_grade, calculer_score


def test_poids_somment_a_un():
    assert abs(sum(POIDS.values()) - 1.0) < 1e-9


def test_score_pondere():
    dims = {
        "sources": {"score": 10}, "factualite": {"score": 20},
        "ton": {"score": 30}, "transparence": {"score": 40},
    }
    assert calculer_score(dims) == 23


def test_score_uniforme():
    dims = {k: {"score": 70} for k in POIDS}
    assert calculer_score(dims) == 70


def test_seuils_grades():
    assert calculer_grade(100) == "A"
    assert calculer_grade(80) == "A"
    assert calculer_grade(79) == "B"
    assert calculer_grade(65) == "B"
    assert calculer_grade(64) == "C"
    assert calculer_grade(50) == "C"
    assert calculer_grade(49) == "D"
    assert calculer_grade(30) == "D"
    assert calculer_grade(29) == "E"
    assert calculer_grade(0) == "E"
