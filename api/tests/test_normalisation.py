import pytest

from lynceus.normalisation import (
    extraire_domaine, hacher_contenu, hacher_url, normaliser_texte, normaliser_url,
)


def test_minuscules_et_fragment():
    assert normaliser_url("HTTPS://Exemple.FR/Chemin#section") == "https://exemple.fr/Chemin"


def test_tracking_supprime_et_tri():
    assert (
        normaliser_url("https://exemple.fr/a?utm_source=nl&b=2&a=1&fbclid=xyz")
        == "https://exemple.fr/a?a=1&b=2"
    )


def test_slash_final_et_racine():
    assert normaliser_url("https://exemple.fr/page/") == normaliser_url("https://exemple.fr/page")
    assert normaliser_url("https://exemple.fr") == "https://exemple.fr/"
    assert normaliser_url("https://exemple.fr/") == "https://exemple.fr/"


def test_port_par_defaut():
    assert normaliser_url("https://exemple.fr:443/x") == "https://exemple.fr/x"
    assert normaliser_url("http://exemple.fr:8080/x") == "http://exemple.fr:8080/x"


def test_meme_hash_pour_variantes():
    a = hacher_url("https://Exemple.fr/article/?utm_campaign=x#haut")
    b = hacher_url("https://exemple.fr/article")
    assert a == b and len(a) == 64


def test_schema_invalide():
    with pytest.raises(ValueError):
        normaliser_url("ftp://exemple.fr/fichier")


def test_domaine():
    assert extraire_domaine("https://Sous.Exemple.FR:8443/x") == "sous.exemple.fr"


def test_contenu_espaces_insensibles():
    assert hacher_contenu("Un  texte\n\navec   espaces") == hacher_contenu("Un texte avec espaces")
    assert normaliser_texte("  a\tb\nc  ") == "a b c"
