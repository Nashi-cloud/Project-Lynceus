# Corpus de calibration

Pages de référence servant à évaluer chaque évolution des prompts et de la méthodologie (aucune régression silencieuse — cf. docs/METHODOLOGIE.md §7).

## Format (`corpus.yaml`)

```yaml
- url: https://exemple-satirique.example/article-parodique
  categorie_attendue: satire
  grade_attendu: [A, B]        # fourchette acceptable
  techniques_interdites: []     # détections qui seraient des faux positifs graves
  notes: Site parodique connu — crash-test satire, ne doit JAMAIS sortir en pseudo_science
- url: https://exemple-pseudo-medical.example/remede-miracle
  categorie_attendue: pseudo_science
  grade_attendu: [D, E]
  techniques_attendues: [conflit_interet_commercial, solution_miracle]
  notes: La boutique liée DOIT être détectée
```

## Cas sentinelles obligatoires

1. **Satire** (type Gorafi) → jamais classée trompeuse.
2. **Éditorial de qualité** → jamais pénalisé pour sa position.
3. **Pseudo-médecine marchande** → conflit d'intérêt détecté.
4. **Article factuel de référence** → grade A/B, peu ou pas de techniques.
5. **Contenu confessionnel non manipulateur** → la foi n'est pas notée.

## À faire (phase 1)

- [ ] Constituer ~50 entrées réelles (fiables, douteuses, satiriques, complotistes, confessionnelles) — de préférence des captures archivées (Wayback Machine) pour la stabilité du contenu.
- [ ] Script `api/cli` : `lynceus calibrer corpus/corpus.yaml` → rapport de conformité.

> ⚠️ Ce corpus référencera des sites de désinformation **à des fins de calibration et d'éducation** uniquement.
