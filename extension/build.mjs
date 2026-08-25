import { build } from "esbuild";
import { cpSync, mkdirSync, rmSync } from "node:fs";

// Portail proposé par défaut dans l'extension : `node build.mjs --portail=https://…`.
// Un portail qui distribue le paquet le construit avec sa propre adresse, si bien que
// l'utilisateur n'a rien à saisir pour obtenir sa clé. Vide par défaut — un paquet
// construit sans cette option ne pointe vers personne, ce qui est le bon défaut.
const portailParDefaut =
  process.argv.find((a) => a.startsWith("--portail="))?.slice("--portail=".length) ?? "";

rmSync("dist", { recursive: true, force: true });
mkdirSync("dist", { recursive: true });

await build({
  entryPoints: [
    "src/fond.ts",            // service worker
    "src/extracteur.ts",      // injecté dans la page (Readability + Turndown)
    "src/panneau/panneau.ts", // side panel
    "src/options/options.ts", // page de réglages
    "src/accueil/accueil.ts",  // page d'accueil (installation)
  ],
  bundle: true,
  format: "iife",
  target: "chrome116",
  outdir: "dist",
  outbase: "src",
  define: { PORTAIL_PAR_DEFAUT: JSON.stringify(portailParDefaut) },
  logLevel: "info",
});

cpSync("manifest.json", "dist/manifest.json");
cpSync("src/panneau/panneau.html", "dist/panneau/panneau.html");
cpSync("src/panneau/panneau.css", "dist/panneau/panneau.css");
cpSync("src/options/options.html", "dist/options/options.html");
cpSync("src/accueil/accueil.html", "dist/accueil/accueil.html");
cpSync("icones", "dist/icones", { recursive: true });
console.log("→ dist/ prêt (chrome://extensions → Charger l'extension non empaquetée)");

// --paquet : archive ZIP prête à distribuer ou à soumettre au Chrome Web Store.
// Écrite en Node plutôt qu'avec la commande `zip`, absente de bien des systèmes.
if (process.argv.includes("--paquet")) {
  const { readFileSync, readdirSync, statSync, writeFileSync } = await import("node:fs");
  const { deflateRawSync } = await import("node:zlib");
  const { join, relative, sep } = await import("node:path");

  const version = JSON.parse(readFileSync("manifest.json", "utf-8")).version;
  const archive = `lynceus-extension-v${version}.zip`;

  const fichiersDe = (racine) =>
    readdirSync(racine).flatMap((entree) => {
      const chemin = join(racine, entree);
      return statSync(chemin).isDirectory() ? fichiersDe(chemin) : [chemin];
    });

  // Écriture manuelle d'un ZIP (méthode « deflate ») : format simple et stable, sans
  // dépendance externe. Horodatage fixe pour que deux builds identiques produisent le même
  // fichier — on peut ainsi vérifier qu'un paquet distribué correspond bien aux sources.
  const DATE_FIXE = 0x2100;
  const entrees = [];
  const morceaux = [];
  let decalage = 0;

  for (const chemin of fichiersDe("dist")) {
    const nom = relative("dist", chemin).split(sep).join("/");
    const contenu = readFileSync(chemin);
    const compresse = deflateRawSync(contenu);
    const crc = crc32(contenu);
    const nomBrut = Buffer.from(nom, "utf-8");

    const enTete = Buffer.alloc(30);
    enTete.writeUInt32LE(0x04034b50, 0);
    enTete.writeUInt16LE(20, 4);
    enTete.writeUInt16LE(8, 8); // deflate
    enTete.writeUInt16LE(DATE_FIXE, 12);
    enTete.writeUInt32LE(crc, 14);
    enTete.writeUInt32LE(compresse.length, 18);
    enTete.writeUInt32LE(contenu.length, 22);
    enTete.writeUInt16LE(nomBrut.length, 26);

    morceaux.push(enTete, nomBrut, compresse);
    entrees.push({ nom: nomBrut, crc, tailleCompressee: compresse.length, taille: contenu.length, decalage });
    decalage += enTete.length + nomBrut.length + compresse.length;
  }

  const central = [];
  for (const e of entrees) {
    const enTete = Buffer.alloc(46);
    enTete.writeUInt32LE(0x02014b50, 0);
    enTete.writeUInt16LE(20, 4);
    enTete.writeUInt16LE(20, 6);
    enTete.writeUInt16LE(8, 10);
    enTete.writeUInt16LE(DATE_FIXE, 14);
    enTete.writeUInt32LE(e.crc, 16);
    enTete.writeUInt32LE(e.tailleCompressee, 20);
    enTete.writeUInt32LE(e.taille, 24);
    enTete.writeUInt16LE(e.nom.length, 28);
    enTete.writeUInt32LE(e.decalage, 42);
    central.push(enTete, e.nom);
  }
  const tailleCentral = central.reduce((total, b) => total + b.length, 0);

  const fin = Buffer.alloc(22);
  fin.writeUInt32LE(0x06054b50, 0);
  fin.writeUInt16LE(entrees.length, 8);
  fin.writeUInt16LE(entrees.length, 10);
  fin.writeUInt32LE(tailleCentral, 12);
  fin.writeUInt32LE(decalage, 16);

  writeFileSync(archive, Buffer.concat([...morceaux, ...central, fin]));
  console.log(`→ ${archive} (${entrees.length} fichiers) prêt à distribuer`);
}

/** CRC-32, exigé par le format ZIP (table calculée au premier appel). */
function crc32(donnees) {
  let table = crc32.table;
  if (!table) {
    table = crc32.table = new Int32Array(256);
    for (let i = 0; i < 256; i++) {
      let valeur = i;
      for (let bit = 0; bit < 8; bit++) valeur = valeur & 1 ? (valeur >>> 1) ^ 0xedb88320 : valeur >>> 1;
      table[i] = valeur;
    }
  }
  let crc = -1;
  for (const octet of donnees) crc = (crc >>> 8) ^ table[(crc ^ octet) & 0xff];
  return (crc ^ -1) >>> 0;
}
