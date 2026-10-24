/** Mise à jour — l'avis qu'une version plus récente existe.
 *
 * Une extension installée depuis l'archive ne se met jamais à jour seule. L'avis doit
 * apparaître quand il le faut, jamais sinon, et ne jamais envoyer la personne télécharger
 * ailleurs que chez son portail. */

import assert from "node:assert/strict";
import { beforeEach, describe, it } from "node:test";
import { importerTs, installerFauxChrome } from "./aide.mjs";

const { comparerVersions, lireAnnonce, doitAnnoncer, verifierMiseAJour, masquerAnnonce } =
  await importerTs("src/commun/mise-a-jour.ts");

const PORTAIL = "https://portail.test";
const ANNONCE = { version: "0.11.6", telechargement: `${PORTAIL}/telecharger` };

describe("comparerVersions", () => {
  it("compare numériquement, pas alphabétiquement", () => {
    assert.ok(comparerVersions("0.11.10", "0.11.9") > 0);
    assert.ok(comparerVersions("0.9.0", "0.11.0") < 0);
    assert.equal(comparerVersions("1.2.3", "1.2.3"), 0);
  });
});

describe("lireAnnonce", () => {
  it("accepte une réponse bien formée qui renvoie chez le portail", () => {
    assert.deepEqual(lireAnnonce(ANNONCE, PORTAIL), ANNONCE);
  });

  it("refuse un lien qui mène hors du portail", () => {
    // Un portail compromis ne doit pas pouvoir faire télécharger une archive d'ailleurs.
    assert.equal(lireAnnonce({ ...ANNONCE, telechargement: "https://ailleurs.test/x.zip" }, PORTAIL), null);
  });

  it("refuse une version qui n'en a pas la forme", () => {
    for (const version of ["0.11", "v0.11.6", "0.11.6-beta", "<b>", 11]) {
      assert.equal(lireAnnonce({ ...ANNONCE, version }, PORTAIL), null, String(version));
    }
  });

  it("refuse ce qui n'est pas un objet", () => {
    for (const donnees of [null, "0.11.6", [], undefined]) {
      assert.equal(lireAnnonce(donnees, PORTAIL), null);
    }
  });
});

describe("doitAnnoncer", () => {
  it("annonce une version plus récente", () => {
    assert.equal(doitAnnoncer("0.11.5", ANNONCE, undefined), true);
  });

  it("n'annonce ni la même version, ni une plus ancienne", () => {
    assert.equal(doitAnnoncer("0.11.6", ANNONCE, undefined), false);
    assert.equal(doitAnnoncer("0.12.0", ANNONCE, undefined), false);
  });

  it("n'annonce plus une version dont l'avis a été masqué, mais annonce la suivante", () => {
    assert.equal(doitAnnoncer("0.11.5", ANNONCE, "0.11.6"), false);
    assert.equal(doitAnnoncer("0.11.5", { ...ANNONCE, version: "0.11.7" }, "0.11.6"), true);
  });
});

describe("verifierMiseAJour", () => {
  let appels;
  let local;

  function preparer({ installType = "development", portail = PORTAIL, reponse = ANNONCE,
                      statut = 200, version = "0.11.5" } = {}) {
    installerFauxChrome({ portail });
    local = {};
    globalThis.chrome.storage.local = {
      async get(cles) { return Object.fromEntries(cles.filter((c) => c in local).map((c) => [c, local[c]])); },
      async set(valeurs) { Object.assign(local, valeurs); },
    };
    globalThis.chrome.management = { async getSelf() { return { installType }; } };
    globalThis.chrome.runtime = { getManifest: () => ({ version }), getURL: () => "" };
    appels = [];
    globalThis.fetch = async (url) => {
      appels.push(url);
      return { ok: statut === 200, json: async () => reponse };
    };
  }

  beforeEach(() => preparer());

  it("annonce la version du portail quand elle est plus récente", async () => {
    assert.deepEqual(await verifierMiseAJour(), ANNONCE);
    assert.deepEqual(appels, [`${PORTAIL}/v1/extension`]);
  });

  it("ne demande rien pour une extension installée depuis un magasin", async () => {
    // Le navigateur la met à jour lui-même : lui proposer l'archive serait la faire régresser.
    preparer({ installType: "normal" });
    assert.equal(await verifierMiseAJour(), null);
    assert.equal(appels.length, 0);
  });

  it("ne demande rien sans portail connu", async () => {
    preparer({ portail: "" });
    assert.equal(await verifierMiseAJour(), null);
    assert.equal(appels.length, 0);
  });

  it("ne demande au portail qu'une fois par jour", async () => {
    const t0 = 1_000_000_000_000;
    await verifierMiseAJour(t0);
    await verifierMiseAJour(t0 + 60_000);
    assert.equal(appels.length, 1);
    await verifierMiseAJour(t0 + 25 * 3600_000);
    assert.equal(appels.length, 2);
  });

  it("se tait si le portail n'a pas de paquet ou ne répond pas", async () => {
    preparer({ statut: 404 });
    assert.equal(await verifierMiseAJour(), null);
    preparer();
    globalThis.fetch = async () => { throw new Error("injoignable"); };
    assert.equal(await verifierMiseAJour(), null);
  });

  it("ne réaffiche pas un avis masqué", async () => {
    await masquerAnnonce("0.11.6");
    assert.equal(await verifierMiseAJour(), null);
  });
});
