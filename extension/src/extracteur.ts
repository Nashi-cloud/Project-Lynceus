/** Script injecté dans la page au moment de l'analyse (et seulement là — activeTab).
 * Expose une fonction globale que le service worker appelle ensuite : c'est ELLE qui
 * extrait le contenu, localement, dans le navigateur — paywalls et protections
 * anti-robots déjà franchis par l'utilisateur (docs/ARCHITECTURE.md). */

import { Readability } from "@mozilla/readability";
import TurndownService from "turndown";
import type { Extraction } from "./commun/types";

declare global {
  // eslint-disable-next-line no-var
  var __lynceusExtraire: (() => Extraction) | undefined;
}

globalThis.__lynceusExtraire = (): Extraction => {
  try {
    // Readability modifie le document : on travaille sur une copie.
    const copie = document.cloneNode(true) as Document;
    const article = new Readability(copie).parse();
    if (!article?.content) {
      return { ok: false, erreur: "Contenu principal introuvable sur cette page (page d'accueil, application… ?)." };
    }
    const turndown = new TurndownService({ headingStyle: "atx", codeBlockStyle: "fenced" });
    turndown.remove(["script", "style", "noscript"]);
    const markdown = turndown.turndown(article.content);
    const langue = document.documentElement.lang ? document.documentElement.lang.slice(0, 2).toLowerCase() : null;
    return {
      ok: true,
      url: location.href,
      titre: article.title || document.title || null,
      markdown,
      langue,
    };
  } catch (erreur) {
    return { ok: false, erreur: `Extraction impossible : ${String(erreur)}` };
  }
};
