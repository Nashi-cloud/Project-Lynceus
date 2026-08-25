/** Inscription — obtention d'une clé auprès d'un portail.
 *
 * Le portail décide de l'instance vers laquelle l'extension enverra désormais le contenu
 * des pages analysées : sa réponse est donc vérifiée avant d'être appliquée, et ces tests
 * portent surtout sur ce qui doit être refusé. */

import assert from "node:assert/strict";
import { beforeEach, describe, it } from "node:test";
import { importerTs, installerFauxChrome } from "./aide.mjs";

const { demanderCle, appliquerBillet, normaliserAdresse, resumerBillet } =
  await importerTs("src/commun/inscription.ts");
const { chargerReglages } = await importerTs("src/commun/reglages.ts");

const BILLET = {
  instance: "https://instance.test",
  cle: "LYNC1.charge.signature",
  quota_jour: 20,
  expire_le: "2027-08-25",
  portail: "Lynceus",
};

function fauxFetch(corps, { ok = true, status = 200 } = {}) {
  const appels = [];
  globalThis.fetch = async (url, options = {}) => {
    appels.push({ url, options });
    return {
      ok,
      status,
      json: async () => corps,
    };
  };
  return appels;
}

describe("normaliserAdresse", () => {
  it("retire les barres obliques finales", () => {
    assert.equal(normaliserAdresse("https://portail.test///"), "https://portail.test");
  });

  it("refuse une adresse vide en disant quoi faire", () => {
    assert.throws(() => normaliserAdresse("   "), /Indiquez l'adresse du portail/);
  });

  it("refuse un protocole autre que http(s)", () => {
    // Un schéma exotique (javascript:, file:…) ne doit jamais atteindre fetch.
    assert.throws(() => normaliserAdresse("javascript:alert(1)"), /http\(s\)/);
  });
});

describe("demanderCle", () => {
  beforeEach(() => installerFauxChrome());

  it("appelle /v1/inscription en POST sur le portail indiqué", async () => {
    const appels = fauxFetch(BILLET);
    const billet = await demanderCle("https://portail.test/");
    assert.equal(appels[0].url, "https://portail.test/v1/inscription");
    assert.equal(appels[0].options.method, "POST");
    assert.equal(billet.cle, BILLET.cle);
    assert.equal(billet.quota_jour, 20);
  });

  it("rapporte le message du portail plutôt qu'un code HTTP nu", async () => {
    fauxFetch({ detail: "Ce portail ne délivre pas de clés." }, { ok: false, status: 503 });
    await assert.rejects(demanderCle("https://portail.test"), /ne délivre pas de clés/);
  });

  it("reste compréhensible si la réponse d'erreur n'est pas du JSON", async () => {
    globalThis.fetch = async () => ({
      ok: false,
      status: 502,
      json: async () => {
        throw new Error("pas du JSON");
      },
    });
    await assert.rejects(demanderCle("https://portail.test"), /HTTP 502/);
  });

  it("refuse un billet sans clé exploitable", async () => {
    fauxFetch({ ...BILLET, cle: "pas-une-cle" });
    await assert.rejects(demanderCle("https://portail.test"), /pas renvoyé de clé/);
  });

  it("refuse une instance qui n'est pas une adresse http(s)", async () => {
    // Sans cette vérification, un portail malveillant pourrait rediriger le contenu des
    // pages lues vers n'importe quel schéma d'URL.
    fauxFetch({ ...BILLET, instance: "javascript:void(0)" });
    await assert.rejects(demanderCle("https://portail.test"), /http\(s\)/);
  });

  it("dit que le portail est injoignable plutôt que de laisser fuir l'erreur réseau", async () => {
    globalThis.fetch = async () => {
      throw new TypeError("Failed to fetch");
    };
    await assert.rejects(demanderCle("https://portail.test"), /injoignable/);
  });
});

describe("appliquerBillet", () => {
  it("enregistre l'instance ET la clé — un billet à moitié appliqué serait inutilisable", async () => {
    installerFauxChrome();
    await appliquerBillet(BILLET);
    const reglages = await chargerReglages();
    assert.equal(reglages.instance, "https://instance.test");
    assert.equal(reglages.cle, BILLET.cle);
  });
});

describe("resumerBillet", () => {
  it("annonce l'instance configurée, l'échéance et le quota", () => {
    const resume = resumerBillet(BILLET);
    assert.match(resume, /instance\.test/);
    assert.match(resume, /2027-08-25/);
    assert.match(resume, /20 analyses par jour/);
  });
});
