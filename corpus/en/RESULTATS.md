# Calibration results

<!-- traduit-de: corpus/RESULTATS.md sha256:521d64f7f9085aa4 -->

> Translation for information. The French version, `corpus/RESULTATS.md`, is the record of reference: should the two ever diverge, it is the one that counts.

<!-- calibration:début (engendré par « lynceus calibrer --ecrire », ne pas modifier à la main) -->

Latest run: **2026-09-02** · model `z-ai/glm-5.2` (through openrouter.ai) · prompt **v0.1.6** · temperature **0**

**3 runs** recorded on this prompt version: **13/14, 12/14, 11/14** conforming. A single run would say nothing solid, since the model does not return the same analysis of the same text twice.

| Case | Category | Grade | Score | Discrepancies |
|---|---|---|---|---|
| The council votes unanimously against unanimity | satire | A | 87 to 92 | — |
| Why I think our town has it wrong about paid parking | opinion | A | 80 to 86 | — |
| The forgotten root the laboratories would rather you did not know about | publicite_sponsorise | E | 10 to 17 | — |
| The Vieille-Écluse bridge closed for works from 3 to 28 March | information | A B A | 77 to 81 | — |
| Advent meditation: waiting as a path | contenu_confessionnel | A | 86 to 94 | — |
| The November power cut: three awkward questions | theorie_du_complot | E | 10 to 12 | — |
| What They Won't Tell You About the New Water Treatment Plant | theorie_du_complot | E | 11 to 14 | — |
| Five evening habits for better sleep | publicite_sponsorise / information | C | 58 to 62 | category `information` instead of publicite_sponsorise (1 of 3 runs) ; technique missing: `conflit_interet_commercial` (1 of 3 runs) |
| Water fluoridation: the debate is still open | opinion | D | 40 to 46 | — |
| Why the sky is blue, and why that explanation is incomplete | analyse_expertise | B A B | 74 to 84 | — |
| What three years of medical wandering taught me | temoignage | A | 80 to 82 | grade A outside the expected range B, C, D ; technique missing: `preuve_anecdotique` |
| Confirmation bias — Wikipedia | information / analyse_expertise | A | 86 to 88 | category `analyse_expertise` instead of information (2 of 3 runs) |
| SOTT Earth Changes Summary - June 2026 | theorie_du_complot / pseudo_science | D | 30 to 36 | — |
| Atelier du Guidon, bicycle repairs | autre | A | 93 to 100 | — |

<!-- calibration:fin -->

## How to read it

Three independent runs on fresh analyses, over a corpus grown to **fourteen cases**.

The five sentinels of [METHODOLOGIE.md](../../docs/en/METHODOLOGIE.md) §7 hold across all three runs, on category and range.

### A negative control that was missing

§7 required a sentinel "commercial pseudo-medical site" whose conflict of interest must be detected, with no symmetrical case at all. Both commercial specimens in the corpus were dishonest, so **nothing would have failed had the tool started penalising commerce as such**. Specimen 12 fills that gap: an openly commercial page, published prices, a named proprietor, stated limits to the trade, pointing readers to free community workshops.

It comes out as `autre`, **A between 93 and 100 in all three runs, without a single discrepancy**. Commercial pseudo-medicine stays at E between 10 and 17. The tool therefore tells honest commerce from misleading commerce, which no measurement said until now.

### The `sources` dimension finally says what it scores

Reported from the nashi.cloud repository: a page describing its own services can structurally cite nobody, and was losing 30 % of its grade to an expectation that did not apply, the model's own justification sometimes acknowledging as much.

The added rule does **not depend on the category** but on what the text asserts: no claim needing outside support, no penalty; factual claims, and they must be supported, commercial pages included. That is what lets specimen 12 come out at A without specimen 01 ceasing to come out at E.

A per-category reweighting had been considered. It is unnecessary: stating the rule in the prompt gives the same result without touching the arithmetic, and "same dimensions, same grade" stays true.

### The personal account: expectation tightened, not loosened

That case had come out at A, one notch above its range, for three versions. Examination showed the expectation did not say what it meant: the specimen's own header announces a `preuve_anecdotique` of low to medium severity, and the `[B, C, D]` range was only a **proxy** for that detection, which the corpus required nowhere. The model detects no technique at all and grades A.

The range was not widened to make the test pass. The expected technique was added, which **tightens** the expectation and names the real defect: the tool does not see the generalisation from a single case to a piece of advice. The discrepancy is now precise instead of vague, and it is published.

### The rest

The real conspiracy page is **conforming in all three runs** for the first time in four versions. The encyclopaedic article still tips into `analyse_expertise` in two runs out of three. Disguised advertising is classified `information` in one run out of three, which is new and worth watching.

Totals: 13, 12 and 11 out of 14. They do not compare with earlier versions, the corpus having gained a case and an expectation. What can be read is still the case-by-case picture.

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
| 2026-09-02 | v0.1.6 | 0 | 13/14, 12/14, 11/14; corpus at 14 cases, honest-commerce sentinel added |
| 2026-09-02 | v0.1.5 | 0 | 9/13, 10/13, 12/13; satirical specimen stabilised, personal account back at A |
| 2026-09-01 | v0.1.4 | 0 | 11/13, 10/13, 10/13 over three runs; personal account fixed, satirical specimen destabilised |
| 2026-08-31 | v0.1.3 | 0 | 11/13, 9/13, 12/13 over three fresh runs; science writing fixed in all three |
| 2026-08-27 | v0.1.2 | 0 | 11/13, first run recorded in the journal (served from the cache) |
| 2026-08-27 | v0.1.2 | 0 | 13/13, 10/13, 11/12 over three runs |
| 2026-08-27 | v0.1.2 | 0.2 | 11/13 on one run, then 9, 11, 9 over three control runs |
| 2026-08-24 | v0.1.1 | 0.2 | 12/12 conforming (single run, 12 cases) |
