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

# ---------- Calibration (optionnelle : serveur requis, consomme des tokens) ----------
if [ "${1:-}" = "--calibrer" ]; then
  etape "Calibration du corpus (appels LLM réels)"
  if curl -sf --max-time 5 "${LYNCEUS_API_URL:-http://localhost:8000}/v1/meta" > /dev/null; then
    api/.venv/bin/lynceus calibrer corpus/corpus.yaml 2>&1 | tail -3
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
