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

## Results

See [en/RESULTATS.md](en/RESULTATS.md). Latest run: three passes with `z-ai/glm-5.2` and prompt v0.1.2 at temperature 0, giving 13/13, 10/13 and 11/12 conforming.

> A corpus adjusted until everything passes measures nothing any more. Every relaxed expectation must be justified by an examination of the case, and must never bear on the expected or forbidden techniques, which are the heart of the test.
