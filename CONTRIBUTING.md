# Contributing to Lynceus

**English** · [Français](CONTRIBUTING.fr.md)

Thank you for wanting to help. Every contribution counts: code, taxonomy, calibration corpus, translations, hosting instances.

## Two things to know first

**The code is in French.** Identifiers, comments and commit messages are written in French, and that is not going to change: rewriting a codebase that already holds together would cost far more than it would bring. The documentation, on the other hand, is in English. Issues and pull requests are welcome in either language, and nobody will be turned away for writing in one rather than the other.

**The documents that bind the project have French as their original.** The charter, the methodology, the taxonomy, the analysis prompts and the calibration results are written in French and the French text prevails in case of divergence. The English versions are real translations, not summaries, and a build fails as soon as one of them falls behind its original. Reading the English is enough to know what the project promises.

## Branch model

```
feat/*  fix/*  docs/*        (topic branches, off dev)
      │
      ▼  PR and review
     dev                      (continuous integration of development)
      │
      ▼  batch judged stable
     next                     (pre-production: stabilisation, instance testing)
      │
      ▼  PR approved on GitHub, then tag (vX.Y.Z)
     main                     (stable: this is what instances deploy)
```

- **`main`**: stable only. It receives merges from `next` and nothing else, through a pull request the maintainer approves on GitHub, and every release is tagged there.
- **`next`**: pre-production. Receives `dev` when a coherent batch is ready; stabilisation happens there.
- **`dev`**: the integration branch. Every topic branch starts from it and comes back to it.
- **Topic branches**: `feat/<subject>`, `fix/<subject>`, `docs/<subject>`. Short, focused, merged into `dev` through a PR.

### Promotion, in order

1. **Develop** on a topic branch started from `dev`.
2. **Merge into `dev`** once `./verifier.sh` passes, using `--no-ff`. The pipeline replays the tests and publishes `:dev`.
3. **Merge `dev` into `next`** when the batch stands up. The pipeline publishes `:next` and deploys to staging: that is where the update is put through its paces on a real instance, migrations included.
4. **Open a `next` → `main` pull request** on GitHub, which the maintainer approves personally. The merge triggers publication of `:latest` and `:v<VERSION>`, and deployment to production.
5. **Add the annotated tag** `vX.Y.Z` on the merge commit, matching the `VERSION` file.

No step is skipped: nothing reaches `main` that has not been through staging.

## Verification routine

**Before any merge into `dev`**:

```bash
./verifier.sh              # API and extension tests, typing, build, version consistency
./verifier.sh --calibrer   # plus a calibration pass (needs a server, spends tokens)
```

The script fails if a test breaks, if strict typing is not respected, or if the extension versions diverge between `manifest.json`, `package.json` and `CHANGELOG.md`.

The individual steps, if you need to run them separately:

| Step | Command | When |
|---|---|---|
| API tests | `cd api && .venv/bin/python -m pytest` | any change under `api/` |
| Extension typing | `cd extension && npm run verifier` | any change under `extension/` |
| Extension tests | `cd extension && npm test` | any change under `extension/` |
| Extension build | `cd extension && npm run build` | before reloading in Chrome |
| Calibration | `lynceus calibrer corpus/corpus.yaml` | **mandatory** if `prompts/`, `docs/METHODOLOGIE.md`, `docs/TAXONOMIE.md` or the model change |

`verifier.sh` also refuses a mismatch between the highest version under `prompts/analyse/`, the stamps in `docs/METHODOLOGIE.md` and `docs/TAXONOMIE.md`, and the version `corpus/RESULTATS.md` reports on. Those four share a single counter, `prompt_version`, the one every analysis announces.

## What a push triggers

The repository is built for a forge with a self-hosted runner (see [api/DEPLOIEMENT.md](api/DEPLOIEMENT.md)). The tests replay there what `verifier.sh` does locally, in throwaway containers.

| Branch | Tests | Image published | Deployment |
|---|---|---|---|
| `feat/*`, `fix/*`, `docs/*` | yes | none | none |
| `dev` | yes | `:dev` | none |
| `next` | yes | `:next` | staging |
| `main` | yes | `:latest` and `:v<VERSION>` | production |

The pipeline is not a substitute for running `./verifier.sh` before merging: it observes, it does not proofread. And it does not run for a proposal coming from a fork, since a self-hosted runner executes whatever code it is handed.

**API version**: the `VERSION` file at the root is authoritative, and must agree with `api/pyproject.toml` and `api/lynceus/__init__.py`. That is what the pipeline reads to tag the image published from `main`, and therefore what makes a rollback possible. `verifier.sh` refuses a mismatch.

## Conventions

- **Commits**: Conventional Commits style, in French: `feat: …`, `fix: …`, `docs: …`, `chore: …`, `test: …`.
- **One branch per subject**, merged into `dev` with `--no-ff` (the history keeps a trace of the grouping).
- **Promotion merges**: `dev` → `next` and `next` → `main` use `--no-ff` as well. Those two branches never diverge, so a fast-forward would work, but it would lose the `merge: next → main (vX.Y.Z)` commit that makes the graph readable and gives an obvious point to roll back to. A fast-forward is still fine to catch `next` up with `dev` when there is nothing to mark.
- **Tests are mandatory** for any bug fix: the test must fail before the fix. For a feature, test at least the business logic that can be isolated from the browser APIs.
- **Extension versions**: any change under `extension/` increments the version in `manifest.json` **and** `package.json`, with an entry in `extension/CHANGELOG.md` (patch for a fix, minor for a feature). Without that, there is no way to tell which build is loaded in Chrome.
- **Prompts and methodology**: any change to `prompts/`, `docs/METHODOLOGIE.md` or `docs/TAXONOMIE.md` increments `prompt_version` (semver) and must pass calibration against `corpus/`. Report the result in [corpus/RESULTATS.md](corpus/en/RESULTATS.md).
- **Corpus**: never relax an expectation to make a test pass without having examined the case, and never on `techniques_attendues` / `techniques_interdites`, which are the heart of the measurement.
- **Taxonomy ids**: stable and final, never renamed (the directory references them).
- **Charter**: every PR must be compatible with [docs/en/ETHIQUE.md](docs/en/ETHIQUE.md). That is review criterion number one.
- **Translations**: the portal is bilingual. An interface string lives in the catalogues (`api/lynceus/portail/traductions/*.po` for the site, `extension/src/_locales/*/messages.json` for the extension) and the tests refuse a string used without a translation. A repository document published by the portal is translated into a language subfolder: `docs/ETHIQUE.md` becomes `docs/en/ETHIQUE.md`. The translated file carries, on its second line, the digest of the version it translates:

  ```
  <!-- traduit-de: docs/ETHIQUE.md sha256:8aa471a51c89 -->
  ```

  `lynceus traductions` reports where each document stands, and `verifier.sh` fails if a translation has fallen behind its original. **Changing a translated document therefore means revisiting its translation and updating that line.** Without it, the portal would publish two texts that no longer say the same thing, with nothing to signal it.

  Two conventions coexist, and the rule is simple: **where a file is a door, English sits at the door; where a file is the law, French stays the original.** `README.md`, `CONTRIBUTING.md`, `INSTALLATION.md` and the `README.md` of each subfolder are in English at their canonical path, with the French next to them as `*.fr.md`. Everything under `docs/`, `prompts/` and `corpus/RESULTATS.md` keeps French at the canonical path, with the translation under `en/`.
- **Generative AI**: a contribution substantially produced by an assistant says so, with `Assisted-by:` and `Prompt:` lines at the end of the commit message, adjacent to `Signed-off-by:`. See [docs/en/IA-GENERATIVE.md](docs/en/IA-GENERATIVE.md). A contribution its author cannot explain in review is refused, assistant or no assistant.

## Rights over contributions

The project applies the **Developer Certificate of Origin** ([DCO.txt](DCO.txt)), the same
mechanism the Linux kernel and Git use. Nothing to sign, nothing to send back: you add one
line to each commit.

```bash
git commit -s -m "feat: ..."      # -s adds the Signed-off-by line
```

```
Signed-off-by: First Last <address@example.org>
```

With that line you certify that you have the right to contribute this code under the
AGPL-3.0 licence. You **keep your copyright** over your contribution: the project asks for
no assignment.

The consequence is accepted knowingly: the project can never be relicensed without the
agreement of every contributor, and can therefore never sell exceptions to the AGPL. That is
the price of paperwork-free contribution, and the choice was made with open eyes. Add
yourself to [AUTHORS.md](AUTHORS.md) with your first contribution.

## Local development

See [api/README.md](api/README.md) (server and CLI) and [extension/README.md](extension/README.md).

## Licence

The project is under **AGPL-3.0**: by contributing, you accept that your contribution is
published under that licence.
