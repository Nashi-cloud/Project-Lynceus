/** Réglages Lynceus — la permission « tabs » n'est demandée QUE si le badge passif
 * est activé, et rendue si on le désactive (permissions minimales, charte §4). */

import { chargerReglages, enregistrerReglages } from "../commun/reglages";
import {
  appliquerBillet,
  demanderCle,
  portailParDefaut,
  resumerBillet,
} from "../commun/inscription";

const champInstance = document.getElementById("instance") as HTMLInputElement;
const champDelai = document.getElementById("delai") as HTMLInputElement;
const champCle = document.getElementById("cle") as HTMLInputElement;
const champPortail = document.getElementById("portail") as HTMLInputElement;
const zoneInscription = document.getElementById("etat-inscription") as HTMLElement;
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
  champDelai.value = String(reglages.delaiAnalyseS);
  champCle.value = reglages.cle;
  champPortail.value = reglages.portail || (await portailParDefaut());
  const permission = await chrome.permissions.contains(DEMANDE_PERMISSION);
  caseBadge.checked = reglages.badgeActif && permission;
}

caseBadge.addEventListener("change", async () => {
  if (caseBadge.checked) {
    const accorde = await chrome.permissions.request(DEMANDE_PERMISSION);
    if (!accorde) {
      caseBadge.checked = false;
      zoneEtat.textContent = "Permission refusée. Badge et contour passifs restent désactivés.";
    }
  } else {
    await chrome.permissions.remove(DEMANDE_PERMISSION).catch(() => {});
  }
});

document.getElementById("enregistrer")?.addEventListener("click", async () => {
  const instance = champInstance.value.trim().replace(/\/+$/, "") || "http://localhost:8000";
  const delaiAnalyseS = Math.min(1800, Math.max(30, Number(champDelai.value) || 300));
  champDelai.value = String(delaiAnalyseS);
  await enregistrerReglages({
    instance,
    badgeActif: caseBadge.checked,
    delaiAnalyseS,
    portail: champPortail.value.trim().replace(/\/+$/, ""),
    cle: champCle.value.trim(),
  });
  zoneEtat.textContent = "Réglages enregistrés.";
  setTimeout(() => (zoneEtat.textContent = ""), 2500);
});

document.getElementById("obtenir-cle")?.addEventListener("click", async (evenement) => {
  const bouton = evenement.currentTarget as HTMLButtonElement;
  bouton.disabled = true;
  zoneInscription.classList.remove("cache");
  zoneInscription.textContent = "Demande en cours…";
  try {
    const billet = await demanderCle(champPortail.value);
    await appliquerBillet(billet);
    await enregistrerReglages({ portail: champPortail.value.trim().replace(/\/+$/, "") });
    // Les champs sont mis à jour avec ce qui a réellement été enregistré : l'instance
    // vient du portail, et l'utilisateur doit la voir plutôt que de la découvrir plus tard.
    champInstance.value = billet.instance;
    champCle.value = billet.cle;
    zoneInscription.textContent = `✓ Clé obtenue. ${resumerBillet(billet)}`;
  } catch (erreur) {
    zoneInscription.textContent =
      erreur instanceof Error ? erreur.message : "L'inscription a échoué.";
  } finally {
    bouton.disabled = false;
  }
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
      capacites?: { cle_requise?: boolean };
    };
    const cleRequise = meta.capacites?.cle_requise === true;
    zoneInfos.textContent =
      `✓ ${meta.nom} v${meta.version}\n` +
      // « via » supposait un fournisseur extérieur. Une instance peut annoncer un
      // modèle auto-hébergé, et « via modèle auto-hébergé » ne veut rien dire.
      `Modèle : ${meta.modele} · ${meta.fournisseur}\n` +
      `Prompt d'analyse : v${meta.prompt_version} · ${meta.taxonomie?.nb_techniques ?? "?"} techniques au référentiel\n` +
      (cleRequise
        ? "Cette instance demande une clé d'accès pour les analyses.\n"
        : "Cette instance n'exige aucune clé.\n") +
      "Elle publie sa méthodologie : c'est le contrat de transparence Lynceus.";
  } catch (erreur) {
    zoneInfos.textContent =
      `✗ Instance injoignable (${erreur instanceof Error ? erreur.message : String(erreur)}). ` +
      "Le serveur est-il démarré ?";
  }
});

const zoneVersion = document.getElementById("version") as HTMLElement;
zoneVersion.textContent = `Lynceus, extension v${chrome.runtime.getManifest().version}`;

void initialiser();
