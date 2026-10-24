/** Mise à jour — dire qu'une version plus récente existe, sans rien installer.
 *
 * Une extension installée depuis l'archive du portail ne se met jamais à jour seule : elle
 * reste à sa version tant que la personne ne la remplace pas. Le panneau le lui dit, avec
 * le lien de téléchargement, quand le portail distribue une version plus récente.
 *
 * Une extension installée depuis un magasin n'est pas concernée : le navigateur la met à
 * jour lui-même, et lui proposer l'archive du portail l'inviterait à remplacer une
 * installation qui se tient à jour par une qui ne l'est pas.
 *
 * Ce que le portail renvoie est une donnée non fiable, comme dans l'inscription : la
 * version doit en avoir la forme, et le lien doit pointer vers le portail lui-même. Un
 * portail compromis ne doit pas pouvoir envoyer la personne télécharger ailleurs. */

import { chargerReglages } from "./reglages";
import { normaliserAdresse, portailParDefaut } from "./inscription";

export interface Annonce {
  version: string;
  telechargement: string;
}

/** Au plus une question au portail par jour : une version ne sort pas toutes les heures,
 * et chaque ouverture du panneau n'a pas à le faire savoir au portail. */
const INTERVALLE_MS = 24 * 60 * 60 * 1000;
const DELAI_MS = 10_000;
const CLE_CACHE = "miseAJour";
const CLE_FERMEE = "miseAJourFermee";

const MOTIF_VERSION = /^\d+\.\d+\.\d+$/;

/** Négatif si `a` précède `b`, positif s'il la suit, zéro si elles sont égales. Numérique
 * et non alphabétique : 0.11.10 suit 0.11.9. */
export function comparerVersions(a: string, b: string): number {
  const pa = a.split(".").map(Number);
  const pb = b.split(".").map(Number);
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const ecart = (pa[i] ?? 0) - (pb[i] ?? 0);
    if (ecart !== 0) return ecart;
  }
  return 0;
}

/** La réponse du portail, si elle a la forme attendue et renvoie chez lui ; sinon null. */
export function lireAnnonce(donnees: unknown, portail: string): Annonce | null {
  if (typeof donnees !== "object" || donnees === null) return null;
  const { version, telechargement } = donnees as Record<string, unknown>;
  if (typeof version !== "string" || !MOTIF_VERSION.test(version)) return null;
  if (typeof telechargement !== "string") return null;
  try {
    const lien = new URL(telechargement);
    if (lien.origin !== new URL(portail).origin) return null;
    if (lien.protocol !== "https:" && lien.protocol !== "http:") return null;
  } catch {
    return null;
  }
  return { version, telechargement };
}

/** Faut-il afficher l'avis ? Seulement pour une version plus récente que la sienne, et
 * pas pour une version dont la personne a déjà masqué l'avis. */
export function doitAnnoncer(locale: string, annonce: Annonce | null,
                             fermee: string | undefined): boolean {
  if (!annonce) return false;
  return comparerVersions(annonce.version, locale) > 0 && annonce.version !== fermee;
}

async function installeeDepuisUnMagasin(): Promise<boolean> {
  try {
    // `getSelf` ne demande pas la permission « management ».
    const soi = await chrome.management.getSelf();
    return soi.installType === "normal";
  } catch {
    return false;
  }
}

async function demanderAuPortail(portail: string): Promise<Annonce | null> {
  const controleur = new AbortController();
  const minuterie = setTimeout(() => controleur.abort(), DELAI_MS);
  try {
    const reponse = await fetch(`${portail}/v1/extension`, { signal: controleur.signal });
    if (!reponse.ok) return null;
    return lireAnnonce(await reponse.json(), portail);
  } catch {
    // Portail injoignable ou réponse illisible : on n'annonce rien, on ne signale rien.
    return null;
  } finally {
    clearTimeout(minuterie);
  }
}

/** L'annonce à afficher dans le panneau, ou null. Ne lève jamais : un portail absent ou
 * en panne ne doit rien changer à l'usage de l'extension. */
export async function verifierMiseAJour(maintenant = Date.now()): Promise<Annonce | null> {
  try {
    if (await installeeDepuisUnMagasin()) return null;
    const reglages = await chargerReglages();
    const brut = reglages.portail || (await portailParDefaut());
    if (!brut) return null;
    const portail = normaliserAdresse(brut);

    const stocke = await chrome.storage.local.get([CLE_CACHE, CLE_FERMEE]);
    const cache = stocke[CLE_CACHE] as
      { portail: string; verifieLe: number; annonce: Annonce | null } | undefined;
    let annonce: Annonce | null;
    if (cache && cache.portail === portail && maintenant - cache.verifieLe < INTERVALLE_MS) {
      annonce = cache.annonce;
    } else {
      annonce = await demanderAuPortail(portail);
      await chrome.storage.local.set({ [CLE_CACHE]: { portail, verifieLe: maintenant, annonce } });
    }
    const locale = chrome.runtime.getManifest().version;
    return doitAnnoncer(locale, annonce, stocke[CLE_FERMEE] as string | undefined) ? annonce : null;
  } catch {
    return null;
  }
}

/** Masquer l'avis pour cette version. Une version suivante sera de nouveau annoncée. */
export async function masquerAnnonce(version: string): Promise<void> {
  await chrome.storage.local.set({ [CLE_FERMEE]: version });
}
