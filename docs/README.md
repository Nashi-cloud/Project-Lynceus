# Lynceus documentation

Each document exists in two versions. **The French text is the original and prevails**:
these documents bind the project, and one authoritative language avoids two texts drifting
apart in silence. The English translations are full translations, not summaries, and
`./verifier.sh` fails as soon as one falls behind its original. Reading the English is
enough to know exactly what the project promises.

| Document | English | Français | What is in it |
|---|---|---|---|
| Ethical charter | [en/ETHIQUE.md](en/ETHIQUE.md) | [ETHIQUE.md](ETHIQUE.md) | Posture, privacy, fairness, acknowledged limits. Review criterion number one. |
| Methodology | [en/METHODOLOGIE.md](en/METHODOLOGIE.md) | [METHODOLOGIE.md](METHODOLOGIE.md) | Categories, dimensions, scale, how the grade is computed, special cases. |
| Taxonomy | [en/TAXONOMIE.md](en/TAXONOMIE.md) | [TAXONOMIE.md](TAXONOMIE.md) | The 31 detectable techniques, documented and sourced. A closed list. |
| Architecture | [en/ARCHITECTURE.md](en/ARCHITECTURE.md) | [ARCHITECTURE.md](ARCHITECTURE.md) | API, data model, deduplication, LLM layer, federation. |
| Compliance | [en/CONFORMITE.md](en/CONFORMITE.md) | [CONFORMITE.md](CONFORMITE.md) | What is processed, transmitted and kept, and under which legal basis. |
| Generative AI | [en/IA-GENERATIVE.md](en/IA-GENERATIVE.md) | [IA-GENERATIVE.md](IA-GENERATIVE.md) | How generative AI is used to build the project, and what is asked of contributions. |

Elsewhere in the repository: the versioned analysis prompts in [prompts/](../prompts/), the
calibration corpus and its results in [corpus/](../corpus/), and the operator guide in
[api/DEPLOIEMENT.md](../api/DEPLOIEMENT.md).
