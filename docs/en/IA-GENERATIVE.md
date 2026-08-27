# Use of generative AI in Lynceus

<!-- traduit-de: docs/IA-GENERATIVE.md sha256:91b6dfbc62f0f8f4 -->

> Translation for information. The French version, `docs/IA-GENERATIVE.md`, is the one that binds the project: should the two ever diverge, it is the one that counts.

Lynceus asks the pages it analyses to be transparent about their devices. It would be
unbecoming for it to be opaque about its own. This document says how generative AI is used
to **build** the project, which is a separate question from the generative AI the product
**uses** when it analyses a page.

It also serves as the policy for contributions, and as an answer to [NLnet's policy on the
use of generative AI](https://nlnet.nl/foundation/policies/generativeAI/), which applies to
work funded by that donor.

## Two things not to confuse

**AI in the product.** Lynceus sends the text of a page to a language model to describe the
persuasion devices it uses. That is the heart of the software, it is owned and documented
elsewhere: [ETHIQUE.md](ETHIQUE.md) for the posture, [METHODOLOGIE.md](METHODOLOGIE.md) for
what the model produces and what the server computes without it,
[CONFORMITE.md](CONFORMITE.md) for what travels and to whom. The warning displayed to the
user cannot be removed.

**AI in the workshop.** That is what this document is about: how the code, the tests and the
documentation were written.

## How this project is developed

The project is developed by a single person, with the assistance of a language model used
as a programming assistant, across almost the whole codebase: server code and extension,
tests, documentation, and part of the portal's prose.

What that does not change:

- **Responsibility.** Every architectural decision, every trade-off, every line merged is
  read and owned by a human, who must be able to explain it. An assistant's answer that is
  not understood does not get merged.
- **The verification routine.** `./verifier.sh` has to pass before any merge into `dev`,
  whatever the origin of the code. A bug fix requires a test that fails before it. Those
  rules know nothing of provenance, and have no need to.
- **The charter.** [ETHIQUE.md](ETHIQUE.md) remains review criterion number one.

What is **not** delegated: the ethical charter, the taxonomy of devices and its
justification, the grade weightings, and the judgement calls on posture. Those are the
places where the project takes on a responsibility towards the people it is meant to help,
and they are discussed, sourced and signed.

## Provenance in commits

A commit introducing a contribution substantially produced by an assistant carries two
trailer lines:

```
Assisted-by: <model identifier, version included>
Prompt: <the request, or a faithful summary if it was long>
```

For example:

```
feat(api): valider les extraits mot pour mot

Assisted-by: claude-opus-5
Prompt: rejeter toute détection dont l'extrait ne se retrouve pas dans le texte
  source, après normalisation des espaces, et renvoyer les rejets au client
Signed-off-by: First Last <address@example.org>
```

Three points of form, because these are real trailers and `git interpret-trailers` has to
be able to read them back:

- the keys carry no accented characters, since git only accepts letters, digits and
  hyphens;
- the block is **contiguous**, with no blank line before `Signed-off-by`, otherwise only
  the last paragraph is recognised;
- a long value continues on the following line with an indent.

The `Signed-off-by` line of the [DCO](../../DCO.txt) is still owed, and it carries the name
of a human: that human is the one certifying they have the right to contribute this work
under AGPL-3.0.

A commit that merely fixes, adapts or integrates generated code does not carry
`Assisted-by`: it is human work, and that is precisely the distinction the convention
exists to make legible.

For documentation and tests alone, the general declaration on this page is enough;
per-commit provenance remains preferable.

## Copyright and licence

Two consequences the project takes into account.

**What is purely generated is not protected.** Under Union law, a production obtained
without substantial human intellectual contribution gives rise to no copyright. It cannot
therefore be contributed under the AGPL as though it did, nor billed to a funder as human
work.

**What is generated must not reproduce someone else's work.** An assistant's output can
reconstruct code under an incompatible licence. Vigilance applies first to long, idiomatic
blocks, which are the most likely to have been reconstructed rather than written.

## What is asked of outside contributions

You may use an assistant. You are asked to:

1. **say so**, using the commit convention above;
2. **understand what you are proposing**, and be able to explain it in review;
3. **check the licence** of whatever the assistant hands you, as you would for a snippet
   found anywhere else;
4. **sign off** with the DCO, which remains a personal commitment.

A contribution a contributor cannot explain is refused, assistant or no assistant. That was
already true before.

## Detailed logs

Full transcripts of development sessions are not published: they contain infrastructure
secrets and personal data. They are kept by the maintainer and can be made available to a
funder on request, redacted of those elements. The provenance logs prepared for an
application follow this format.
