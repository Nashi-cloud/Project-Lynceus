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


# ---------- cache de prompt ----------

def _charge_envoyee(monkeypatch, messages, parametres) -> dict:
    """Ce qui part réellement au fournisseur."""
    capturee = {}

    def faux_post(url, json=None, headers=None, timeout=None):
        capturee.update(json)
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    monkeypatch.setattr(httpx, "post", faux_post)
    llm.appeler(messages, parametres)
    return capturee


def test_le_prompt_systeme_n_est_pas_marque_par_defaut(monkeypatch):
    """L'auto-hébergement passe avant l'économie : un endpoint minimal peut refuser un
    contenu découpé en blocs, et il ne doit pas casser parce qu'une instance publique
    veut réduire sa facture."""
    messages = [{"role": "system", "content": "consignes"},
                {"role": "user", "content": "page"}]
    assert _p().llm_cache_prompt is False
    assert _charge_envoyee(monkeypatch, messages, _p())["messages"] == messages


def test_le_prompt_systeme_est_marque_quand_l_instance_le_demande(monkeypatch):
    messages = [{"role": "system", "content": "consignes"},
                {"role": "user", "content": "page"}]
    charge = _charge_envoyee(monkeypatch, messages, _p(llm_cache_prompt=True))
    assert charge["messages"][0]["content"][0]["cache_control"] == {"type": "ephemeral"}


def test_le_prompt_systeme_marque_porte_le_point_de_cesure():
    messages = [{"role": "system", "content": "consignes"},
                {"role": "user", "content": "page"}]
    marques = llm.marquer_le_cache(messages)
    assert marques[0]["content"] == [
        {"type": "text", "text": "consignes", "cache_control": {"type": "ephemeral"}}
    ]
    assert marques[1] == messages[1], "le message utilisateur change à chaque analyse"
    assert messages[0]["content"] == "consignes", "l'appelant ne doit pas être modifié"


def test_un_message_deja_en_blocs_n_est_pas_reemballe():
    blocs = [{"type": "text", "text": "consignes"}]
    messages = [{"role": "system", "content": blocs}]
    assert llm.marquer_le_cache(messages)[0]["content"] is blocs


# ---------- réglage du raisonnement ----------

def test_sans_reglage_rien_n_est_demande_au_fournisseur(monkeypatch):
    """Le défaut du fournisseur doit rester le défaut : une instance qui n'a rien choisi
    ne doit pas se voir imposer un comportement par le code."""
    charge = _charge_envoyee(monkeypatch, [{"role": "user", "content": "x"}], _p())
    assert "reasoning" not in charge


def test_le_raisonnement_se_desactive(monkeypatch):
    charge = _charge_envoyee(monkeypatch, [{"role": "user", "content": "x"}],
                             _p(llm_raisonnement="non"))
    assert charge["reasoning"] == {"enabled": False}


def test_l_ampleur_du_raisonnement_se_regle(monkeypatch):
    charge = _charge_envoyee(monkeypatch, [{"role": "user", "content": "x"}],
                             _p(llm_raisonnement="Faible"))
    assert charge["reasoning"] == {"effort": "low"}


def test_un_reglage_inconnu_est_ignore_plutot_que_fatal(monkeypatch):
    """Une faute de frappe dans un .env ne doit pas éteindre le service."""
    charge = _charge_envoyee(monkeypatch, [{"role": "user", "content": "x"}],
                             _p(llm_raisonnement="beaucoup"))
    assert "reasoning" not in charge
