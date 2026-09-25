# Calibration results

<!-- traduit-de: corpus/RESULTATS.md sha256:907f2818f82f1bea -->

> Translation for information. The French version, `corpus/RESULTATS.md`, is the record of reference: should the two ever diverge, it is the one that counts.

<!-- calibration:début (engendré par « lynceus calibrer --ecrire », ne pas modifier à la main) -->

Latest run: **2026-09-25** · model `z-ai/glm-5.2` (through openrouter.ai) · prompt **v0.1.8** · temperature **0**

**3 runs** recorded on this prompt version: **12/15, 11/15, 13/15** conforming. A single run would say nothing solid, since the model does not return the same analysis of the same text twice.

| Case | Category | Grade | Score | Discrepancies |
|---|---|---|---|---|
| The council votes unanimously against unanimity | satire | A | 84 to 92 | — |
| Why I think our town has it wrong about paid parking | opinion | A | 81 to 86 | — |
| The forgotten root the laboratories would rather you did not know about | publicite_sponsorise | E | 4 to 12 | — |
| The Vieille-Écluse bridge closed for works from 3 to 28 March | information | B A A | 78 to 80 | — |
| Advent meditation: waiting as a path | contenu_confessionnel | A | 85 to 92 | — |
| The November power cut: three awkward questions | theorie_du_complot | E | 7 to 14 | technique missing: `hyper_intentionnalisme` (1 of 3 runs) |
| What They Won't Tell You About the New Water Treatment Plant | theorie_du_complot | E | 12 to 14 | analysis written in fr instead of en (2 of 3 runs) |
| Five evening habits for better sleep | publicite_sponsorise | C | 55 to 64 | — |
| Water fluoridation: the debate is still open | opinion / information | D D C | 42 to 50 | — |
| Why the sky is blue, and why that explanation is incomplete | analyse_expertise | A B B | 70 to 80 | — |
| What three years of medical wandering taught me | temoignage | A | 82 to 84 | grade A outside the expected range B, C, D ; technique missing: `preuve_anecdotique` |
| Confirmation bias — Wikipedia | information / analyse_expertise | A | 88 to 90 | — |
| SOTT Earth Changes Summary - June 2026 | opinion / pseudo_science | D | 39 to 42 | category `opinion` instead of theorie_du_complot, pseudo_science (2 of 3 runs) ; technique missing: `verite_cachee` (2 of 3 runs) |
| Atelier du Guidon, bicycle repairs | autre | A | 90 to 94 | — |
| La Gazette de Saint-Aubin, the homepage | autre | A B B | 76 to 84 | — |

<!-- calibration:fin -->

## How to read it

Three independent runs on fresh analyses, on the **fifteen cases** of the previous version, expectations unchanged.

The sentinels of [docs/METHODOLOGIE.md](../../docs/METHODOLOGIE.md) §7 hold across all three runs, category and range alike, **except one**: the English page received an analysis written in French in two runs out of three. This had never happened in any recorded run. Four control draws made right away on that case alone returned it in English in all three draws that completed, the fourth having failed in transport, and so did four draws under v0.1.7. Nothing in v0.1.8 touches language. The gap is recorded as it is: the next measurement will tell whether it comes back.

### Selling is not a technique (v0.1.8)

The definition of `conflit_interet_commercial` only covered an “alarmist or miraculous message” from which the author profits. Specimen 08, sleep advice leading to a mattress with a disclosed partner link, has nothing alarmist about it: the model detected it by going beyond the definition, **eleven times out of eighteen** since v0.1.3, and nothing told it where to stop.

The definition was first rewritten on its own, to name both cases, the disguise and the fear or the miracle pushing a purchase. Measured over thirteen draws of specimen 08, it did **worse**: four detections out of thirteen, and the category fell back to `information` or `opinion` one time in two. The model's justification said why: since the partnership was “explicitly disclosed, which is commendable”, there was in its view nothing left to report. A special case in the prompt therefore states plainly that **disclosing the partnership lowers the severity without removing the detection**, and that the excerpt is the passage recommending the product.

Result over six targeted draws: detection five times out of six, `publicite_sponsorise` six times out of six, grade C every time, inside the C to D range the case expected and missed under v0.1.7. Then over the three full runs: detection three times out of three. The counter-test holds: honest commerce (specimen 12), which announces itself as commercial and only describes its services, receives the detection in none of the six draws where it was measured.

The totals, 12/15, 11/15, 13/15 against 12/15, 11/15, 12/15, cannot be told apart, and they should not be made to say more. What can be read is the targeted case.

### An index page is not an article

Reported by a user: on a home page, the analysis “goes off in all directions”. Specimen 13 puts that under measurement, the home page of a local newspaper, headlines and links, no continuous text.

Under prompt v0.1.6, three runs gave `information`, `information`, `autre`: **the same index filed twice out of three as an article**. Taken for an article, it is graded against expectations that make no sense for it, which is exactly the disorder reported.

The rule did exist, but stated in terms the model cannot map onto what it receives: “non-textual page (shop, home page, forum)”. The home page of a newspaper is perfectly textual. That is the fourth time running that the fault sits in the same place: **the corpus was enforcing a boundary the prompt drew nowhere**. Version 0.1.7 describes an index by its shape, a run of headlines announcing content that is absent, and forbids grading what has not been read.

Result: `autre` in all three runs, and again in all three runs of the following measurement, six out of six.

### The encyclopaedia, or a boundary the method does not draw

The expectation on the Wikipedia article demanded `information`. The case failed two runs out of three under v0.1.6, then all three under v0.1.7.

The first instinct was to demand `analyse_expertise` instead, since that is what the model returned. That would repeat the same mistake: the prompt defines `information` as “factual journalistic content (who, what, where, when)” and `analyse_expertise` as “in-depth analysis, science writing”, and **neither definition mentions an encyclopaedia**. Both categories are therefore accepted.

The measurement settled it better than the reasoning did: the three runs give `analyse_expertise`, `information`, `analyse_expertise`. Demanding either one would have produced one failure out of three, on a page that has no reason to fail.

No quality requirement has been loosened. The prompt itself says the category is “the dominant nature of the content, **not its quality**”: what judges this page remains its `[A, B]` range and its three forbidden techniques, all held across the three runs.

### The most instructive result of the day

The SOTT summary, a frozen capture whose content fingerprint is checked on every run, came out as `pseudo_science` or `theorie_du_complot` in **all three** runs of the previous measurement, without a single discrepancy. It comes out as `opinion` in **all three** runs of this one.

Same capture, same prompt, same model, same temperature, an hour apart. Nothing in the repository changed for that case between the two measurements. The only explanation consistent with the facts is variation on the provider's side, which nothing here allows us to observe.

Three runs already could not tell an improvement from a draw. This page can now say something sharper: **six draws of the same text split three against three between two opposite verdicts.** That is the best justification there is for an annotated corpus at another scale, and for a model trained for the task rather than rented by the call.

### Two guards, born of two mistakes on the same day

The cache clearing between runs targeted a column that does not exist. It failed in silence, and two runs were served entirely from the directory: three identical totals, a hair away from being published as three measurements. The `depuis_cache` field was already there, with the right reasoning in a comment; the guard had never been built. `--ecrire` now refuses a run served entirely from the cache.

Then the instance's rate limit left five cases without an analysis across three runs. They count as serious discrepancies, so an “11/15” read like a measurement where it was a queue. `--ecrire` now refuses a truncated run, naming the cases and advising a lower `--parallele`.

To which is added a latent fault that correcting the expectation exposed: the aggregation did not filter on the corpus. Changing an expectation changes what “conformant” means, and nothing stopped runs measured against different expectations from being mixed. The case had never arisen by coincidence, every corpus change having so far come with a prompt version change.

What the three have in common: the right reasoning existed, in a comment or in a README, and nothing enforced it.

### The rest

The personal account still fails its expected technique in all three runs, and its grade in two out of three. That is deliberate: the expectation was **tightened** in v0.1.6 rather than widened, to name a real fault, the tool not seeing the leap from a single case to a piece of advice. It stays published as a failure for as long as the fault lasts.

Totals: 10, 13 and 13 out of 15. The three-conformity gap between the first run and the other two is of the same order as the dispersion described above, and cannot be read.

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
| 2026-09-25 | v0.1.8 | 0 | 12/15, 11/15, 13/15; sponsored advice detected in all three runs, English page rendered twice in French |
| 2026-09-05 | v0.1.7 | 0 | 10/15, 13/15, 13/15; encyclopaedia expectation corrected, the SOTT summary flips to `opinion` in all three runs |
| 2026-09-05 | v0.1.7 | 0 | 12/15, 11/15, 12/15; corpus at 15 cases, index page added and fixed in all three runs |
| 2026-09-02 | v0.1.6 | 0 | 13/14, 12/14, 11/14; corpus at 14 cases, honest-commerce sentinel added |
| 2026-09-02 | v0.1.5 | 0 | 9/13, 10/13, 12/13; satirical specimen stabilised, personal account back at A |
| 2026-09-01 | v0.1.4 | 0 | 11/13, 10/13, 10/13 over three runs; personal account fixed, satirical specimen destabilised |
| 2026-08-31 | v0.1.3 | 0 | 11/13, 9/13, 12/13 over three fresh runs; science writing fixed in all three |
| 2026-08-27 | v0.1.2 | 0 | 11/13, first run recorded in the journal (served from the cache) |
| 2026-08-27 | v0.1.2 | 0 | 13/13, 10/13, 11/12 over three runs |
| 2026-08-27 | v0.1.2 | 0.2 | 11/13 on one run, then 9, 11, 9 over three control runs |
| 2026-08-24 | v0.1.1 | 0.2 | 12/12 conforming (single run, 12 cases) |
