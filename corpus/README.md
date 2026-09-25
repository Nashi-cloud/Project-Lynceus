# Calibration corpus

**English** · [Français](README.fr.md)

Reference pages used to evaluate every change to the prompts and to the methodology (no silent regression, see [docs/en/METHODOLOGIE.md](../docs/en/METHODOLOGIE.md) §7).

## Format (`corpus.yaml`)

Each entry carries **either** `fichier` (a frozen specimen from the repository) **or** `url` (a real page):

```yaml
- fichier: specimens/04-fictif-satire.md
  titre: Le conseil municipal vote à l'unanimité contre l'unanimité
  categorie_attendue: satire            # or categories_acceptables: [a, b]
  grade_attendu: [A, B, C]              # acceptable range
  techniques_attendues: []              # ids that MUST be detected
  techniques_interdites: [verite_cachee]  # detections that would be serious false positives
  confiance_min: 0.5                    # optional floor
  notes: Crash-test satire — ne doit JAMAIS sortir en pseudo_science
```

The base is **local by choice**: a corpus of URLs breaks as soon as a page is edited, and fails on sites protected against automatic downloading. `url` entries remain possible, to anchor the calibration in the real world alongside the rest.

`categories_acceptables` exists for legitimately hybrid content (a pseudo-medical article selling a product is also disguised advertising): demanding a single label would test an arbitrary judgement call rather than the quality of the analysis.

## Running a calibration

```bash
lynceus calibrer corpus/corpus.yaml                      # report on the console
lynceus calibrer corpus/corpus.yaml --json rapport.json  # plus a detailed report
lynceus calibrer corpus/corpus.yaml --filtre satire      # a subset
lynceus calibrer corpus/corpus.yaml --parallele 12       # faster on your own instance
```

Cases are analysed **concurrently** (4 at a time by default), which divides the wait accordingly: measured on 12 cases at 3 s per analysis, 37 s sequentially against 9.6 s at 4 in parallel, and 4.2 s at 12. The default stays modest out of courtesy towards a shared instance; going up to 12 is justified on your own. Hitting the rate limit is not a failure: the request waits and resumes.

Deviations are graded: a wrong category, a missing expected technique or a false positive on a forbidden technique are **serious failures** (exit code 1); a grade one notch outside the range is a **minor deviation**.

## Mandatory sentinel cases

1. **Satire** → never classified as misleading.
2. **A good editorial** → never penalised for its position.
3. **Commercial pseudo-medicine** → conflict of interest detected.
4. **A factual reference article** → grade A or B, few techniques or none.
5. **Non-manipulative faith-based content** → faith is not graded.

Two traps complete the base: **false balance** (neutral tone, misleading device, must be detected) and **dense science writing** (legitimate technical vocabulary, must NOT trigger `jargon_pseudo_scientifique`).

## Growing the corpus

### Fictional specimens

The stable base, written to carry one precise device, versioned in the repository. See [specimens/README.md](specimens/README.md).

### Captures of real pages

They anchor the measurement in the real world: a specimen written to illustrate a technique necessarily contains it, whereas a real page does not.

**Captures are not versioned.** Reproducing whole articles in a public repository would raise a copyright problem, calibration use included. The repository contains only the **manifest**: URL, capture date, content digest and expectations. Everyone recreates the captures locally; the `content_hash` digest guarantees that everybody measures exactly the same text.

Practical consequences:

- a **missing** capture means the case is skipped, never counted as a failure (a freshly cloned repository must not look red);
- a **diverging** capture is reported explicitly: the page has changed, so it must be recaptured and the expectations re-examined, not adjusted blindly.

**Adding a page:**

```bash
# 1. Get the text of the page (extension, copy and paste, or trafilatura)
# 2. Save it as a capture; the command prints the entry to paste
lynceus capturer article.md --url https://example.org/article --titre "…"

# 3. ANALYSE it before fixing anything
lynceus analyser corpus/captures/article.md

# 4. Examine the result, then fill in the entry in corpus.yaml
```

The order matters: fixing an expectation before having seen the result amounts to inventing a ground truth. Fixing the expectation after examination means recording what is defensible, and only recording it if it is.

**Choosing the expected techniques.** Models vary in what they detect: only require the **stable** markers, the ones several models pick up. The SOTT case in the corpus requires a single technique (`verite_cachee`), the only one common to both models tested; the rest varied.

## Measuring beyond pass or fail

Calibration says whether a card meets its expectations, case by case. It cannot say by how much one analysis chain beats another, nor whether two runs of the same chain return the same thing. That is what [docs/en/ARCHITECTURE-CIBLE.md](../docs/en/ARCHITECTURE-CIBLE.md) calls step zero, and `lynceus mesurer` provides it without running any analysis:

```bash
lynceus mesurer corpus/corpus.yaml                          # gap between runs, annotator agreement
lynceus calibrer corpus/corpus.yaml --json rapport.json
lynceus mesurer corpus/corpus.yaml --rapport rapport.json   # + the chain against the annotations
```

Three measurements:

- **The gap between runs**, read from `passes.jsonl`: same category, same grade, score difference, and overlap of the detected techniques. The target is a zero gap.
- **Agreement between annotators**, on pages read by at least two of them. It is the reasonable ceiling for any machine.
- **The chain against the annotations**: category, grade, techniques per page, spans with partial overlap as in SemEval 2020 task 11 and CheckThat! 2024 task 3, and the share of excerpts found in the page.

### Annotating a page

The full procedure, from page selection to arbitration, is in [docs/en/ANNOTATION.md](../docs/en/ANNOTATION.md). In short:

One YAML file per page and per annotator, under `annotations/<annotator>/`. `lynceus annoter <case> --annotateur <pseudonym>` prints the skeleton, fingerprint included. Annotators copy the excerpt, never a position: the position is derived from the text, counted on the normalised Markdown whose fingerprint is `content_hash`. The annotated pages are listed in `evaluation.yaml`, apart from the calibration cases: a calibration run costs one analysis per case, and the evaluation set is far larger.

```yaml
cas: specimens/06-fictif-complotisme.md   # the case id, as in corpus.yaml
annotateur: a-pseudonym
guide: "1.4"                              # version of the annotation guide
content_hash: 3f2a…                       # printed by « lynceus annoter »
categorie: theorie_du_complot
grade: [D, E]
intervalles:
  - extrait: "what they will never tell you"
    technique: verite_cachee
  - extrait: "Coincidence?"
    occurrence: 2                         # when the excerpt appears several times
    technique: hyper_intentionnalisme
notes: Free text, read by the next annotator only after their own reading.
```

Annotate **before** looking at any card, and without looking at the other annotator's file: an annotation made with the answer in view measures agreement with the model, not the page. A faulty annotation (changed fingerprint, unknown technique, excerpt not in the page) makes `lynceus mesurer` fail, and the tests with it.

### Public corpora

`correspondances/` maps the labels of public datasets onto our 31 techniques: SemEval 2023 task 3, whose inventory is also that of CheckThat! 2024 task 3, and FLICC. Each label is `exact`, `partiel` (kept, with a caveat), `revue` (a human picks among candidates) or `aucun` (dropped). The tests check that every label is covered and every target exists in the reference list. The datasets themselves are not in the repository: each has its own licence.

## Results, and where the figures come from

The table in [en/RESULTATS.md](en/RESULTATS.md) is not written by hand: it is **generated** from `passes.jsonl`, the journal of runs actually executed.

```bash
lynceus calibrer corpus/corpus.yaml --ecrire
```

The command appends the run to the journal, then regenerates the table between its two markers, in both languages. Everything outside the markers, the reading of the results and what they teach, stays hand-written: a machine cannot say what a discrepancy means.

That is what makes the published figure checkable. `verifier.sh` regenerates the table and fails if it differs from the published one, or if no run exists for the prompt version in force. Before that, only the version stamp was checked: nothing stopped anyone from moving it forward without having run a single analysis, and the build would still have gone green.

The journal only ever grows, and the git history shows every addition: walking something back becomes a visible act. A run served entirely from the directory cache is counted as such, since it replays a measurement instead of producing a new one, and `--ecrire` refuses to journal it: three copies of one draw are not three runs.

**Repeating a run on an unchanged prompt version.** An analysis is cached on the pair (content fingerprint, prompt version), so a second run on the same version would simply be served the first one. Bumping the prompt version clears the way on its own, which covers the usual case. To repeat one version, the analyses of that version have to be cleared on the instance under measurement. On a development instance backed by SQLite:

```bash
python3 - <<'EOF'
import sqlite3
c = sqlite3.connect("lynceus.sqlite3")
ids = [r[0] for r in c.execute("SELECT id FROM analyses WHERE prompt_version = '0.1.7'")]
c.executemany("UPDATE pages SET analyse_courante_id = NULL WHERE analyse_courante_id = ?", [(i,) for i in ids])
c.executemany("DELETE FROM analyses WHERE id = ?", [(i,) for i in ids])
c.commit()
print(len(ids), "analyses cleared")
EOF
```

Never do this on the production instance: those analyses are the public directory, and pages point at them.

> A corpus adjusted until everything passes measures nothing any more. Every relaxed expectation must be justified by an examination of the case, and must never bear on the expected or forbidden techniques, which are the heart of the test.
