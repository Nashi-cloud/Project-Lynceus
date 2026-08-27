# Lynceus ethical charter

<!-- traduit-de: docs/ETHIQUE.md sha256:8aa471a51c8942a1 -->

> Translation for information. The French version, `docs/ETHIQUE.md`, is the one that binds the project: should the two ever diverge, it is the one that counts.

This charter is binding: every feature, every prompt, every design decision must be answerable to it. It is versioned with the code, and changing it is a public act.

## 1. A lookout, not a judge

Lynceus **describes methods**; it does not judge people or beliefs.

- We say “this text uses an appeal to fear, here is the excerpt”. Never “this site is lying”, nor “you are wrong to believe it”.
- **Religious faith and personal convictions are not graded.** What is assessed: verifiable factual claims (“this remedy cures cancer”) and manipulation techniques (fear, urgency, “us against them” isolation), whatever tradition or ideology employs them.
- Readers draw their own conclusions. The aim is intellectual autonomy (inoculation theory), not agreement with a verdict.

## 2. Radical transparency

You cannot denounce opacity while being opaque.

- The **analysis prompts are public and versioned** in this repository ([prompts/](../../prompts/)).
- The **methodology, the weightings and the scale** are published ([METHODOLOGIE.md](../METHODOLOGIE.md)).
- Every analysis card states the model used, the prompt version and the confidence index.
- AGPL-3.0 licence: any modified public instance must publish its sources.

## 3. Scanning is deliberate

- **No page is analysed without the user knowing.** The analysis (sending the content) is always triggered by an explicit action.
- The passive badge (a directory lookup) sends only a URL hash, never content, and **can be turned off** in the settings.
- The side panel never opens by itself. No alarming notification, no page blocking: Lynceus informs, it prevents nothing.

## 4. Privacy

- **The server stores no browsing history.** Lookups are not logged with identifiers (no IP and URL pair is kept).
- No account required, no tracker, no hidden telemetry.
- The passive lookup works **under k-anonymity** (the HaveIBeenPwned technique): only the first 5 characters of the URL hash are sent, and the final match is made in the browser. The server cannot determine which page is being read. The historical mode (full hash) survives only for instances that do not advertise this capability.
- **What this promise does not cover, and must be said.** Analysing a page means sending its text to the model provider configured by the instance, which may be established outside the European Union. It is the most significant data transfer in the system, and the only one a user of the hosted service cannot avoid. A charter that praised k-anonymity without mentioning that flow would be misleading by omission, exactly the technique this project teaches people to spot.
- **The remedy exists and is part of what is delivered**: a self-hosted instance with a local model lets no text leave the machine. Full self-hosting is a first-class right, and the server “kit” is a deliverable of the project, not a second-rate option.
- Any instance open to the public must publish a privacy policy naming the model provider actually in use. The portal generates it from what the instance declares, so that it cannot go stale in silence.

## 5. Fairness of the analysis

- **Satire is not disinformation.** Satirical content is categorised as such, with a plain second-degree warning. (The standing crash test: never classify a parody site as “fake news”.)
- **An openly stated opinion is not manipulation.** An editorial is assessed on the honesty of its argument and on its openness, not on the position it defends.
- **Strong points are sought out systematically** and displayed. An analysis that can only say bad things loses all credibility with the very people it means to help.
- Quoted excerpts are **verbatim**: no technique is reported without an exact quotation from the page.

## 6. Fallibility, acknowledged

- The analysis is produced by a language model: **it can be wrong**. Every card shows a confidence index and that warning.
- Every analysis can be **disputed** from the panel or the API (`POST /v1/signalements`), including by the publishers of the sites analysed (reason `droit_de_reponse`). A dispute is anonymous by default: no personal data is required. The number of disputes is public on each analysis; their content is reserved to the operator of the instance (it may contain a contact).

  **What Lynceus promises, and what it does not.** A dispute is recorded, made visible as a count, and handed to the operator of the instance, who decides what follows. Their decision and its justification are kept. Since the project is self-hostable and has no central authority, no instance can guarantee systematic human review: the message shown to the user says so explicitly rather than promise moderation that would not exist. Only the “page has changed” reason is handled automatically (the content is checked again, and re-analysed where appropriate).
- Analyses are dated and can be regenerated: a site that improves will see its card change.

## 7. Teaching rather than judging

- Descriptive vocabulary (“signals to be careful about”, “techniques found”). Never “FAKE NEWS”, never a rubbish-bin emoji, never an accusing shade of red.
- Every technique found comes with an **explanation of the psychological mechanism**: it is learning the technique that inoculates, not the label.
- **“Questions to ask yourself”** accompany every card: the reader remains the investigator.

## 8. Independence

- No advertising, no sale of data, ever.
- Funding (hosting of the reference instance, inference costs) is transparent and published.
- No favours: the methodology applies identically to all content, whatever its leaning.

## 9. Legal framing

Lynceus publishes **methodologically grounded assessments of public content**, on the established ground of media-literacy initiatives (Décodex, NewsGuard, IFCN fact-checkers). Three safeguards: a published methodology, verbatim quotations, and a right of reply. Cards are about content and techniques, not about people.

## References

- *The Debunking Handbook 2020*, Lewandowsky, Cook et al.
- Sander van der Linden, *Foolproof* (2023): inoculation theory and prebunking.
- John Cook, the FLICC taxonomy (Fake experts, Logical fallacies, Impossible expectations, Cherry picking, Conspiracy theories).
- First Draft, typology of information disorder (Wardle & Derakhshan).
