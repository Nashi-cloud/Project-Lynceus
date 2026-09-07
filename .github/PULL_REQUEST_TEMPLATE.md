<!--
Write in French or in English, whichever you are more comfortable with.

The list below is not ceremony. Each line exists because its absence has already broken
something, and `verifier.sh` catches most of them before the pipeline does. Delete what does
not apply rather than leaving it unticked, so the remaining boxes still mean something.
-->

## What this changes, and why

<!-- The problem first, the solution second. A reviewer who understands the problem can
     judge whether the solution is the right size. -->

## How you know it works

<!-- What you measured, not what you expect. A prompt change is judged on a calibration run,
     a fix on the test that fails before and passes after. -->

## Before merging

- [ ] `./verifier.sh` passes (tests, typing, build, version consistency, secrets)
- [ ] Every non-merge commit increments `VERSION` by one patch, and `api/pyproject.toml` and `api/lynceus/__init__.py` agree with it
- [ ] Each commit carries `Signed-off-by:` (`DCO.txt` at the root, `git commit -s`)
- [ ] A contribution substantially produced by an assistant says so, with `Assisted-by:` and `Prompt:` next to the sign-off (`docs/en/IA-GENERATIVE.md`)
- [ ] The branch is merged with `--no-ff`, and targets `dev`, or `main` if it comes from `next`

## If it touches the analysis

- [ ] `prompts/`, `docs/METHODOLOGIE.md` or `docs/TAXONOMIE.md` changed: `prompt_version` incremented, and all four stamps agree
- [ ] `lynceus calibrer corpus/corpus.yaml --ecrire` run **three times**, on fresh analyses. One run says nothing solid: the model does not return the same analysis of the same text twice
- [ ] The reading section of `corpus/RESULTATS.md` is rewritten in both languages. The table is generated, that paragraph is not
- [ ] A corpus expectation that was loosened is justified case by case, in its `notes:`. Before touching an expectation, check that the prompt states the rule it enforces

## If it touches a translated document

- [ ] The translation has been revisited, and its `traduit-de` line updated (`lynceus traductions`)

## If it touches the extension

- [ ] `extension/manifest.json`, `package.json` and `CHANGELOG.md` announce the same version
- [ ] Name and description stay within the store limits, 75 and 132 characters, in every catalogue
