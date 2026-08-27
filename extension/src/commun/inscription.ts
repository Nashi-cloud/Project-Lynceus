/** Inscription — obtenir une clé d'accès auprès d'un portail, en un clic.
 *
 * Le portail est un service distinct de l'instance : lui seul détient la clé privée qui
 * signe les clés. L'extension ne signe rien et ne pourrait pas le faire — mettre cette
 * clé privée ici reviendrait à la publier.
 *
 * Ce que le portail renvoie est traité comme une donnée non fiable : c'est lui qui décide
 * de l'instance vers laquelle l'extension enverra désormais le contenu des pages. On
 * vérifie donc la forme de sa réponse, et l'interface affiche ce qui a été configuré
 * plutôt que de l'appliquer en silence. */

import { enregistrerReglages } from "./reglages";
import { msg } from "./i18n";

/** Portail inscrit à la compilation (`node build.mjs --portail=…`). Utile pour un paquet
 * qu'on construit soi-même ; vide dans l'archive publiée, qui doit rester valable pour
 * n'importe quel portail. */
declare const PORTAIL_PAR_DEFAUT: string;

const PORTAIL_COMPILE: string =
  typeof PORTAIL_PAR_DEFAUT === "string" ? PORTAIL_PAR_DEFAUT : "";

/** Fichier ajouté à l'archive par le portail qui l'a servie. Il ne contient que son
 * adresse : c'est ce qui permet de publier une seule image pour tous les portails, tout
 * en évitant à chaque utilisateur de recopier une adresse à la main. */
const FICHIER_PORTAIL = "portail.json";

/** Portail à proposer dans l'interface, dans l'ordre : celui inscrit à la compilation,
 * puis celui écrit dans l'archive au téléchargement. Vide si l'extension a été construite
 * localement, auquel cas l'utilisateur saisit l'adresse lui-même. */
export async function portailParDefaut(): Promise<string> {
  if (PORTAIL_COMPILE) return PORTAIL_COMPILE;
  const url = globalThis.chrome?.runtime?.getURL?.(FICHIER_PORTAIL);
  if (!url) return "";
  try {
    const reponse = await fetch(url);
    if (!reponse.ok) return "";
    const donnees = (await reponse.json()) as { portail?: unknown };
    // Le fichier vient d'un serveur : on le valide comme n'importe quelle donnée reçue.
    return typeof donnees?.portail === "string" ? normaliserAdresse(donnees.portail) : "";
  } catch {
    // Archive construite sans portail, ou fichier illisible : on n'en propose aucun.
    return "";
  }
}

export interface Billet {
  instance: string;
  cle: string;
  quota_jour: number;
  expire_le: string;
  portail: string;
}

const DELAI_MS = 20_000;

export function normaliserAdresse(adresse: string): string {
  const propre = adresse.trim().replace(/\/+$/, "");
  if (!propre) throw new Error(msg("erreur_adresse_vide"));
  let analysee: URL;
  try {
    analysee = new URL(propre);
  } catch {
    throw new Error(msg("erreur_adresse_invalide", propre));
  }
  if (analysee.protocol !== "https:" && analysee.protocol !== "http:") {
    throw new Error(msg("erreur_adresse_schema"));
  }
  return propre;
}

function verifierBillet(donnees: unknown): Billet {
  const b = donnees as Partial<Billet>;
  if (typeof b?.cle !== "string" || !b.cle.startsWith("LYNC1.")) {
    throw new Error(msg("erreur_billet_invalide"));
  }
  // L'instance décide où partira le contenu des pages analysées : une valeur inattendue
  // ici enverrait le texte lu ailleurs que là où l'utilisateur croit.
  const instance = normaliserAdresse(String(b.instance ?? ""));
  return {
    instance,
    cle: b.cle,
    quota_jour: Number(b.quota_jour) || 0,
    expire_le: String(b.expire_le ?? ""),
    portail: String(b.portail ?? instance),
  };
}

/** Demande une clé au portail. Ne touche pas aux réglages : c'est `appliquerBillet` qui
 * les modifie, une fois que l'appelant a pu montrer ce qui allait être configuré. */
export async function demanderCle(adressePortail: string): Promise<Billet> {
  const portail = normaliserAdresse(adressePortail);
  const controleur = new AbortController();
  const minuteur = setTimeout(() => controleur.abort(), DELAI_MS);
  let reponse: Response;
  try {
    reponse = await fetch(`${portail}/v1/inscription`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: controleur.signal,
    });
  } catch {
    throw new Error(msg("erreur_portail_injoignable", portail));
  } finally {
    clearTimeout(minuteur);
  }

  if (!reponse.ok) {
    let detail = `HTTP ${reponse.status}`;
    try {
      const corps = (await reponse.json()) as { detail?: string };
      if (typeof corps?.detail === "string") detail = corps.detail;
    } catch {
      /* réponse non JSON : on garde le code HTTP, seule information sûre */
    }
    throw new Error(detail);
  }
  return verifierBillet(await reponse.json());
}

export async function appliquerBillet(billet: Billet): Promise<void> {
  await enregistrerReglages({ instance: billet.instance, cle: billet.cle });
}

export function resumerBillet(billet: Billet): string {
  const quota = billet.quota_jour > 0
    ? msg("billet_quota", String(billet.quota_jour))
    : msg("billet_quota_inconnu");
  const echeance = billet.expire_le
    ? msg("billet_echeance", billet.expire_le)
    : msg("billet_echeance_inconnue");
  return msg("billet_resume", billet.instance, echeance, quota);
}
