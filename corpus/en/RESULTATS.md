# Calibration results

<!-- traduit-de: corpus/RESULTATS.md sha256:fd49cc72cbe8b276 -->

> Translation for information. The French version, `corpus/RESULTATS.md`, is the record of reference: should the two ever diverge, it is the one that counts.

Latest run: **2026-08-27** · model `z-ai/glm-5.2` (through OpenRouter) · prompt **v0.1.2** · temperature **0**

**Three runs**, each on a fresh database to bypass the cache: **13/13**, **10/13** and **11/12** conforming. A single run would say nothing solid, since the model does not return the same analysis of the same text twice.

| Case | Category | Grade | Score | Discrepancies |
|---|---|---|---|---|
| The council votes unanimously against unanimity | satire | A | 91 to 98 | — |
| Why I think our town has it wrong | opinion | A | 82 to 87 | — |
| The forgotten root the laboratories would rather you did not know about | publicite_sponsorise | E | 7 to 14 | — |
| The Vieille-Écluse bridge closed for works | information | A | 80 to 86 | — |
| Advent meditation: waiting as a path | contenu_confessionnel | A | 82 to 89 | — |
| The November power cut: three awkward questions | theorie_du_complot | E | 8 to 12 | — |
| *What They Won't Tell You About the New Water Treatment Plant* (English) | opinion / theorie_du_complot | E | 10 to 11 | category `opinion` on one run |
| Five evening habits for better sleep | publicite_sponsorise | C | 61 to 64 | technique missing on one run: `conflit_interet_commercial` |
| Water fluoridation: the debate is still open | information / opinion | D D C | 46 to 52 | — |
| Why the sky is blue, and why that explanation is incomplete | analyse_expertise | B C B | 64 to 75 | grade C outside the expected range on one run |
| What three years of medical wandering taught me | temoignage | C | 55 to 63 | — |
| *Wikipedia — Confirmation bias* (real) | information | A | 89 to 93 | — |
| *SOTT — Earth changes* (real) | theorie_du_complot / opinion | D | 30 to 32 | category `opinion` on one run; page unreachable on another |

## How to read it

The six sentinels of [METHODOLOGIE.md](../../docs/en/METHODOLOGIE.md) §7 pass on all three runs:

- **Satire** classified as `satire`, never as disinformation.
- **Argued opinion** not penalised for its position (grade A).
- **Commercial pseudo-medicine**: grade E, and the commercial conflict of interest detected.
- **Factual news** graded well, with no detection of complacency.
- **Religious content**: no technique found, faith is not graded.
- **A page in English**: the analysis written in English, with the same techniques detected as on the equivalent French specimen.

## The temperature, measured

On 27 August a run revealed two cases whose verdict changed from one execution to the next. Rather than adjust the expectations, the question was put to the experiment: **is the model more stable at temperature 0?**

Six full runs of the corpus, three at 0.2 and three at 0.0, each on a fresh database so that no analysis could be served from the cache. Comparison over the 12 cases present in all six runs.

| | temperature 0.2 | temperature 0 |
|---|---|---|
| Conforming per run | 9, 11, 9 | 12, 10, 11 |
| Category changing between runs | 2 cases out of 12 | 2 cases out of 12 |
| Grade changing | 3 cases out of 12 | 2 cases out of 12 |
| Techniques detected changing | 4 cases out of 12 | 4 cases out of 12 |
| Spread of the score between runs | **10.8 on average, 61 at most** | **5.8 on average, 11 at most** |
| Cases strictly identical across the three runs | 5 out of 12 | 7 out of 12 |

The case that settled it is the satirical specimen. At temperature 0.2 the same text scored **99, then 79, then 38 out of 100**, that is grades A, B and D. A grade that shifts by three letters depending on the draw is not a grade. At 0 that case no longer moves (91 to 98, always A).

**Consequence: the default temperature is now 0.** The setting remains adjustable per instance, since reproducibility is not the only criterion one may hold to.

## What the experiment does not say

It does not make the system deterministic, and that must be said plainly: **at temperature 0, 5 cases out of 12 still vary** somewhere, in category, grade or techniques found. The provider is not deterministic even at 0, and two cases in the corpus sit close to a category boundary (science communication or expert analysis; news or opinion on a contested subject). The English specimen itself flips to `opinion` one run in three.

Nor are three runs enough to tell a difference of one conforming case from chance. What is solid here is the spread of the scores, where the gap is clear and points the same way across every case.

A single run will therefore keep being published with its discrepancies, never smoothed over.

## History

| Date | Prompt | Temperature | Result |
|---|---|---|---|
| 2026-08-27 | v0.1.2 | 0 | 13/13, 10/13, 11/12 over three runs |
| 2026-08-27 | v0.1.2 | 0.2 | 11/13 on one run, then 9, 11, 9 over three control runs |
| 2026-08-24 | v0.1.1 | 0.2 | 12/12 conforming (single run, 12 cases) |
