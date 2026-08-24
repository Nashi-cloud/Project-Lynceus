import httpx
import pytest

from lynceus.extraction import ErreurExtraction, recuperer_markdown


class _Meta:
    title = "Titre extrait"


def test_fallback_navigateur_quand_trafilatura_echoue(monkeypatch):
    monkeypatch.setattr("trafilatura.fetch_url", lambda url: None)
    monkeypatch.setattr("trafilatura.extract", lambda html, **kw: "contenu markdown extrait")
    monkeypatch.setattr("trafilatura.extract_metadata", lambda html: _Meta())
    monkeypatch.setattr(httpx, "get",
                        lambda url, headers=None, follow_redirects=True, timeout=None: httpx.Response(200, text="<html>page</html>"))
    titre, markdown = recuperer_markdown("https://exemple.fr/article")
    assert titre == "Titre extrait"
    assert markdown == "contenu markdown extrait"


def test_blocage_anti_robots_message_actionnable(monkeypatch):
    monkeypatch.setattr("trafilatura.fetch_url", lambda url: None)
    monkeypatch.setattr(httpx, "get",
                        lambda url, headers=None, follow_redirects=True, timeout=None: httpx.Response(403, text="challenge"))
    with pytest.raises(ErreurExtraction) as exc:
        recuperer_markdown("https://bloque.exemple/page")
    message = str(exc.value)
    assert "HTTP 403" in message
    assert "anti-robots" in message
    assert "--url" in message  # le remède est donné


def test_reseau_en_echec(monkeypatch):
    monkeypatch.setattr("trafilatura.fetch_url", lambda url: None)

    def boom(url, **kwargs):
        raise httpx.ConnectError("réseau injoignable")

    monkeypatch.setattr(httpx, "get", boom)
    with pytest.raises(ErreurExtraction):
        recuperer_markdown("https://injoignable.exemple/")


def test_page_sans_contenu(monkeypatch):
    monkeypatch.setattr("trafilatura.fetch_url", lambda url: "<html><body></body></html>")
    monkeypatch.setattr("trafilatura.extract", lambda html, **kw: None)
    with pytest.raises(ErreurExtraction) as exc:
        recuperer_markdown("https://vide.exemple/")
    assert "extractible" in str(exc.value)
