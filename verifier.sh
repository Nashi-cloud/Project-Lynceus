#!/usr/bin/env bash
# Vérification complète du projet Lynceus — à lancer avant tout merge dans dev.
#
#   ./verifier.sh              tests API + extension (hors ligne, rapide)
#   ./verifier.sh --calibrer   + passe de calibration (nécessite le serveur ET consomme des tokens)
#
# Code de sortie non nul dès qu'une étape échoue.

set -uo pipefail
cd "$(dirname "$0")"

VERT='\033[0;32m'; ROUGE='\033[0;31m'; JAUNE='\033[0;33m'; GRAS='\033[1m'; FIN='\033[0m'
echecs=0

etape() { printf "\n${GRAS}▸ %s${FIN}\n" "$1"; }
verdict() {
  if [ "$1" -eq 0 ]; then printf "${VERT}  ✓ %s${FIN}\n" "$2"
  else printf "${ROUGE}  ✗ %s${FIN}\n" "$2"; echecs=$((echecs + 1)); fi
}

# ---------- API ----------
etape "API — tests unitaires et d'intégration"
if [ -x api/.venv/bin/python ]; then
  (cd api && .venv/bin/python -m pytest -q 2>&1 | tail -3)
  verdict "${PIPESTATUS[0]}" "pytest"
else
  printf "${JAUNE}  ⚠ environnement absent — lancer : cd api && python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'${FIN}\n"
  echecs=$((echecs + 1))
fi

# ---------- Extension ----------
etape "Extension — typage strict"
if [ -d extension/node_modules ]; then
  (cd extension && npx tsc --noEmit)
  verdict $? "tsc --noEmit"

  etape "Extension — tests unitaires et parité de hachage avec l'API"
  (cd extension && npm test --silent 2>&1 | grep -E "^# (tests|pass|fail)|URL en parité")
  verdict "${PIPESTATUS[0]}" "npm test"

  etape "Extension — build"
  (cd extension && npm run build --silent > /dev/null)
  verdict $? "dist/ reconstruit"
else
  printf "${JAUNE}  ⚠ dépendances absentes — lancer : cd extension && npm install${FIN}\n"
  echecs=$((echecs + 1))
fi

# ---------- Cohérence des versions de l'extension ----------
etape "Extension — cohérence des versions"
if [ -f extension/manifest.json ]; then
  v_manifest=$(python3 -c "import json;print(json.load(open('extension/manifest.json'))['version'])")
  v_package=$(python3 -c "import json;print(json.load(open('extension/package.json'))['version'])")
  if [ "$v_manifest" = "$v_package" ]; then
    if grep -q "^## $v_manifest " extension/CHANGELOG.md; then
      verdict 0 "v$v_manifest cohérente (manifest, package, changelog)"
    else
      printf "${ROUGE}  ✗ v%s absente de extension/CHANGELOG.md${FIN}\n" "$v_manifest"
      echecs=$((echecs + 1))
    fi
  else
    printf "${ROUGE}  ✗ manifest.json (%s) ≠ package.json (%s)${FIN}\n" "$v_manifest" "$v_package"
    echecs=$((echecs + 1))
  fi
fi

# ---------- Cohérence des versions de l'API ----------
# Trois fichiers portent le même numéro, et la CI en fait une étiquette d'image
# (`vX.Y.Z`) au moment de publier `main`. Un décalage ici, et l'image publiée ne dit
# pas la même chose que l'instance qu'elle fait tourner : `/v1/meta` annoncerait une
# version que personne ne pourrait redéployer.
etape "API — cohérence des versions"
if [ -f VERSION ]; then
  v_fichier=$(tr -d '[:space:]' < VERSION)
  v_paquet=$(grep -m1 '^version = ' api/pyproject.toml | cut -d'"' -f2)
  v_module=$(grep -m1 '^__version__' api/lynceus/__init__.py | cut -d'"' -f2)
  if [ "$v_fichier" = "$v_paquet" ] && [ "$v_fichier" = "$v_module" ]; then
    verdict 0 "v$v_fichier cohérente (VERSION, pyproject, __init__)"
  else
    printf "${ROUGE}  ✗ VERSION (%s) ≠ pyproject (%s) ≠ __init__ (%s)${FIN}\n" \
      "$v_fichier" "$v_paquet" "$v_module"
    echecs=$((echecs + 1))
  fi
fi

# Un second fichier VERSION n'est lu par personne : ni par le contrôle ci-dessus, ni par la
# CI qui étiquette l'image depuis celui de la racine. Il affiche donc un numéro qui n'engage
# rien et que rien ne fait vieillir, ce qui est pire que pas de numéro du tout. `api/VERSION`
# est resté ainsi trois versions mineures en arrière sans qu'aucun contrôle s'en aperçoive.
doublons=$(git ls-files '*VERSION' | grep -v '^VERSION$' || true)
if [ -n "$doublons" ]; then
  verdict 1 "fichier VERSION en double, seul celui de la racine fait foi : $(echo $doublons)"
else
  verdict 0 "un seul fichier VERSION, à la racine"
fi

# ---------- Traductions des documents de référence ----------
# Une traduction est une copie : elle dérive dès que l'original bouge, et rien ne le
# signale puisque les deux pages s'affichent aussi bien. L'inventaire est tenu par
# `lynceus traductions`, qui échoue si une traduction est en retard et se contente de
# nommer celles qui manquent encore.
etape "Documents traduits — accord avec leur original"
if [ -x api/.venv/bin/lynceus ]; then
  if sortie=$(api/.venv/bin/lynceus traductions 2>&1); then
    verdict 0 "$(printf '%s' "$sortie" | grep -c 'à jour') traduction(s) à jour"
    printf '%s\n' "$sortie" | grep -E "encore à traduire" | sed 's/^/  /' || true
  else
    printf '%s\n' "$sortie" | tail -3
    echecs=$((echecs + 1))
  fi
fi

# ---------- Cohérence de la version de prompt ----------
# Un seul compteur pour trois fichiers : le prompt, la méthodologie et la taxonomie
# évoluent ensemble, et `prompt_version` est ce que chaque analyse annonce. Un décalage
# ici, et le portail publie une méthodologie qui dit appliquer une version que le moteur
# n'utilise plus. RESULTATS.md est du même lot : la calibration porte sur une version
# précise, sans quoi le taux d'erreur affiché ne se rapporte à rien.
etape "Prompt, méthodologie et calibration — cohérence des versions"
v_prompt=$(ls prompts/analyse/v*.md 2>/dev/null | sed 's|.*/v||;s|\.md$||' | sort -V | tail -1)
if [ -n "$v_prompt" ]; then
  v_methode=$(grep -m1 -oE 'Version : \*\*[0-9.]+\*\*' docs/METHODOLOGIE.md | tr -dc '0-9.')
  v_taxo=$(grep -m1 -oE 'Version : \*\*[0-9.]+\*\*' docs/TAXONOMIE.md | tr -dc '0-9.')
  v_calib=$(grep -m1 -oE 'prompt \*\*v[0-9.]+\*\*' corpus/RESULTATS.md | tr -dc '0-9.')
  if [ "$v_prompt" = "$v_methode" ] && [ "$v_prompt" = "$v_taxo" ] && [ "$v_prompt" = "$v_calib" ]; then
    verdict 0 "v$v_prompt cohérente (prompt, méthodologie, taxonomie, calibration)"
  else
    printf "${ROUGE}  ✗ prompt (%s) ≠ méthodologie (%s) ≠ taxonomie (%s) ≠ calibration (%s)${FIN}\n" \
      "$v_prompt" "$v_methode" "$v_taxo" "$v_calib"
    printf "${ROUGE}    Une passe de calibration est due, ou une estampille n'a pas suivi.${FIN}\n"
    echecs=$((echecs + 1))
  fi
fi

# ---------- Secrets ----------
# La détection de GitHub reconnaît les jetons de fournisseurs connus, à leur préfixe. Elle
# ne reconnaîtra jamais les trois secrets propres à ce projet, qui n'ont aucune forme
# remarquable : la clé privée qui signe les accès, les URL de webhook Portainer, et les noms
# de machines du tailnet. Les motifs personnalisés demandent Advanced Security, absent d'un
# dépôt public gratuit. Cette étape est donc la seule qui les couvre.
etape "Secrets — rien qui ne doive rester hors du dépôt"
if sortie=$(outils/chercher-secrets.py 2>&1); then
  verdict 0 "$(printf '%s' "$sortie" | tail -1)"
else
  printf '%s\n' "$sortie" | sed 's/^/  /'
  echecs=$((echecs + 1))
fi

# ---------- Provenance des chiffres publiés ----------
# L'étape précédente vérifie que les estampilles s'accordent. Elle ne dit rien de la
# provenance des chiffres : rien n'empêcherait d'avancer une version sans avoir relancé la
# moindre analyse. Le tableau publié est donc engendré depuis `corpus/passes.jsonl`, journal
# des passes réellement exécutées, et cette étape le réengendre pour le comparer.
etape "Calibration — les chiffres publiés viennent d'une passe enregistrée"
if [ -x api/.venv/bin/lynceus ]; then
  if sortie=$(api/.venv/bin/lynceus calibration 2>&1); then
    verdict 0 "$(printf '%s' "$sortie" | tr -d '\n' | sed 's/^[[:space:]]*//')"
  else
    printf '%s\n' "$sortie" | sed 's/^/  /'
    echecs=$((echecs + 1))
  fi
fi

# ---------- Calibration (optionnelle : serveur requis, consomme des tokens) ----------
if [ "${1:-}" = "--calibrer" ]; then
  etape "Calibration du corpus (appels LLM réels)"
  if curl -sf --max-time 5 "${LYNCEUS_API_URL:-http://localhost:8000}/v1/meta" > /dev/null; then
    api/.venv/bin/lynceus calibrer corpus/corpus.yaml --ecrire 2>&1 | tail -4
    verdict "${PIPESTATUS[0]}" "corpus conforme"
  else
    printf "${ROUGE}  ✗ instance injoignable — démarrer : cd api && .venv/bin/uvicorn lynceus.main:creer_application --factory --host 0.0.0.0${FIN}\n"
    echecs=$((echecs + 1))
  fi
else
  printf "\n${JAUNE}Calibration non exécutée (--calibrer pour l'inclure : serveur requis, consomme des tokens).${FIN}\n"
fi

# ---------- Verdict ----------
if [ "$echecs" -eq 0 ]; then
  printf "\n${VERT}${GRAS}Tout est vert.${FIN}\n"
else
  printf "\n${ROUGE}${GRAS}%d étape(s) en échec.${FIN}\n" "$echecs"
fi
exit $((echecs > 0))
