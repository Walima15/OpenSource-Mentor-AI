# HRF application draft — OSMA

**Draft for Mwila Alfred Walima to edit. Not submitted.**

This draft answers the live Human Rights Foundation Bitcoin Development Fund form as read on 27 November 2026. The public program page is [Bitcoin Development Fund](https://hrf.org/program/financial-freedom/bitcoin-development-fund/). The form linked from [hrf.org/bdfapply](https://hrf.org/bdfapply) redirects to the Airtable form titled **HRF Bitcoin Development Fund Grant Application Form**:

https://airtable.com/apphkk1AtkOUhTKGn/pagYVcAbWIGehYzo6/form

The form’s own intro says this application is the first step, that required fields are marked, and that a question which does not apply should be answered `N/A`. It also says a later stage may ask for audited financials, legal documents, and a detailed budget breakdown. References are optional and described as highly recommended. Letters can be sent to `bdf@hrf.org` with the project name and the reference’s name.

Every dollar figure below is a **proposal for Mwila to adjust** before anything is submitted. This file does not record users, graduates, signed partnerships, or prior grants. Where a fact was not supplied, the field says to fill it in.

A shorter note at the end maps the same project to HRF’s [AI for Individual Rights](https://hrf.org/program/ai-for-individual-rights/) program. That is a different fund. Do not paste this whole document into both forms without editing.

## Fill in before submitting

- Applicant email
- Applicant phone (the label says optional; on 27 November 2026 the control was still marked required)
- Personal social media handles
- Two references, or a plan to have them email `bdf@hrf.org`
- Confirm prior funding. This draft does not know of any.
- Confirm the start date, end date, and every budget line
- Read the form disclaimer and the note to applicants, then check those boxes yourself
- Confirm “Individual” and “not a pseudonym” still match how you want to apply

## Form answers

### Are you applying as

**Proposed answer:** Individual.

OSMA is maintained by one person. Change this if an organization will hold the grant.

### Are you applying under a pseudonym?

**Proposed answer:** No.

The form says that if you select No, HRF may use your real name in public reference to the grant. The repository copyright already uses this name. Select Yes only if you want a different public name, and be ready for a later stage to ask for a legal name.

### Applicant's first and last name

Mwila Alfred Walima

### Applicant email

Fill in the address you want HRF to use. It is left blank here so this public draft does not add a contact address.

### Applicant phone

Fill in. Left blank on purpose.

### Project title

Open Source Mentor AI (OSMA)

### Project area of focus

**Proposed selection:** Financial Freedom Education.

The dropdown is a single choice. The options seen on the form were: Bitcoin Core, Lightning Network, Nostr, Community Building, Financial Freedom Education, Conferences, Translation Work, Others.

Education is the closest fit for a mentor that teaches people to contribute to Bitcoin software. Bitcoin Core, Lightning, translation, and community work are part of the project and of the proposed grant, but they are not separate applications.

### Other, please describe

If this field accepts `N/A` when the area is not “Others”, use `N/A`. If it stays required, use:

OSMA is a local-first open-source mentor for contributing to Bitcoin software (including Bitcoin Core and Lightning). The proposed grant work adds African-language lessons, Nostr and ecash study tracks, an offline model bundle, and pilot cohorts.

### Short project description (1–2 sentences)

OSMA is a local-first, open-source mentor that teaches developers how to contribute to Bitcoin open-source projects. It runs on their own computer, and guide mode works with no API key and no cloud model.

### Detailed project description

**The problem.** Bitcoin’s censorship resistance depends on software that people can read, run, and maintain: full nodes, wallets, Lightning, and the review culture around them. That work is hard to enter. Documentation is scattered, review norms (ACK and NACK, tests, signed commits, mailing lists) are easy to get wrong, and many newcomers are steered toward opening a pull request before they can read a diff. For a developer in a repressive environment, a cloud chatbot is a poor substitute: the prompts, the repository names, and the study notes leave the machine and sit with a company that can be ordered to keep or surrender them.

**Proposed solution.** OSMA is a mentor you run locally. The web app and the API bind to loopback. Lessons, quizzes, and project setup notes ship in the repository. With an empty `OPENAI_API_KEY`, guide mode answers from those notes and from public GitHub tools, and it does not call a model. If you want conversation, the default server is Ollama on the same machine, not a cloud API. Cloud OpenAI is a separate opt-in. OSMA will not open a pull request and will not ACK code the reader has not reviewed. The point is to train contributors, not to file patches for them.

**What v0.1.0 already contains.** This is scope in the git tree, not traction:

- English paths: Bitcoin fundamentals (8 lessons), Lightning (3 lessons), contribution craft (8 lessons), each with a quiz graded locally.
- Guides for Bitcoin Core, libsecp256k1, rust-bitcoin, rust-miniscript, BDK, LDK, LND, Core Lightning, BTCPay Server, and the Lightning BOLTs.
- GitHub lookups for issues, files, and pull requests.
- MIT license, contributing and security docs, a privacy note, GitHub Actions CI, and one-command local setup (`make start`, `make up`).
- Versions declared as 0.1.0. The git tag is not created yet.

**Key activities and timeline (proposal).** 1 January 2027–31 December 2027, if that window still fits when you apply.

1. Tag and maintain v0.1.0. Keep guide mode working without a key.
2. Add a translation path and ship lessons in three languages reviewed by native speakers, including African languages. Bemba and Nyanja are candidates because the maintainer is in Lusaka. The third language is not chosen. No translator is hired.
3. Add study tracks for Nostr, for Bitcoin ecash (Cashu or Fedimint), and a deeper Lightning contribution track.
4. Package a documented offline open-weight model bundle for Ollama, tested on two modest laptops. Guide mode stays the default.
5. Approach Bitshala and African developer communities about pilot cohorts. Run a cohort only after a host agrees. No host has agreed. Mwila is a Bitshala MB Season 07 participant; that is personal participation, not a partnership with Bitshala.

**Target communities.** Developers who want to contribute to Bitcoin and related freedom-tech projects, with proposed emphasis on developers in Africa and on anyone who should not send study notes to a hosted model. OSMA does not have a user count. Do not describe a community as already served.

**Expected results.** See the targets under “How do you measure success”. They are goals. They are not outcomes already achieved.

### How does your project relate to HRF's mission?

HRF’s Bitcoin Development Fund, as described on the program page, supports work that makes Bitcoin and related freedom technologies more useful for human rights defenders and other people in difficult political environments, including education, translation, and community building. The same page says HRF is particularly interested in Bitcoin Core, Nostr, ecash, and complementary freedom technologies, and that it does not fund alternative cryptocurrencies.

OSMA serves that mission as education and as contributor infrastructure. People living under financial surveillance and confiscation need software they can run themselves. That software stays alive only if new contributors can enter Bitcoin Core, wallets, Lightning, and neighboring freedom tech without a corporate gate. A local mentor lowers that entry cost while leaving the learner in control of the patch and the review.

The privacy property is part of the rights argument, not a side feature. Studying Bitcoin, reading a dissident’s toolchain, or drafting a first contribution can itself be sensitive. Guide mode keeps lesson text and chat on the machine. There is no account and no OSMA-operated analytics service. The optional model defaults to local Ollama. That matches the individual-rights case for tools a person can inspect and run without handing a transcript to a company or a regime.

Limits, so this is not oversold: public GitHub lookups still leave the machine; a cloud model is possible if someone opts in; the local database is not an encrypted vault; the app should stay on localhost. `docs/PRIVACY.md` and `SECURITY.md` state this. The project does not claim to be anonymity software.

OSMA does not promote an altcoin. Proposed ecash work is Bitcoin ecash. Proposed Nostr work is the freedom-tech protocol HRF already lists, taught as a contribution track beside Bitcoin.

### Why should HRF fund your project?

The first version is already public, MIT-licensed, and runnable with no API key. CI is on. The maintainer is one developer, Mwila Alfred Walima, in Lusaka, Zambia: a Bitshala MB Season 07 participant, a ZecHub contributor, and a blockchain educator. Funding would buy time to keep that local-first mentor maintained and to add the pieces a grant is actually for: reviewed African-language lessons, Nostr and ecash tracks, a packaged offline model, and the first real cohorts.

Those additions are not built, and they are the work product. There is no existing user base to cite, and this draft does not invent one. What exists is a tool a learner can clone today and a written plan with targets that can be checked later without telemetry.

### Project proposed start date

**Proposal:** 2027-01-01

### Project proposed end date

**Proposal:** 2027-12-31

### Project's geographic focus

Global software, maintained from Lusaka, Zambia. Anyone can clone it. The proposed pilots focus on developers in Africa, including communities the maintainer can reach from Zambia, and on learners elsewhere who need an offline or local-only study tool. No country program is operating.

### Project history

OSMA was rewritten as this local mentor on 31 October 2026 (commit `58c7fc3`), replacing an earlier hosted prototype that is not part of the current app. Local Ollama defaults, the MIT license, and privacy, security, and contributing docs landed on 26 November 2026. CI, Next.js 16.4.5, and one-command setup landed on 27 November 2026. v0.1.0 is prepared and not tagged.

It has not been piloted with a cohort. It has not been translated. It has not been packaged as an offline model bundle. Treat earlier repository history as engineering history, not as evidence of adoption.

### Deliverables

Concrete outputs the proposed grant would produce:

- A tagged v0.1.0 release of the existing local-first mentor, kept installable with `make start` and covered by CI.
- Reviewed translations of the curriculum into three languages beyond English, including African languages, with the reviewer credited. Specific languages stay open until native speakers agree. Bemba and Nyanja are candidates only.
- New open-source study tracks for Nostr, Bitcoin ecash, and a deeper Lightning contribution path, in this same repository, under the MIT license.
- A documented offline model bundle for local Ollama, plus notes on two modest machines it was tried on. Guide mode remains the default and still requires no model.
- Written pilot materials (a session plan and a way for participants to opt in to reporting what they finished). Cohorts themselves happen only if a host agrees.
- A short public report at the end that lists only numbers people chose to share, and that says when a target was missed.

### Expected outcomes

Proposed impact, not impact already measured:

- More developers can practice Bitcoin contribution skills without sending prompts to a hosted model.
- Native-speaker-reviewed lessons make a portion of that path readable beyond English.
- Learners who finish a path are better prepared to open their own small pull request and to survive review, which is how Bitcoin and freedom-tech projects actually gain maintainers.
- People who cannot rely on cloud AI still have a mentor that runs on hardware they control.

No outcome below should be described as finished.

### How do you measure success of your project?

All figures are **targets**. The app will not collect them by phoning home. Sources would be opt-in workshop rolls, messages people choose to send, public pull-request links they share, and files in the repository.

| Target | Proposed bar |
| --- | --- |
| Release | Git tag `v0.1.0` exists and `make check` is green on that tag. |
| Languages | English plus 3 languages with native-speaker review recorded in the repo. |
| Freedom-tech tracks | Nostr, Bitcoin ecash, and an expanded Lightning track are in the tree, with upstream sources linked. |
| Offline bundle | One documented bundle, repeated on two modest laptop profiles. |
| Local installs | **Target:** 100 installs reported voluntarily. |
| Developers onboarded | **Target:** 40 people complete one learning path in a pilot. |
| Pull requests mentored | **Target:** 15 pull requests opened by those learners on upstream Bitcoin or freedom-tech repositories. OSMA does not open them. |
| Pilots | **Target:** 2 cohorts, only after a host agrees. Proposed places to ask: Bitshala and African developer communities. Zero are agreed. |

A missed target stays missed in the report. It is not replaced with a softer number after the fact.

### Has this project received any prior funding?

**Not recorded in this draft.** Before submitting, write the true answer. If there has been no grant, contract, or sponsorship for OSMA, say so in your own words. Do not leave this file’s uncertainty in the form.

### Is the project free and open source?

**Yes.** MIT License, Copyright (c) 2026 Mwila Alfred Walima. Repository: https://github.com/Walima15/OpenSource-Mentor-AI

### Github, social media, and websites

- https://github.com/Walima15/OpenSource-Mentor-AI
- https://github.com/Walima15

No project social account or project website is recorded here. Do not list a dead deployment URL. The app is meant to be run locally.

### Applicant's personal social media handles

Fill in from the profiles you actually use (X, Nostr, and others). Left blank so this draft does not guess handles.

### Annual project budget

**Proposal: $36,000**

This equals the amount requested below because this draft records no other income for the year. If you add unpaid time, a fiscal sponsor fee, or other funds, change both numbers so the form stays consistent. Format on the form is `$`.

### Amount requested from HRF

**Proposal: $36,000**

HRF’s program page says a selected grant is arranged as a Bitcoin grant and that amounts vary by project. The form asks for dollars. These figures are planning numbers for that dollar field. They are not a conversion into satoshis and not a quote from HRF.

### What will funding be used for?

**Every line is a proposal. Adjust the amounts, the split, and the total before submitting.** HRF’s form asks for categories such as direct costs (salaries), equipment and materials, travel, and taxes. It says the program does not fund personal expenses, and that a later stage would require a line-item budget and financial documentation.

| Proposal line | USD | What the line is for |
| --- | ---: | --- |
| Direct costs (maintainer time) | 22,000 | One maintainer for the year: tag and maintain v0.1.0, translation workflow, Nostr, ecash, and Lightning tracks, offline-bundle packaging, pilot materials, and the closing report. This is project labor, not a personal-expense allowance. |
| Translation and review stipends | 6,000 | Stipends for native-speaker review of three languages. No reviewer is identified or contracted. Unused stipends are not personal spending. |
| Equipment and materials | 3,000 | Disks, a spare modest test machine if needed, and the practical cost of building and re-testing the offline model bundle. Hardware bought for the project stays with the project. |
| Pilot cohort costs | 3,500 | Connectivity, a room, and materials for proposed cohorts. Spend only if a host agrees. No venue is booked. |
| Travel costs | 1,500 | One proposed in-person working session tied to a cohort. Cut this line first if you want a smaller request. |
| Taxes | 0 | Not estimated. Confirm what you personally owe on a grant before submitting. Do not treat tax as a padded contingency. |
| **Amount requested (proposal)** | **36,000** | Sum of the lines above. |
| **Annual project budget (proposal)** | **36,000** | Same total, because no other funding is recorded in this draft. |

If you request less, keep the same activities and drop travel first, then shrink equipment, then shrink stipends, and say which target moves. Do not promise two cohorts and three languages on a budget that cannot pay for the review or the travel.

### References

Left blank. The form says references are optional and highly recommended. Provide the name and email of two people HRF may contact, or ask them to email letters to `bdf@hrf.org` with the project name “Open Source Mentor AI (OSMA)” and their name. Do not invent referees.

### Anything else

v0.1.0 release notes are in `docs/releases/v0.1.0.md`. The public roadmap, with the same targets labelled as targets, is in `docs/ROADMAP.md`. A local walkthrough of guide mode (no API key) is described in the README.

The maintainer will read the form’s disclaimer and the note to applicants at submission time. This draft does not check those boxes.

## Why local-first matters here

Developers and human rights defenders under repressive conditions are not only at risk when they move money. They are at risk when a hosted tool stores the fact that they were studying Bitcoin Core, a privacy project, or a dissident toolchain.

OSMA’s default is built for that constraint:

- No account, no telemetry, no OSMA-operated service required.
- Guide mode does not call Ollama and does not call a cloud model. Chat text stays in local SQLite.
- Quizzes and lessons are graded and read on the machine.
- The optional model defaults to loopback Ollama. A cloud model requires the operator to change the base URL and set a real key.
- Secrets are environment-only and are not stored in the database.

That is the case for funding the offline bundle and the language work together. A mentor that only works by sending prompts to a foreign API is the wrong default for someone whose queries should not exist on someone else’s server. A mentor that only exists in English misses developers who will maintain freedom tech in their own language.

The same docs name the holes: GitHub lookups are outbound, the database is not encrypted, and the port must stay on localhost. Those limits should stay in the application if a reviewer asks. Closing them by adding accounts or analytics would make the project worse for this mission.

## Add-ons this grant would fund

These are not in v0.1.0. They are the proposed use of funds.

1. **Languages, including African languages.** A contribution path for translations and three reviewed languages. Candidates to discuss with native speakers include Bemba and Nyanja. Not started. No translator contracted.
2. **Freedom-tech tracks.** Nostr, Bitcoin ecash, and a deeper Lightning contribution track, alongside the Bitcoin Core and Lightning material already in the tree. No altcoin track.
3. **Packaged offline model bundles.** A documented open-weight model for local Ollama so conversational help does not require a cloud key. Guide mode still works if the download never happens.
4. **Pilot cohorts.** Proposed outreach to Bitshala and to African developer communities. Mwila’s Bitshala MB Season 07 participation is the reason Bitshala is on the list. It is not an agreement, a co-brand, or a promised venue. Cohorts run only after a host says yes.

## AI for Individual Rights — optional second conversation

HRF’s AI for Individual Rights program, as published on https://hrf.org/program/ai-for-individual-rights/, funds open-source, privacy-protecting AI tools for dissidents and describes local inference (including Ollama) as a way to avoid sending sensitive prompts to a centralized provider. A May 2026 HRF note pointed proposals at https://hrf.org/AIGrants. Confirm that URL still works before using it. This BDF draft is not that application.

If you apply there later, the relevant facts are the same ones already written above: MIT license, guide mode with no key, default local Ollama, no telemetry, and a proposed offline bundle. Also state prior funding honestly, the proposed budget, and the targets table. Do not claim the BDF and the AI fund are one grant, and do not submit the same costs to both for the same work unless both funders have agreed to co-fund it. Nothing in this file is that agreement.

## Source notes for this draft

Read on 27 November 2026:

- Program page: https://hrf.org/program/financial-freedom/bitcoin-development-fund/
- Application form (via https://hrf.org/bdfapply): HRF Bitcoin Development Fund Grant Application Form on Airtable
- AI program page: https://hrf.org/program/ai-for-individual-rights/

The program page says applications are accepted year-round, applicants can expect more information within 4–6 weeks, and grantees are announced at the end of each quarter. Grant size is case by case. The form itself showed no deadline. Those process notes can change; re-read the form on the day you submit.
