# Calibration results

<!-- traduit-de: corpus/RESULTATS.md sha256:0c81d92333ac8ea7 -->

> Translation for information. The French version, `corpus/RESULTATS.md`, is the record of reference: should the two ever diverge, it is the one that counts.

<!-- calibration:début (engendré par « lynceus calibrer --ecrire », ne pas modifier à la main) -->

Latest run: **2026-09-02** · model `z-ai/glm-5.2` (through openrouter.ai) · prompt **v0.1.5** · temperature **0**

**3 runs** recorded on this prompt version: **9/13, 10/13, 12/13** conforming. A single run would say nothing solid, since the model does not return the same analysis of the same text twice.

| Case | Category | Grade | Score | Discrepancies |
|---|---|---|---|---|
| The council votes unanimously against unanimity | satire | A | 84 to 89 | — |
| Why I think our town has it wrong about paid parking | opinion | A | 80 to 88 | — |
| The forgotten root the laboratories would rather you did not know about | publicite_sponsorise | E | 10 to 16 | — |
| The Vieille-Écluse bridge closed for works from 3 to 28 March | information | B A B | 75 to 80 | — |
| Advent meditation: waiting as a path | contenu_confessionnel | A | 88 to 94 | — |
| The November power cut: three awkward questions | theorie_du_complot | E | 10 to 12 | — |
| What They Won't Tell You About the New Water Treatment Plant | theorie_du_complot | E | 16 to 21 | — |
| Five evening habits for better sleep | publicite_sponsorise | C | 52 to 64 | technique missing: `conflit_interet_commercial` (1 of 3 runs) |
| Water fluoridation: the debate is still open | opinion | D | 41 to 47 | technique missing: `faux_equilibre` (1 of 3 runs) |
| Why the sky is blue, and why that explanation is incomplete | analyse_expertise | B | 65 to 71 | — |
| What three years of medical wandering taught me | temoignage | A | 82 to 84 | grade A outside the expected range B, C, D |
| Confirmation bias — Wikipedia | analyse_expertise / information | A | 82 to 90 | category `analyse_expertise` instead of information (2 of 3 runs) |
| SOTT Earth Changes Summary - June 2026 | pseudo_science / opinion / theorie_du_complot | D | 33 to 37 | category `opinion` instead of theorie_du_complot, pseudo_science (1 of 3 runs) ; technique missing: `verite_cachee` (1 of 3 runs) |

<!-- calibration:fin -->

## How to read it

Three independent runs, on fresh analyses: caching is keyed on the pair of content and prompt version, and the analyses for the current version were removed from the database between runs.

The five sentinels of [METHODOLOGIE.md](../../docs/en/METHODOLOGIE.md) §7 hold across all three runs, on category **and** grade range.

### What prompt v0.1.5 fixes, and how it was established

v0.1.4 had destabilised the satirical specimen: from a stable A, it had dropped to a D in one run out of three. The diagnosis was made on that single case rather than on the whole corpus, which costs one analysis instead of thirteen. Eight draws of the same text, four under v0.1.3 and four under v0.1.4, showed a clear failure mode: on one draw, `sources` and `factualite` fell to **exactly 0** while `ton` and `transparence` stayed at 90 and 95. The model was switching from "this is a parody" to "this text has no sources and its claims are false".

The cause was not a regression introduced by v0.1.4 but a **gap in the specification** that v0.1.4 made more visible. The satire rule said how to score `transparence` only, and left the model to decide the other two on its own. It decided differently from one draw to the next.

v0.1.5 states the missing rule: a parody invents its facts by construction and cites no sources, neither is a failing, and those two dimensions are scored on the fairness of the device. The result: **eleven draws without a single collapse**, eight in the targeted measurement and three in full runs, against two collapses in seven before. The specimen comes out at A in all three runs, between 84 and 89.

The methodological point, because it will serve again: when a corpus expectation fails **unstably**, look first at what the specification leaves implicit. A model left to decide for itself does not decide the same way twice. This is the second time in three versions that the defect was there, and not in the model nor in the expectation.

### What moved the other way

**The personal account is back at A in all three runs**, one notch above its range, where v0.1.4 had brought it down to B. The two movements are probably connected: saying that a dimension is not read literally for satire seems to generalise to content that structurally has no sources to cite, which a personal account also is. That case has now moved three versions running, and it is **its expectation that needs examining**, not bending.

Two discrepancies stay in a minority and are already known: the encyclopaedic article tips into `analyse_expertise` in two runs out of three, the conspiracy page into `opinion` in one out of three.

### The totals, still silent

9, 10 and 12 out of 13, against 11, 10, 10 under v0.1.4 and 11, 9, 12 under v0.1.3. Three versions, nine runs, no readable difference in the totals. What can be read is still the case-by-case picture and whether the runs agree. Over thirteen cases the corpus says whether a behaviour is stable, never whether a version is better.

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
| 2026-09-02 | v0.1.5 | 0 | 9/13, 10/13, 12/13; satirical specimen stabilised, personal account back at A |
| 2026-09-01 | v0.1.4 | 0 | 11/13, 10/13, 10/13 over three runs; personal account fixed, satirical specimen destabilised |
| 2026-08-31 | v0.1.3 | 0 | 11/13, 9/13, 12/13 over three fresh runs; science writing fixed in all three |
| 2026-08-27 | v0.1.2 | 0 | 11/13, first run recorded in the journal (served from the cache) |
| 2026-08-27 | v0.1.2 | 0 | 13/13, 10/13, 11/12 over three runs |
| 2026-08-27 | v0.1.2 | 0.2 | 11/13 on one run, then 9, 11, 9 over three control runs |
| 2026-08-24 | v0.1.1 | 0.2 | 12/12 conforming (single run, 12 cases) |
