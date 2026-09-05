# Publishing the extension to a store

**English** · [Français](PUBLICATION.fr.md)

Everything a human needs to submit this extension to the Chrome Web Store, and the decisions
that shape the submission. The steps that require an account, a payment or a screenshot cannot
be automated and are marked as such.

## The decisions, before the paperwork

**Unlisted first.** The listing is published but does not appear in searches: it is reached by
link only. That is proportionate to an audience of a handful of people and to a tool that has
never been diffused. Automatic updates, which is the whole point of a store, work exactly the
same for an unlisted listing as for a public one. Switching to public later is one setting.

**The store is added, never substituted.** A store is a chokepoint held by one company. For a
tool that publicly grades pages, and therefore comments on publishers, removal is not a
far-fetched hypothesis and there is no appeal worth the name. `/telecharger` on the portal
stays the documented fallback, and the self-hosting kit never depends on a store.

**One portal address is baked in, and that is a real concession.** The published container
image carries a *neutral* package, and the portal serving it injects its own address into
`portail.json` at download time. That is what lets anyone deploy the same image without
privileging any instance. A store package cannot do that: it is one immutable file for every
user, so it must carry one address, and that address is `https://lynx.nashi.cloud`. Every user
who does not change the setting will therefore send page content to that instance. It is
changeable in the settings, the source is public, and self-hosters keep the portal path. It is
still a centralisation, it is deliberate, and it is written here so that it is not mistaken for
an accident.

## Building the package

```bash
cd extension
npm run icones                                        # only if the logotype changed
node build.mjs --paquet --portail=https://lynx.nashi.cloud
```

The archive is **reproducible**: timestamps are fixed, so two builds of the same sources give a
byte-identical file. Publishing its fingerprint lets anyone check that the package distributed
by the store really is the published code. Note that `--portail=` is part of the sources for
this purpose: without the same flag the fingerprint differs, legitimately.

Rebuild `dist/` without the flag afterwards (`npm run build`) so that the locally loaded
extension goes back to proposing no portal.

## Listing fields

Name and short description are **already bilingual** and need no manual entry: the manifest
points at `__MSG_nom_extension__` and `__MSG_description_extension__`, and the store reads the
catalogues in `src/_locales/`. Their length is checked by `test/identite.test.mjs`, the store
truncating a name beyond 75 characters and rejecting a description beyond 132.

**Category**: Education. The tool teaches how to read a page, it does not filter or block.

**Single purpose**, to be stated in the form:

> Analyse the web page the user explicitly submits, grade how trustworthy it is, and explain
> the persuasion techniques it uses.

**Detailed description**, English:

> Lynceus analyses the web page you ask it to analyse, and explains the persuasion techniques
> it uses. It describes methods, never people or beliefs, and it quotes the page verbatim for
> every technique it reports.
>
> You start an analysis yourself, by right-clicking and choosing "Analyse this page with
> Lynceus". Nothing is sent without that gesture. The page is turned into text inside your
> browser before anything leaves it, so what travels is the article, not your session.
>
> The analysis card gives a grade from A to E, four scores (sources, factual accuracy, tone,
> transparency), the techniques found with the exact quote that supports each one, what the
> page does well, and questions you can ask yourself on any page.
>
> Everything is public and checkable: the analysis prompt, the catalogue of techniques, the
> methodology, and the calibration figures with their failures, are all published on the
> portal. The source code is free software under AGPL-3.0, and the whole stack can be
> self-hosted, in which case the extension talks to your own instance and no key is needed.
>
> Free of charge, no account, no email, no advertising, no tracking.

**Privacy policy URL**: `https://lynx.nashi.cloud/confidentialite`

## Permission justifications

The form asks for one sentence per permission. These are accurate, which matters more than
being brief: a justification that oversells is what gets a submission rejected.

| Permission | Justification |
|---|---|
| `activeTab` | Read the current page only at the moment the user explicitly asks for an analysis, from the context menu or the panel button. Grants nothing before that gesture and nothing on other tabs. |
| `scripting` | Inject the extraction script into the page being analysed, which turns it into text locally with Readability, and draw a coloured border on a page graded D or E. All the injected code ships in the package. |
| `contextMenus` | Add the "Analyse this page with Lynceus" entry, which is the main way a user starts an analysis. |
| `sidePanel` | Display the analysis card. The panel never opens on its own. |
| `storage` | Keep the user's settings: the address of the instance, the access key, and whether the passive badge is on. `storage.sync` so the settings follow the browser profile. |
| `tabs` (optional) | Read the address of the current tab so the toolbar badge can show a grade already known for that page. Requested only if the user turns the badge on, refusable, and the extension is fully usable without it. |
| Host permissions (optional) | Let the badge see the address after an in-page navigation, without a new user gesture, and let the border be drawn. Off by default, requested together with the badge in the settings, and revocable from Chrome. |

## Data usage disclosures

Answer the form honestly. Under-declaring is what gets an extension pulled.

- **Website content: yes.** The text of a page is sent to the configured instance, in Markdown,
  and only after the user has explicitly asked for that page to be analysed.
- **Web history: yes.** With the passive badge turned on, the extension sends a SHA-256
  fingerprint of the normalised address, or only its first five characters when the instance
  supports the k-anonymous lookup, to find out whether the page is already in the directory.
  The address itself is never sent. Declaring this is the honest reading even though the
  fingerprint is designed not to identify the page.
- **Everything else: no.** No name, no email, no account, no location, no financial data, no
  personal communications, no analytics, no advertising identifier. The access key is an
  anonymous bearer token, carries no identity, and goes only to the instance the user
  configured.
- **Remote code: no.** Everything executed ships inside the package. No CDN, no eval, no
  remotely fetched script.

The three certifications can all be signed truthfully: the data is not sold to third parties,
not used for any purpose unrelated to the single purpose above, and not used to determine
creditworthiness or for lending.

## What still needs a human

1. A Chrome Web Store developer account, with its one-off registration fee. Creating accounts
   and entering payment details is out of scope for automation.
2. **Screenshots**, at least one, 1280x800 or 640x400. The useful ones are the analysis card on
   a real page, the passive badge on the toolbar, and the settings page. A 440x280 promotional
   tile is optional for an unlisted listing.
3. Uploading the package and filling the form.
4. Review, usually a few days. An extension asking for host permissions, even optional ones, is
   often looked at more closely.

## Firefox, later

`addons.mozilla.org` gives the same automatic updates and its review is usually faster. The
manifest is already MV3, which Firefox supports, but the port is milestone 1 of the roadmap and
the shared test suite comes with it. Nothing here needs redoing: the same justifications and
the same disclosures apply, and AMO additionally accepts a source archive for reproducibility,
which this package is built for.
