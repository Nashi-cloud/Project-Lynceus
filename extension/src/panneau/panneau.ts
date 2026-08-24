/** Panneau latéral Lynceus — affiche l'état d'analyse de l'onglet actif.
 * Tout le rendu passe par textContent : aucun contenu de page ni de carte
 * n'est jamais interprété comme du HTML. */

import type { CarteAnalyse, EtatOnglet, MessageVersPanneau, Technique } from "../commun/types";

const CATEGORIES: Record<string, string> = {
  information: "Information",
  opinion: "Opinion",
  analyse_expertise: "Analyse / expertise",
  satire: "Satire — second degré",
  publicite_sponsorise: "Contenu commercial",
  temoignage: "Témoignage",
  contenu_confessionnel: "Contenu confessionnel",
  pseudo_science: "Pseudo-science",
  theorie_du_complot: "Théorie du complot",
  autre: "Autre",
};

const DIMENSIONS: [keyof CarteAnalyse["dimensions"], string][] = [
  ["sources", "Sources"],
  ["factualite", "Rigueur factuelle"],
  ["ton", "Ton et procédés"],
  ["transparence", "Transparence"],
];

const app = document.getElementById("app") as HTMLElement;
let ongletCourant: number | null = null;
let intervalleMinuteur: ReturnType<typeof setInterval> | undefined;

function arreterMinuteur(): void {
  if (intervalleMinuteur !== undefined) {
    clearInterval(intervalleMinuteur);
    intervalleMinuteur = undefined;
  }
}

function formaterDuree(ms: number): string {
  const secondes = Math.max(0, Math.floor(ms / 1000));
  const minutes = Math.floor(secondes / 60);
  return `${minutes}:${String(secondes % 60).padStart(2, "0")}`;
}

// ---------- fabrique DOM (sûre par construction) ----------

function el<K extends keyof HTMLElementTagNameMap>(
  balise: K,
  classe?: string,
  texte?: string,
): HTMLElementTagNameMap[K] {
  const noeud = document.createElement(balise);
  if (classe) noeud.className = classe;
  if (texte !== undefined) noeud.textContent = texte;
  return noeud;
}

function section(titre: string, ouvert: boolean, compteur?: string): [HTMLDetailsElement, HTMLDivElement] {
  const bloc = el("details");
  bloc.open = ouvert;
  const resume = el("summary", undefined, titre);
  if (compteur !== undefined) resume.append(el("span", "compteur", compteur));
  const contenu = el("div", "contenu-section");
  bloc.append(resume, contenu);
  return [bloc, contenu];
}

// ---------- rendus par phase ----------

function rendreRepos(): void {
  app.replaceChildren();
  const bloc = el("div", "bloc-centre");
  bloc.append(
    el("h2", undefined, "Analyser cette page ?"),
    el("div", undefined,
      "Lynceus lit le contenu, puis décrit les techniques de persuasion qu'il emploie " +
      "— avec extraits, explications et points positifs. À vous de conclure."),
  );
  const bouton = el("button", "bouton", "🔭 Analyser cette page");
  bouton.addEventListener("click", () => {
    if (ongletCourant !== null) {
      chrome.runtime.sendMessage({ type: "lynceus:analyser", tabId: ongletCourant }).catch(() => {});
    }
  });
  bloc.append(bouton, el("div", "note-vie-privee",
    "Rien n'est envoyé sans ce geste : le contenu de la page part vers votre instance Lynceus " +
    "uniquement quand vous demandez l'analyse."));
  app.append(bloc);
  void proposerReconnaissanceAuto(bloc);
}

/** Invitation discrète : sans la permission d'hôte, l'utilisateur ignore souvent que Lynceus
 * peut reconnaître seul les pages déjà analysées. On propose, on n'impose pas — et la demande
 * de permission part d'un clic, comme Chrome l'exige. */
async function proposerReconnaissanceAuto(bloc: HTMLElement): Promise<void> {
  const dejaAccorde = await chrome.permissions.contains({
    permissions: ["tabs"],
    origins: ["http://*/*", "https://*/*"],
  });
  if (dejaAccorde) return;

  const invitation = el("div", "invitation");
  invitation.append(el("div", undefined,
    "Lynceus peut aussi reconnaître seul les pages déjà analysées, et afficher leur note " +
    "sans que vous ayez à cliquer."));
  const lien = el("button", "lien-invitation", "Activer la reconnaissance automatique");
  lien.addEventListener("click", async () => {
    const accorde = await chrome.permissions.request({
      permissions: ["tabs"],
      origins: ["http://*/*", "https://*/*"],
    });
    if (accorde) {
      await chrome.storage.sync.set({ badgeActif: true });
      invitation.replaceChildren(el("div", undefined, "✓ Reconnaissance automatique activée."));
    }
  });
  invitation.append(lien);
  bloc.append(invitation);
}

function rendreAttente(phase: "extraction" | "analyse", depuis: number): void {
  app.replaceChildren();
  const bloc = el("div", "bloc-centre");
  bloc.append(el("div", "spinner"));
  bloc.append(el("div", undefined,
    phase === "extraction"
      ? "Extraction du contenu, localement dans votre navigateur…"
      : "Analyse en cours — le modèle lit la page…"));
  const minuteur = el("div", "minuteur", formaterDuree(Date.now() - depuis));
  bloc.append(minuteur);

  const boutonAnnuler = el("button", "bouton bouton-secondaire", "Annuler");
  boutonAnnuler.addEventListener("click", () => {
    if (ongletCourant !== null) {
      chrome.runtime.sendMessage({ type: "lynceus:annuler", tabId: ongletCourant }).catch(() => {});
    }
  });
  bloc.append(boutonAnnuler);
  app.append(bloc);

  intervalleMinuteur = setInterval(() => {
    minuteur.textContent = formaterDuree(Date.now() - depuis);
  }, 1000);
}

function rendreErreur(message: string): void {
  app.replaceChildren();
  const bloc = el("div", "erreur");
  bloc.append(el("strong", undefined, "Analyse impossible"), el("p", undefined, message));
  const bouton = el("button", "bouton", "Réessayer");
  bouton.addEventListener("click", rendreRepos);
  bloc.append(bouton);
  app.append(bloc);
}

function rendreCarte(carte: CarteAnalyse, enCache: boolean, rejetees: number): void {
  app.replaceChildren();

  // En-tête : la lecture en deux secondes
  const enTete = el("div", "resume-note");
  enTete.append(el("div", `pastille grade-${carte.note.grade}`, carte.note.grade));
  const infos = el("div", "infos");
  infos.append(el("div", "categorie", CATEGORIES[carte.categorie] ?? carte.categorie));
  infos.append(el("div", "sous-info",
    `Indice ${carte.note.score}/100 · confiance de l'analyse : ${Math.round(carte.note.confiance * 100)} %`));
  if (enCache) infos.append(el("div", "badge-cache", "Déjà dans l'annuaire — réponse instantanée"));
  enTete.append(infos);
  app.append(enTete);

  if (carte.titre) app.append(el("p", "titre-page", carte.titre));
  app.append(el("p", "resume-neutre", carte.resume_neutre));

  // Techniques — le cœur pédagogique, ouvert par défaut
  const techniques = carte.techniques_detectees;
  const [blocTech, contenuTech] = section("Techniques relevées", true, String(techniques.length));
  if (techniques.length === 0) {
    contenuTech.append(el("div", "aucune-technique", "✓ Aucune technique de manipulation relevée."));
  } else {
    for (const technique of techniques) contenuTech.append(rendreTechnique(technique));
  }
  app.append(blocTech);

  // Dimensions
  const [blocDim, contenuDim] = section("Le détail de l'indice", false);
  for (const [cle, etiquette] of DIMENSIONS) {
    const dimension = carte.dimensions[cle];
    const ligne = el("div", "dimension");
    const entete = el("div", "dimension-entete");
    entete.append(el("span", undefined, etiquette), el("span", undefined, `${dimension.score}/100`));
    const jauge = el("div", "jauge");
    const remplissage = el("div");
    remplissage.style.width = `${Math.max(0, Math.min(100, dimension.score))}%`;
    jauge.append(remplissage);
    ligne.append(entete, jauge, el("div", "detail", dimension.detail));
    contenuDim.append(ligne);
  }
  app.append(blocDim);

  // Points positifs — l'équité rend crédible
  const [blocPositifs, contenuPositifs] = section("Points positifs", false, String(carte.points_positifs.length));
  const listePositifs = el("ul");
  for (const point of carte.points_positifs) listePositifs.append(el("li", undefined, `✓ ${point}`));
  if (carte.points_positifs.length === 0) listePositifs.append(el("li", undefined, "—"));
  contenuPositifs.append(listePositifs);
  app.append(blocPositifs);

  // Questions à se poser — le lecteur reste l'enquêteur
  const [blocQuestions, contenuQuestions] = section("Questions à se poser", true);
  const listeQuestions = el("ul");
  for (const question of carte.questions_a_se_poser) listeQuestions.append(el("li", undefined, question));
  contenuQuestions.append(listeQuestions);
  app.append(blocQuestions);

  // Avertissements + transparence
  const avertissements = el("div", "avertissements");
  for (const avertissement of carte.avertissements ?? []) {
    avertissements.append(el("div", "avertissement", `⚠ ${avertissement}`));
  }
  if (rejetees > 0) {
    avertissements.append(el("div", "avertissement",
      `ℹ ${rejetees} détection(s) proposée(s) par le modèle ont été écartées par le serveur ` +
      "(citation introuvable dans la page ou hors référentiel)."));
  }
  app.append(avertissements);
  app.append(el("div", "meta",
    `${carte.meta.modele} · prompt v${carte.meta.prompt_version} · ${carte.meta.analyse_le.slice(0, 10)} · ` +
    "méthodologie et prompts publics (AGPL-3.0)"));
}

function rendreTechnique(technique: Technique): HTMLElement {
  const bloc = el("div", "technique");
  const entete = el("div", "technique-entete");
  const nom = technique.id.replace(/_/g, " ");
  entete.append(el("span", "technique-nom", nom.charAt(0).toUpperCase() + nom.slice(1)));
  entete.append(el("span", `gravite gravite-${technique.gravite}`, `gravité ${technique.gravite}`));
  bloc.append(entete);
  bloc.append(el("blockquote", "extrait", `« ${technique.extrait} »`));
  bloc.append(el("div", "explication", technique.explication));
  return bloc;
}

// ---------- orchestration ----------

function rendre(etat: EtatOnglet): void {
  arreterMinuteur(); // ne persiste que le temps d'un rendu "extraction"/"analyse"
  switch (etat.phase) {
    case "repos": rendreRepos(); break;
    case "extraction":
    case "analyse": rendreAttente(etat.phase, etat.depuis); break;
    case "ok": rendreCarte(etat.carte, etat.enCache, etat.rejetees); break;
    case "erreur": rendreErreur(etat.erreur); break;
  }
}

async function rafraichir(): Promise<void> {
  const [onglet] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!onglet?.id) return;
  ongletCourant = onglet.id;
  try {
    const etat = (await chrome.runtime.sendMessage({ type: "lynceus:etat", tabId: onglet.id })) as EtatOnglet;
    rendre(etat ?? { phase: "repos" });
  } catch {
    rendre({ phase: "repos" });
  }
}

chrome.runtime.onMessage.addListener((message: MessageVersPanneau) => {
  if (message.type === "lynceus:maj" && message.tabId === ongletCourant) rendre(message.etat);
});

chrome.tabs.onActivated.addListener(() => void rafraichir());

document.getElementById("lien-options")?.addEventListener("click", (evenement) => {
  evenement.preventDefault();
  chrome.runtime.openOptionsPage();
});

void rafraichir();
