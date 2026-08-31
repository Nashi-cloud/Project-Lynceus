# Calibration results

<!-- traduit-de: corpus/RESULTATS.md sha256:36d3e668899dab5b -->

> Translation for information. The French version, `corpus/RESULTATS.md`, is the record of reference: should the two ever diverge, it is the one that counts.

<!-- calibration:début (engendré par « lynceus calibrer --ecrire », ne pas modifier à la main) -->

Latest run: **2026-08-31** · model `z-ai/glm-5.2` (through openrouter.ai) · prompt **v0.1.3** · temperature **0**

**One run** recorded on this prompt version: **11/13** conforming. A single run says nothing solid, since the model does not return the same analysis of the same text twice.

| Case | Category | Grade | Score | Discrepancies |
|---|---|---|---|---|
| The council votes unanimously against unanimity | satire | A | 85 | — |
| Why I think our town has it wrong about paid parking | opinion | A | 82 | — |
| The forgotten root the laboratories would rather you did not know about | publicite_sponsorise | E | 7 | — |
| The Vieille-Écluse bridge closed for works from 3 to 28 March | information | A | 82 | — |
| Advent meditation: waiting as a path | contenu_confessionnel | A | 89 | — |
| The November power cut: three awkward questions | theorie_du_complot | E | 8 | — |
| What They Won't Tell You About the New Water Treatment Plant | theorie_du_complot | E | 14 | — |
| Five evening habits for better sleep | publicite_sponsorise | C | 50 | — |
| Water fluoridation: the debate is still open | information | D | 38 | — |
| Why the sky is blue, and why that explanation is incomplete | analyse_expertise | B | 70 | — |
| What three years of medical wandering taught me | temoignage | A | 81 | grade A outside the expected range B, C, D |
| Confirmation bias — Wikipedia | information | A | 93 | — |
| SOTT Earth Changes Summary - June 2026 | opinion | D | 39 | category `opinion` instead of theorie_du_complot, pseudo_science |

<!-- calibration:fin -->

## How to read it

Only one run is recorded on this prompt version. Nothing in it was served from the directory cache: caching is keyed on the pair of content and prompt version, so a change of prompt forces a fresh analysis of all thirteen cases. It therefore says what one draw returned, not what three draws would return. The runs carried out before the journal existed appear in the history at the end of the page, with the figures as they were noted at the time.

The five sentinels of [METHODOLOGIE.md](../../docs/en/METHODOLOGIE.md) §7 hold: satire stays classified as `satire`, argued opinion is not penalised for its position, commercial pseudo-medicine comes out at E, factual news at A, and religious content stays in its category with none of the forbidden techniques found. The English specimen is analysed in English, which the corpus checks explicitly through `langue_attendue`.

Two discrepancies out of thirteen cases:

- **A real captured page aggregating conspiracy material** classified as `opinion` instead of `theorie_du_complot` or `pseudo_science`. A serious failure: the category is an exact expectation. The grade stays at D and the score at 39, so the judgement shown to the reader is not inverted, but the nature of the content is named wrongly, and naming it is exactly what the tool claims to do.
- **A personal account** graded A where the expected range is B to D. One notch above. A minor discrepancy.

### What moving from v0.1.2 to v0.1.3 shifted

Prompt v0.1.3 gives the ten categories the definitions `docs/METHODOLOGIE.md` already published. Until then they were a bare list of identifiers, and calibration was penalising a boundary the prompt drew nowhere. The total does not move, 11 out of 13 before and after, but the composition changes entirely, and it has to be read case by case rather than on the total.

**Both discrepancies published under v0.1.2 are gone.** Science writing now comes out as `analyse_expertise`, which the added definition states explicitly. Disguised advertising returns to C, inside its range. The first is a causal fix, the definition settles the boundary; the second may be no more than a kinder draw.

**Two new discrepancies appear**, described above.

**Two conforming cases moved a great deal without leaving their range.** Religious content goes from C 57 to A 89, the personal account from C 60 to A 81. Both movements exceed the spread measured at temperature 0, which peaked at 11 points between runs, so they come from the prompt and not from the draw. The plausible explanation is that the added wording, "the dominant nature of the content, **not its quality**", stopped a text being penalised for not being journalism. If that reading is right, this is the intended behaviour, and it is then the expected ranges of those two cases that carry the old bias. That cannot be settled on one run, and certainly not by relaxing an expectation to make a test pass.

**Two questions therefore stay open**, to be settled by independent draws on a clean database and not by adjusting the corpus: is the conspiracy page tipping into `opinion` an effect of the definitions or the category instability already documented below, and is the rise in scores on the personal account and the religious content the correction of a bias or a new leniency.

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
| 2026-08-31 | v0.1.3 | 0 | 11/13, fresh analyses, both v0.1.2 discrepancies fixed and two others appeared |
| 2026-08-27 | v0.1.2 | 0 | 11/13, first run recorded in the journal (served from the cache) |
| 2026-08-27 | v0.1.2 | 0 | 13/13, 10/13, 11/12 over three runs |
| 2026-08-27 | v0.1.2 | 0.2 | 11/13 on one run, then 9, 11, 9 over three control runs |
| 2026-08-24 | v0.1.1 | 0.2 | 12/12 conforming (single run, 12 cases) |
