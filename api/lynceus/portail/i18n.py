"""Traduction du portail — catalogues .po lus au démarrage.

Trois décisions, et leurs raisons.

**Le format .po** plutôt qu'un dictionnaire maison : c'est celui qu'attendent les outils
de traduction (Weblate, Poedit, Transifex). Ajouter une langue ne demandera donc pas de
toucher au code, ce qui est la condition pour que la traduction soit contribuée plutôt
qu'écrite par nous.

**Les msgid sont les phrases françaises elles-mêmes**, pas des clés abstraites. Un gabarit
reste lisible tel quel, et une phrase modifiée en français apparaît comme non traduite au
lieu de garder silencieusement son ancienne traduction. Le test qui exige une traduction
pour chaque phrase transforme cette dérive en échec de la vérification.

**Une langue par environnement Jinja**, plutôt qu'un état global changé à chaque requête :
le portail est asynchrone, et un état partagé finirait par servir la mauvaise langue sous
charge.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from babel.core import negotiate_locale
from babel.messages.pofile import read_po
from markupsafe import Markup

RACINE = Path(__file__).parent
TRADUCTIONS = RACINE / "traductions"

# Langue d'écriture du projet : ses phrases sont les msgid, elle n'a pas de catalogue.
LANGUE_SOURCE = "fr"
LANGUES = {"fr": "Français", "en": "English"}

# La même chose vue comme une table de correspondance, et ce n'est pas un doublon.
# Un code de langue vient de l'URL et finit dans un chemin de fichier, `docs/<langue>/…`.
# Comparer la valeur reçue à la liste des langues suffit à écarter une traversée, mais
# c'est toujours la chaîne de la requête qui entre ensuite dans le chemin. Passer par cette
# table rend le code écrit sur disque littéralement celui du projet, et non celui du
# visiteur : la garde ne repose plus sur une comparaison faite plus haut, et l'analyse
# statique cesse à juste titre de suivre la valeur.
CODES_SERVIS = {code: code for code in LANGUES}


def code_servi(demande: str) -> str | None:
    """Le code de langue du projet correspondant à la demande, ou None."""
    return CODES_SERVIS.get(demande)


@lru_cache
def catalogue(langue: str) -> dict[str, str]:
    """Les phrases traduites d'une langue. Vide pour la langue source, ou si le fichier
    n'existe pas encore : le portail sert alors le français, ce qui vaut mieux qu'une page
    blanche."""
    if langue == LANGUE_SOURCE:
        return {}
    chemin = TRADUCTIONS / f"{langue}.po"
    if not chemin.exists():
        return {}
    with chemin.open(encoding="utf-8") as fichier:
        lu = read_po(fichier)
    return {
        message.id: message.string
        for message in lu
        # Une entrée « fuzzy » est une traduction que l'outil a rapprochée d'une phrase
        # modifiée sans qu'un humain l'ait relue : la servir serait un pari.
        if message.id and message.string and not message.fuzzy
    }


def N_(texte: str) -> str:
    """Marque une phrase à traduire sans la traduire ici.

    Certaines phrases sont définies au chargement d'un module, avant qu'une requête et donc
    une langue existent. Le marqueur les rend visibles de l'extraction et du test de
    couverture ; la traduction a lieu au moment du rendu."""
    return texte


def traducteur(langue: str):
    """Rend la fonction `_` injectée dans les gabarits.

    Elle accepte des paramètres nommés, au format `%(nom)s` : une phrase traduite ne place
    pas ses variables dans le même ordre qu'en français, et une concaténation dans le
    gabarit interdirait de les déplacer.

    Le résultat est du balisage, pas du texte brut : beaucoup de phrases portent une mise
    en valeur ou un lien, et l'échappement automatique de Jinja les afficherait en clair.
    Les phrases viennent de nos propres fichiers, donc elles sont sûres ; les valeurs
    interpolées, elles, sont échappées par Markup au moment de la substitution, ce qui
    protège aussi bien ce qui vient d'une recherche ou d'une carte d'analyse."""
    phrases = catalogue(langue)

    def _(message: str, **valeurs) -> Markup:
        texte = Markup(phrases.get(message, message))
        return texte % valeurs if valeurs else texte

    return _


def prefixe(langue: str) -> str:
    """Ce qui précède le chemin d'une page dans cette langue.

    Le français reste à la racine : les adresses déjà publiées ne changent pas."""
    return "" if langue == LANGUE_SOURCE else f"/{langue}"


def negocier(entete: str | None) -> str:
    """La langue à servir à la racine, d'après l'en-tête Accept-Language du navigateur.

    Repli sur la langue source : une préférence exprimée pour une langue que le portail ne
    parle pas ne doit pas le faire hésiter."""
    if not entete:
        return LANGUE_SOURCE
    preferees = []
    for morceau in entete.split(","):
        code = morceau.split(";")[0].strip().replace("-", "_")
        if code and code != "*":
            preferees.append(code)
    return negotiate_locale(preferees, list(LANGUES)) or LANGUE_SOURCE
