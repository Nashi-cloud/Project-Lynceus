# Analysis methodology

<!-- traduit-de: docs/METHODOLOGIE.md sha256:4be9346600b6464b -->

> Translation for information. The French version, `docs/METHODOLOGIE.md`, is the one the project applies: should the two ever diverge, it is the one that counts.

Version: **0.1.2**. Any change to this document or to the prompts increments `prompt_version` (semver) and triggers a run against the [calibration corpus](../../corpus/).

## Overview

```
Content (Markdown) ──▶ 1. Categorisation ──▶ 2. Dimensions (4 scores) ──▶ 3. Techniques (verbatim excerpts)
                                                                              │
Final card ◀── 6. Server assembly ◀── 5. Overall grade (server-side) ◀────────┤
(validated JSON)    (grade + meta)      published weightings                  └▶ 4. Strong points + questions
```

The language model produces the material (category, dimensions, techniques, text); **the overall grade is computed by the server** from the dimensions, using the weightings published below. Determinism and auditability: two instances with the same dimensions produce the same grade.

## 1. Categorising the content

The category describes the **dominant nature** of the content, not its quality:

| Category | Description |
|---|---|
| `information` | Factual journalistic content (who, what, where, when) |
| `opinion` | Editorial, op-ed, a piece openly presented as a point of view |
| `analyse_expertise` | In-depth analysis, science communication |
| `satire` | Parody or humorous content |
| `publicite_sponsorise` | Commercial content, advertorial, sales page |
| `temoignage` | Personal account, lived experience |
| `contenu_confessionnel` | Religious or spiritual content, presented as such |
| `pseudo_science` | Discourse with the appearance of science but no scientific method |
| `theorie_du_complot` | A story of hidden coordinated intent, presented as news |
| `autre` | Everything else (home page, shop, forum and so on) |

The category governs how the grade should be read (see “Special cases”).

## 2. The four dimensions (0 to 100 each)

### `sources`: quality of sourcing (weight: 30 %)
- Are the important claims sourced? Are primary sources identifiable and checkable?
- Real links to the sources, or bare assertions (“studies show”)?
- Do the cited sources actually say what they are made to say (where the text allows checking)?

### `factualite`: factual rigour (weight: 30 %)
- Extraordinary claims, extraordinary evidence?
- Contradictions with established facts or with the scientific consensus (within the limits of what the model knows, and cautiously)?
- Are facts kept distinct from interpretations? Are figures and dates consistent?

### `ton`: register and rhetorical techniques (weight: 20 %)
- Dominant register: factual or emotional (fear, outrage, urgency)?
- Density of manipulation techniques detected (see [TAXONOMIE.md](TAXONOMIE.md))?
- Does the headline match the content, or is it clickbait?

### `transparence`: openness of the publisher (weight: 20 %)
- Is the author identifiable? Are there legal notices, a named publishing entity?
- Conflicts of interest visible in the text (selling products related to the claims)?
- Opinion presented as news, advertising in disguise?

## 3. Detecting techniques

- Only techniques **from the catalogue** [TAXONOMIE.md](TAXONOMIE.md) (ids validated by the server).
- Every detection requires a **verbatim excerpt** from the page. No exact quotation, no detection.
- Every detection carries a severity (`faible` / `moyenne` / `haute`) and a plain explanation of the mechanism.

## 4. Strong points and questions

- **Strong points**: always look for them (exact dates, a correct source, a named author and so on). Finding none must stay exceptional and justified.
- **Questions to ask yourself**: 2 to 4 socratic questions the reader can apply themselves (“Who funds this site?”, “Why is no source linked?”).

## 5. Overall grade (computed by the server)

```
score = 0.30·sources + 0.30·factualite + 0.20·ton + 0.20·transparence
```

| Grade | Score | How to read it |
|---|---|---|
| **A** | ≥ 80 | Good information practice |
| **B** | 65 to 79 | Broadly reliable, with some reservations |
| **C** | 50 to 64 | Be careful, check before sharing |
| **D** | 30 to 49 | Considerable caution, serious signals |
| **E** | < 30 | Many critical signals |

The **confidence index** (0 to 1, supplied by the model) is shown separately: it qualifies the analysis, not the content.

## 6. Special cases

- **Satire**: the grade assesses *how openly the satire is signalled* (an openly parodic site grades well). The card carries the warning “satirical content, not to be read literally”. It is never treated as disinformation.
- **Opinion / editorial**: assessed on the honesty of its argument (sources for the facts invoked, absence of unfair techniques), **never on the position it defends**.
- **Religious content**: faith is not graded. Only factual claims (health, science, history) and any manipulation techniques (fear, urgency, isolation) are.
- **Short or truncated content** (paywall, excerpt): lowered confidence index plus an explicit warning.
- **Foreign language**: analysed in the language of the content where the model allows, otherwise a warning.

## 7. Calibration

- The [corpus](../../corpus/) holds reference pages with an expected category and grade range.
- Every change to a prompt or to the methodology is assessed against the corpus before merging: no silent regression.
- Mandatory sentinel cases: a satirical site (never “disinformation”), a quality editorial (never penalised for its position), a commercial pseudo-medical site (the conflict of interest must be detected), and a page in English (the analysis must be written in the language of the page).
- The model is not deterministic: two runs over the same content can differ. An isolated discrepancy is therefore not a regression, and a regression is established by replaying the case. Observed discrepancies are published with their results rather than fixed by loosening the expectation.

## Known and accepted limits

1. The model can be wrong (hallucination, dated knowledge) → confidence index, disputes, re-analysis.
2. The analysis covers **one page**, not a whole site → a domain profile is only an aggregate, and is presented as such.
3. The underlying model has biases → public prompts, calibration corpus, model chosen per instance.
4. Fine-grained factuality (fact-checking every figure) is not the point: Lynceus detects *methods*, fact-checkers verify *facts*. The two complement each other.
