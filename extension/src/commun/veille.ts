/** Veille du panneau pendant une attente : que faire de l'état renvoyé par le service worker.
 *
 * Le service worker MV3 n'est pas un processus qui dure. Chrome l'arrête dès qu'il le juge
 * inactif, et l'état d'analyse, qui vit dans une Map en mémoire (fond.ts), disparaît avec
 * lui — comme l'appel réseau en cours. Plus personne n'envoie alors la notification de fin,
 * et un panneau qui se contente d'écouter tourne indéfiniment. Une notification peut aussi
 * se perdre à l'ouverture du panneau : elle part sans accusé de réception.
 *
 * Redemander l'état pendant l'attente lève l'ambiguïté. Un service worker qui répond
 * « repos » alors que le panneau attend est un service worker qui a tout oublié : il ne peut
 * pas répondre autre chose, puisque le message qui l'interroge est justement ce qui vient de
 * le relancer.
 *
 * Décision séparée du panneau, qui dépend du DOM et des API Chrome : elle est ainsi testable
 * sans navigateur, comme SuiviAnalyses l'est pour fond.ts. */

import type { EtatOnglet } from "./types";

/** Ce que le panneau affiche pendant une attente : la phase et l'instant de départ, qui
 * distingue deux analyses successives dans la même phase. */
export interface AttenteAffichee {
  phase: "extraction" | "analyse";
  depuis: number;
}

export type DecisionVeille =
  /** L'analyse suit son cours : le rendu en place reste valable, on ne le refait pas. */
  | { action: "patienter" }
  /** L'analyse a avancé : afficher ce nouvel état. */
  | { action: "rendre"; etat: EtatOnglet }
  /** Plus personne ne travaille sur cet onglet : l'analyse a été perdue en chemin. */
  | { action: "perdue" };

export function deciderVeille(
  affiche: AttenteAffichee,
  recu: EtatOnglet | undefined,
): DecisionVeille {
  // Pas de réponse : le service worker redémarre peut-être à l'instant. On ne conclut rien
  // d'une absence, le battement suivant tranchera.
  if (!recu) return { action: "patienter" };
  // Même phase et même départ : rien de neuf. Re-rendre ici referait le DOM chaque seconde,
  // et le minuteur repartirait de zéro sous les yeux de l'utilisateur.
  const attend = recu.phase === "extraction" || recu.phase === "analyse";
  if (attend && recu.phase === affiche.phase && recu.depuis === affiche.depuis) {
    return { action: "patienter" };
  }
  if (recu.phase === "repos") return { action: "perdue" };
  return { action: "rendre", etat: recu };
}
