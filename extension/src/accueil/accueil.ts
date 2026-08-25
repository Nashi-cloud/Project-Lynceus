/** Page d'accueil affichée à l'installation — propose explicitement la reconnaissance
 * automatique plutôt que de la cacher dans les réglages. Chrome exige que
 * permissions.request() parte d'un clic réel : d'où le bouton, impossible d'automatiser. */

import { chargerReglages, enregistrerReglages } from "../commun/reglages";
import {
  appliquerBillet,
  demanderCle,
  PORTAIL_DEFAUT,
  resumerBillet,
} from "../commun/inscription";

const DEMANDE_PERMISSION: chrome.permissions.Permissions = {
  permissions: ["tabs"],
  origins: ["http://*/*", "https://*/*"],
};

const zoneEtat = document.getElementById("etat") as HTMLElement;
const champPortail = document.getElementById("portail") as HTMLInputElement;
const boutonCle = document.getElementById("obtenir-cle") as HTMLButtonElement;
const etatInscription = document.getElementById("etat-inscription") as HTMLElement;

void (async () => {
  const reglages = await chargerReglages();
  champPortail.value = reglages.portail || PORTAIL_DEFAUT;
  if (reglages.cle) {
    etatInscription.textContent =
      "Une clé est déjà enregistrée. En demander une nouvelle remplacera l'actuelle.";
  }
})();

boutonCle.addEventListener("click", async () => {
  boutonCle.disabled = true;
  etatInscription.className = "";
  etatInscription.textContent = "Demande en cours…";
  try {
    const billet = await demanderCle(champPortail.value);
    await appliquerBillet(billet);
    await enregistrerReglages({ portail: champPortail.value.trim().replace(/\/+$/, "") });
    etatInscription.className = "ok";
    // On montre ce qui vient d'être configuré : c'est le portail qui a choisi l'instance
    // vers laquelle partiront désormais les pages analysées, pas l'utilisateur.
    etatInscription.textContent = `✓ Clé obtenue. ${resumerBillet(billet)}`;
  } catch (erreur) {
    etatInscription.className = "";
    etatInscription.textContent =
      erreur instanceof Error ? erreur.message : "L'inscription a échoué.";
  } finally {
    boutonCle.disabled = false;
  }
});

document.getElementById("deja-instance")?.addEventListener("click", (evenement) => {
  evenement.preventDefault();
  chrome.runtime.openOptionsPage();
});

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
