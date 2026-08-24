/** Réglages Lynceus — la permission « tabs » n'est demandée QUE si le badge passif
 * est activé, et rendue si on le désactive (permissions minimales, charte §4). */

import { chargerReglages, enregistrerReglages } from "../commun/reglages";

const champInstance = document.getElementById("instance") as HTMLInputElement;
const caseBadge = document.getElementById("badge") as HTMLInputElement;
const zoneEtat = document.getElementById("etat") as HTMLElement;
const zoneInfos = document.getElementById("instance-infos") as HTMLElement;

// Les deux permissions sont demandées et retirées ensemble : le badge (connaître l'adresse
// en continu) et l'accès aux pages (poser/retirer le contour, fiabiliser le bouton Analyser
// après navigation) n'ont de sens que réunis — cf. l'explication dans options.html.
const DEMANDE_PERMISSION: chrome.permissions.Permissions = {
  permissions: ["tabs"],
  origins: ["http://*/*", "https://*/*"],
};

async function initialiser(): Promise<void> {
  const reglages = await chargerReglages();
  champInstance.value = reglages.instance;
  const permission = await chrome.permissions.contains(DEMANDE_PERMISSION);
  caseBadge.checked = reglages.badgeActif && permission;
}

caseBadge.addEventListener("change", async () => {
  if (caseBadge.checked) {
    const accorde = await chrome.permissions.request(DEMANDE_PERMISSION);
    if (!accorde) {
      caseBadge.checked = false;
      zoneEtat.textContent = "Permission refusée — badge et contour passifs restent désactivés.";
    }
  } else {
    await chrome.permissions.remove(DEMANDE_PERMISSION).catch(() => {});
  }
});

document.getElementById("enregistrer")?.addEventListener("click", async () => {
  const instance = champInstance.value.trim().replace(/\/+$/, "") || "http://localhost:8000";
  await enregistrerReglages({ instance, badgeActif: caseBadge.checked });
  zoneEtat.textContent = "Réglages enregistrés.";
  setTimeout(() => (zoneEtat.textContent = ""), 2500);
});

document.getElementById("tester")?.addEventListener("click", async () => {
  const instance = champInstance.value.trim().replace(/\/+$/, "") || "http://localhost:8000";
  zoneInfos.classList.remove("cache");
  zoneInfos.textContent = "Connexion…";
  try {
    const reponse = await fetch(`${instance}/v1/meta`);
    if (!reponse.ok) throw new Error(`HTTP ${reponse.status}`);
    const meta = (await reponse.json()) as {
      nom: string; version: string; prompt_version: string; modele: string;
      fournisseur: string; taxonomie?: { nb_techniques?: number };
    };
    zoneInfos.textContent =
      `✓ ${meta.nom} v${meta.version}\n` +
      `Modèle : ${meta.modele} (via ${meta.fournisseur})\n` +
      `Prompt d'analyse : v${meta.prompt_version} · ${meta.taxonomie?.nb_techniques ?? "?"} techniques au référentiel\n` +
      "Cette instance publie sa méthodologie — c'est le contrat de transparence Lynceus.";
  } catch (erreur) {
    zoneInfos.textContent =
      `✗ Instance injoignable (${erreur instanceof Error ? erreur.message : String(erreur)}). ` +
      "Le serveur est-il démarré ?";
  }
});

void initialiser();
