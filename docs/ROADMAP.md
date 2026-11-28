# Roadmap

OSMA is a local mentor for people learning to contribute to Bitcoin open-source projects. This page is the public plan. It is not a build checklist for a private milestone.

The app does not send telemetry. It cannot count installs, lesson completions, or pull requests. Anything numeric below is a **target**. A target is a goal to measure later from opt-in reports, not a result that has already happened.

No pilot cohort has been run. No language besides English is in the tree. No partnership is claimed.

## v0.1.0 candidate (prepared, not tagged)

The git tag and the GitHub Release are intentionally not created with this document. Notes for the release that would be published later are in [releases/v0.1.0.md](releases/v0.1.0.md). History is in [CHANGELOG.md](../CHANGELOG.md).

What is in the tree now:

- Guide mode when `OPENAI_API_KEY` is empty. No language model is called.
- Default model endpoint, if a key is set later: local Ollama (`llama3.2` at `http://127.0.0.1:11434/v1`). Cloud OpenAI is opt-in.
- Three English learning paths and local quiz grading:
  - Bitcoin fundamentals (8 lessons)
  - Lightning (3 lessons)
  - Contribution craft (8 lessons)
- Setup, test, and review notes for ten projects: Bitcoin Core, libsecp256k1, rust-bitcoin, rust-miniscript, BDK, LDK, LND, Core Lightning, BTCPay Server, and the Lightning BOLTs.
- Tools that read public GitHub issues, files, and pull requests. OSMA does not fork, push, or open pull requests, and it will not ACK a diff for the reader.
- SQLite on the machine for conversations. No accounts.
- `make start` for a host install and `make up` for Docker Compose.
- GitHub Actions: API `ruff` and `pytest`; web lint, test, and production build.
- MIT license, contributing guide, security policy, and [privacy notes](PRIVACY.md).

## Targets after v0.1.0

Proposed window: 1 January 2027 through 31 December 2027. These dates are a proposal for planning. They are not a commitment already funded.

| Milestone | Proposal | Target (not a result) |
| --- | --- | --- |
| M1. Publish v0.1.0 | Tag the release and keep guide mode, CI, and the English curriculum working. | **Target:** one public git tag `v0.1.0`. Not created yet. |
| M2. Languages | Add a way to contribute reviewed translations. Ship lesson text in African languages chosen with native-speaker reviewers. Candidate languages to consider from Zambia, where the maintainer lives, include Bemba and Nyanja. The third language is not chosen. | **Target:** English plus 3 languages whose lesson text a native speaker has reviewed. |
| M3. Freedom-tech tracks | Add study tracks beyond the current catalog: Nostr, ecash (Cashu or Fedimint, as Bitcoin-adjacent ecash), and a deeper Lightning contribution track. Still no pull-request automation. | **Target:** those three tracks present in the curriculum or project catalog, with sources linked. |
| M4. Offline model bundle | Document and package a small open-weight model for Ollama so a conversational mentor can run after the download, without an API key sent to a cloud provider. Guide mode remains the default. | **Target:** one bundle tested on two modest laptop profiles and documented so someone else can repeat the install. |
| M5. Pilots | Invite cohorts only after a host agrees. Proposed hosts to approach: Bitshala, and developer communities in Africa. Approaching them is future work. Nobody has agreed. | **Target:** 2 cohorts held. **Target:** 40 people finish one path. **Target:** 15 of those people open their own first pull request on an upstream Bitcoin or freedom-tech repository. **Target:** 100 local installs reported by people who choose to say so. |

Pull-request targets count work the learner opens upstream. OSMA staying unable to open a pull request is part of the design, not a gap to close with the grant.

## How targets would be counted

Because the app stays local:

- Installs and path completions would come from people who opt in to say what they finished (a form, a workshop roll, or a message). They would not come from the binary phoning home.
- Pull requests would be counted from public upstream links that learners choose to share.
- Language targets would be counted from files in this repository reviewed by a named native speaker.
- If a number cannot be collected without tracking, it will not be collected.

## Out of scope

- Hosted multi-user accounts, analytics, or a required cloud model.
- Opening, pushing, or ACKing pull requests on the learner's behalf.
- Curricula for cryptocurrencies other than Bitcoin and the freedom-tech tools that carry Bitcoin (Lightning, ecash on Bitcoin, Nostr as a companion freedom technology).
- Claiming users, graduates, or partners that do not exist.
