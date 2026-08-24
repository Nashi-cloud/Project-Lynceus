/** Normalisation d'URL et hachage — MIROIR EXACT de api/lynceus/normalisation.py.
 * Les deux implémentations doivent produire le même hash pour que le lookup
 * de l'annuaire fonctionne (testé par test/parite_normalisation.mjs). */

const PREFIXES_TRACKING = ["utm_"];
const PARAMS_TRACKING = new Set([
  "fbclid", "gclid", "gclsrc", "dclid", "msclkid", "twclid", "yclid",
  "igshid", "mc_cid", "mc_eid", "_hsenc", "_hsmi", "wt_mc",
]);

function estTracking(nom: string): boolean {
  const minuscule = nom.toLowerCase();
  return PREFIXES_TRACKING.some((p) => minuscule.startsWith(p)) || PARAMS_TRACKING.has(minuscule);
}

export function normaliserUrl(brute: string): string {
  const u = new URL(brute.trim());
  const schema = u.protocol.replace(/:$/, "").toLowerCase();
  if (schema !== "http" && schema !== "https") {
    throw new Error(`URL non supportée (http/https attendu) : ${brute}`);
  }

  let hote = u.hostname.toLowerCase();
  if (!hote) throw new Error(`URL sans hôte : ${brute}`);
  const port = u.port; // vide si port par défaut
  if (port && !(schema === "http" && port === "80") && !(schema === "https" && port === "443")) {
    hote = `${hote}:${port}`;
  }

  let chemin = u.pathname || "/";
  if (chemin.length > 1) chemin = chemin.replace(/\/+$/, "") || "/";

  const params: [string, string][] = [];
  u.searchParams.forEach((valeur, nom) => {
    if (!estTracking(nom)) params.push([nom, valeur]);
  });
  params.sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0));
  const requete = new URLSearchParams(params).toString();

  return `${schema}://${hote}${chemin}${requete ? "?" + requete : ""}`;
}

export async function hacherUrl(brute: string): Promise<string> {
  const donnees = new TextEncoder().encode(normaliserUrl(brute));
  const empreinte = await crypto.subtle.digest("SHA-256", donnees);
  return [...new Uint8Array(empreinte)].map((o) => o.toString(16).padStart(2, "0")).join("");
}
