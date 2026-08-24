/** Service worker Lynceus — orchestre menu contextuel, extraction, analyse, badge et contour.
 * Règles de la charte appliquées ici :
 *  - l'analyse (envoi de contenu) n'est déclenchée QUE par un geste explicite, quelle que
 *    soit la permission accordée ;
 *  - le badge et le contour passifs n'envoient/n'affichent qu'à partir d'un hash d'URL, et
 *    seulement si activés (permission « tabs » + accès aux pages, optionnels, demandés
 *    ensemble dans les réglages — sans eux, extension au minimum : geste explicite requis
 *    pour tout, y compris pour ré-analyser après une navigation) ;
 *  - le panneau ne s'ouvre jamais tout seul. */

import { analyser, lookupParHash } from "./commun/api";
import { hacherUrl } from "./commun/hachage";
import { chargerReglages } from "./commun/reglages";
import type { EtatOnglet, Extraction, Grade, MessageVersFond } from "./commun/types";

const MENU_ANALYSER = "lynceus-analyser";

const COULEURS_GRADE: Record<Grade, string> = {
  A: "#1a7f37",
  B: "#5a8f29",
  C: "#b58900",
  D: "#c9662a",
  E: "#b3261e",
};

/** État d'analyse par onglet (mémoire du service worker). */
const etats = new Map<number, EtatOnglet>();

// Annulation : chaque lancement d'analyse incrémente sa génération ; un résultat qui arrive
// après une annulation (ou un nouveau lancement) se reconnaît en comparant sa génération à la
// dernière connue, et est silencieusement ignoré — nécessaire car chrome.scripting.executeScript
// ne peut pas être interrompu en cours de route, contrairement à un fetch.
const generations = new Map<number, number>();
const controleurs = new Map<number, AbortController>();

function nouvelleGeneration(tabId: number): number {
  const generation = (generations.get(tabId) ?? 0) + 1;
  generations.set(tabId, generation);
  return generation;
}

function estGenerationCourante(tabId: number, generation: number): boolean {
  return generations.get(tabId) === generation;
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: MENU_ANALYSER,
    title: "🔭 Analyser cette page avec Lynceus",
    contexts: ["page", "selection"],
  });
  // Un clic sur l'icône ouvre le panneau latéral (sans déclencher d'analyse).
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});
});

chrome.contextMenus.onClicked.addListener((info, onglet) => {
  if (info.menuItemId !== MENU_ANALYSER || !onglet?.id) return;
  chrome.sidePanel.open({ tabId: onglet.id }).catch(() => {});
  void lancerAnalyse(onglet.id);
});

chrome.runtime.onMessage.addListener((message: MessageVersFond, _expediteur, repondre) => {
  if (message.type === "lynceus:etat") {
    repondre(etats.get(message.tabId) ?? { phase: "repos" });
    // Rafraîchissement passif en tâche de fond : couvre le cas où le panneau s'ouvre sur un
    // onglet déjà chargé, sans navigation ni changement d'onglet récent pour l'avoir déclenché.
    chrome.tabs
      .get(message.tabId)
      .then((onglet) => majBadgePassif(message.tabId, onglet.url))
      .catch(() => {});
    return false;
  }
  if (message.type === "lynceus:analyser") {
    void lancerAnalyse(message.tabId);
    repondre({ ok: true });
    return false;
  }
  if (message.type === "lynceus:annuler") {
    nouvelleGeneration(message.tabId); // invalide silencieusement tout résultat déjà en vol
    controleurs.get(message.tabId)?.abort();
    controleurs.delete(message.tabId);
    majEtat(message.tabId, { phase: "repos" });
    repondre({ ok: true });
    return false;
  }
  return false;
});

chrome.tabs.onRemoved.addListener((tabId) => {
  etats.delete(tabId);
  generations.delete(tabId);
  controleurs.delete(tabId);
});

// ---------- analyse ----------

function majEtat(tabId: number, etat: EtatOnglet): void {
  etats.set(tabId, etat);
  chrome.runtime
    .sendMessage({ type: "lynceus:maj", tabId, etat })
    .catch(() => {}); // le panneau peut être fermé : silencieux
}

async function lancerAnalyse(tabId: number): Promise<void> {
  const etatCourant = etats.get(tabId);
  if (etatCourant?.phase === "extraction" || etatCourant?.phase === "analyse") return; // déjà en cours

  const generation = nouvelleGeneration(tabId);
  const controleur = new AbortController();
  controleurs.set(tabId, controleur);

  majEtat(tabId, { phase: "extraction", depuis: Date.now() });
  try {
    await chrome.scripting.executeScript({ target: { tabId }, files: ["extracteur.js"] });
    if (!estGenerationCourante(tabId, generation)) return; // annulé pendant l'injection du script
    const resultats = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => (globalThis as { __lynceusExtraire?: () => unknown }).__lynceusExtraire?.(),
    });
    if (!estGenerationCourante(tabId, generation)) return; // annulé pendant l'extraction

    const extraction = resultats[0]?.result as Extraction | undefined;
    if (!extraction) throw new Error("L'extraction n'a rien renvoyé.");
    if (!extraction.ok) throw new Error(extraction.erreur);

    majEtat(tabId, { phase: "analyse", depuis: Date.now() });
    const reponse = await analyser(
      {
        url: extraction.url,
        contenu_markdown: extraction.markdown,
        titre: extraction.titre ?? undefined,
        langue: extraction.langue ?? undefined,
      },
      controleur.signal,
    );
    if (!estGenerationCourante(tabId, generation)) return; // annulé pendant l'appel réseau

    majEtat(tabId, {
      phase: "ok",
      carte: reponse.carte,
      enCache: reponse.en_cache,
      rejetees: reponse.detections_rejetees?.length ?? 0,
    });
    poserBadge(tabId, reponse.carte.note.grade);
    appliquerBordureSelonGrade(tabId, reponse.carte.note.grade);
  } catch (erreur) {
    if (!estGenerationCourante(tabId, generation)) return; // résultat d'une génération annulée
    if (erreur instanceof DOMException && erreur.name === "AbortError") return; // annulation volontaire, silencieuse
    majEtat(tabId, { phase: "erreur", erreur: messageLisible(erreur) });
  } finally {
    if (controleurs.get(tabId) === controleur) controleurs.delete(tabId);
  }
}

function messageLisible(erreur: unknown): string {
  const texte = erreur instanceof Error ? erreur.message : String(erreur);
  if (/cannot access|cannot be scripted|showErrorPage|chrome:\/\//i.test(texte)) {
    return (
      "Lynceus n'a pas accès à cette page. Si c'est une page interne du navigateur ou le Web " +
      "Store, elle n'est pas analysable. Sinon : relancez via le clic droit → « Analyser cette " +
      "page avec Lynceus » (l'accès expire après un changement de page) — ou activez le badge " +
      "passif dans les réglages pour que ce bouton fonctionne aussi après une navigation."
    );
  }
  return texte;
}

// ---------- contour de page ----------
// Après une analyse explicite, l'accès à l'onglet (activeTab) suffit toujours. Pour les pages
// reconnues passivement par le badge, poser un contour requiert la permission d'hôte optionnelle
// (accordée ou non avec le badge, cf. options) — sans elle, executeScript échoue et on l'ignore
// silencieusement (voir les .catch ci-dessous) : aucun contour, aucune erreur visible.

const ID_BORDURE = "lynceus-bordure-risque";

function appliquerBordureSelonGrade(tabId: number, grade: Grade): void {
  if (grade === "D" || grade === "E") poserBordure(tabId, COULEURS_GRADE[grade]);
  else retirerBordure(tabId);
}

function poserBordure(tabId: number, couleur: string): void {
  chrome.scripting
    .executeScript({
      target: { tabId },
      func: (id: string, couleur: string) => {
        let bordure = document.getElementById(id);
        if (!bordure) {
          bordure = document.createElement("div");
          bordure.id = id;
          document.documentElement.appendChild(bordure);
        }
        Object.assign(bordure.style, {
          position: "fixed",
          inset: "0",
          pointerEvents: "none",
          zIndex: "2147483647",
          border: `5px solid ${couleur}`,
          boxSizing: "border-box",
        });
      },
      args: [ID_BORDURE, couleur],
    })
    .catch(() => {}); // page protégée (chrome://, Web Store…) : on ignore silencieusement
}

function retirerBordure(tabId: number): void {
  chrome.scripting
    .executeScript({
      target: { tabId },
      func: (id: string) => document.getElementById(id)?.remove(),
      args: [ID_BORDURE],
    })
    .catch(() => {});
}

// ---------- badge passif (opt-in, permission « tabs » optionnelle) ----------

function poserBadge(tabId: number, grade: Grade): void {
  chrome.action.setBadgeText({ tabId, text: grade }).catch(() => {});
  chrome.action.setBadgeBackgroundColor({ tabId, color: COULEURS_GRADE[grade] }).catch(() => {});
  chrome.action.setBadgeTextColor?.({ tabId, color: "#ffffff" }).catch(() => {});
}

function effacerBadge(tabId: number): void {
  chrome.action.setBadgeText({ tabId, text: "" }).catch(() => {});
}

async function majBadgePassif(tabId: number, url: string | undefined): Promise<void> {
  const reglages = await chargerReglages();
  if (!reglages.badgeActif || !url || !/^https?:/i.test(url)) {
    effacerBadge(tabId);
    return;
  }
  // Une analyse en cours ou déjà affichée (déclenchée par l'utilisateur) ne doit pas être écrasée
  // par ce rafraîchissement passif, sauf pour reposer le même résultat (idempotent).
  const etatActuel = etats.get(tabId);
  if (etatActuel && etatActuel.phase !== "repos" && etatActuel.phase !== "erreur") return;

  try {
    // Seul un hash SHA-256 de l'URL normalisée quitte le navigateur — jamais l'URL, jamais le contenu.
    const reponse = await lookupParHash(await hacherUrl(url));
    if (reponse.statut === "connue" && reponse.carte) {
      poserBadge(tabId, reponse.carte.note.grade);
      appliquerBordureSelonGrade(tabId, reponse.carte.note.grade);
      // La page est déjà dans l'annuaire : on l'affiche directement dans le panneau, sans
      // déclencher d'analyse (aucun contenu envoyé — seule une consultation déjà consentie
      // via l'activation du badge passif, cf. docs/ETHIQUE.md §3-4).
      majEtat(tabId, { phase: "ok", carte: reponse.carte, enCache: true, rejetees: 0 });
    } else {
      effacerBadge(tabId);
      retirerBordure(tabId);
    }
  } catch {
    effacerBadge(tabId); // le badge est un bonus : jamais d'erreur bruyante
  }
}

// Sans permission d'hôte, `changement.url` reste toujours undefined : cette détection SPA
// (navigation interne sans rechargement, ex. YouTube passant d'une vidéo à l'autre) ne
// fonctionne qu'avec le badge passif activé. Sans lui, seul un rechargement complet
// ("loading") est détecté — limite documentée, cf. extension/README.md.
chrome.tabs.onUpdated.addListener((tabId, changement, onglet) => {
  const nouvellePage = changement.status === "loading" || changement.url !== undefined;
  if (nouvellePage) {
    // La carte affichée ne concerne plus cette page. On ne coupe pas une analyse en cours
    // (extraction/analyse) déclenchée juste avant.
    const etatActuel = etats.get(tabId);
    if (!etatActuel || (etatActuel.phase !== "extraction" && etatActuel.phase !== "analyse")) {
      majEtat(tabId, { phase: "repos" });
      retirerBordure(tabId);
    }
  }
  if (changement.status === "complete" || changement.url !== undefined) {
    void majBadgePassif(tabId, onglet.url);
  }
});

chrome.tabs.onActivated.addListener(({ tabId }) => {
  chrome.tabs
    .get(tabId)
    .then((onglet) => majBadgePassif(tabId, onglet.url))
    .catch(() => {});
});
