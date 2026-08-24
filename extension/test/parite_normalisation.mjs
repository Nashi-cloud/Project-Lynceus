/** Test de parité : normaliserUrl/hacherUrl (TypeScript) doivent produire EXACTEMENT
 * les mêmes résultats que api/lynceus/normalisation.py — sinon le lookup annuaire échoue. */

import { execFileSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { buildSync } from "esbuild";

const URLS = [
  "https://Exemple.FR/Chemin#section",
  "https://exemple.fr/a?utm_source=nl&b=2&a=1&fbclid=xyz",
  "https://exemple.fr/page/",
  "https://exemple.fr",
  "https://exemple.fr:443/x",
  "http://exemple.fr:8080/x?z=1&a=2",
  "https://sous.Exemple.fr/Article-Titre?gclid=abc&utm_campaign=x&id=42",
  "https://exemple.fr/recherche?q=esprit%20critique&page=2",
  "https://exemple.fr/a?vide=&plein=1",
  "https://fr.sott.net/article/44562-Resume-SOTT-des-changements-terrestres-Juin-2026",
  "https://exemple.fr/multi///",
  "https://exemple.fr/?utm_source=x",
];

// 1. Compiler hachage.ts en module Node
const dossier = mkdtempSync(join(tmpdir(), "lynceus-parite-"));
const sortieJs = join(dossier, "hachage.mjs");
buildSync({ entryPoints: ["src/commun/hachage.ts"], bundle: true, format: "esm", platform: "neutral", outfile: sortieJs });
const { normaliserUrl, hacherUrl } = await import(sortieJs);

// 2. Côté TypeScript
const resultatsTs = [];
for (const url of URLS) resultatsTs.push([normaliserUrl(url), await hacherUrl(url)]);

// 3. Côté Python (implémentation de référence)
const scriptPython = `
import json, sys
sys.path.insert(0, "../api")
from lynceus.normalisation import normaliser_url, hacher_url
urls = json.load(sys.stdin)
print(json.dumps([[normaliser_url(u), hacher_url(u)] for u in urls]))
`;
const cheminScript = join(dossier, "reference.py");
writeFileSync(cheminScript, scriptPython);
const resultatsPy = JSON.parse(
  execFileSync("../api/.venv/bin/python", [cheminScript], { input: JSON.stringify(URLS), encoding: "utf-8" }),
);

// 4. Comparaison
let echecs = 0;
for (let i = 0; i < URLS.length; i++) {
  const [normTs, hashTs] = resultatsTs[i];
  const [normPy, hashPy] = resultatsPy[i];
  const ok = normTs === normPy && hashTs === hashPy;
  if (!ok) {
    echecs++;
    console.error(`✗ ${URLS[i]}\n    TS : ${normTs}\n    PY : ${normPy}`);
  } else {
    console.log(`✓ ${normTs}`);
  }
}
console.log(`\n${URLS.length - echecs}/${URLS.length} URL en parité TypeScript ↔ Python`);
if (echecs) process.exit(1);
