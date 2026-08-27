# Regulatory compliance

<!-- traduit-de: docs/CONFORMITE.md sha256:e70cd6ee17fe00b4 -->

> Translation for information. The French version, `docs/CONFORMITE.md`, is the one that binds the project: should the two ever diverge, it is the one that counts.

This document sets out the compliance analysis of the project and of the reference
instance. It is versioned with the code, like the charter: changing it is a public act.

> **This document is not legal advice.** It sets out the project's own analysis and the
> measures actually implemented, together with the points that still need a professional's
> validation. Claims that can be verified in the code point at the file concerned.

## 1. Identifying the publisher

Any service communicating with the public online must identify its publisher. Since
Lynceus is self-hostable, that identity **depends on whoever operates the instance** and
cannot be hard-coded.

It is therefore configured (`LYNCEUS_PORTAIL_EDITEUR_*`, `LYNCEUS_PORTAIL_HEBERGEUR_*`)
and published on `/mentions-legales`. Two safeguards:

- if the identity is incomplete, the page **says so** instead of displaying invented
  details (`gabarits/_legal_incomplet.html`);
- the portal **warns at startup** when it declares itself a public instance without a
  complete identity (`portail/__init__.py`).

## 2. Personal data

### What is processed

| Processing | Data | Legal basis relied on | Retention |
|---|---|---|---|
| Directory lookup | prefix of a URL digest, IP address for the duration of the request | legitimate interest | none |
| Analysing a page | page text, title, URL, IP address | legitimate interest | the analysis, with no link to a person |
| Rate limiting | IP address, counter | legitimate interest (protecting the service) | one-minute sliding window, in memory |
| Dispute | message, optional contact | legitimate interest (right of reply) | as long as the analysis is published |
| Issuing a key | none | not applicable | none |

### The transfer that must not be glossed over

Analysing means transmitting the text of the page to the configured **language model
provider**, which may be established outside the European Union. It is the most
significant flow in the system.

Three consequences, accepted knowingly:

1. the privacy policy states it **at the top of the page**, not in a footnote;
2. it names the provider **actually configured**, read from the instance's `/v1/meta`
   rather than typed by hand, so that it cannot quietly become false;
3. the remedy is a deliverable of the project, not a rhetorical dodge: a self-hosted
   instance running a local model lets no text out at all.

An instance aiming at strict compliance with regard to transfers outside the Union should
choose a provider established in the Union, or a local model. The project locks in no
provider: it is an OpenAI-compatible adapter, changed by configuration.

### Minimisation by construction, not by promise

- **K-anonymity**: a lookup sends only the first characters of the URL digest, and the
  final match happens on the client. A dedicated test checks that the server never returns
  the whole digest (`tests/test_phase3.py`, `tests/test_portail.py`).
- **Local extraction**: the server never visits pages on the user's behalf, and therefore
  learns nothing about their browsing.
- **No account**: access keys carry nothing but an expiry date and a quota. The portal
  keeps no record of what it issues.
- **No cookie, no third-party resource**: fonts, stylesheet and scripts are served by the
  portal itself. No consent banner, because there is nothing to consent to.

### An honest limit on data subject rights

Attaching nothing to a person has an awkward consequence: in practice there is no way to
find "somebody's data". That is not a loophole, but it has to be said rather than
promising a right of access that cannot be exercised. Disputes filed with a contact, on
the other hand, are identifiable and can be erased.

## 3. Transparency of AI systems

The European regulation on artificial intelligence requires people to be informed when
they interact with an AI system or read content it produced.

Measures in place:

- every analysis card carries a warning **added by the server**, which the client cannot
  remove (`main.py`, the `AVERTISSEMENT_IA` constant);
- the model's confidence index is displayed;
- the model and its prompt version are published in every analysis and in `/v1/meta`;
- the methodology, the weightings and the reference list of techniques are public and
  versioned.

**Risk level analysis.** The system describes rhetorical devices in publicly available
content and takes no decision producing legal effects on people. It falls under none of
the uses listed as high risk: it does not determine access to education or to employment,
it does not evaluate persons, and it is not intended to influence an election. The
obligations retained are therefore those of transparency. **This classification still has
to be confirmed by a professional** before any public communication relies on it.

## 4. Analysed content and third-party rights

- Analyses bear on **publicly accessible content** and quote short passages for the
  purpose of analysis and comment, with the source stated. The server refuses any quote
  that cannot be found **word for word** in the page, which makes it impossible to
  attribute to someone words they did not say (`moteur/validation.py`).
- Analyses describe **devices**, never people. The charter requires it and the prompt
  states it explicitly.
- A **right of reply** is open to everyone, and first of all to the publishers of the
  sites analysed. The number of disputes received is public even before they are examined,
  and every moderation decision is justified and kept.
- The calibration corpus does **not** version captures of real pages, only their
  manifest: URL, date, content digest and expectations.

## 5. Licence and intellectual property

- The project is published under **AGPL-3.0**. Any modified version made available over a
  network must publish its sources.
- The rights holder is named in [AUTHORS.md](../../AUTHORS.md).
- Outside contributions fall under the **Developer Certificate of Origin**: every
  contributor certifies that they have the right to contribute their code under this
  licence ([DCO.txt](../../DCO.txt), see [CONTRIBUTING.md](../../CONTRIBUTING.md)).
- Embedded dependencies carry their own licence: htmx under 0BSD, Fraunces and Newsreader
  under the SIL Open Font License, with their notices in `api/lynceus/portail/statique/`.

## 6. What is still to be done

- [ ] Have the legal notice, the privacy policy and the terms of use reviewed by a
      professional before opening to the public.
- [ ] Decide on the model provider for the reference instance with regard to transfers
      outside the Union, and document it.
- [ ] Keep a record of processing activities if the operator is required to.
- [ ] Check the availability of the name "Lynceus" as a trade mark before any large-scale
      communication.
