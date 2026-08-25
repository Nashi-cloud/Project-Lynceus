/** Réglages de l'extension — chrome.storage.sync. Badge passif DÉSACTIVÉ par défaut :
 * la vie privée est le réglage d'usine (docs/ETHIQUE.md §3-4). */

export interface Reglages {
  instance: string;
  badgeActif: boolean;
  /** Filet de sécurité réseau (secondes) : au-delà, une analyse est abandonnée automatiquement.
   * Un chronomètre et un bouton « Annuler » restent disponibles dans le panneau en attendant —
   * ce délai n'est qu'un dernier recours contre une connexion réellement bloquée. Le serveur a
   * son propre plafond (LYNCEUS_LLM_TIMEOUT_S, 180 s par défaut, jusqu'à 360 s avec un retry) :
   * garder cette valeur nettement au-dessus pour ne jamais couper une analyse légitime en cours. */
  delaiAnalyseS: number;
  /** Portail auprès duquel demander une clé. Ce n'est pas l'instance : le portail
   * distribue les clés, l'instance analyse. Un même portail peut servir plusieurs
   * instances, et un auto-hébergeur n'en a besoin d'aucun. */
  portail: string;
  /** Clé d'accès, si l'instance en exige une. Elle n'est ni un identifiant ni un compte :
   * elle porte seulement une date d'expiration et un quota, et ne dit rien de son porteur. */
  cle: string;
}

export const REGLAGES_DEFAUT: Reglages = {
  instance: "http://localhost:8000",
  badgeActif: false,
  delaiAnalyseS: 300,
  portail: "",
  cle: "",
};

export async function chargerReglages(): Promise<Reglages> {
  const stocke = await chrome.storage.sync.get(REGLAGES_DEFAUT);
  return { ...REGLAGES_DEFAUT, ...stocke } as Reglages;
}

export async function enregistrerReglages(valeurs: Partial<Reglages>): Promise<void> {
  await chrome.storage.sync.set(valeurs);
}
