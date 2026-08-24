/** Réglages de l'extension — chrome.storage.sync. Badge passif DÉSACTIVÉ par défaut :
 * la vie privée est le réglage d'usine (docs/ETHIQUE.md §3-4). */

export interface Reglages {
  instance: string;
  badgeActif: boolean;
}

export const REGLAGES_DEFAUT: Reglages = {
  instance: "http://localhost:8000",
  badgeActif: false,
};

export async function chargerReglages(): Promise<Reglages> {
  const stocke = await chrome.storage.sync.get(REGLAGES_DEFAUT);
  return { ...REGLAGES_DEFAUT, ...stocke } as Reglages;
}

export async function enregistrerReglages(valeurs: Partial<Reglages>): Promise<void> {
  await chrome.storage.sync.set(valeurs);
}
