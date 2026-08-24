/** Suivi des analyses en vol — la logique qui empêche une carte annulée de s'afficher. */

import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { importerTs } from "./aide.mjs";

const { SuiviAnalyses } = await importerTs("src/commun/generations.ts");

describe("SuiviAnalyses", () => {
  it("considère une analyse fraîchement démarrée comme courante", () => {
    const suivi = new SuiviAnalyses();
    const { generation } = suivi.demarrer(1);
    assert.equal(suivi.estCourante(1, generation), true);
  });

  it("invalide la génération précédente quand une nouvelle analyse démarre", () => {
    const suivi = new SuiviAnalyses();
    const premiere = suivi.demarrer(1);
    const seconde = suivi.demarrer(1);
    assert.equal(suivi.estCourante(1, premiere.generation), false);
    assert.equal(suivi.estCourante(1, seconde.generation), true);
  });

  it("invalide la génération en cours à l'annulation", () => {
    const suivi = new SuiviAnalyses();
    const { generation } = suivi.demarrer(1);
    suivi.annuler(1);
    assert.equal(suivi.estCourante(1, generation), false);
  });

  it("interrompt l'appel réseau à l'annulation", () => {
    const suivi = new SuiviAnalyses();
    const { controleur } = suivi.demarrer(1);
    assert.equal(controleur.signal.aborted, false);
    suivi.annuler(1);
    assert.equal(controleur.signal.aborted, true);
  });

  it("isole les onglets les uns des autres", () => {
    const suivi = new SuiviAnalyses();
    const ongletA = suivi.demarrer(1);
    const ongletB = suivi.demarrer(2);
    suivi.annuler(1);
    assert.equal(suivi.estCourante(1, ongletA.generation), false);
    assert.equal(suivi.estCourante(2, ongletB.generation), true, "l'onglet 2 ne doit pas être affecté");
  });

  it("annuler un onglet sans analyse en cours ne lève pas", () => {
    const suivi = new SuiviAnalyses();
    assert.doesNotThrow(() => suivi.annuler(42));
  });

  it("terminer ne libère pas le contrôleur d'une analyse plus récente", () => {
    const suivi = new SuiviAnalyses();
    const ancienne = suivi.demarrer(1);
    const recente = suivi.demarrer(1);
    suivi.terminer(1, ancienne.controleur); // l'ancienne se termine après le nouveau lancement
    suivi.annuler(1);
    assert.equal(recente.controleur.signal.aborted, true, "la récente doit rester annulable");
  });

  it("oublier un onglet remet le compteur à zéro", () => {
    const suivi = new SuiviAnalyses();
    const { generation } = suivi.demarrer(1);
    suivi.oublier(1);
    assert.equal(suivi.estCourante(1, generation), false);
  });
});
