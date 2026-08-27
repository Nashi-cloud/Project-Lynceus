# Calibration results

<!-- traduit-de: corpus/RESULTATS.md sha256:a1d721e5971c128c -->

> Translation for information. The French version, `corpus/RESULTATS.md`, is the record of reference: should the two ever diverge, it is the one that counts.

<!-- calibration:début (engendré par « lynceus calibrer --ecrire », ne pas modifier à la main) -->

Latest run: **2026-08-27** · model `z-ai/glm-5.2` (through openrouter.ai) · prompt **v0.1.2** · temperature **0**

**One run** recorded on this prompt version: **11/13\*** conforming. A single run says nothing solid, since the model does not return the same analysis of the same text twice.

Runs marked with an asterisk were served entirely from the directory cache: they replay an already recorded measurement instead of producing a new one. A genuinely independent draw needs a blank database.

| Case | Category | Grade | Score | Discrepancies |
|---|---|---|---|---|
| The council votes unanimously against unanimity | satire | A | 88 | — |
| Why I think our town has it wrong about paid parking | opinion | A | 84 | — |
| The forgotten root the laboratories would rather you did not know about | publicite_sponsorise | E | 7 | — |
| The Vieille-Écluse bridge closed for works from 3 to 28 March | information | A | 84 | — |
| Advent meditation: waiting as a path | contenu_confessionnel | C | 57 | — |
| The November power cut: three awkward questions | theorie_du_complot | E | 9 | — |
| What They Won't Tell You About the New Water Treatment Plant | theorie_du_complot | E | 2 | — |
| Five evening habits for better sleep | publicite_sponsorise | B | 66 | grade B outside the expected range C, D |
| Water fluoridation: the debate is still open | opinion | D | 40 | — |
| Why the sky is blue, and why that explanation is incomplete | information | B | 70 | category `information` instead of analyse_expertise |
| What three years of medical wandering taught me | temoignage | C | 60 | — |
| Confirmation bias — Wikipedia | information | A | 92 | — |
| SOTT Earth Changes Summary - June 2026 | pseudo_science | D | 30 | — |

<!-- calibration:fin -->

## How to read it

Only one run is recorded on this prompt version, and it was served from the directory cache. It therefore says what the instance returns today, not what a fresh draw would give. The runs carried out before the journal existed appear in the history at the end of the page, with the figures as they were noted at the time.

The five sentinels of [METHODOLOGIE.md](../../docs/en/METHODOLOGIE.md) §7 hold: satire stays classified as `satire`, argued opinion is not penalised for its position, commercial pseudo-medicine comes out at E, factual news at A, and religious content stays in its category with none of the forbidden techniques found. The English specimen is analysed in English, which the corpus checks explicitly through `langue_attendue`.

Two discrepancies out of thirteen cases:

- **Science writing** classified as `information` instead of `analyse_expertise`. The line between the two is thin: an article explaining a phenomenon while citing the state of knowledge fits both readings. It is nonetheless a serious failure as far as the corpus is concerned, because the category there is an exact expectation and not an appreciation.
- **Disguised advertising** graded B where the expected range is C to D. One notch above: the device is seen, its seriousness judged lower. A minor discrepancy.

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
| 2026-08-27 | v0.1.2 | 0 | 11/13, first run recorded in the journal (served from the cache) |
| 2026-08-27 | v0.1.2 | 0 | 13/13, 10/13, 11/12 over three runs |
| 2026-08-27 | v0.1.2 | 0.2 | 11/13 on one run, then 9, 11, 9 over three control runs |
| 2026-08-24 | v0.1.1 | 0.2 | 12/12 conforming (single run, 12 cases) |
