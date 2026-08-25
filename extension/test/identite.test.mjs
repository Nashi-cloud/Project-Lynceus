/** Identité visuelle : l'extension et le portail doivent rester le même objet.
 *
 * L'extension ne peut pas partager la feuille de style du portail : un .zip chargé dans
 * Chrome n'a accès qu'à lui-même, et aller chercher le CSS ou les polices sur le réseau
 * signalerait chaque ouverture du panneau au serveur. La copie est donc inévitable. Ces
 * tests existent pour qu'elle ne dérive pas en silence : un grade B doit avoir exactement
 * la même couleur dans le panneau, sur le site et dans l'annuaire, faute de quoi la note
 * cesse d'être une échelle et devient une impression. */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { describe, it } from "node:test";
import { CHEMIN_LOGO, TAILLES, cheminIcone, encoderPng, rendre } from "../icones.mjs";

const CSS_PORTAIL = "../api/lynceus/portail/statique/lynceus.css";
const CSS_EXTENSION = "src/commun/lynceus.css";
const LOGO_PORTAIL = "../api/lynceus/portail/gabarits/_logo.html";
const POLICES_PORTAIL = "../api/lynceus/portail/statique/polices";

const lire = (chemin) => readFileSync(chemin, "utf-8");

/** Les jetons des blocs `:root`, dans l'ordre : d'abord le thème clair, puis le sombre. */
function jetons(css) {
  const blocs = [...css.matchAll(/:root\s*\{([^}]*)\}/g)].map((m) => m[1]);
  return blocs.map((bloc) =>
    Object.fromEntries(
      [...bloc.matchAll(/(--[a-z0-9-]+)\s*:\s*([^;]+);/g)].map(([, nom, valeur]) => [
        nom,
        valeur.trim().replace(/\s+/g, " "),
      ]),
    ),
  );
}

/** Géométrie d'un SVG : la suite des attributs de forme, dans l'ordre du document. */
const geometrie = (svg) =>
  [...svg.matchAll(/\s(d|r|cx|cy)="([^"]*)"/g)].map(([, nom, valeur]) => `${nom}=${valeur}`);

describe("palette partagée avec le portail", () => {
  const [portailClair, portailSombre] = jetons(lire(CSS_PORTAIL));
  const [extensionClair, extensionSombre] = jetons(lire(CSS_EXTENSION));

  it("donne la même valeur à tout jeton défini des deux côtés", () => {
    for (const [nom, valeur] of Object.entries(extensionClair)) {
      if (nom in portailClair) {
        assert.equal(valeur, portailClair[nom], `thème clair, jeton ${nom}`);
      }
    }
    for (const [nom, valeur] of Object.entries(extensionSombre)) {
      if (nom in portailSombre) {
        assert.equal(valeur, portailSombre[nom], `thème sombre, jeton ${nom}`);
      }
    }
  });

  it("reprend bien les jetons qui portent l'identité", () => {
    // Sans cette liste, le test précédent passerait sur un fichier vide.
    for (const nom of ["--fond", "--encre", "--trait", "--accent", "--laiton", "--carte",
                       "--or", "--creme", "--nuit", "--display", "--texte",
                       "--a", "--b", "--c", "--d", "--e"]) {
      assert.ok(nom in extensionClair, `jeton ${nom} absent de ${CSS_EXTENSION}`);
    }
    for (const nom of ["--fond", "--encre", "--trait", "--accent", "--laiton", "--carte"]) {
      assert.ok(nom in extensionSombre, `jeton ${nom} absent du thème sombre`);
    }
  });

  it("donne aux grades la couleur que le service worker peint sur le badge", () => {
    // Le badge est dessiné par Chrome, hors de toute feuille de style : la couleur est
    // codée dans fond.ts. Une divergence donnerait un badge d'une autre couleur que la
    // pastille du panneau qu'il annonce.
    const fond = lire("src/fond.ts");
    for (const grade of ["A", "B", "C", "D", "E"]) {
      const couleur = extensionClair[`--${grade.toLowerCase()}`];
      assert.match(
        fond,
        new RegExp(`${grade}:\\s*"${couleur}"`),
        `fond.ts ne peint pas le grade ${grade} en ${couleur}`,
      );
    }
  });
});

describe("logotype", () => {
  it("a le même tracé que celui du bandeau du portail", () => {
    assert.deepEqual(geometrie(lire(CHEMIN_LOGO)), geometrie(lire(LOGO_PORTAIL)));
  });

  it("suit la couleur du texte plutôt qu'une couleur en dur", () => {
    const svg = lire(CHEMIN_LOGO);
    assert.match(svg, /stroke="currentColor"/);
    assert.doesNotMatch(svg, /#[0-9a-fA-F]{3,6}/);
  });

  it("est injecté dans chaque page par le build, jamais recopié à la main", () => {
    for (const page of ["src/accueil/accueil.html", "src/options/options.html",
                        "src/panneau/panneau.html"]) {
      const html = lire(page);
      assert.equal(html.split("<!--LOGO-->").length - 1, 1, `marqueur absent ou en double : ${page}`);
      assert.doesNotMatch(html, /<svg/, `${page} contient un SVG recopié`);
    }
    const build = lire("build.mjs");
    assert.match(build, /<!--LOGO-->/);
  });
});

describe("icônes de la barre d'outils", () => {
  it("sont à jour vis-à-vis du logotype", () => {
    // Engendrées, pas dessinées : si quelqu'un modifie le tracé sans relancer
    // `npm run icones`, l'icône de Chrome ne représenterait plus la même chose que le site.
    for (const taille of TAILLES) {
      const attendu = encoderPng(rendre(taille), taille);
      const versionne = readFileSync(cheminIcone(taille));
      assert.ok(
        attendu.equals(versionne),
        `icones/lynceus-${taille}.png diffère du logotype : relancer « npm run icones »`,
      );
    }
  });

  it("sont des PNG valides à la taille annoncée par le manifeste", () => {
    const manifeste = JSON.parse(lire("manifest.json"));
    for (const [taille, chemin] of Object.entries(manifeste.icons)) {
      const png = readFileSync(chemin);
      assert.deepEqual([...png.subarray(0, 8)], [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
      assert.equal(png.readUInt32BE(16), Number(taille), `largeur de ${chemin}`);
      assert.equal(png.readUInt32BE(20), Number(taille), `hauteur de ${chemin}`);
    }
  });
});

describe("polices embarquées", () => {
  it("sont les fichiers du portail, à l'octet près", () => {
    for (const nom of ["fraunces-latin.woff2", "newsreader-latin.woff2"]) {
      assert.ok(
        readFileSync(`polices/${nom}`).equals(readFileSync(`${POLICES_PORTAIL}/${nom}`)),
        `polices/${nom} diffère de celle du portail`,
      );
    }
  });

  it("sont servies depuis l'extension, jamais depuis un tiers", () => {
    // Une page qui charge sa police sur un CDN annonce son ouverture à une société
    // extérieure. Pour une extension qui promet la vie privée, ce serait une faute.
    const css = lire(CSS_EXTENSION);
    assert.match(css, /url\("\.\.\/polices\/fraunces-latin\.woff2"\)/);
    assert.match(css, /url\("\.\.\/polices\/newsreader-latin\.woff2"\)/);
    assert.doesNotMatch(css, /https?:\/\//);
  });

  it("gardent leur licence OFL auprès des fichiers", () => {
    assert.match(lire("polices/LICENSE"), /Open Font License/);
  });
});

describe("textes visibles", () => {
  it("ne contiennent pas de tiret cadratin", () => {
    // Demande explicite de l'utilisateur : les textes sont reformulés, pas ponctués au
    // tiret long. Le manifeste compte, c'est ce que Chrome affiche dans sa liste.
    for (const fichier of ["manifest.json", "package.json", "src/accueil/accueil.html",
                           "src/options/options.html", "src/panneau/panneau.html",
                           "src/panneau/panneau.css", CSS_EXTENSION]) {
      assert.ok(!lire(fichier).includes("—"), `tiret cadratin dans ${fichier}`);
    }
  });
});
