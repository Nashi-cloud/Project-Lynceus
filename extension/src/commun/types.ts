/** Types de la carte d'analyse — miroir de schema/carte-analyse.schema.json (source de vérité). */

export type Grade = "A" | "B" | "C" | "D" | "E";
export type Gravite = "faible" | "moyenne" | "haute";

export interface Dimension {
  score: number;
  detail: string;
}

export interface Technique {
  id: string;
  extrait: string;
  explication: string;
  gravite: Gravite;
}

export interface CarteAnalyse {
  version_schema: string;
  url?: string;
  titre?: string;
  domaine?: string;
  langue?: string;
  categorie: string;
  note: { grade: Grade; score: number; confiance: number };
  dimensions: Record<"sources" | "factualite" | "ton" | "transparence", Dimension>;
  techniques_detectees: Technique[];
  points_positifs: string[];
  questions_a_se_poser: string[];
  resume_neutre: string;
  avertissements?: string[];
  meta: {
    modele: string;
    fournisseur?: string;
    prompt_version: string;
    analyse_le: string;
    duree_ms?: number;
  };
}

export interface ReponseAnalyse {
  en_cache: boolean;
  carte: CarteAnalyse;
  detections_rejetees?: { id: string; raison: string }[];
}

export interface ProfilDomaine {
  domaine: string;
  nb_analyses: number;
  score_moyen: number;
  distribution_grades: Record<string, number>;
  maj_le: string;
}

export interface ReponseLookup {
  statut: "connue" | "inconnue";
  carte: CarteAnalyse | null;
  domaine: ProfilDomaine | null;
}

export interface DemandeAnalyse {
  url?: string;
  contenu_markdown?: string;
  titre?: string;
  langue?: string;
}

/** État d'analyse d'un onglet, tenu par le service worker, affiché par le panneau. */
export type EtatOnglet =
  | { phase: "repos" }
  | { phase: "extraction" }
  | { phase: "analyse" }
  | { phase: "ok"; carte: CarteAnalyse; enCache: boolean; rejetees: number }
  | { phase: "erreur"; erreur: string };

export type MessageVersFond =
  | { type: "lynceus:etat"; tabId: number }
  | { type: "lynceus:analyser"; tabId: number };

export interface MessageVersPanneau {
  type: "lynceus:maj";
  tabId: number;
  etat: EtatOnglet;
}

/** Résultat de l'extraction locale (Readability → Markdown) injectée dans la page. */
export type Extraction =
  | { ok: true; url: string; titre: string | null; markdown: string; langue: string | null }
  | { ok: false; erreur: string };
