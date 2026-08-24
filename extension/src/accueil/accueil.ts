/** Page d'accueil affichée à l'installation — propose explicitement la reconnaissance
 * automatique plutôt que de la cacher dans les réglages. Chrome exige que
 * permissions.request() parte d'un clic réel : d'où le bouton, impossible d'automatiser. */

import { enregistrerReglages } from "../commun/reglages";

const DEMANDE_PERMISSION: chrome.permissions.Permissions = {
  permissions: ["tabs"],
  origins: ["http://*/*", "https://*/*"],
};

const zoneEtat = document.getElementById("etat") as HTMLElement;

document.getElementById("activer")?.addEventListener("click", async () => {
  const accorde = await chrome.permissions.request(DEMANDE_PERMISSION);
  await enregistrerReglages({ badgeActif: accorde });
  if (accorde) {
    zoneEtat.className = "ok";
    zoneEtat.textContent =
      "✓ Reconnaissance automatique activée. Vous pouvez fermer cet onglet et naviguer normalement.";
  } else {
    zoneEtat.className = "";
    zoneEtat.textContent =
      "Permission refusée — Lynceus reste utilisable via le clic droit. " +
      "Vous pourrez l'activer plus tard dans les réglages.";
  }
});

document.getElementById("plus-tard")?.addEventListener("click", async () => {
  await enregistrerReglages({ badgeActif: false });
  zoneEtat.className = "";
  zoneEtat.textContent =
    "Entendu — utilisez le clic droit → « Analyser cette page ». " +
    "La reconnaissance automatique reste disponible dans les réglages.";
});

document.getElementById("lien-reglages")?.addEventListener("click", (evenement) => {
  evenement.preventDefault();
  chrome.runtime.openOptionsPage();
});

const zoneVersion = document.getElementById("version") as HTMLElement;
zoneVersion.textContent = `Lynceus — extension v${chrome.runtime.getManifest().version}`;
