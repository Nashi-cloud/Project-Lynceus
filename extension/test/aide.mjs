/** Compile un module TypeScript de l'extension en module ESM importable par node:test. */

import { mkdtempSync, readFileSync } from "node:fs";
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
    // Injecté par build.mjs à la compilation du paquet : sans valeur ici, les modules
    // qui le lisent lèveraient une ReferenceError au chargement du test.
    define: { PORTAIL_PAR_DEFAUT: '""' },
    outfile: sortie,
  });
  return import(sortie);
}

/** Le catalogue français, lu tel quel : les tests vérifient les phrases réellement
 * livrées, pas une copie qui pourrait diverger. */
const MESSAGES = JSON.parse(readFileSync("src/_locales/fr/messages.json", "utf-8"));

/** Faux chrome minimal : stockage synchronisé et traduction. */
export function installerFauxChrome(valeursInitiales = {}) {
  const stockage = { ...valeursInitiales };
  globalThis.chrome = {
    i18n: {
      getMessage(cle, valeurs = []) {
        const message = MESSAGES[cle]?.message ?? "";
        return message.replace(/\$(\d)/g, (_, rang) => valeurs[Number(rang) - 1] ?? "");
      },
      getUILanguage: () => "fr",
    },
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
