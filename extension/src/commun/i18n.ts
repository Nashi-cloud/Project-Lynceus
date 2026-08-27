/* Traduction de l'extension — mécanisme natif de Chrome (`chrome.i18n`).
 *
 * Pas de sélecteur de langue : le navigateur choisit d'après sa propre langue d'interface,
 * et c'est le comportement attendu d'une extension. Les catalogues vivent dans
 * `_locales/<langue>/messages.json`, format que Chrome lit lui-même, ce qui évite d'embarquer
 * une bibliothèque et permet une traduction contribuée sans toucher au code.
 *
 * La langue de repli est le français, déclarée dans le manifeste (`default_locale`).
 */

/** Le texte traduit, ou la clé si le catalogue ne la connaît pas.
 *
 * Rendre la clé plutôt qu'une chaîne vide est délibéré : un manque se voit à l'écran et se
 * corrige, là où un blanc passe inaperçu. Le test de couverture le rend de toute façon
 * impossible à livrer. */
export function msg(cle: string, ...valeurs: string[]): string {
  return chrome.i18n.getMessage(cle, valeurs) || cle;
}

/** Traduit une page entière au chargement.
 *
 * `data-i18n` remplace le texte de l'élément, `data-i18n-attr="attribut:cle"` remplace un
 * attribut (titre, placeholder, aria-label). Le balisage reste dans le HTML, seul le texte
 * vient du catalogue. */
export function traduireDocument(racine: ParentNode = document): void {
  for (const element of racine.querySelectorAll<HTMLElement>("[data-i18n]")) {
    const cle = element.dataset.i18n;
    if (cle) element.textContent = msg(cle);
  }
  for (const element of racine.querySelectorAll<HTMLElement>("[data-i18n-html]")) {
    // Quelques phrases portent une mise en valeur ou un lien. Le contenu vient de nos
    // propres catalogues, jamais d'une page analysée : aucune donnée extérieure ici.
    const cle = element.dataset.i18nHtml;
    if (cle) element.innerHTML = msg(cle);
  }
  for (const element of racine.querySelectorAll<HTMLElement>("[data-i18n-attr]")) {
    for (const paire of (element.dataset.i18nAttr || "").split(",")) {
      const [attribut, cle] = paire.split(":").map((p) => p.trim());
      if (attribut && cle) element.setAttribute(attribut, msg(cle));
    }
  }
  const titre = document.querySelector<HTMLElement>("title[data-i18n]");
  if (titre?.textContent) document.title = titre.textContent;
  document.documentElement.lang = chrome.i18n.getUILanguage().split("-")[0] ?? "fr";
}
