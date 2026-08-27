import httpx
import pytest

from lynceus.config import Parametres
from lynceus.moteur import llm


def _client_simule(monkeypatch, statut: int, corps: str = '{"error": "simulée"}'):
    def faux_post(url, json=None, headers=None, timeout=None):
        return httpx.Response(statut, text=corps)

    monkeypatch.setattr(httpx, "post", faux_post)


def _p(**kw) -> Parametres:
    defauts = dict(llm_api_key="cle-test", llm_model="test/modele")
    defauts.update(kw)
    return Parametres(**defauts)


def test_erreur_401_actionnable(monkeypatch):
    _client_simule(monkeypatch, 401)
    with pytest.raises(llm.ErreurLLM) as exc:
        llm.appeler([{"role": "user", "content": "x"}], _p())
    message = str(exc.value)
    assert "LYNCEUS_LLM_API_KEY" in message and "REDÉMARRER" in message


def test_erreur_404_pointe_le_modele(monkeypatch):
    _client_simule(monkeypatch, 404)
    with pytest.raises(llm.ErreurLLM) as exc:
        llm.appeler([{"role": "user", "content": "x"}], _p())
    assert "LYNCEUS_LLM_MODEL" in str(exc.value)


def test_erreur_500_sans_aide_specifique(monkeypatch):
    _client_simule(monkeypatch, 500, corps="boom")
    with pytest.raises(llm.ErreurLLM) as exc:
        llm.appeler([{"role": "user", "content": "x"}], _p())
    assert "HTTP 500" in str(exc.value) and "boom" in str(exc.value)


def test_reseau_injoignable(monkeypatch):
    def faux_post(url, json=None, headers=None, timeout=None):
        raise httpx.ConnectError("connexion refusée")

    monkeypatch.setattr(httpx, "post", faux_post)
    with pytest.raises(llm.ErreurLLM) as exc:
        llm.appeler([{"role": "user", "content": "x"}], _p())
    assert "injoignable" in str(exc.value)


def test_extraire_json_tolerant():
    assert llm.extraire_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert llm.extraire_json('Voici :\n{"a": 1}\nvoilà.') == {"a": 1}
    with pytest.raises(ValueError):
        llm.extraire_json("aucun objet ici")
    with pytest.raises(ValueError):
        llm.extraire_json('[1, 2]')


# ---------------------------------------------------- nom public du fournisseur

@pytest.mark.parametrize("adresse, attendu, distant", [
    ("https://openrouter.ai/api/v1", "openrouter.ai", True),
    ("https://api.mistral.ai/v1", "api.mistral.ai", True),
    ("http://localhost:11434/v1", "modèle auto-hébergé", False),
    ("http://ollama:11434/v1", "modèle auto-hébergé", False),        # service Docker
    ("http://192.168.1.20:8000/v1", "modèle auto-hébergé", False),   # réseau privé
    ("http://gpu.interne.lan/v1", "modèle auto-hébergé", False),
])
def test_un_modele_prive_est_annonce_sans_nommer_la_machine(adresse, attendu, distant):
    """Le nom d'hôte d'un endpoint privé ne dit rien au lecteur et renseigne le réseau de
    l'exploitant : il n'a pas à figurer dans une carte publiée."""
    assert llm.fournisseur_annonce(adresse) == (attendu, distant)


def test_le_libelle_configure_l_emporte_sur_le_nom_d_hote():
    """Un routeur d'inférence porte son nom, pas celui de l'entreprise qui exécute le
    modèle : seul l'exploitant peut le dire correctement."""
    nom, distant = llm.fournisseur_annonce("https://openrouter.ai/api/v1",
                                           "OpenRouter, qui sous-traite l'inférence")
    assert nom == "OpenRouter, qui sous-traite l'inférence"
    assert distant is True


def test_sans_adresse_le_fournisseur_est_reput_distant():
    """Promettre à tort que le texte ne sort pas ferait de la page de confidentialité un
    mensonge : dans le doute, on annonce le cas le moins favorable."""
    assert llm.fournisseur_annonce("") == ("non renseigné", True)
