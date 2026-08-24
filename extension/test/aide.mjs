/** Compile un module TypeScript de l'extension en module ESM importable par node:test. */

import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { buildSync } from "esbuild";

const dossier = mkdtempSync(join(tmpdir(), "lynceus-test-"));

export async function importerTs(chemin) {
  const sortie = join(dossier, chemin.replace(/[\/]/g, "_").replace(/\.ts$/, ".mjs"));
  buildSync({
    entryPoints: [chemin],
    bundle: true,
    format: "esm",
    platform: "neutral",
    external: ["@mozilla/readability", "turndown"],
    outfile: sortie,
  });
  return import(sortie);
}

/** Faux chrome.storage.sync minimal, suffisant pour chargerReglages/enregistrerReglages. */
export function installerFauxChrome(valeursInitiales = {}) {
  const stockage = { ...valeursInitiales };
  globalThis.chrome = {
    storage: {
      sync: {
        async get(defauts) {
          const resultat = {};
          for (const [cle, valeur] of Object.entries(defauts ?? {})) {
            resultat[cle] = cle in stockage ? stockage[cle] : valeur;
          }
          return resultat;
        },
        async set(valeurs) {
          Object.assign(stockage, valeurs);
        },
      },
    },
  };
  return stockage;
}
