/** Client de l'API Lynceus (instance configurable — auto-hébergement de premier ordre). */

import { chargerReglages } from "./reglages";
import type { DemandeAnalyse, ReponseAnalyse, ReponseLookup } from "./types";

/** Combine un délai (filet de sécurité) et une annulation externe (bouton « Annuler ») en un
 * seul signal — implémenté à la main plutôt qu'avec AbortSignal.any/timeout pour rester
 * indépendant des lacunes de typage DOM d'une version de TypeScript donnée. */
function signalAvecDelai(delaiMs: number, externe?: AbortSignal): AbortSignal {
  const controleur = new AbortController();
  const minuteur = setTimeout(
    () => controleur.abort(new DOMException("Délai dépassé", "TimeoutError")),
    delaiMs,
  );
  controleur.signal.addEventListener("abort", () => clearTimeout(minuteur), { once: true });
  if (externe) {
    if (externe.aborted) controleur.abort(externe.reason);
    else externe.addEventListener("abort", () => controleur.abort(externe.reason), { once: true });
  }
  return controleur.signal;
}

async function requete<T>(
  chemin: string,
  options: RequestInit = {},
  delaiMs: number,
  signalAnnulation?: AbortSignal,
): Promise<T> {
  const { instance } = await chargerReglages();
  let reponse: Response;
  try {
    reponse = await fetch(`${instance.replace(/\/+$/, "")}${chemin}`, {
      ...options,
      signal: signalAvecDelai(delaiMs, signalAnnulation),
    });
  } catch (erreur) {
    if (erreur instanceof DOMException && erreur.name === "TimeoutError") {
      throw new Error(
        `L'instance n'a pas répondu dans le délai imparti (${Math.round(delaiMs / 1000)} s). ` +
          "Le fournisseur LLM configuré est peut-être lent ou indisponible ; vous pouvez " +
          "augmenter ce délai dans les réglages, ou réessayer plus tard.",
      );
    }
    if (erreur instanceof DOMException && erreur.name === "AbortError") throw erreur; // annulation volontaire
    throw new Error(
      `Instance Lynceus injoignable (${instance}). Le serveur est-il démarré ? ` +
        "L'adresse se règle dans les options de l'extension.",
    );
  }
  if (!reponse.ok) {
    let detail = `HTTP ${reponse.status}`;
    try {
      const corps = (await reponse.json()) as { detail?: string };
      if (corps.detail) detail = corps.detail;
    } catch {
      /* corps non JSON */
    }
    throw new Error(detail);
  }
  return (await reponse.json()) as T;
}

// Consultation d'annuaire : bon marché côté serveur (une lecture), délai court fixe.
export function lookupParHash(urlHash: string): Promise<ReponseLookup> {
  return requete<ReponseLookup>(`/v1/lookup?url_hash=${urlHash}`, undefined, 10_000);
}

// Analyse : peut appeler un LLM (jusqu'à 360 s au pire côté serveur avec retry) — délai
// configurable par l'utilisateur, et annulable via le bouton du panneau.
export async function analyser(demande: DemandeAnalyse, signal?: AbortSignal): Promise<ReponseAnalyse> {
  const { delaiAnalyseS } = await chargerReglages();
  return requete<ReponseAnalyse>(
    "/v1/analyses",
    { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(demande) },
    delaiAnalyseS * 1000,
    signal,
  );
}
