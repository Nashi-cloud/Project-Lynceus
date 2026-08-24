/** Client de l'API — le délai et l'annulation sont ce qui empêche le panneau de tourner
 * indéfiniment (bug constaté en usage réel sur YouTube). */

import assert from "node:assert/strict";
import { beforeEach, describe, it } from "node:test";
import { importerTs, installerFauxChrome } from "./aide.mjs";

const { analyser, lookupParHash } = await importerTs("src/commun/api.ts");

function fauxFetch(reponse, { delaiMs = 0 } = {}) {
  const appels = [];
  globalThis.fetch = (url, options = {}) =>
    new Promise((resoudre, rejeter) => {
      appels.push({ url, options });
      const abandonner = () =>
        rejeter(options.signal?.reason ?? new DOMException("Annulé", "AbortError"));

      // Comme le vrai fetch : un signal DÉJÀ annulé rejette immédiatement — l'événement
      // "abort" ne se redéclenchera pas.
      if (options.signal?.aborted) return abandonner();

      const minuteur = setTimeout(() => resoudre(reponse), delaiMs);
      minuteur.unref?.(); // ne pas retenir la boucle d'événements après le test
      options.signal?.addEventListener("abort", () => {
        clearTimeout(minuteur);
        abandonner();
      });
    });
  return appels;
}

const REPONSE_OK = {
  ok: true,
  status: 200,
  json: async () => ({ en_cache: false, carte: { note: { grade: "B" } } }),
};

describe("client API", () => {
  beforeEach(() => installerFauxChrome());

  it("appelle l'instance configurée", async () => {
    installerFauxChrome({ instance: "http://100.x.y.z:8000" });
    const appels = fauxFetch(REPONSE_OK);
    await analyser({ url: "https://exemple.fr/a", contenu_markdown: "texte" });
    assert.equal(appels[0].url, "http://100.x.y.z:8000/v1/analyses");
    assert.equal(appels[0].options.method, "POST");
  });

  it("retire le slash final de l'instance", async () => {
    installerFauxChrome({ instance: "http://localhost:8000///" });
    const appels = fauxFetch(REPONSE_OK);
    await lookupParHash("a".repeat(64));
    assert.equal(appels[0].url, `http://localhost:8000/v1/lookup?url_hash=${"a".repeat(64)}`);
  });

  it("abandonne une analyse qui dépasse le délai configuré", async () => {
    installerFauxChrome({ delaiAnalyseS: 0.05 });
    fauxFetch(REPONSE_OK, { delaiMs: 5000 });
    await assert.rejects(
      analyser({ contenu_markdown: "texte" }),
      /délai imparti/,
      "le message doit expliquer la cause et le remède",
    );
  });

  it("laisse aboutir une analyse plus rapide que le délai", async () => {
    installerFauxChrome({ delaiAnalyseS: 5 });
    fauxFetch(REPONSE_OK, { delaiMs: 10 });
    const resultat = await analyser({ contenu_markdown: "texte" });
    assert.equal(resultat.carte.note.grade, "B");
  });

  it("propage une annulation volontaire sans la transformer en erreur réseau", async () => {
    fauxFetch(REPONSE_OK, { delaiMs: 5000 });
    const controleur = new AbortController();
    const promesse = analyser({ contenu_markdown: "texte" }, controleur.signal);
    controleur.abort();
    await assert.rejects(promesse, (erreur) => erreur.name === "AbortError");
  });

  it("respecte un signal déjà annulé avant l'appel", async () => {
    fauxFetch(REPONSE_OK, { delaiMs: 5000 });
    const controleur = new AbortController();
    controleur.abort();
    await assert.rejects(analyser({ contenu_markdown: "texte" }, controleur.signal));
  });

  it("remonte le detail renvoyé par l'API en cas d'erreur", async () => {
    globalThis.fetch = async () => ({
      ok: false,
      status: 400,
      json: async () => ({ detail: "Contenu trop court pour une analyse fiable" }),
    });
    await assert.rejects(analyser({ contenu_markdown: "x" }), /trop court/);
  });

  it("explique qu'une instance est injoignable plutôt que de propager l'erreur brute", async () => {
    globalThis.fetch = async () => {
      throw new TypeError("Failed to fetch");
    };
    await assert.rejects(analyser({ contenu_markdown: "texte" }), /injoignable/);
  });

  it("n'applique pas le réglage d'analyse au lookup, qui garde son propre plafond", async () => {
    // Le lookup est bon marché : son délai est fixe (10 s) et ne suit pas delaiAnalyseS.
    // On le vérifie par le comportement : un réglage d'analyse minuscule ne doit PAS
    // couper un lookup rapide.
    installerFauxChrome({ delaiAnalyseS: 0.05 });
    fauxFetch(REPONSE_OK, { delaiMs: 100 });
    const resultat = await lookupParHash("a".repeat(64));
    assert.ok(resultat, "le lookup ne doit pas hériter du délai d'analyse");
  });
});
