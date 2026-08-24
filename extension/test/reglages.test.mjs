/** Réglages — les valeurs par défaut engagent la vie privée : le badge passif doit rester
 * désactivé tant que l'utilisateur ne l'a pas explicitement demandé (charte §3-4). */

import assert from "node:assert/strict";
import { beforeEach, describe, it } from "node:test";
import { importerTs, installerFauxChrome } from "./aide.mjs";

const { REGLAGES_DEFAUT, chargerReglages, enregistrerReglages } = await importerTs("src/commun/reglages.ts");

describe("réglages", () => {
  beforeEach(() => installerFauxChrome());

  it("désactive le badge passif par défaut", () => {
    assert.equal(REGLAGES_DEFAUT.badgeActif, false);
  });

  it("pointe une instance locale par défaut", () => {
    assert.equal(REGLAGES_DEFAUT.instance, "http://localhost:8000");
  });

  it("prévoit un délai d'analyse supérieur au plafond serveur (360 s au pire)", () => {
    assert.ok(
      REGLAGES_DEFAUT.delaiAnalyseS < 360,
      "un défaut trop court couperait une analyse légitime : il doit rester un filet, pas une contrainte",
    );
    assert.ok(REGLAGES_DEFAUT.delaiAnalyseS >= 120, "un défaut trop court gênerait les modèles lents");
  });

  it("retourne les valeurs par défaut quand rien n'est stocké", async () => {
    assert.deepEqual(await chargerReglages(), REGLAGES_DEFAUT);
  });

  it("relit ce qui a été enregistré", async () => {
    await enregistrerReglages({ instance: "http://100.x.y.z:8000", badgeActif: true });
    const reglages = await chargerReglages();
    assert.equal(reglages.instance, "http://100.x.y.z:8000");
    assert.equal(reglages.badgeActif, true);
    assert.equal(reglages.delaiAnalyseS, REGLAGES_DEFAUT.delaiAnalyseS, "les autres clés restent aux défauts");
  });
});
