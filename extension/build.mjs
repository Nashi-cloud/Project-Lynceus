import { build } from "esbuild";
import { cpSync, mkdirSync, rmSync } from "node:fs";

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
  logLevel: "info",
});

cpSync("manifest.json", "dist/manifest.json");
cpSync("src/panneau/panneau.html", "dist/panneau/panneau.html");
cpSync("src/panneau/panneau.css", "dist/panneau/panneau.css");
cpSync("src/options/options.html", "dist/options/options.html");
cpSync("src/accueil/accueil.html", "dist/accueil/accueil.html");
cpSync("icones", "dist/icones", { recursive: true });
console.log("→ dist/ prêt (chrome://extensions → Charger l'extension non empaquetée)");
