# Security policy

**English** · [Français](SECURITY.fr.md)

## Reporting a vulnerability

Use **[private vulnerability reporting](https://github.com/Nashi-cloud/Project-Lynceus/security/advisories/new)** on this repository. It opens a private channel between you and the maintainer, and it is the right place even if you are unsure whether what you found counts.

Please do not open a public issue for a security problem, and please give the maintainer a chance to fix it before writing about it publicly. There is one maintainer and no service-level agreement: expect an acknowledgement within a few days, not within hours. Saying so plainly is better than promising a response time nobody can hold to.

## What is in scope

- **The directory API** (`api/`): access-key verification, the daily quota, rate limiting, the k-anonymous lookup, anything that would let someone spend an operator's model budget or read what they should not.
- **The portal** (`lynceus.portail`): key issuance and signing. The private Ed25519 key is the most sensitive secret in the project, since it mints keys valid on an instance.
- **The extension**: anything that would let an analysed page reach beyond its own tab, or send content without the user asking.
- **The privacy promises**, which are testable claims rather than intentions: no browsing history stored, no IP-and-URL pair logged, the prefix lookup never returning a full digest. If you can show one of them is false, that is a vulnerability.

## What is not a vulnerability

**An analysis you consider wrong, unfair or biased.** The card says so itself: it is produced by a language model and can be mistaken. That is what the dispute channel is for, `POST /v1/signalements` or the "Dispute this analysis" link on any card, including for publishers of analysed sites. See §6 of the [ethical charter](docs/en/ETHIQUE.md).

**The fact that page text reaches a model provider.** It is the most significant flow in the system, it is documented at the top of every instance's privacy policy, and the remedy is part of the deliverable: self-host with a local model and nothing leaves your machine. See [docs/en/CONFORMITE.md](docs/en/CONFORMITE.md).

**A third-party instance that is misconfigured.** Lynceus is self-hostable and there is no central authority. An instance exposed without access keys, or running a modified version, is the responsibility of whoever operates it. Report it to them. If the flaw is in what this repository ships, then it is in scope and we want to hear about it.

## Supported versions

The latest release on `main`. Older tags receive no fixes: instances are expected to follow, and updating is a `pull` away.

## If you operate an instance

The two things worth checking first, both documented in [api/DEPLOIEMENT.md](api/DEPLOIEMENT.md):

- the **private key must not live on the instance**. It belongs to whoever issues keys. Compromising the instance must not let anyone mint keys;
- `LYNCEUS_ENTETE_IP_REELLE` must only be set if the instance is reachable **solely** through your proxy. An HTTP header is trivial to forge, and setting it on a directly reachable instance hands the rate limit to anyone.
