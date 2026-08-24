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

/** Capacités annoncées par l'instance (/v1/meta) — permet de ne pas coder en dur ce que
 * le serveur sait faire, et de rester compatible avec des instances plus anciennes. */
export interface MetaInstance {
  version: string;
  prompt_version: string;
  modele: string;
  fournisseur?: string;
  capacites?: {
    lookup_k_anonyme?: boolean;
    longueur_prefixe?: number;
    signalements?: boolean;
    motifs_signalement?: string[];
  };
  limites?: {
    contenu_max_cars?: number;
    analyses_par_minute?: number;
  };
}

export interface ProfilDomaine {
  domaine: string;
  nb_analyses: number;
  score_moyen: number;
  distribution_grades: Record<string, number>;
  maj_le: string;
}

export interface CorrespondancePrefixe {
  suffixe: string;
  analyse_id: number;
  grade: Grade;
  categorie: string;
  score: number;
}

export interface ReponseLookupPrefixe {
  prefixe: string;
  correspondances: CorrespondancePrefixe[];
}

export interface DemandeSignalement {
  analyse_id: number;
  motif: string;
  message: string;
  contact?: string;
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
  /** Le contenu a été raccourci pour tenir dans la limite de l'instance. La carte en
   * portera la mention : elle est mise en cache et resservie à d'autres lecteurs. */
  tronque?: boolean;
}

/** État d'analyse d'un onglet, tenu par le service worker, affiché par le panneau. */
export type EtatOnglet =
  /** Page non analysée. Le profil du domaine, quand il est connu, informe déjà
   * l'utilisateur sans rien coûter : « 5 pages de ce site analysées, indice moyen D ». */
  | { phase: "repos"; domaine?: ProfilDomaine }
  | { phase: "extraction"; depuis: number }
  | { phase: "analyse"; depuis: number }
  /** Page reconnue par le lookup k-anonyme : on connaît la note, pas encore le détail.
   * La carte complète n'est chargée que si le panneau est ouvert — inutile de la demander
   * au serveur pour un simple badge (docs/ETHIQUE.md §4). */
  | { phase: "resume"; resume: CorrespondancePrefixe }
  | { phase: "ok"; carte: CarteAnalyse; enCache: boolean; rejetees: number; signalements?: number }
  | { phase: "erreur"; erreur: string };

export type MessageVersFond =
  | { type: "lynceus:etat"; tabId: number }
  | { type: "lynceus:analyser"; tabId: number }
  | { type: "lynceus:annuler"; tabId: number }
  /** Le panneau est ouvert sur une page reconnue : charger la carte complète. */
  | { type: "lynceus:detailler"; tabId: number; analyseId: number }
  | { type: "lynceus:signaler"; analyseId: number; motif: string; message: string };

export interface MessageVersPanneau {
  type: "lynceus:maj";
  tabId: number;
  etat: EtatOnglet;
}

/** Résultat de l'extraction locale (Readability → Markdown) injectée dans la page. */
export type Extraction =
  | { ok: true; url: string; titre: string | null; markdown: string; langue: string | null }
  | { ok: false; erreur: string };
