/** Script injecté dans la page au moment de l'analyse (et seulement là — activeTab).
 * Expose une fonction globale que le service worker appelle ensuite : c'est ELLE qui
 * extrait le contenu, localement, dans le navigateur — paywalls et protections
 * anti-robots déjà franchis par l'utilisateur (docs/ARCHITECTURE.md). */

import { Readability } from "@mozilla/readability";
import TurndownService from "turndown";
import { msg } from "./commun/i18n";
import type { Extraction } from "./commun/types";

declare global {
  // eslint-disable-next-line no-var
  var __lynceusExtraire: (() => Promise<Extraction>) | undefined;
}

/** Sur une page à navigation interne (SPA — YouTube, X…), le contenu et le <title> du
 * document sont mis à jour par des mécanismes internes distincts, pas forcément au même
 * instant : juste après un changement de vidéo/page, le corps peut déjà afficher le nouveau
 * contenu pendant que document.title traîne encore l'ancien. On attend que le titre cesse
 * de changer (stable 100 ms) avant d'extraire, avec un plafond pour ne jamais bloquer
 * indéfiniment une page qui ne se stabiliserait pas. */
async function attendreTitreStable(delaiVerificationMs = 100, delaiMaxMs = 500): Promise<void> {
  const debut = Date.now();
  let precedent = document.title;
  while (Date.now() - debut < delaiMaxMs) {
    await new Promise((resoudre) => setTimeout(resoudre, delaiVerificationMs));
    const actuel = document.title;
    if (actuel === precedent) return; // inchangé depuis le dernier passage : considéré stable
    precedent = actuel;
  }
}

globalThis.__lynceusExtraire = async (): Promise<Extraction> => {
  try {
    await attendreTitreStable();
    // Readability modifie le document : on travaille sur une copie, prise APRÈS stabilisation
    // pour que titre et contenu proviennent du même instant.
    const copie = document.cloneNode(true) as Document;
    const article = new Readability(copie).parse();
    if (!article?.content) {
      return { ok: false, erreur: msg("erreur_contenu_introuvable") };
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
    return { ok: false, erreur: msg("erreur_extraction_impossible", String(erreur)) };
  }
};
