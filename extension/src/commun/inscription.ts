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

/** Portail proposé par défaut. Injecté à la compilation (`node build.mjs --portail=…`)
 * pour qu'un paquet distribué par un portail arrive déjà configuré ; vide sinon. */
declare const PORTAIL_PAR_DEFAUT: string;

export const PORTAIL_DEFAUT: string =
  typeof PORTAIL_PAR_DEFAUT === "string" ? PORTAIL_PAR_DEFAUT : "";

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
  if (!propre) throw new Error("Indiquez l'adresse du portail (https://…).");
  let analysee: URL;
  try {
    analysee = new URL(propre);
  } catch {
    throw new Error(`« ${propre} » n'est pas une adresse valide.`);
  }
  if (analysee.protocol !== "https:" && analysee.protocol !== "http:") {
    throw new Error("Seules les adresses http(s) sont acceptées.");
  }
  return propre;
}

function verifierBillet(donnees: unknown): Billet {
  const b = donnees as Partial<Billet>;
  if (typeof b?.cle !== "string" || !b.cle.startsWith("LYNC1.")) {
    throw new Error("Ce portail n'a pas renvoyé de clé exploitable.");
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
    throw new Error(
      `Portail injoignable (${portail}). Vérifiez l'adresse et votre connexion.`,
    );
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
  const quota = billet.quota_jour > 0 ? `${billet.quota_jour} analyses par jour` : "quota non précisé";
  const echeance = billet.expire_le ? `valable jusqu'au ${billet.expire_le}` : "sans échéance annoncée";
  return `Instance : ${billet.instance} · clé ${echeance} · ${quota}.`;
}
