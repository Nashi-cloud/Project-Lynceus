/** Suivi des analyses en vol, par onglet.
 *
 * Une analyse enchaîne plusieurs étapes asynchrones (injection du script, extraction, appel
 * réseau) dont certaines ne sont pas interruptibles : chrome.scripting.executeScript ne
 * s'annule pas, contrairement à un fetch. Plutôt que de tenter d'arrêter ces étapes, on
 * numérote chaque lancement : un résultat dont la génération n'est plus la dernière connue
 * appartient à une analyse annulée ou remplacée, et doit être ignoré silencieusement.
 *
 * Logique volontairement séparée de fond.ts, qui dépend des API Chrome : elle est ainsi
 * testable sans navigateur. */

export class SuiviAnalyses {
  private generations = new Map<number, number>();
  private controleurs = new Map<number, AbortController>();

  /** Démarre une analyse : retourne sa génération et son contrôleur d'annulation. */
  demarrer(tabId: number): { generation: number; controleur: AbortController } {
    const generation = (this.generations.get(tabId) ?? 0) + 1;
    this.generations.set(tabId, generation);
    const controleur = new AbortController();
    this.controleurs.set(tabId, controleur);
    return { generation, controleur };
  }

  /** Vrai si cette génération est toujours celle en cours pour cet onglet. */
  estCourante(tabId: number, generation: number): boolean {
    return this.generations.get(tabId) === generation;
  }

  /** Annule l'analyse en cours : invalide sa génération et interrompt son appel réseau. */
  annuler(tabId: number): void {
    this.generations.set(tabId, (this.generations.get(tabId) ?? 0) + 1);
    this.controleurs.get(tabId)?.abort();
    this.controleurs.delete(tabId);
  }

  /** Libère le contrôleur d'une analyse terminée, sans toucher à la génération
   * (un lancement plus récent a pu prendre sa place entre-temps). */
  terminer(tabId: number, controleur: AbortController): void {
    if (this.controleurs.get(tabId) === controleur) this.controleurs.delete(tabId);
  }

  /** Oublie complètement un onglet (fermeture). */
  oublier(tabId: number): void {
    this.generations.delete(tabId);
    this.controleurs.delete(tabId);
  }
}
