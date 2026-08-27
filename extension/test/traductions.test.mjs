/** Traductions de l'extension : aucune phrase ne doit manquer dans une langue.
 *
 * Chrome ne signale pas une clé absente : `getMessage` rend une chaîne vide, et l'interface
 * affiche un blanc que personne ne remarque avant un utilisateur. Ces tests transforment
 * l'oubli en échec de construction. */

import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, it } from "node:test";

const catalogue = (langue) =>
  JSON.parse(readFileSync(`src/_locales/${langue}/messages.json`, "utf-8"));

const LANGUES = readdirSync("src/_locales");

/** Familles de clés construites à l'exécution (`categorie_${id}`) : le scan littéral ne peut
 * pas les voir, elles sont donc vérifiées par leur liste d'identifiants. */
const FAMILLES = {
  categorie_: ["information", "opinion", "analyse_expertise", "satire", "publicite_sponsorise",
               "temoignage", "contenu_confessionnel", "pseudo_science", "theorie_du_complot",
               "autre"],
  dimension_: ["sources", "factualite", "ton", "transparence"],
  gravite_: ["faible", "moyenne", "haute"],
  motif_: ["analyse_erronee", "extrait_hors_contexte", "categorie_erronee", "note_injustifiee",
           "page_modifiee", "droit_de_reponse", "autre"],
};

// Le module de traduction lui-même est écarté : sa documentation montre la forme des
// marqueurs, et le scan prendrait ces exemples pour de vraies clés.
const IGNORES = new Set(["i18n.ts"]);

const fichiers = (racine) =>
  readdirSync(racine, { withFileTypes: true }).flatMap((entree) => {
    const chemin = join(racine, entree.name);
    if (entree.isDirectory()) return entree.name === "_locales" ? [] : fichiers(chemin);
    if (IGNORES.has(entree.name)) return [];
    return /\.(ts|html)$/.test(entree.name) ? [chemin] : [];
  });

function clesUtilisees() {
  const cles = new Set();
  for (const chemin of fichiers("src")) {
    const source = readFileSync(chemin, "utf-8");
    // Tous les littéraux d'un appel, pas seulement le premier : une clé peut être
    // choisie par une condition, « msg(x ? "a" : "b") ».
    for (const [, appel] of source.matchAll(/\bmsg\(([^;]*?)\)/g)) {
      // En première position, ou après « ? » et « : ». Ailleurs dans l'appel, un
      // littéral est une valeur de comparaison ou une substitution, pas une clé.
      for (const [, cle] of appel.matchAll(/(?:^|\?|:|\()\s*"([a-z0-9_]+)"/g)) cles.add(cle);
    }
    for (const [, cle] of source.matchAll(/data-i18n(?:-html)?="([^"]+)"/g)) cles.add(cle);
    for (const [, paires] of source.matchAll(/data-i18n-attr="([^"]+)"/g)) {
      for (const paire of paires.split(",")) cles.add(paire.split(":")[1].trim());
    }
  }
  for (const [prefixe, ids] of Object.entries(FAMILLES)) {
    for (const id of ids) cles.add(prefixe + id);
  }
  const manifeste = readFileSync("manifest.json", "utf-8");
  for (const [, cle] of manifeste.matchAll(/__MSG_([a-z_]+)__/g)) cles.add(cle);
  return cles;
}

describe("catalogues de traduction", () => {
  it("déclare la langue de repli du manifeste", () => {
    const manifeste = JSON.parse(readFileSync("manifest.json", "utf-8"));
    assert.ok(LANGUES.includes(manifeste.default_locale),
              `default_locale « ${manifeste.default_locale} » sans catalogue`);
  });

  it("traduit chaque phrase employée, dans toutes les langues", () => {
    const utilisees = clesUtilisees();
    assert.ok(utilisees.size > 50, "le scan n'a presque rien trouvé : le motif a dérivé");
    for (const langue of LANGUES) {
      const messages = catalogue(langue);
      const absentes = [...utilisees].filter((cle) => !messages[cle]?.message).sort();
      assert.deepEqual(absentes, [], `${langue} : ${absentes.length} clé(s) sans traduction`);
    }
  });

  it("ne garde aucune phrase devenue inutile", () => {
    const utilisees = clesUtilisees();
    for (const langue of LANGUES) {
      const orphelines = Object.keys(catalogue(langue)).filter((cle) => !utilisees.has(cle)).sort();
      assert.deepEqual(orphelines, [], `${langue} : ${orphelines.length} clé(s) plus employée(s)`);
    }
  });

  it("garde les mêmes substitutions d'une langue à l'autre", () => {
    // « $1 » absent d'une traduction laisse un trou à l'écran : le nom du portail, la
    // version, le nombre de pages. Le compte doit correspondre partout.
    const reference = catalogue("fr");
    for (const langue of LANGUES.filter((l) => l !== "fr")) {
      const messages = catalogue(langue);
      for (const [cle, entree] of Object.entries(reference)) {
        const attendues = new Set(entree.message.match(/\$\d/g) ?? []);
        const obtenues = new Set(messages[cle]?.message.match(/\$\d/g) ?? []);
        assert.deepEqual([...obtenues].sort(), [...attendues].sort(),
                         `${langue} : substitutions différentes pour « ${cle} »`);
      }
    }
  });
});
