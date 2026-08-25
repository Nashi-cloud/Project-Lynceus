// Icônes de la barre d'outils, engendrées depuis le logotype du portail.
//
//   npm run icones
//
// Pourquoi un générateur plutôt que quatre PNG dessinés à la main : l'identité doit tenir
// en un seul endroit. Le tracé de référence est src/commun/logo.svg, celui du bandeau du
// site ; les valeurs reprises ici (l'œil s'ouvre de x=3,4 à x=28,6 et culmine à y=8,2,
// l'iris fait 3,7 de rayon) en sont extraites, et test/identite.test.mjs échoue si le SVG
// change sans que les icônes suivent.
//
// Le rendu est fait à la main, sans dépendance : Chrome n'accepte que des bitmaps pour
// l'icône d'action, et faire venir une bibliothèque de rendu SVG dans un projet qui ne
// dessine que quatre images serait payer cher une géométrie de trois cercles. L'œil est
// l'intersection de deux disques, ce qui donne exactement l'amande du logotype, et
// l'anticrénelage vient d'un suréchantillonnage 8x8.
//
// Une nuance assumée par rapport au SVG : ici le dessin est PLEIN, pas au trait. Un trait
// de 1,5 sur 32 devient un demi-pixel à 16x16, c'est-à-dire une bouillie grise. La forme
// reste la même, les couleurs sont celles du portail.

import { deflateSync } from "node:zlib";
import { writeFileSync, readFileSync } from "node:fs";

export const TAILLES = [16, 32, 48, 128];

// Palette du portail (statique/lynceus.css). Le fond est la nuit du récit, l'œil la crème,
// l'iris l'or : les trois couleurs qui portent l'identité partout ailleurs.
const NUIT = [0x12, 0x1a, 0x2c];
const CREME = [0xf6, 0xe8, 0xd4];
const OR = [0xe0, 0xa9, 0x62];

// Géométrie, dans le repère 0..32 du logotype.
const C = 16;            // centre
const R_DISQUE = 15.4;
const DEMI_LARGEUR = 12.6; // l'œil va de 3,4 à 28,6
const HAUTEUR = 7.8;       // il culmine à 8,2, soit 7,8 au-dessus de l'axe
const R_IRIS = 3.7;
const R_PUPILLE = 1.55;
// Arc de cercle passant par les trois points de l'amande : R = (a² + h²) / 2h.
const R_PAUPIERE = (DEMI_LARGEUR ** 2 + HAUTEUR ** 2) / (2 * HAUTEUR);
const DECALAGE = R_PAUPIERE - HAUTEUR; // centre des deux arcs, de part et d'autre de l'axe
// Graduations de la lunette : lisibles à partir de 48 px, du bruit en dessous.
const GRADUATION = { interieur: 13.4, exterieur: 14.9, demi_epaisseur: 0.62 };

const distance = (x, y, cx, cy) => Math.hypot(x - cx, y - cy);

/** Couleur d'un point du repère logotype, ou null s'il est hors de l'icône.
 *
 *  Le détail dépend de la taille : à 16 px, la pupille ferait moins d'un pixel et les
 *  graduations un liseré sale. Mieux vaut un dessin franc qu'un dessin complet illisible. */
function couleur(x, y, { graduations, pupille }) {
  const dCentre = distance(x, y, C, C);
  if (dCentre > R_DISQUE) return null;

  if (pupille && dCentre <= R_PUPILLE) return NUIT;
  if (dCentre <= R_IRIS) return OR;

  const dansAmande =
    distance(x, y, C, C + DECALAGE) <= R_PAUPIERE &&
    distance(x, y, C, C - DECALAGE) <= R_PAUPIERE;
  if (dansAmande) return CREME;

  if (graduations && dCentre >= GRADUATION.interieur && dCentre <= GRADUATION.exterieur) {
    const surAxeVertical = Math.abs(x - C) <= GRADUATION.demi_epaisseur;
    const surAxeHorizontal = Math.abs(y - C) <= GRADUATION.demi_epaisseur;
    if (surAxeVertical || surAxeHorizontal) return OR;
  }

  return NUIT;
}

/** Rendu d'une icône carrée, en RGBA non prémultiplié. */
export function rendre(taille) {
  const detail = { graduations: taille >= 48, pupille: taille >= 32 };
  const echantillons = 8; // 64 sous-pixels par pixel
  const pixels = Buffer.alloc(taille * taille * 4);

  for (let ligne = 0; ligne < taille; ligne++) {
    for (let colonne = 0; colonne < taille; colonne++) {
      let r = 0, v = 0, b = 0, couverts = 0;

      for (let sy = 0; sy < echantillons; sy++) {
        for (let sx = 0; sx < echantillons; sx++) {
          const x = ((colonne + (sx + 0.5) / echantillons) / taille) * 32;
          const y = ((ligne + (sy + 0.5) / echantillons) / taille) * 32;
          const c = couleur(x, y, detail);
          if (c) { r += c[0]; v += c[1]; b += c[2]; couverts++; }
        }
      }

      const total = echantillons * echantillons;
      const decalage = (ligne * taille + colonne) * 4;
      if (couverts > 0) {
        // Moyenne des seuls sous-pixels couverts : la couleur reste franche sur le bord,
        // c'est l'alpha qui adoucit. Mélanger avec du transparent donnerait un liseré terne.
        pixels[decalage] = Math.round(r / couverts);
        pixels[decalage + 1] = Math.round(v / couverts);
        pixels[decalage + 2] = Math.round(b / couverts);
        pixels[decalage + 3] = Math.round((couverts / total) * 255);
      }
    }
  }
  return pixels;
}

// ------------------------------------------------------------------ encodage PNG

const TABLE_CRC = (() => {
  const table = new Int32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    table[n] = c;
  }
  return table;
})();

function crc32(donnees) {
  let c = 0xffffffff;
  for (const octet of donnees) c = TABLE_CRC[(c ^ octet) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function morceau(type, donnees) {
  const longueur = Buffer.alloc(4);
  longueur.writeUInt32BE(donnees.length, 0);
  const corps = Buffer.concat([Buffer.from(type, "ascii"), donnees]);
  const controle = Buffer.alloc(4);
  controle.writeUInt32BE(crc32(corps), 0);
  return Buffer.concat([longueur, corps, controle]);
}

export function encoderPng(pixels, taille) {
  const entete = Buffer.alloc(13);
  entete.writeUInt32BE(taille, 0);
  entete.writeUInt32BE(taille, 4);
  entete[8] = 8;  // 8 bits par canal
  entete[9] = 6;  // RGBA
  // Les octets 10 à 12 restent à zéro : compression deflate, filtrage standard, pas d'entrelacement.

  // Chaque ligne est précédée de son octet de filtre. « 0 » (aucun filtre) suffit : les
  // images font quelques kilo-octets, et un filtre optimal n'en gagnerait que des poussières.
  const brut = Buffer.alloc(taille * (taille * 4 + 1));
  for (let ligne = 0; ligne < taille; ligne++) {
    const source = ligne * taille * 4;
    const cible = ligne * (taille * 4 + 1);
    brut[cible] = 0;
    pixels.copy(brut, cible + 1, source, source + taille * 4);
  }

  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    morceau("IHDR", entete),
    morceau("IDAT", deflateSync(brut, { level: 9 })),
    morceau("IEND", Buffer.alloc(0)),
  ]);
}

// ------------------------------------------------------------------------ sortie

/** Vérifie que le logotype n'a pas changé sous les constantes ci-dessus. */
export function verifierLogotype(svg) {
  for (const attendu of ["3.4 16", "8.2 16 8.2", "28.6 16", 'r="3.7"']) {
    if (!svg.includes(attendu)) {
      throw new Error(
        `src/commun/logo.svg ne contient plus « ${attendu} » : la géométrie du logotype a ` +
        "changé, il faut reprendre les constantes de icones.mjs avant d'engendrer les icônes.",
      );
    }
  }
}

export const CHEMIN_LOGO = new URL("./src/commun/logo.svg", import.meta.url);
export const cheminIcone = (taille) => new URL(`./icones/lynceus-${taille}.png`, import.meta.url);

// Exécuté seulement en ligne de commande : le fichier est aussi importé par les tests, qui
// ne doivent surtout pas réécrire les icônes au passage.
if (process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href) {
  engendrer();
}

function engendrer() {
// Garde-fou : si le logotype est modifié sans que ce fichier suive, les icônes ne
// représenteraient plus la même chose que le bandeau. On vérifie que les nombres repris
// ci-dessus figurent bien dans le SVG.
  verifierLogotype(readFileSync(CHEMIN_LOGO, "utf-8"));

  for (const taille of TAILLES) {
    const png = encoderPng(rendre(taille), taille);
    writeFileSync(cheminIcone(taille), png);
    console.log(`→ icones/lynceus-${taille}.png (${png.length} octets)`);
  }
}
