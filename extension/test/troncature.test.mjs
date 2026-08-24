/** Raccourcissement des pages trop longues pour l'instance.
 *
 * Refuser tout net un article long est le pire comportement : l'utilisateur n'y peut rien.
 * Analyser son début en le signalant reste utile — à condition que la mention voyage avec
 * la carte, qui sera mise en cache et resservie à d'autres. */

import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { importerTs } from "./aide.mjs";

const { raccourcir } = await importerTs("src/commun/troncature.ts");

describe("raccourcissement", () => {
  it("laisse intact un contenu sous la limite", () => {
    const court = "Un article court.";
    const resultat = raccourcir(court, 1000);
    assert.equal(resultat.texte, court);
    assert.equal(resultat.tronque, false);
  });

  it("signale la troncature au-delà de la limite", () => {
    const resultat = raccourcir("x".repeat(2000), 1000);
    assert.equal(resultat.tronque, true);
    assert.ok(resultat.texte.length <= 1000);
  });

  it("coupe à une frontière de paragraphe quand elle est proche", () => {
    const texte = "a".repeat(900) + "\n\n" + "b".repeat(500);
    const resultat = raccourcir(texte, 1000);
    assert.ok(!resultat.texte.endsWith("b"), "ne doit pas couper au milieu du paragraphe suivant");
    assert.equal(resultat.texte, "a".repeat(900));
  });

  it("ne remonte pas trop haut pour trouver un paragraphe", () => {
    // Frontière à 10 % : remonter jusque-là jetterait 90 % du texte analysable.
    const texte = "a".repeat(100) + "\n\n" + "b".repeat(2000);
    const resultat = raccourcir(texte, 1000);
    assert.ok(resultat.texte.length > 900, "doit garder le texte plutôt que couper trop tôt");
  });

  it("gère un contenu exactement à la limite", () => {
    const resultat = raccourcir("x".repeat(1000), 1000);
    assert.equal(resultat.tronque, false);
  });
});
