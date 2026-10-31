"""How Bitcoin open-source projects expect contributors to behave."""

from __future__ import annotations

LESSONS: list[dict] = [
    {
        "id": "project-maps",
        "path_id": "contribution-craft",
        "title": "How the projects are organized",
        "order": 1,
        "summary": "A map of the Bitcoin open-source landscape OSMA cares about.",
        "concepts": ["bitcoin core", "bdk", "project map", "repository"],
        "keywords": ["organized", "organization", "which project", "project map", "landscape", "where to contribute"],
        "sources": [
            {"title": "Bitcoin Core", "url": "https://github.com/bitcoin/bitcoin"},
            {"title": "Bitcoin Dev Kit", "url": "https://github.com/bitcoindevkit/bdk"},
        ],
        "body": """"Bitcoin open source" is a collection of projects with different jobs. Picking the right one is the first contribution skill.

**The node.** [Bitcoin Core](https://github.com/bitcoin/bitcoin) is the full-node implementation most of the network runs. Consensus, peer-to-peer networking, the mempool, the wallet, and the RPC server live here. Changes are reviewed in public on GitHub, with a culture closer to a long-running engineering mailing list than to a typical app repo. [libsecp256k1](https://github.com/bitcoin-core/secp256k1) is the signature library it depends on. Treat cryptographic changes there as specialist work.

**Libraries for building software.** [rust-bitcoin](https://github.com/rust-bitcoin/rust-bitcoin) is the Rust crate for primitives (transactions, blocks, addresses, consensus encoding). [rust-miniscript](https://github.com/rust-bitcoin/rust-miniscript) builds policies on top. [BDK](https://github.com/bitcoindevkit/bdk) is a wallet library: descriptors, chain sources, coin selection, PSBT. If you want to build a wallet, start with BDK and rust-bitcoin, not by forking Bitcoin Core's wallet.

**Lightning.** The spec is [lightning/bolts](https://github.com/lightning/bolts). [LDK](https://github.com/lightningdevkit/rust-lightning) is the Rust library. [LND](https://github.com/lightningnetwork/lnd) and [Core Lightning](https://github.com/ElementsProject/lightning) are daemons operators run. Interoperability is the point.

**Applications.** [BTCPay Server](https://github.com/btcpayserver/btcpayserver) is a payment processor. It is often a better first code contribution than consensus code: the domain is payments, the stack is .NET, and issues are more likely to be user-facing.

How to choose:

- Want to learn the protocol by reading? Pick one subsystem in Bitcoin Core or one crate in rust-bitcoin and read tests.
- Want a merged pull request that helps users soon? Look at BDK, BTCPay, docs, and tests in the library repos.
- Want to review rather than author? Bitcoin Core's review club and "good first review" culture exist because review is the bottleneck.

OSMA's project guides list build steps and the files to open first. The upstream `README` and `CONTRIBUTING` still win when they disagree with a guide.
""",
        "quiz": [
            {
                "prompt": "BDK is best described as:",
                "choices": [
                    "A replacement consensus implementation",
                    "A wallet library for descriptors, chain state, and PSBTs",
                    "The Lightning specification",
                    "A mining pool",
                ],
                "answer": 1,
                "explanation": "BDK helps applications build and sign wallet transactions. It is not a full node and it does not define consensus.",
            },
            {
                "prompt": "libsecp256k1 changes should be treated as:",
                "choices": [
                    "Beginner-friendly typo fixes in the elliptic-curve implementation",
                    "Specialist cryptographic work with a high review bar",
                    "Lightning invoice formatting",
                    "Mempool eviction policy",
                ],
                "answer": 1,
                "explanation": "The library is consensus-critical cryptography. New contributors should read and test, not rewrite formulas.",
            },
        ],
    },
    {
        "id": "reading-a-codebase",
        "path_id": "contribution-craft",
        "title": "Reading a Bitcoin codebase",
        "order": 2,
        "summary": "A way to learn a repository without reading it from the first file to the last.",
        "concepts": ["code reading", "tests", "git blame", "subsystem"],
        "keywords": ["read the code", "codebase", "understand the repo", "where do I start", "git blame", "subsystem"],
        "sources": [
            {
                "title": "Bitcoin Core developer notes",
                "url": "https://github.com/bitcoin/bitcoin/blob/master/doc/developer-notes.md",
            }
        ],
        "body": """Large Bitcoin projects are not learned by scrolling. Learn them by following one behavior.

1. **Read the contract, not the lore.** Start with `README`, `CONTRIBUTING`, and the doc index. Note the build command and the test command. If you cannot build, you are not ready to change behavior.
2. **Pick one user-visible behavior.** An RPC, a CLI flag, a wallet method, a BOLT message, a single functional test. Search for the string a user would see.
3. **Read the test first.** Tests name the cases the authors were afraid of. In Bitcoin Core, `test/functional` is Python and talks to a regtest node. Unit tests sit next to the C++ they cover. In Rust projects, `cargo test` and the `tests/` directory are the map.
4. **Follow the call one level at a time.** Write down the function, the file, and the question it answers. Stop when you can explain the path out loud.
5. **Use history.** `git log -p -- path` and `git blame` show why a weird line exists. In these projects the weird line is often a consensus bugfix. Do not delete it because it looks untidy.
6. **Separate the layers.** Consensus, policy, wallet, RPC, and tests have different review bars. A drive-by refactor that crosses all of them will stall.

Bitcoin Core orientation, knowing that files move:

- `src/net.cpp`, `src/net_processing.cpp` — peers and messages
- `src/txmempool.cpp`, `src/policy/` — mempool policy
- `src/validation.cpp` — connecting blocks and transactions
- `src/script/interpreter.cpp` — script rules
- `src/wallet/` — wallet, which is not consensus
- `src/rpc/` — the RPC surface
- `test/functional/` — end-to-end tests on regtest

Ask the mentor to explain a file by owner, repo, and path. Then explain it back in your own words before you propose a patch. If you cannot explain it, you cannot defend it in review.
""",
        "quiz": [
            {
                "prompt": "A practical way to start reading Bitcoin Core is to:",
                "choices": [
                    "Rewrite `validation.cpp` from scratch",
                    "Follow one RPC or one functional test through the code it calls",
                    "Memorize every file in `src/` in alphabetical order",
                    "Ignore tests until the patch is written",
                ],
                "answer": 1,
                "explanation": "One behavior, starting from the test or the RPC, keeps the reading bounded and checkable.",
            },
            {
                "prompt": "Before deleting a surprising line, you should:",
                "choices": [
                    "Assume it is dead code",
                    "Read `git blame` and `git log -p` for that line",
                    "Open a pull request titled `cleanup`",
                    "Disable the unit test that mentions it",
                ],
                "answer": 1,
                "explanation": "Strange code in consensus and wallet paths is often a pinned bugfix. History says why it is there.",
            },
        ],
    },
    {
        "id": "review-culture",
        "path_id": "contribution-craft",
        "title": "Review culture, ACK, and NACK",
        "order": 3,
        "summary": "What Bitcoin Core reviewers mean, and why review is the real contribution.",
        "concepts": ["ack", "nack", "concept ack", "approach ack", "utack", "review"],
        "keywords": ["ack", "acks", "nack", "nacks", "utack", "concept ack", "approach ack", "nit", "review culture", "review club"],
        "sources": [
            {
                "title": "Bitcoin Core CONTRIBUTING.md",
                "url": "https://github.com/bitcoin/bitcoin/blob/master/CONTRIBUTING.md",
            },
            {"title": "Bitcoin Core PR Review Club", "url": "https://bitcoincore.reviews"},
        ],
        "body": """Bitcoin Core review uses a small vocabulary. Other Bitcoin projects borrowed pieces of it. Using the words precisely is part of being taken seriously.

- **Concept ACK** — you agree the problem is real and the project should solve it. You are not saying the patch is correct.
- **Approach ACK** — you agree with the design. You may still want code changes.
- **ACK** plus a commit id — you reviewed the code at that commit and you believe it is correct and is a good change. Say what you did: read the diff, built it, ran a test.
- **utACK** — untested ACK. You read the code and did not run it. Do not hide that.
- **NACK** — you disagree. A NACK without a reason is noise. A reason can be a concrete bug, a worse design than an alternative, or a claim that the change should not happen at all.
- **nit** — a non-blocking comment. Do not pretend a nit is a NACK, and do not ignore a real bug by calling it a nit.

Rules that keep the culture honest:

- Do not ACK code you did not review. An ACK moves maintainers toward merge. False ACKs waste the scarce thing, which is attention.
- Review comments should be specific: file, behavior, and what you expected instead.
- Disagree with the change, not with the person. Bitcoin projects are blunt about code and still expect you to be fair.
- Re-review after the author pushes. An ACK of an old commit does not cover a force-push. Say which commit you reviewed.
- **Review is a contribution.** Bitcoin Core's review club (`bitcoincore.reviews`) exists because the merge bottleneck is review, not ideas. A careful review on someone else's pull request teaches you the codebase faster than a drive-by patch.

Library projects (rust-bitcoin, BDK, LDK) use GitHub review more like other Rust projects, but you will still see Concept ACK. LND and Core Lightning expect tests and a reviewer who ran them. The principle travels even when the acronym does not: say what you checked.

OSMA will help you write a review. It will not ACK a pull request for you.
""",
        "quiz": [
            {
                "prompt": "Concept ACK means:",
                "choices": [
                    "The code is correct and ready to merge",
                    "You agree with the goal of the change, not that the patch is right",
                    "You tested on mainnet",
                    "You are a maintainer",
                ],
                "answer": 1,
                "explanation": "Concept ACK is about the idea. Code review is a separate step, usually written as ACK plus a commit.",
            },
            {
                "prompt": "utACK means:",
                "choices": [
                    "You reject the change",
                    "You read the change and did not test it",
                    "The pull request is merged",
                    "The patch changes consensus",
                ],
                "answer": 1,
                "explanation": "utACK is an untested acknowledgement. Hiding that you did not run the tests is worse than saying so.",
            },
        ],
    },
    {
        "id": "testing-and-commits",
        "path_id": "contribution-craft",
        "title": "Testing and signed commits",
        "order": 4,
        "summary": "What to run, how to write a commit, and why signing matters here.",
        "concepts": ["testing", "signed commit", "commit message", "regtest"],
        "keywords": ["test", "tests", "testing", "signed commit", "gpg", "ssh signing", "commit message", "regtest", "sign-off"],
        "sources": [
            {
                "title": "Bitcoin Core developer notes",
                "url": "https://github.com/bitcoin/bitcoin/blob/master/doc/developer-notes.md",
            }
        ],
        "body": """These projects secure money. "It compiles" is not a test plan.

**Bitcoin Core.** Unit tests are C++ and run through the build (`ctest` or the test binary). Functional tests are Python under `test/functional` and spin up regtest nodes. Regtest is a local network with relaxed difficulty so tests can mine blocks instantly. If you change node behavior, a functional test that fails before your fix and passes after it is the usual bar. Run the tests you touched, not a random subset you hope is related.

**Rust projects** (rust-bitcoin, BDK, LDK, rust-miniscript). `cargo test` is the start. Also run `cargo fmt --check` and clippy if the project enables it. Feature flags matter. A test that passes only on the default features can hide a broken `no-std` or `serde` path. Read the CI config and run the same commands locally.

**LND** uses `make check` and Go tests, plus integration tests for protocol behavior. **Core Lightning** uses `make check`. **BTCPay** uses `dotnet test`. The project guide in OSMA names the command. The CI file is the source of truth when they differ.

Commit messages:

- Subject line says the area and the why, not a novel. Bitcoin Core prefixes the subsystem: `wallet:`, `rpc:`, `net:`, `test:`, `doc:`.
- The body explains the motivation, the approach, and the testing. Link the issue.
- One logical change per commit when you can. Reviewers use `git range-diff` after a rebase. A fixup that quietly changes behavior is hostile.
- Do not mix a drive-by reformat into a bugfix. It makes the diff unreadable.

**Signed commits.** Bitcoin Core and several related projects expect contributors who can sign their work, especially anyone touching security-sensitive code. You can sign with GPG or with an SSH key (`git commit -S`, and `commit.gpgsign` if you want it every time). Signing does not prove the code is correct. It makes the history attributable, which matters when a bad patch has to be understood later. Do not paste a private key into a chat, including this one, to "set up signing." Generate the key on your machine and follow the project's own notes.

If a maintainer asks you to squash and sign, do that as a separate push and say so. Do not sign a commit you do not understand.
""",
        "quiz": [
            {
                "prompt": "A regtest functional test is useful because it:",
                "choices": [
                    "Spends real bitcoin on mainnet",
                    "Runs a local node with easy mining so you can exercise behavior end to end",
                    "Replaces code review",
                    "Signs your commits automatically",
                ],
                "answer": 1,
                "explanation": "Regtest is a private network for tests. Functional tests talk to a real binary and check behavior, not just a single function.",
            },
            {
                "prompt": "A signed commit primarily gives reviewers:",
                "choices": [
                    "Proof that the consensus change is desirable",
                    "Attribution: the commit was signed by a key the contributor controls",
                    "A higher block subsidy",
                    "An automatic ACK",
                ],
                "answer": 1,
                "explanation": "Signatures bind history to a key. They are not a substitute for tests or review.",
            },
        ],
    },
    {
        "id": "pr-etiquette",
        "path_id": "contribution-craft",
        "title": "Pull request etiquette",
        "order": 5,
        "summary": "How to open a change that reviewers can actually review.",
        "concepts": ["pull request", "pr etiquette", "rebase", "ci"],
        "keywords": ["pull request", "etiquette", "rebase", "force-push", "ci", "draft", "pr body", "description"],
        "sources": [
            {
                "title": "Bitcoin Core contributing guide",
                "url": "https://github.com/bitcoin/bitcoin/blob/master/CONTRIBUTING.md",
            }
        ],
        "body": """A pull request is a request for someone's time. Write it that way.

**Before you open it**

- Search issues and pull requests. Duplicate work is the most common wasted week.
- For anything that changes consensus, policy, the wire protocol, or a public API, talk first. A draft pull request can be the conversation, if the title says `draft` and the body asks a question instead of demanding a merge.
- Keep the change small. A bugfix plus a rename plus a new feature is three reviews pretending to be one.

**The description**

- What is wrong or missing, in one paragraph a reviewer can check.
- What you changed, at the level of behavior.
- How you tested it, with the exact command.
- What you did not do. Reviewers relax when the boundary is explicit.
- User-facing changes need a release note if the project uses them.

**During review**

- Answer every comment. If you disagree, say why. Silence reads as stalled.
- Bitcoin Core prefers a rebase onto master and no merge commits. Other projects say so in their docs. Do not mix merge commits into a rebase-based history.
- Force-pushing is normal after review. Say what changed. Do not force-push over a conversation without a note, and do not force-push to erase a reviewer's inline comment without addressing it.
- If CI fails, read the log. Do not ask reviewers to ignore a red build.
- If you realize the approach is wrong, close the pull request and say what you learned. That is a success.

**What not to do**

- Do not open pull requests you cannot explain. If a tool wrote the patch, you still have to defend every line. Reviewers can tell when you cannot.
- Do not ping maintainers the same day because nobody has replied. These projects have long queues. A week of silence is normal. A polite bump after the project's stated window is fine.
- Do not expand the pull request with "while I was here" refactors.
- Do not argue a NACK into an ACK by repetition. Address the reason or take the idea back to design.

OSMA can plan the change and review the diff with you. You open the pull request, you sign the commits, and you show up for the comments.
""",
        "quiz": [
            {
                "prompt": "A good pull request description includes:",
                "choices": [
                    "Only the sentence `fixed it`",
                    "The motivation, the behavior change, and how you tested it",
                    "A request for an immediate ACK",
                    "Every file in the repository, listed",
                ],
                "answer": 1,
                "explanation": "Reviewers need the why, the what, and the test command. They should not have to reconstruct your intent from the diff.",
            },
            {
                "prompt": "After you rebase and force-push, you should:",
                "choices": [
                    "Assume old ACKs still apply",
                    "Comment on what changed so reviewers know what to re-read",
                    "Close the pull request immediately",
                    "Disable CI",
                ],
                "answer": 1,
                "explanation": "An ACK is tied to a commit. A new push needs a note, and reviewers re-check the new range.",
            },
        ],
    },
    {
        "id": "where-to-talk",
        "path_id": "contribution-craft",
        "title": "Mailing lists and IRC",
        "order": 6,
        "summary": "Where Bitcoin developers actually talk, and how not to show up.",
        "concepts": ["mailing list", "irc", "bitcoin-dev", "libera"],
        "keywords": ["mailing list", "irc", "libera", "bitcoin-dev", "lightning-dev", "#bitcoin-core-dev", "forum"],
        "sources": [
            {"title": "Bitcoin Core IRC channels", "url": "https://github.com/bitcoin/bitcoin/blob/master/CONTRIBUTING.md"},
            {"title": "Libera.Chat", "url": "https://libera.chat"},
        ],
        "body": """GitHub is not the only room. Bitcoin still uses mailing lists and IRC because the design conversations are older than a single pull request and need a stable archive.

**Mailing lists**

- **bitcoin-dev** is where protocol and consensus ideas are discussed. Do not post a drive-by implementation request there. Do post a design problem, a BIP draft, or a question that needs the people who have argued about this for years.
- **lightning-dev** is the same idea for Lightning and the BOLTs.
- Read the archives before you post. The question has often been answered, sometimes painfully.
- Write like a letter: context, question, what you already tried. Plain text. No screenshots of an IDE as the entire argument.

**IRC on Libera.Chat**

- `#bitcoin-core-dev` and `#bitcoin-core-pr-reviews` are working channels for Bitcoin Core. `#bitcoin` is broader. Lightning work often sits in `#lightning-dev` and project channels.
- Lurk first. Read the topic. Do not ask "can I ask a question."
- Paste logs and diffs on a paste site, not as a hundred lines into the channel.
- The people there are not a help desk. A specific question ("the functional test `wallet_basic.py` fails on this assertion, here is the commit") gets a better answer than "how do I bitcoin."
- Conversations are public and logged by third parties. Do not put keys, exploits, or private user data in the channel.

**Review club and project calls**

Bitcoin Core PR Review Club picks a pull request and walks through it on a schedule. Showing up prepared, having read the patch, is one of the best ways to become useful. Other projects have office hours or weekly calls listed in their docs. Use those instead of private messages to maintainers.

If you are unsure where a question belongs: a code defect in one repo goes to that repo's issue tracker. A protocol idea goes to the mailing list. A "how do I build this" question goes to the docs first, then the project channel.
""",
        "quiz": [
            {
                "prompt": "bitcoin-dev is the right place for:",
                "choices": [
                    "A private key you want checked",
                    "A protocol design discussion or BIP draft",
                    "Demanding a same-day review of an untested patch",
                    "Mempool contents from your node, pasted in full",
                ],
                "answer": 1,
                "explanation": "The list is for design. Implementation nits belong on the pull request. Secrets belong nowhere public.",
            },
            {
                "prompt": "Good IRC etiquette in `#bitcoin-core-dev` includes:",
                "choices": [
                    "Lurking, reading the topic, and asking a specific question",
                    "Pasting your seed phrase so someone can debug a wallet",
                    "Pinging maintainers until they answer",
                    "Asking the channel to write your patch",
                ],
                "answer": 0,
                "explanation": "The channel is a workplace. Specific questions are welcome. Secrets and demands are not.",
            },
        ],
    },
    {
        "id": "planning-a-change",
        "path_id": "contribution-craft",
        "title": "Planning a change",
        "order": 7,
        "summary": "From an issue to a patch you can defend, without skipping the design.",
        "concepts": ["contribution plan", "issue", "scope", "reproduction"],
        "keywords": ["plan", "planning", "approach this issue", "how should i contribute", "scope", "reproduction"],
        "sources": [
            {
                "title": "Bitcoin Core contributing guide",
                "url": "https://github.com/bitcoin/bitcoin/blob/master/CONTRIBUTING.md",
            }
        ],
        "body": """A contribution plan is a short document you could paste into a pull request. Write it before you write a lot of code.

1. **Restate the issue in your own words.** If you cannot, you do not understand it yet. Quote the issue, then say what behavior should change and what must not change.
2. **Reproduce it.** A bug without a failing test is a rumor. For a feature, name the smallest demonstration (a test, a regtest command, a unit test).
3. **Find the code.** Three to seven files, not the whole repo. Mark which layer they are: consensus, policy, wallet, RPC, tests, docs.
4. **Choose the smallest design.** Write the alternative you rejected and why. Reviewers trust a plan that shows a choice.
5. **Name the tests** you will add or extend, and the command to run them.
6. **Name the review risks.** Consensus? Wire compatibility? Wallet funds? Fee pinning? API stability? If any of those are yes, stop and ask on the issue, the mailing list, or IRC before you invest in the patch.
7. **Commit shape.** One commit or a short stack. Subject lines. Whether you will sign them.
8. **What you will not do.** Out of scope refactors, drive-by cleanups, unrelated issues you noticed.

Then implement. If the plan breaks when you see the code, update the plan. The pull request body is the plan, edited to match what you actually did, plus the test output you actually got.

OSMA's planning tool fetches the issue and the project's guide and drafts this outline. You still have to check the code and decide. Do not open the pull request until you can explain the diff without reading it line by line.
""",
        "quiz": [
            {
                "prompt": "The first step in a contribution plan is to:",
                "choices": [
                    "Open a pull request so the issue is reserved",
                    "Restate the problem and reproduce it, or name the demonstration you will add",
                    "Rewrite the subsystem",
                    "Request an ACK from a maintainer",
                ],
                "answer": 1,
                "explanation": "Understanding and reproduction come before code. A pull request is the end of the plan, not the start.",
            },
            {
                "prompt": "If the change touches consensus or the wire protocol, you should:",
                "choices": [
                    "Ship it as a surprise pull request for speed",
                    "Discuss the design in public before investing in a large patch",
                    "Hide the behavior change in a refactor commit",
                    "Skip tests so the diff stays small",
                ],
                "answer": 1,
                "explanation": "High-impact changes are design conversations first. A patch is how you implement an agreed approach.",
            },
        ],
    },
    {
        "id": "reviewing-a-pr",
        "path_id": "contribution-craft",
        "title": "Reviewing a pull request",
        "order": 8,
        "summary": "A repeatable way to review Bitcoin project diffs.",
        "concepts": ["code review", "diff", "checklist"],
        "keywords": ["review a pr", "review this", "code review", "diff review", "how to review"],
        "sources": [
            {"title": "Bitcoin Core PR Review Club", "url": "https://bitcoincore.reviews"}
        ],
        "body": """Review is a skill you can practice on other people's pull requests before you have a large one of your own.

A review pass that works in these projects:

1. **Read the motivation** in the pull request body and the linked issue. Decide concept first. If you disagree with the goal, say Concept NACK or "I do not understand the goal" and stop. Do not line-edit a change you think should not exist.
2. **Read the test changes before the production code.** The tests tell you what the author thinks the behavior is. Missing tests are a review comment.
3. **Read the diff once for structure.** Is it one change? Are there unrelated edits? Is the commit message accurate?
4. **Read it again for the layer it touches.** Consensus and script: assume you are wrong and check the spec. Mempool policy: ask who gets relayed and who gets pinned. Wallet: ask about change, fees, and reorgs. RPC: ask about help text, errors, and compatibility. Lightning: ask which BOLT section, which commitment, and what the peer does if you are weird.
5. **Run the tests** if you can. If you cannot, say so. utACK is allowed. Pretending is not.
6. **Write the review** as comments a stranger can act on. Quote the behavior. Suggest the alternative. Mark nits as nits.
7. **Leave a summary.** Concept ACK, Approach ACK, ACK with the commit you reviewed, or NACK with the reason. OSMA will not choose one of these for you.

Things that should slow you down:

- A silent behavior change in a refactor.
- New integer conversions around amounts (satoshis vs BTC, weight vs vsize).
- Error paths that swallow a failed signature or a failed peer read.
- Tests that mock away the function they claim to test.
- A pull request the author cannot explain. You may still review it. You should not ACK it out of politeness.

Good first reviews in Bitcoin Core are often documentation, tests, and RPC changes. In Rust projects they are API docs, edge-case tests, and fuzz targets. Start there. Leave the subsidy schedule alone.
""",
        "quiz": [
            {
                "prompt": "When reviewing, you should read tests early because:",
                "choices": [
                    "Tests are shorter and can be skipped after a glance",
                    "They state the behavior the author believes they changed",
                    "CI ignores production code",
                    "Maintainers only read tests",
                ],
                "answer": 1,
                "explanation": "The test diff is the author's claim about behavior. Review it against the code, and notice claims that have no test.",
            },
            {
                "prompt": "OSMA's rule about ACK is:",
                "choices": [
                    "The mentor ACKs once the diff looks short",
                    "Only a human who reviewed that commit should ACK it",
                    "ACK and Concept ACK are interchangeable",
                    "A NACK does not need a reason",
                ],
                "answer": 1,
                "explanation": "ACK is a claim that a person reviewed a specific commit. The mentor can coach the review. It does not stand in for the reviewer.",
            },
        ],
    },
]
