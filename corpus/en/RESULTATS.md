# Calibration results

<!-- traduit-de: corpus/RESULTATS.md sha256:4610462410cdce59 -->

> Translation for information. The French version, `corpus/RESULTATS.md`, is the record of reference: should the two ever diverge, it is the one that counts.

<!-- calibration:début (engendré par « lynceus calibrer --ecrire », ne pas modifier à la main) -->

Latest run: **2026-09-01** · model `z-ai/glm-5.2` (through openrouter.ai) · prompt **v0.1.4** · temperature **0**

**3 runs** recorded on this prompt version: **11/13, 10/13, 10/13** conforming. A single run would say nothing solid, since the model does not return the same analysis of the same text twice.

| Case | Category | Grade | Score | Discrepancies |
|---|---|---|---|---|
| The council votes unanimously against unanimity | satire | B D A | 38 to 85 | grade D outside the expected range A, B, C (1 of 3 runs) |
| Why I think our town has it wrong about paid parking | opinion | A | 80 to 83 | — |
| The forgotten root the laboratories would rather you did not know about | publicite_sponsorise | E | 9 to 16 | case not measured: HTTP 500 : Internal Server Error (1 of 3 runs) |
| The Vieille-Écluse bridge closed for works from 3 to 28 March | information | A B A | 79 to 84 | — |
| Advent meditation: waiting as a path | contenu_confessionnel | B A A | 78 to 84 | — |
| The November power cut: three awkward questions | theorie_du_complot | E | 8 to 9 | technique missing: `hyper_intentionnalisme` (1 of 3 runs) |
| What They Won't Tell You About the New Water Treatment Plant | theorie_du_complot | E | 10 to 14 | — |
| Five evening habits for better sleep | publicite_sponsorise | C D C | 48 to 64 | technique missing: `conflit_interet_commercial` (2 of 3 runs) |
| Water fluoridation: the debate is still open | opinion | D | 42 to 46 | — |
| Why the sky is blue, and why that explanation is incomplete | analyse_expertise | B | 68 to 76 | — |
| What three years of medical wandering taught me | temoignage | B | 66 to 74 | — |
| Confirmation bias — Wikipedia | analyse_expertise / information | A | 90 | category `analyse_expertise` instead of information (2 of 3 runs) |
| SOTT Earth Changes Summary - June 2026 | theorie_du_complot / opinion | D D E | 29 to 40 | category `opinion` instead of theorie_du_complot, pseudo_science (1 of 3 runs) |

<!-- calibration:fin -->

## How to read it

Three independent runs are recorded on this prompt version, on fresh analyses: caching is keyed on the pair of content and prompt version, and the analyses for the current version were removed from the database between runs.

The five sentinels of [METHODOLOGIE.md](../../docs/en/METHODOLOGIE.md) §7 hold as far as the **category** goes: satire stays classified as `satire`, argued opinion is not penalised for its position, commercial pseudo-medicine comes out at E, factual news at A, and religious content stays in its category. The English specimen is analysed in English.

### What prompt v0.1.4 fixed

v0.1.4 forbids a question to presuppose, and extends the attribution rule to every text returned. Two discrepancies established under v0.1.3 disappear.

**The personal account returns to its range.** It came out at A in two runs out of three, one notch too high; it now comes out at B in all three, between 66 and 74, without a single discrepancy. It is the clearest of the changes, and it points the expected way: a question that no longer presupposes stops lending the text credit.

**The real conspiracy page returns to its category** in two runs out of three, against `opinion` in two out of three under v0.1.3.

### What it degraded, which must be said too

**The satirical specimen became unstable.** It held at A between 85 and 100 under v0.1.3; it now swings between 38 and 85 and comes out at D in one run out of three. The category holds, so the §7 sentinel is not at stake, but a parody piece graded D is an error a reader spots at once. That is the first thing to watch on the next version.

**Disguised advertising no longer triggers `conflit_interet_commercial`** in two runs out of three, although it is the expected technique and the defining trait of the case. **The encyclopaedic article tips into `analyse_expertise`** in two runs out of three instead of one.

### What three runs still do not establish

The totals are 11, 10 and 10 out of 13, against 11, 9 and 12 under v0.1.3. Indistinguishable. The conclusion drawn last time stands unchanged: over thirteen cases and at that spread, a difference of two conformities is not a signal. What can be read is the cases one by one, and whether the three runs agree on each.

One run returned an HTTP 500 error on one case, marked "not measured" rather than counted as conforming, which is the right behaviour. The error was not reproduced. The most likely explanation is a SQLite lock under four simultaneous analyses, the development database being SQLite where production runs on PostgreSQL; it is not verified.

### One barrier added, and one measurement that failed

The server now checks **every quotation in quotation marks**, wherever it appears, and no longer only inside a detection. The free-text fields were escaping every check. The calibration report does not yet count those rejections, so their rate remains to be measured on real pages.

A corpus expectation was tried, to measure what the barrier does not cover: a list of terms the analysis was not to use because the specimen does not use them. It was **withdrawn after one run**, where it flagged "Is the product assessed or certified by the competent health authorities?" on the pseudo-medicine page. That is a good Socratic question, generic, asserting nothing. A lexical check cannot tell a question that asks from a question that presupposes, and keeping a wrong expectation would have been worse than having none. The attribution rule therefore stays constrained by the prompt and unmeasured, which [METHODOLOGIE.md](../../docs/en/METHODOLOGIE.md) §3 now states explicitly.

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
| 2026-09-01 | v0.1.4 | 0 | 11/13, 10/13, 10/13 over three runs; personal account fixed, satirical specimen destabilised |
| 2026-08-31 | v0.1.3 | 0 | 11/13, 9/13, 12/13 over three fresh runs; science writing fixed in all three |
| 2026-08-27 | v0.1.2 | 0 | 11/13, first run recorded in the journal (served from the cache) |
| 2026-08-27 | v0.1.2 | 0 | 13/13, 10/13, 11/12 over three runs |
| 2026-08-27 | v0.1.2 | 0.2 | 11/13 on one run, then 9, 11, 9 over three control runs |
| 2026-08-24 | v0.1.1 | 0.2 | 12/12 conforming (single run, 12 cases) |
