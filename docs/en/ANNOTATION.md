<!-- traduit-de: docs/ANNOTATION.md sha256:de7408580e52842a -->

# Building the annotated evaluation set

Guide version: **1.0**, September 2026.

This document describes how the set of hand-annotated pages is built, against which every
Lynceus analysis chain is measured. It is step zero of the
[target architecture](ARCHITECTURE-CIBLE.md): as long as this set does not exist, an
improvement and a lucky draw look alike. The tooling is described in
[corpus/README.md](../../corpus/README.md); this document describes the human work.

Section 5, the annotation guide proper, is versioned. Every annotation carries the version
of the guide under which it was made, and every revision of the guide increments that
number.

## 1. What this set is, and what it is not

- **A measuring instrument.** It says, in figures, what a chain finds and what it misses,
  and how far two human readers agree on the same page.
- **Not a truth.** Two careful annotators do not always agree. Their agreement is
  published with the rest, and sets the reasonable ceiling for any machine.
- **Not a training set.** The `test` part is never shown to a model being trained nor to a
  chain being tuned. A learnt set measures nothing any more. Training data comes from
  elsewhere (section 9).
- **Not the calibration corpus.** The fifteen cases of `corpus.yaml` remain the sentinels
  and the traps, with their expectations. The evaluation set lives in
  `corpus/evaluation.yaml`, without expectations: the annotation takes their place.

## 2. Roles

| Role | Who | What they do |
|---|---|---|
| Coordination | One person, the maintainer by default | Selects the pages, makes the captures, distributes them, collects the readings, has them arbitrated, publishes the batches. |
| Annotation | At least two people, under a pseudonym | Read each page independently and produce one reading each. |
| Arbitration | A third person, never one of the page's two annotators | Settles the pages whose two readings diverge. |

Profiles sought for annotation: media literacy education, journalism, fact-checking,
teaching, documentation. No technical skill is needed.

### 2.1 The start-up phase: a single annotator

At first, the maintainer coordinates and annotates alone. The work does not wait for
volunteers, but one must say what this phase measures and what it does not.

- **What cannot be measured yet**: agreement between two people, which alone says whether
  the guide reads only one way. `lynceus mesurer` flags the pages that have only one
  reading, and any figure published on them says so.
- **What partly replaces it**: re-reading. One page in ten, drawn at random, is read again
  by the same annotator at least four weeks later, without reopening their first reading
  (`lynceus annoter --relecture`). An annotator's agreement with themselves is published
  under that name, never as an agreement between annotators.
- **Select before reading.** Whoever chooses the pages and annotates them risks choosing
  those they know how to read. A batch is therefore selected in full, according to the
  quotas, before the first reading, and each page's reason is written in `notes`.
- **Keep the readings for those who follow.** Readings of the `test` part stay in
  `corpus/annotations-en-cours/`, which git ignores, until a second person has read the
  page. Published earlier, they would be in front of the second annotator, whose reading
  would no longer be independent. Pages of the `reglage` part may be published as soon as
  they are first read.
- **Arbitrating without a third party.** When a volunteer has made the second reading and
  no third person is available, the two readers arbitrate together, in a session, and the
  arbitration says so in `notes`. It is less solid than a third party, and that is stated.

## 3. Rules that are not up for discussion

1. **Annotate without having seen a card.** Neither Lynceus's nor any other tool's, nor
   the silver set's annotation (section 11), neither before nor during the reading. An annotation made with the answer in view
   measures agreement with the model, not with the page.
2. **Annotate without AI.** No language model suggests, completes or proofreads an
   annotation. The project's [AI policy](IA-GENERATIVE.md) applies here without exception,
   for the same reason as rule 1.
3. **Read alone.** No discussion of a page between annotators before both readings are
   handed in. The other's notes are read only afterwards.
4. **No conflict of interest.** No page from nashi.cloud nor from a site linked to the
   project. An annotator declares the sites they are linked to (employer, collaboration,
   activism) and receives none of their pages.
5. **Captures are never versioned.** The repository contains only the manifest and the
   annotations. Annotations contain only short excerpts, at most 600 characters each,
   which falls under quotation for the purpose of analysis (see
   [CONFORMITE.md](CONFORMITE.md) §4).
6. **Techniques, not people.** One annotates what a text does, never what its author
   supposedly is. Pages centred on a private individual are excluded at selection.

## 4. Composing the set

### 4.1 Size and split

| | Pages | Role |
|---|---|---|
| `test` part | 200 at least | The published figure. Never seen during tuning. |
| `reglage` (tuning) part | About 40, plus the pilot pages | Allowed for adjusting thresholds. |

Two hundred pages is the threshold below which a difference of a few points remains
noise. Each page's part is **drawn at random** at selection time, one page in six going to
`reglage`: choosing it after seeing a result would bias everything.

### 4.2 Balance

- **Languages**: about 60% French, 40% English.
- **Categories**: at least 12 pages per category of [METHODOLOGIE.md](METHODOLOGIE.md) §1,
  8 for `autre`. The category aimed at during selection is an intention, not a label:
  only the annotation settles it.
- **Sources**: at most 3 pages per domain. A mix of national and regional press, blogs,
  alternative health sites, sales pages, forums, institutional sites, satire, religious
  content and popular science.
- **Pages without techniques.** About half the set must come from sources where no
  manipulation is expected. Without them, false positives cannot be measured, and they
  are the ones that betray the charter.
- **Lengths**: short (under 3,000 characters), medium, long. Captures of more than 60,000
  characters are excluded, since the extension truncates beyond that.
- **Dates**: pages published over several years, not only the news of the month.

### 4.3 Finding pages

Problematic pages can be found notably among content already examined by newsrooms'
fact-checking sections, which cite their sources. The others are chosen by source,
according to the quotas, without looking at their content beforehand.

No page is chosen after submitting it to Lynceus: one would unwittingly keep those it
handles well or badly. The reason for selection is written in `notes`.

No page of the silver set (section 11) enters the test set either: models have already
read it, and an encoder may learn from it. The list of these pages is published by
lynx-corpus in `argent/deja-vus.txt`. Pointed to by `LYNCEUS_DEJA_VUS`, it makes
`lynceus capturer` refuse such a page, and `lynceus mesurer` flag any test page that is
already in it:

```bash
export LYNCEUS_DEJA_VUS=../lynx-corpus/argent/deja-vus.txt
lynceus capturer page.md --url https://example.org/article --vers corpus/captures
lynceus mesurer corpus/evaluation.yaml
```

## 5. The annotation guide, version 1.0

<!-- Headings 5.1 to 5.4 of the French original are read by lynx-corpus, which turns them
     into its panel's prompt: renaming them breaks that chain, and a lynx-corpus test says so. -->

### 5.1 Reading order

1. Read the whole page once, marking nothing.
2. Settle the category.
3. Mark the passages.
4. Settle the grade range, last, once the passages have been seen.
5. Write the notes: hesitations, choices, what nearly got marked.

Allow between 15 and 30 minutes per page. Beyond that, note why and move to the next.

### 5.2 The category

The **dominant nature** of the content, according to [METHODOLOGIE.md](METHODOLOGIE.md)
§1, not its quality. A few tie-breaking rules:

- An article that leads to the sale of what it praises is `publicite_sponsorise`, even if
  it presents itself as information.
- `satire` only if the page or the site announces itself as such, or if the excess makes
  the parodic intent obvious to a careful reader.
- `analyse_expertise` for an in-depth analysis or popular science; `information` for an
  account of facts.

`categories_acceptables` is for true hybrids, where two labels are equally defensible: the
typical example is pseudo-medical discourse that sells its remedy. It is not for hedging
when hesitating: in that case, choose and note it.

### 5.3 Passages

One marks a passage where **the page itself uses** one of the 31 techniques of
[TAXONOMIE.md](TAXONOMIE.md). Nothing else: no technique outside the list, no judgement on
the truth of the facts.

**Delimiting.**

- The smallest passage that is enough to recognise the technique: usually a sentence,
  never more than a paragraph, at most 600 characters.
- Copy the text exactly, without ellipsis or cuts. If the technique spans two distant
  sentences, make two passages.
- When the same text appears several times in the page, specify `occurrence`.
- The same passage may carry two techniques: it is entered twice.
- A recurring technique: mark each clear occurrence, and beyond five, the five clearest
  with a note.

**What is not marked.**

- **The reported technique.** A page that quotes conspiracy discourse in order to take it
  apart does not use hidden truth. Only what the page does counts, not what it describes.
- **The parodied technique.** In satire, the techniques being mocked are not marked.
- **Faith.** A statement of faith is not a technique (charter, [ETHIQUE.md](ETHIQUE.md)).
- **Style.** A lively tone or strong vocabulary are not techniques. The emotional lexicon
  belongs to an automatic count, not to annotation.

**Techniques of absence.** `absence_de_sources` is marked on the important factual claim
that is not sourced, the most important first. `conflit_interet_commercial` is marked on
the passage where the sale, the affiliation or the call for donations tied to the
discourse appears.

**When in doubt, do not mark.** Mark what a careful reader would certainly point out. A
doubtful passage goes into the notes, with the technique considered. A cautious and stable
annotation is worth more than an exhaustive one that nobody reproduces.

Severity is not requested in this version of the guide.

### 5.4 The grade range

One or two **adjacent** letters, never more. Reason through the four dimensions of
[METHODOLOGIE.md](METHODOLOGIE.md) §2: sources, factuality, tone, transparency. The range
says where one would place the page, not where one thinks Lynceus will place it.

### 5.5 The file

`lynceus annoter` prepares the skeleton, with the right fingerprint:

```bash
lynceus annoter captures/name-of-the-page.md --annotateur my-pseudonym \
  > my-pseudonym-name-of-the-page.yaml
```

```yaml
cas: captures/name-of-the-page.md
annotateur: my-pseudonym
guide: "1.0"
content_hash: 5c1e…
categorie: pseudo_science
categories_acceptables: [publicite_sponsorise]   # only for a true hybrid
grade: [D, E]
intervalles:
  - extrait: "what the laboratories do not want you to know"
    technique: verite_cachee
  - extrait: "Order before it runs out of stock"
    technique: urgence_artificielle
notes: |
  Selection: fact-checking section, batch 3.
  Hesitated on autorite_anonyme for "American researchers", not marked: the study is cited further down.
```

## 6. The process

### 6.1 Training

Each annotator reads [TAXONOMIE.md](TAXONOMIE.md), [METHODOLOGIE.md](METHODOLOGIE.md)
§1 and §2, and this guide. They then annotate five specimens of the calibration corpus,
compare their reading with the expectations in `corpus.yaml`, and discuss it with the
coordination.

### 6.2 Pilot

Twenty pages, all read by two annotators. Each disagreement is discussed in a session, and
the guide is revised accordingly: this is what moves the version to 1.1. The pilot pages go
to the `reglage` part, since they have been discussed.

In the start-up phase, the pilot is done alone: twenty pages read, then all read again four
weeks later. Each gap between the two readings points at a rule of the guide that needs
sharpening. Each new volunteer then does their own pilot on those twenty pages, whose
readings are published since they belong to the `reglage` part, and compares afterwards.

### 6.3 Production, in batches of twenty pages

1. **Selection and capture** by the coordination: each page is captured with
   `lynceus capturer`, which computes the fingerprint. The capture joins the
   coordination's private archive, backed up elsewhere: a lost capture cannot be recreated
   identically, and its annotations would become unusable. The entry is added to
   `corpus/evaluation.yaml`, with `lot` and `partie`.
2. **Distribution** of the captures to each page's two annotators, outside the repository.
3. **Reading**, independently. Each annotator hands their files to the coordination,
   outside the repository: a reading published before the other one is done would be
   visible to all.
4. **Checking**: the coordination places the batch's readings in
   `corpus/annotations-en-cours/<pseudonym>/`, which git ignores, and runs
   `lynceus mesurer corpus/evaluation.yaml`, which reads both folders. A faulty annotation (fingerprint,
   technique, excerpt not found) is sent back to its author. The command lists the pages to
   arbitrate.
5. **Arbitration** of the listed pages: the arbiter reads the page, then the two readings,
   and writes their own with `lynceus annoter --arbitrage`. They consult no card. A
   disagreement on the boundaries of the same technique needs no arbiter: partial overlap
   accounts for it.
6. **Publication** of the batch in a single pull request: closed pages move from
   `annotations-en-cours/` to `annotations/`, with the manifest entries and the
   arbitrations. The commit message gives the batch's inter-annotator agreement, and credits
   each volunteer with a `Co-authored-by:` line (section 10).

### 6.4 Watching agreement

After each batch, `lynceus mesurer` gives the agreement between annotators. Starting
thresholds, to be revisited after the pilot:

| Measurement on a batch | Threshold | Below it |
|---|---|---|
| Category kappa | 0.6 | Pause, calibration session, revision of the guide |
| Technique F1 between annotators | 0.5 | Same |

Low agreement is not the annotators' fault: it is almost always a rule of the guide that
is missing or that can be read two ways.

### 6.5 Freeze and first measurement

When the `test` part reaches 200 pages, each read by two people:

1. Git tag `evaluation-v1` on the commit that contains the last batch.
2. Publication of the inter-annotator agreement over the whole set.
3. First measurement of the current chain:

```bash
lynceus calibrer corpus/evaluation.yaml --json evaluation-v1.json
lynceus mesurer corpus/evaluation.yaml --rapport evaluation-v1.json --json mesures-v1.json
```

This run costs one analysis per page, about 240 calls to the model provider. It is done on
a development instance, never on production.

## 7. Where each thing lives

| What | Where | Public |
|---|---|---|
| This guide | `docs/ANNOTATION.md` | Yes |
| Manifest of the set | `corpus/evaluation.yaml` | Yes |
| Published readings and arbitrations | `corpus/annotations/<pseudonym>/` | Yes |
| Captures | The coordination's private archive, backed up | No |
| Readings in progress | With the annotator, then `corpus/annotations-en-cours/` with the coordination | No, until the page is closed |
| List of annotators and licence | `corpus/annotations/README.md` | Yes |
| Annotators' declarations of ties | Coordination | No |

## 8. The time needed

Estimates to be confirmed on the pilot:

| Task | Unit | Volume | Total |
|---|---|---|---|
| Selection and capture | 5 min per page | 240 pages | 20 h |
| Reading | 20 min | 480 readings | 160 h |
| Arbitration | 10 min | about 80 pages, one in three | 15 h |
| Coordination and sessions | | | 15 h |

That is in the order of **210 hours**, three quarters of it reading. With two regular
annotators at four hours a week each, that makes about five months; with four, under
three.

## 9. Public corpora, a parallel track

Public datasets (SemEval 2023 task 3, CheckThat! 2024, FLICC, MAFALDA) are brought back to
our techniques through the tables in `corpus/correspondances/`. They serve for training
and rough work, and give a secondary measurement. They **do not replace** the annotated
set: their annotation guidelines are not ours, and most are not in French.

The conversion tool remains to be written. Each dataset's licence is checked before any
import, and none of these datasets enters the repository.

## 10. Licence, agreement and credit

**The licence.** The annotations and the manifest of the evaluation set are published under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), not under the code's
AGPL-3.0, which is not designed for data. Anyone may reuse them, including to train a model,
provided they cite the source and share their own derived annotations under the same
licence. The notice is in `corpus/annotations/README.md`.

**Each annotator's agreement.** A volunteer joins the set through a first pull request,
which adds their line to the list of annotators in `corpus/annotations/README.md`. Their
commit carries their own `Signed-off-by`: under the [DCO](../../DCO.txt), they thereby
certify that they have the right to publish their readings under the licence stated in
that folder. That is their written agreement, dated, public, and it does not depend on the
coordination. None of their readings is published before it.

**Credit.** The annotator pseudonym is the GitHub handle, and it is known that it can
reveal a name. Each commit that publishes a volunteer's readings carries a
`Co-authored-by:` line in their name, with the address of their joining commit, which lists
them as co-author on the forge. Any reuse of the set cites "Lynceus annotations" and links
to the list of annotators.

**Still open**: recruiting volunteers and an arbiter.

## 11. The silver set, annotated by models

The test set measures; it is not enough to train an encoder, which needs thousands of
examples. Those come from a second set, the **silver set**, annotated by a panel of
language models and built in a separate repository,
[lynx-corpus](https://github.com/Nashi-cloud/lynx-corpus). The two sets never mix.

| | Test set | Silver set |
|---|---|---|
| Read by | humans, blind, without AI | two models, and a third that arbitrates |
| Size | 200 pages and more | thousands |
| Used to | measure | train |
| Where | `corpus/` in this repository | lynx-corpus |

**The panel.** Three open-weight models from three different providers: two read each page
independently, with this guide as instructions, and the third settles their disagreements
without being able to add a passage. Open weights by choice: several providers of closed
models forbid training a competing model on their outputs. Each model's licence is
checked before anything is published.

**The same check.** Each panel reading goes through the verification that human
annotations go through: technique from the reference list, excerpt found word for word,
fingerprint.

**Why it is never a reference.** A reference written by models would make the measurement
circular, since the chain being measured is itself a model. Different providers do not make
errors independent: three models in agreement can be wrong together.

**How it is measured.** By a blind audit: one page in ten, drawn at random, is read again by
a human who sees nothing of what the panel said about it. The panel is measured against
those readings like any chain, with the measurements of `lynceus mesurer`. If it
approaches the agreement between two humans, the silver set is usable; otherwise, we know
how noisy it is.

**Safeguards.**

- Each silver annotation carries `origine: machine` and the annotator `panel-argent`, and
  never enters `corpus/annotations/`.
- Pages of the calibration corpus and of the test set are excluded from the silver set, by
  address and by fingerprint.
- Pages of the silver set are excluded from the test set, through the `deja-vus.txt` list
  (section 4.3).
- No capture is versioned, here or there.

