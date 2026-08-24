/** Service worker Lynceus — orchestre menu contextuel, extraction, analyse et badge.
 * Règles de la charte appliquées ici :
 *  - l'analyse (envoi de contenu) n'est déclenchée QUE par un geste explicite ;
 *  - le badge passif n'envoie qu'un hash d'URL, et seulement s'il est activé
 *    (permission « tabs » optionnelle, demandée dans les réglages) ;
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
  return false;
});

chrome.tabs.onRemoved.addListener((tabId) => etats.delete(tabId));

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

  majEtat(tabId, { phase: "extraction" });
  try {
    await chrome.scripting.executeScript({ target: { tabId }, files: ["extracteur.js"] });
    const resultats = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => (globalThis as { __lynceusExtraire?: () => unknown }).__lynceusExtraire?.(),
    });
    const extraction = resultats[0]?.result as Extraction | undefined;
    if (!extraction) throw new Error("L'extraction n'a rien renvoyé.");
    if (!extraction.ok) throw new Error(extraction.erreur);

    majEtat(tabId, { phase: "analyse" });
    const reponse = await analyser({
      url: extraction.url,
      contenu_markdown: extraction.markdown,
      titre: extraction.titre ?? undefined,
      langue: extraction.langue ?? undefined,
    });
    majEtat(tabId, {
      phase: "ok",
      carte: reponse.carte,
      enCache: reponse.en_cache,
      rejetees: reponse.detections_rejetees?.length ?? 0,
    });
    poserBadge(tabId, reponse.carte.note.grade);
    const grade = reponse.carte.note.grade;
    if (grade === "D" || grade === "E") poserBordure(tabId, COULEURS_GRADE[grade]);
    else retirerBordure(tabId);
  } catch (erreur) {
    majEtat(tabId, { phase: "erreur", erreur: messageLisible(erreur) });
  }
}

function messageLisible(erreur: unknown): string {
  const texte = erreur instanceof Error ? erreur.message : String(erreur);
  if (/cannot access|cannot be scripted|showErrorPage|chrome:\/\//i.test(texte)) {
    return (
      "Lynceus n'a pas accès à cette page. Les pages internes du navigateur et le Web Store " +
      "ne sont pas analysables ; pour une page normale, relance via le clic droit → " +
      "« Analyser cette page avec Lynceus » (c'est ce geste qui autorise l'accès)."
    );
  }
  return texte;
}

// ---------- contour de page (analyse explicite uniquement — pas de permission supplémentaire) ----------
// Le geste qui déclenche l'analyse (menu contextuel / action) accorde activeTab pour cet onglet :
// on réutilise ce même accès pour poser un contour discret, jamais pour les pages reconnues
// passivement par le badge (cela demanderait un accès à toutes les pages, hors de portée ici).

const ID_BORDURE = "lynceus-bordure-risque";

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
      // La page est déjà dans l'annuaire : on l'affiche directement dans le panneau, sans
      // déclencher d'analyse (aucun contenu envoyé — seule une consultation déjà consentie
      // via l'activation du badge passif, cf. docs/ETHIQUE.md §3-4).
      majEtat(tabId, { phase: "ok", carte: reponse.carte, enCache: true, rejetees: 0 });
    } else {
      effacerBadge(tabId);
    }
  } catch {
    effacerBadge(tabId); // le badge est un bonus : jamais d'erreur bruyante
  }
}

// Sans la permission optionnelle « tabs », `url` est undefined : le badge reste muet.
chrome.tabs.onUpdated.addListener((tabId, changement, onglet) => {
  if (changement.status === "loading") {
    // Nouvelle navigation ou rechargement : la carte affichée ne concerne plus cette page.
    // On ne coupe pas une analyse en cours (extraction/analyse) déclenchée juste avant.
    const etatActuel = etats.get(tabId);
    if (!etatActuel || (etatActuel.phase !== "extraction" && etatActuel.phase !== "analyse")) {
      majEtat(tabId, { phase: "repos" });
      retirerBordure(tabId);
    }
  }
  if (changement.status === "complete") void majBadgePassif(tabId, onglet.url);
});

chrome.tabs.onActivated.addListener(({ tabId }) => {
  chrome.tabs
    .get(tabId)
    .then((onglet) => majBadgePassif(tabId, onglet.url))
    .catch(() => {});
});
