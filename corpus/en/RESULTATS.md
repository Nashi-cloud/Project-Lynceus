# Calibration results

<!-- traduit-de: corpus/RESULTATS.md sha256:e1d411ebdb7f9522 -->

> Translation for information. The French version, `corpus/RESULTATS.md`, is the record of reference: should the two ever diverge, it is the one that counts.

<!-- calibration:début (engendré par « lynceus calibrer --ecrire », ne pas modifier à la main) -->

Latest run: **2026-09-05** · model `z-ai/glm-5.2` (through openrouter.ai) · prompt **v0.1.7** · temperature **0**

**3 runs** recorded on this prompt version: **12/15, 11/15, 12/15** conforming. A single run would say nothing solid, since the model does not return the same analysis of the same text twice.

| Case | Category | Grade | Score | Discrepancies |
|---|---|---|---|---|
| The council votes unanimously against unanimity | satire | A | 86 to 89 | — |
| Why I think our town has it wrong about paid parking | opinion | A | 83 to 85 | — |
| The forgotten root the laboratories would rather you did not know about | publicite_sponsorise | E | 10 to 14 | — |
| The Vieille-Écluse bridge closed for works from 3 to 28 March | information | A | 80 to 82 | — |
| Advent meditation: waiting as a path | contenu_confessionnel | A | 90 | — |
| The November power cut: three awkward questions | theorie_du_complot | E | 1 to 10 | technique missing: `hyper_intentionnalisme` (1 of 3 runs) |
| What They Won't Tell You About the New Water Treatment Plant | theorie_du_complot | E | 14 to 18 | — |
| Five evening habits for better sleep | publicite_sponsorise | B C B | 62 to 67 | grade B outside the expected range C, D (2 of 3 runs) ; technique missing: `conflit_interet_commercial` (2 of 3 runs) |
| Water fluoridation: the debate is still open | information / opinion | D | 43 to 49 | — |
| Why the sky is blue, and why that explanation is incomplete | analyse_expertise | B | 66 to 73 | — |
| What three years of medical wandering taught me | temoignage | A | 82 to 98 | grade A outside the expected range B, C, D ; technique missing: `preuve_anecdotique` |
| Confirmation bias — Wikipedia | analyse_expertise | A | 88 to 92 | category `analyse_expertise` instead of information |
| SOTT Earth Changes Summary - June 2026 | pseudo_science / theorie_du_complot | E D D | 28 to 38 | — |
| Atelier du Guidon, bicycle repairs | autre | A | 89 to 98 | — |
| La Gazette de Saint-Aubin, the homepage | autre | A A B | 78 to 85 | — |

<!-- calibration:fin -->

## How to read it

Three independent runs on fresh analyses, on a corpus grown to **fifteen cases**.

The five sentinels of [docs/METHODOLOGIE.md](../../docs/METHODOLOGIE.md) §7 hold across all three runs, category and range alike.

### An index page is not an article

Reported by a user: on a home page, the analysis “goes off in all directions”. Specimen 13 puts that under measurement, the home page of a local newspaper, headlines and links, no continuous text.

Under prompt v0.1.6, three runs gave `information`, `information`, `autre`: **the same index filed twice out of three as an article**. Taken for an article, it is graded against expectations that make no sense for it, which is exactly the disorder reported.

The rule did exist, but stated in terms the model cannot map onto what it receives: “non-textual page (shop, home page, forum)”. The home page of a newspaper is perfectly textual. That is the fourth time running that the fault sits in the same place: **the corpus was enforcing a boundary the prompt drew nowhere**. Version 0.1.7 describes an index by its shape, a run of headlines announcing content that is absent, and forbids grading what has not been read.

Result over the three runs: `autre`, `autre`, `autre`, with confidence falling from 0.90 to 0.85, 0.70 and 0.82, as the rule asks.

### An expectation written before the measurement, and wrong

`verite_cachee` had first been listed among the forbidden techniques for this case, on the grounds that nothing in an index amounts to a revelation device. The measurement proved the model right: the headline “Ce que votre facture d'eau cache vraiment” is on the page, put there by the author of the specimen, and it is indeed the revelation formula. The index chooses to display that headline, so the formula is its own. The expectation was withdrawn, not the detection.

### Three runs that were only one

The cache clearing between runs targeted a column that does not exist. It failed in silence, and the two following runs were served entirely from the directory: three rigorously identical totals, a hair away from being published as three independent measurements.

The journal already carried a `depuis_cache` field, with this comment in the code: “counting it is what keeps three copies of one analysis from passing for three independent runs”. The reasoning was written down, the guard had never been built. `lynceus calibrer --ecrire` now refuses to record a run whose cases all come from the cache. Two tests cover the refusal, and the clearing procedure is documented in [README.md](../README.md).

A run of the same kind had been sitting in the journal since 27 August, on prompt v0.1.2. It stays there: it did happen, it simply measures nothing, the table already marks it with an asterisk, and deleting a line from a journal would destroy a trace. It is for the aggregation to know what it is worth, not for the archive to lie.

### The two chronic discrepancies

The encyclopaedia article comes out as `analyse_expertise` in **all three** runs, against two out of three under v0.1.6. The expectation says `information`. Yet the methodology files science writing under `analyse_expertise`, and an encyclopaedia entry is not journalism. The model is consistent and appears to be right: **it is the expectation that needs revisiting**, which will take three fresh runs and was therefore not folded into this change.

The personal account still fails both its expectations, technique and range. That is deliberate: the expectation was **tightened** in v0.1.6 rather than widened, to name a real fault, the tool not seeing the leap from a single case to a piece of advice. It stays published as a failure for as long as the fault lasts.

### The rest

The disguised advertisement misses `conflit_interet_commercial` in two runs out of three, against one out of three under v0.1.6. The real conspiracy page loses `hyper_intentionnalisme` once out of three, which it did not do in the previous version.

Totals: 12, 11 and 12 out of 15. Set against the 13, 12 and 11 out of 14 of v0.1.6, that is 9 serious discrepancies over 45 measurements against 7 over 42, or 20 % against 17 %. **That difference cannot be read**: it is precisely what this page has been saying for four versions, a corpus of this size cannot tell an improvement from a draw. What can be read is the targeted case, which goes from two failures out of three to none.

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
| 2026-09-05 | v0.1.7 | 0 | 12/15, 11/15, 12/15; corpus at 15 cases, index page added and fixed in all three runs |
| 2026-09-02 | v0.1.6 | 0 | 13/14, 12/14, 11/14; corpus at 14 cases, honest-commerce sentinel added |
| 2026-09-02 | v0.1.5 | 0 | 9/13, 10/13, 12/13; satirical specimen stabilised, personal account back at A |
| 2026-09-01 | v0.1.4 | 0 | 11/13, 10/13, 10/13 over three runs; personal account fixed, satirical specimen destabilised |
| 2026-08-31 | v0.1.3 | 0 | 11/13, 9/13, 12/13 over three fresh runs; science writing fixed in all three |
| 2026-08-27 | v0.1.2 | 0 | 11/13, first run recorded in the journal (served from the cache) |
| 2026-08-27 | v0.1.2 | 0 | 13/13, 10/13, 11/12 over three runs |
| 2026-08-27 | v0.1.2 | 0.2 | 11/13 on one run, then 9, 11, 9 over three control runs |
| 2026-08-24 | v0.1.1 | 0.2 | 12/12 conforming (single run, 12 cases) |
