/** Panneau latéral Lynceus — affiche l'état d'analyse de l'onglet actif.
 * Tout le rendu passe par textContent : aucun contenu de page ni de carte
 * n'est jamais interprété comme du HTML. */

import { msg, traduireDocument } from "../commun/i18n";
import type {
  CarteAnalyse,
  CorrespondancePrefixe,
  EtatOnglet,
  MessageVersPanneau,
  ProfilDomaine,
  Technique,
} from "../commun/types";

// Les ids de catégorie et de dimension viennent du serveur et ne se traduisent pas : ce
// sont des identifiants. Seul leur libellé change de langue, d'où la clé construite.
const CATEGORIES = ["information", "opinion", "analyse_expertise", "satire",
                    "publicite_sponsorise", "temoignage", "contenu_confessionnel",
                    "pseudo_science", "theorie_du_complot", "autre"] as const;

const libelleCategorie = (id: string): string =>
  CATEGORIES.includes(id as (typeof CATEGORIES)[number]) ? msg(`categorie_${id}`) : id;

const DIMENSIONS: (keyof CarteAnalyse["dimensions"])[] =
  ["sources", "factualite", "ton", "transparence"];

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

/** Grade correspondant à un score, selon le même barème que le serveur
 * (docs/METHODOLOGIE.md §5). Sert uniquement à colorer le profil d'un domaine. */
function gradeDuScore(score: number): string {
  if (score >= 80) return "A";
  if (score >= 65) return "B";
  if (score >= 50) return "C";
  if (score >= 30) return "D";
  return "E";
}

/** Profil du domaine, affiché sur une page pas encore analysée.
 *
 * Formulation prudente et volontaire : on décrit ce que l'annuaire sait DU SITE, jamais ce
 * que vaut LA page — elle n'a pas été lue. Préjuger d'un article à partir de son domaine
 * serait exactement le raccourci que Lynceus cherche à défaire. */
function rendreProfilDomaine(profil: ProfilDomaine): HTMLElement {
  const bloc = el("div", "profil-domaine");
  const moyenne = Math.round(profil.score_moyen);
  const grade = gradeDuScore(moyenne);

  const entete = el("div", "profil-entete");
  entete.append(el("span", `pastille-mini grade-${grade}`, grade));
  // Compte en fin de phrase plutôt qu'accordé : les règles d'accord en nombre diffèrent
  // d'une langue à l'autre, et un libellé suivi de son compte se traduit partout.
  entete.append(el("span", undefined,
    msg("panneau_profil_pages", profil.domaine, String(profil.nb_analyses))));
  bloc.append(entete);

  bloc.append(el("div", "profil-detail", msg("panneau_profil_moyenne", String(moyenne))));

  const distribution = Object.entries(profil.distribution_grades ?? {}).sort();
  if (distribution.length > 1) {
    bloc.append(el("div", "profil-detail",
      msg("panneau_profil_repartition",
          distribution.map(([g, n]) => `${n} × ${g}`).join(", "))));
  }

  bloc.append(el("div", "profil-avertissement", msg("panneau_profil_avertissement")));
  return bloc;
}

function rendreRepos(domaine?: ProfilDomaine): void {
  app.replaceChildren();
  const bloc = el("div", "bloc-centre");
  bloc.append(
    el("h2", undefined, msg("panneau_repos_titre")),
    el("div", undefined, msg("panneau_repos_texte")),
  );
  const bouton = el("button", "bouton", msg("panneau_analyser"));
  bouton.addEventListener("click", () => {
    if (ongletCourant !== null) {
      chrome.runtime.sendMessage({ type: "lynceus:analyser", tabId: ongletCourant }).catch(() => {});
    }
  });
  bloc.append(bouton, el("div", "note-vie-privee", msg("panneau_repos_vie_privee")));
  app.append(bloc);
  if (domaine) app.append(rendreProfilDomaine(domaine));
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
  invitation.append(el("div", undefined, msg("panneau_reconnaissance_texte")));
  const lien = el("button", "lien-invitation", msg("panneau_reconnaissance_activer"));
  lien.addEventListener("click", async () => {
    const accorde = await chrome.permissions.request({
      permissions: ["tabs"],
      origins: ["http://*/*", "https://*/*"],
    });
    if (accorde) {
      await chrome.storage.sync.set({ badgeActif: true });
      invitation.replaceChildren(el("div", undefined, msg("panneau_reconnaissance_activee")));
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
    msg(phase === "extraction" ? "panneau_attente_extraction" : "panneau_attente_analyse")));
  const minuteur = el("div", "minuteur", formaterDuree(Date.now() - depuis));
  bloc.append(minuteur);

  const boutonAnnuler = el("button", "bouton bouton-secondaire", msg("annuler"));
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
  bloc.append(el("strong", undefined, msg("panneau_erreur_titre")), el("p", undefined, message));
  const bouton = el("button", "bouton", msg("reessayer"));
  // () => : sans cela, l'événement de clic serait passé comme profil de domaine.
  bouton.addEventListener("click", () => rendreRepos());
  bloc.append(bouton);
  app.append(bloc);
}

/** Page reconnue par le lookup k-anonyme : on affiche la note tout de suite et on demande
 * le détail, qui n'avait pas été chargé tant qu'un badge suffisait. */
function rendreResume(resume: CorrespondancePrefixe): void {
  app.replaceChildren();

  const enTete = el("div", "resume-note");
  enTete.append(el("div", `pastille grade-${resume.grade}`, resume.grade));
  const infos = el("div", "infos");
  infos.append(el("div", "categorie", libelleCategorie(resume.categorie)));
  infos.append(el("div", "sous-info", msg("panneau_indice", String(resume.score))));
  infos.append(el("div", "badge-cache", msg("panneau_deja_annuaire")));
  enTete.append(infos);
  app.append(enTete);

  const attente = el("div", "bloc-centre");
  attente.append(el("div", "spinner"), el("div", undefined, msg("panneau_chargement_detail")));
  app.append(attente);

  if (ongletCourant !== null) {
    chrome.runtime
      .sendMessage({ type: "lynceus:detailler", tabId: ongletCourant, analyseId: resume.analyse_id })
      .catch(() => {});
  }
}

function rendreCarte(
  carte: CarteAnalyse,
  enCache: boolean,
  rejetees: number,
  signalements = 0,
): void {
  app.replaceChildren();

  // En-tête : la lecture en deux secondes
  const enTete = el("div", "resume-note");
  enTete.append(el("div", `pastille grade-${carte.note.grade}`, carte.note.grade));
  const infos = el("div", "infos");
  infos.append(el("div", "categorie", libelleCategorie(carte.categorie)));
  infos.append(el("div", "sous-info",
    msg("panneau_indice_confiance", String(carte.note.score),
        String(Math.round(carte.note.confiance * 100)))));
  if (enCache) infos.append(el("div", "badge-cache", msg("panneau_deja_annuaire_cache")));
  enTete.append(infos);
  app.append(enTete);

  if (carte.titre) app.append(el("p", "titre-page", carte.titre));
  app.append(el("p", "resume-neutre", carte.resume_neutre));

  // Techniques — le cœur pédagogique, ouvert par défaut
  const techniques = carte.techniques_detectees;
  const [blocTech, contenuTech] = section(msg("panneau_techniques"), true, String(techniques.length));
  if (techniques.length === 0) {
    contenuTech.append(el("div", "aucune-technique", msg("panneau_aucune_technique")));
  } else {
    for (const technique of techniques) contenuTech.append(rendreTechnique(technique));
  }
  app.append(blocTech);

  // Dimensions
  const [blocDim, contenuDim] = section(msg("panneau_detail_indice"), false);
  for (const cle of DIMENSIONS) {
    const dimension = carte.dimensions[cle];
    const ligne = el("div", "dimension");
    const entete = el("div", "dimension-entete");
    entete.append(el("span", undefined, msg(`dimension_${cle}`)),
                  el("span", undefined, `${dimension.score}/100`));
    const jauge = el("div", "jauge");
    const remplissage = el("div");
    remplissage.style.width = `${Math.max(0, Math.min(100, dimension.score))}%`;
    jauge.append(remplissage);
    ligne.append(entete, jauge, el("div", "detail", dimension.detail));
    contenuDim.append(ligne);
  }
  app.append(blocDim);

  // Points positifs — l'équité rend crédible
  const [blocPositifs, contenuPositifs] =
    section(msg("points_positifs"), false, String(carte.points_positifs.length));
  const listePositifs = el("ul");
  for (const point of carte.points_positifs) listePositifs.append(el("li", undefined, `✓ ${point}`));
  if (carte.points_positifs.length === 0) listePositifs.append(el("li", undefined, msg("panneau_aucun_point_positif")));
  contenuPositifs.append(listePositifs);
  app.append(blocPositifs);

  // Questions à se poser — le lecteur reste l'enquêteur
  const [blocQuestions, contenuQuestions] = section(msg("panneau_questions"), true);
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
      `ℹ ${msg("panneau_detections_ecartees", String(rejetees))}`));
  }
  app.append(avertissements);
  app.append(el("div", "meta",
    `${carte.meta.modele} · prompt v${carte.meta.prompt_version} · ` +
    `${carte.meta.analyse_le.slice(0, 10)} · ${msg("panneau_meta_publics")}`));

  app.append(rendreContestation(carte, signalements));
}

// Les valeurs sont des identifiants attendus par l'instance : seul le libellé se traduit.
const MOTIFS = ["analyse_erronee", "extrait_hors_contexte", "categorie_erronee",
                "note_injustifiee", "page_modifiee", "droit_de_reponse", "autre"];

/** Contester une analyse — charte §6 : toute analyse est faillible et contestable, y compris
 * par l'éditeur du site analysé. Le lien reste discret : c'est un recours, pas une invitation
 * à rejeter ce qui déplaît. */
function rendreContestation(carte: CarteAnalyse, signalements: number): HTMLElement {
  const bloc = el("div", "contestation");
  if (signalements > 0) {
    bloc.append(el("div", "signalements-info",
      `${signalements} contestation(s) déjà enregistrée(s) sur cette analyse.`));
  }

  const lien = el("button", "lien-invitation", msg("contester_cette_analyse"));
  bloc.append(lien);

  const analyseId = extraireIdAnalyse(carte);
  lien.addEventListener("click", () => {
    if (analyseId === null) {
      bloc.replaceChildren(el("div", "signalements-info", msg("panneau_contestation_impossible")));
      return;
    }
    bloc.replaceChildren(construireFormulaire(analyseId, bloc));
  });
  return bloc;
}

function construireFormulaire(analyseId: number, bloc: HTMLElement): HTMLElement {
  const formulaire = el("div", "formulaire");
  formulaire.append(el("div", "formulaire-titre", msg("panneau_formulaire_titre")));

  const selection = document.createElement("select");
  selection.className = "champ";
  for (const valeur of MOTIFS) {
    const option = document.createElement("option");
    option.value = valeur;
    option.textContent = msg(`motif_${valeur}`);
    selection.append(option);
  }
  formulaire.append(selection);

  const zone = document.createElement("textarea");
  zone.className = "champ";
  zone.rows = 4;
  zone.placeholder = msg("panneau_formulaire_invite");
  formulaire.append(zone);

  const envoyer = el("button", "bouton", msg("envoyer"));
  const annuler = el("button", "bouton bouton-secondaire", msg("annuler"));
  const etat = el("div", "signalements-info");

  envoyer.addEventListener("click", () => {
    const message = zone.value.trim();
    if (message.length < 10) {
      etat.textContent = msg("panneau_formulaire_trop_court");
      return;
    }
    envoyer.setAttribute("disabled", "true");
    etat.textContent = msg("envoi_en_cours");
    chrome.runtime
      .sendMessage({ type: "lynceus:signaler", analyseId, motif: selection.value, message })
      .then((reponse: { ok: boolean; message: string }) => {
        bloc.replaceChildren(el("div", "signalements-info",
          reponse?.ok ? reponse.message
                      : msg("envoi_echec_detail", reponse?.message ?? msg("erreur_inconnue"))));
      })
      .catch(() => {
        envoyer.removeAttribute("disabled");
        etat.textContent = msg("envoi_echec");
      });
  });
  annuler.addEventListener("click", () => bloc.replaceChildren(rendreContestation({} as CarteAnalyse, 0)));

  formulaire.append(envoyer, annuler, etat);
  return formulaire;
}

/** L'identifiant d'analyse n'est pas dans la carte : il vient du lookup. On le mémorise
 * lors du rendu pour permettre la contestation. */
let idAnalyseCourante: number | null = null;

function extraireIdAnalyse(_carte: CarteAnalyse): number | null {
  return idAnalyseCourante;
}

function rendreTechnique(technique: Technique): HTMLElement {
  const bloc = el("div", "technique");
  const entete = el("div", "technique-entete");
  const nom = technique.id.replace(/_/g, " ");
  entete.append(el("span", "technique-nom", nom.charAt(0).toUpperCase() + nom.slice(1)));
  entete.append(el("span", `gravite gravite-${technique.gravite}`,
                    msg(`gravite_${technique.gravite}`)));
  bloc.append(entete);
  bloc.append(el("blockquote", "extrait", `« ${technique.extrait} »`));
  bloc.append(el("div", "explication", technique.explication));
  return bloc;
}

// ---------- orchestration ----------

function rendre(etat: EtatOnglet): void {
  arreterMinuteur(); // ne persiste que le temps d'un rendu "extraction"/"analyse"
  switch (etat.phase) {
    case "repos": idAnalyseCourante = null; rendreRepos(etat.domaine); break;
    case "extraction":
    case "analyse": rendreAttente(etat.phase, etat.depuis); break;
    case "resume": idAnalyseCourante = etat.resume.analyse_id; rendreResume(etat.resume); break;
    case "ok": rendreCarte(etat.carte, etat.enCache, etat.rejetees, etat.signalements ?? 0); break;
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

traduireDocument();
void rafraichir();
