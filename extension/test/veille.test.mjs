/** Veille du panneau — la logique qui empêche le sablier de tourner indéfiniment.
 *
 * Le cas rapporté : l'analyse aboutit en quelques secondes, mais le panneau continue de
 * tourner. Deux causes, l'une comme l'autre invisibles depuis le panneau s'il se contente
 * d'écouter : une notification de fin perdue, ou un service worker arrêté par Chrome avec
 * l'analyse dedans. */

import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { importerTs } from "./aide.mjs";

const { deciderVeille } = await importerTs("src/commun/veille.ts");

const AFFICHE = { phase: "analyse", depuis: 1_000 };

describe("deciderVeille", () => {
  it("patiente tant que le service worker décrit la même attente", () => {
    assert.deepEqual(deciderVeille(AFFICHE, { phase: "analyse", depuis: 1_000 }),
                     { action: "patienter" });
  });

  it("patiente si le service worker n'a rien répondu", () => {
    // Une absence de réponse n'est pas une réponse : le service worker redémarre peut-être.
    assert.deepEqual(deciderVeille(AFFICHE, undefined), { action: "patienter" });
  });

  it("déclare l'analyse perdue quand le service worker répond « repos »", () => {
    // Personne ne travaille sur cet onglet alors que le panneau attend : l'état en mémoire
    // est parti avec le service worker, et l'appel réseau avec lui.
    assert.deepEqual(deciderVeille(AFFICHE, { phase: "repos" }), { action: "perdue" });
  });

  it("rend le résultat quand la notification de fin s'est perdue", () => {
    const etat = { phase: "ok", carte: {}, enCache: false, rejetees: 0 };
    assert.deepEqual(deciderVeille(AFFICHE, etat), { action: "rendre", etat });
  });

  it("rend l'erreur remontée par le service worker", () => {
    const etat = { phase: "erreur", erreur: "instance injoignable" };
    assert.deepEqual(deciderVeille(AFFICHE, etat), { action: "rendre", etat });
  });

  it("suit le passage de l'extraction à l'analyse", () => {
    const etat = { phase: "analyse", depuis: 2_000 };
    assert.deepEqual(deciderVeille({ phase: "extraction", depuis: 1_000 }, etat),
                     { action: "rendre", etat });
  });

  it("rend une nouvelle attente de la même phase, reconnue à son départ", () => {
    // Analyse annulée puis relancée pendant que le panneau attendait : même phase, autre
    // analyse. Patienter afficherait le minuteur de la précédente.
    const etat = { phase: "analyse", depuis: 9_000 };
    assert.deepEqual(deciderVeille(AFFICHE, etat), { action: "rendre", etat });
  });
});
