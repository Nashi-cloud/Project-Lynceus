# Calibration results

<!-- traduit-de: corpus/RESULTATS.md sha256:1e2a5d6450d65d74 -->

> Translation for information. The French version, `corpus/RESULTATS.md`, is the record of reference: should the two ever diverge, it is the one that counts.

<!-- calibration:début (engendré par « lynceus calibrer --ecrire », ne pas modifier à la main) -->

Latest run: **2026-08-31** · model `z-ai/glm-5.2` (through openrouter.ai) · prompt **v0.1.3** · temperature **0**

**3 runs** recorded on this prompt version: **11/13, 9/13, 12/13** conforming. A single run would say nothing solid, since the model does not return the same analysis of the same text twice.

| Case | Category | Grade | Score | Discrepancies |
|---|---|---|---|---|
| The council votes unanimously against unanimity | satire | A | 85 to 100 | — |
| Why I think our town has it wrong about paid parking | opinion | A | 82 to 84 | — |
| The forgotten root the laboratories would rather you did not know about | publicite_sponsorise | E | 7 to 16 | — |
| The Vieille-Écluse bridge closed for works from 3 to 28 March | information | A B A | 79 to 82 | — |
| Advent meditation: waiting as a path | contenu_confessionnel | A | 84 to 91 | — |
| The November power cut: three awkward questions | theorie_du_complot | E | 5 to 13 | — |
| What They Won't Tell You About the New Water Treatment Plant | theorie_du_complot | E | 10 to 14 | technique missing: `autorite_anonyme` (1 of 3 runs) |
| Five evening habits for better sleep | publicite_sponsorise | C B C | 50 to 66 | grade B outside the expected range C, D (1 of 3 runs) |
| Water fluoridation: the debate is still open | information / opinion | D | 38 to 40 | — |
| Why the sky is blue, and why that explanation is incomplete | analyse_expertise | B | 70 to 74 | — |
| What three years of medical wandering taught me | temoignage | A C A | 64 to 82 | grade A outside the expected range B, C, D (2 of 3 runs) |
| Confirmation bias — Wikipedia | information / analyse_expertise | A | 88 to 94 | category `analyse_expertise` instead of information (1 of 3 runs) |
| SOTT Earth Changes Summary - June 2026 | opinion / theorie_du_complot | D | 31 to 39 | category `opinion` instead of theorie_du_complot, pseudo_science (2 of 3 runs) |

<!-- calibration:fin -->

## How to read it

Three independent runs are recorded on this prompt version. Nothing in them was served from the directory cache: caching is keyed on the pair of content and prompt version, and the analyses for the current version were removed from the database between runs, so all thirteen cases were analysed afresh three times. The runs carried out before the journal existed appear in the history at the end of the page, with the figures as they were noted at the time.

The five sentinels of [METHODOLOGIE.md](../../docs/en/METHODOLOGIE.md) §7 hold across all three runs: satire stays classified as `satire`, argued opinion is not penalised for its position, commercial pseudo-medicine comes out at E, factual news at A, and religious content stays in its category with none of the forbidden techniques found. The English specimen is analysed in English, which the corpus checks explicitly through `langue_attendue`.

### What prompt v0.1.3 changed

v0.1.3 gives the ten categories the definitions `docs/METHODOLOGIE.md` already published. Until then they were a bare list of identifiers, and calibration was penalising a boundary the prompt drew nowhere.

**The intended fix holds.** Science writing comes out as `analyse_expertise` in all three runs, between 70 and 74, without a single discrepancy. That is a causal effect of the added definition rather than a kind draw: it was the serious failure published under v0.1.2, and it is gone.

**Religious content changed grade for good**, from C 57 under v0.1.2 to A in all three runs, between 84 and 91. The added wording, "the dominant nature of the content, not its quality", has plausibly stopped a text being penalised for not being journalism. The case stays conforming, its range running from A to C, but the shift is real and reproducible.

### What three runs do not allow us to conclude

The totals are **11, 9 and 12 out of 13**. Three figures that, over thirteen cases, cannot be told apart from chance: the score spread between runs reaches 7.8 points on average and 18 at most, and **3 cases out of 13 change category outright from one run to the next**. At that spread, a difference of two or three conformities is not a signal. This is a limit of the corpus, not of the prompt, and it is why enlarging the annotated corpus comes before any other optimisation: without it, an improvement cannot be told from a draw.

Two discrepancies recur in a majority of runs, and are therefore something other than noise:

- **The real conspiracy page comes out as `opinion` two runs out of three**, instead of `theorie_du_complot` or `pseudo_science`. The grade stays at D in every run, so the judgement shown to the reader is not inverted, but the nature of the content is named wrongly. The flip cannot be pinned on the definitions with certainty: v0.1.2 was never measured over three runs on this case, its single recorded run having been served from the directory cache.
- **The personal account comes out at A two runs out of three**, one notch above its range, with the largest score spread in the corpus at 18 points. That case sits on a boundary rather than inside a category.

One new discrepancy, in a minority of runs but instructive: **the encyclopaedic article on confirmation bias tips into `analyse_expertise` one run in three**, where `information` is expected. That is the mirror image of the defect just fixed. Giving `analyse_expertise` a definition now draws in-depth explanatory content towards it, which is consistent with the published definition and raises the question of its boundary with `information` for an encyclopaedia article.

None of these expectations has been adjusted. They are published as they stand, with the number of runs concerned.

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

The lines predating the journal were noted by hand, before `lynceus calibrer --ecrire` existed. They are kept as they are: rewriting them would give them a guarantee they do not have.

| Date | Prompt | Temperature | Result |
|---|---|---|---|
| 2026-08-31 | v0.1.3 | 0 | 11/13, 9/13, 12/13 over three fresh runs; science writing fixed in all three |
| 2026-08-27 | v0.1.2 | 0 | 11/13, first run recorded in the journal (served from the cache) |
| 2026-08-27 | v0.1.2 | 0 | 13/13, 10/13, 11/12 over three runs |
| 2026-08-27 | v0.1.2 | 0.2 | 11/13 on one run, then 9, 11, 9 over three control runs |
| 2026-08-24 | v0.1.1 | 0.2 | 12/12 conforming (single run, 12 cases) |
