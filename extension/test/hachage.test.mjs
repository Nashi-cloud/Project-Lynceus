/** Normalisation d'URL — cas limites et propriétés, en complément du test de parité
 * avec l'implémentation Python (parite_normalisation.mjs). */

import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { importerTs } from "./aide.mjs";

const { normaliserUrl, hacherUrl } = await importerTs("src/commun/hachage.ts");

describe("normaliserUrl", () => {
  it("met le schéma et l'hôte en minuscules, garde la casse du chemin", () => {
    assert.equal(normaliserUrl("HTTPS://Exemple.FR/Chemin"), "https://exemple.fr/Chemin");
  });

  it("supprime le fragment", () => {
    assert.equal(normaliserUrl("https://exemple.fr/a#section"), "https://exemple.fr/a");
  });

  it("supprime les paramètres de tracking et trie les autres", () => {
    assert.equal(
      normaliserUrl("https://exemple.fr/a?utm_source=x&b=2&a=1&fbclid=y"),
      "https://exemple.fr/a?a=1&b=2",
    );
  });

  it("supprime le port par défaut mais conserve un port explicite", () => {
    assert.equal(normaliserUrl("https://exemple.fr:443/x"), "https://exemple.fr/x");
    assert.equal(normaliserUrl("http://exemple.fr:8080/x"), "http://exemple.fr:8080/x");
  });

  it("normalise le slash final sans écraser la racine", () => {
    assert.equal(normaliserUrl("https://exemple.fr/page/"), "https://exemple.fr/page");
    assert.equal(normaliserUrl("https://exemple.fr"), "https://exemple.fr/");
  });

  it("refuse les schémas non http(s)", () => {
    for (const url of ["ftp://exemple.fr/f", "file:///etc/passwd", "javascript:alert(1)"]) {
      assert.throws(() => normaliserUrl(url), /non support/, `${url} devrait être refusée`);
    }
  });

  it("conserve les sous-domaines, qui désignent des sites distincts", () => {
    assert.notEqual(
      normaliserUrl("https://blog.exemple.fr/a"),
      normaliserUrl("https://exemple.fr/a"),
    );
  });
});

describe("hacherUrl", () => {
  it("produit un SHA-256 hexadécimal", async () => {
    const empreinte = await hacherUrl("https://exemple.fr/a");
    assert.match(empreinte, /^[0-9a-f]{64}$/);
  });

  it("donne la même empreinte pour des variantes équivalentes", async () => {
    const [a, b] = await Promise.all([
      hacherUrl("https://Exemple.fr/article/?utm_campaign=x#haut"),
      hacherUrl("https://exemple.fr/article"),
    ]);
    assert.equal(a, b);
  });

  it("donne des empreintes différentes pour des pages différentes", async () => {
    const [a, b] = await Promise.all([
      hacherUrl("https://exemple.fr/article-1"),
      hacherUrl("https://exemple.fr/article-2"),
    ]);
    assert.notEqual(a, b);
  });
});
