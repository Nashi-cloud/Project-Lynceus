/** Client de l'API Lynceus (instance configurable — auto-hébergement de premier ordre). */

import { chargerReglages } from "./reglages";
import type { DemandeAnalyse, ReponseAnalyse, ReponseLookup } from "./types";

async function requete<T>(chemin: string, options?: RequestInit): Promise<T> {
  const { instance } = await chargerReglages();
  let reponse: Response;
  try {
    reponse = await fetch(`${instance.replace(/\/+$/, "")}${chemin}`, options);
  } catch {
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

export function lookupParHash(urlHash: string): Promise<ReponseLookup> {
  return requete<ReponseLookup>(`/v1/lookup?url_hash=${urlHash}`);
}

export function analyser(demande: DemandeAnalyse): Promise<ReponseAnalyse> {
  return requete<ReponseAnalyse>("/v1/analyses", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(demande),
  });
}
