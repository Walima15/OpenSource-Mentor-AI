"""Bitcoin protocol lessons. Teaching notes, not a specification."""

from __future__ import annotations

LESSONS: list[dict] = [
    {
        "id": "utxos",
        "path_id": "bitcoin-fundamentals",
        "title": "UTXOs",
        "order": 1,
        "summary": "Bitcoin tracks coins as unspent transaction outputs, not as account balances.",
        "concepts": ["utxo", "utxos", "unspent transaction output", "coin"],
        "keywords": ["utxo", "utxos", "unspent", "coin selection", "change output"],
        "sources": [
            {
                "title": "Bitcoin Developer Guide — Transactions",
                "url": "https://developer.bitcoin.org/devguide/transactions.html",
            }
        ],
        "body": """A Bitcoin full node does not store a balance for each address. It stores the **UTXO set**: every unspent transaction output. An output leaves that set once a later transaction spends it.

A transaction output is a record of value (an integer number of satoshis) plus a locking script (`scriptPubKey`) that says who may spend it. An output is identified by an **outpoint**: the transaction id that created it, and the output index (`vout`) inside that transaction.

Spending means naming that outpoint as an input and supplying an unlocking witness (a signature, a script, or both) that the locking script accepts. Once the spending transaction is confirmed under consensus rules, the old output leaves the UTXO set and the new outputs enter it. The same outpoint cannot be spent twice. That is the double-spend rule, enforced by every validating node, not by an account ledger.

The fee is not a separate field. It is the difference:

`fee = sum(input values) − sum(output values)`

Wallets hide this. They select UTXOs (coin selection), build outputs for the payment and usually a **change output** back to the wallet, and leave the remainder as the fee. If you forget change, the remainder is the fee. That mistake is real, and reviewers look for it in wallet code.

Why this matters for contributors:

- Wallet bugs are usually UTXO bugs: wrong outpoint, missing change, double-counting a coin, or treating an unconfirmed output as settled.
- "Balance" in a UI is a sum of spendable UTXOs, sometimes excluding immature coinbase outputs (100 confirmations) and locked coins.
- Bitcoin Core's chainstate, BDK's local chain, and Electrum-style wallets are all views of this same model. When you read those codebases, look for outpoints, not account rows.

A useful exercise: pick one of your own transactions on a block explorer and name each input's previous outpoint, each output's value and script type, and the implied fee.
""",
        "quiz": [
            {
                "prompt": "What does a Bitcoin transaction consume?",
                "choices": [
                    "A global account balance stored by miners",
                    "Specific unspent outputs identified by outpoint",
                    "The recipient's public key hash only",
                    "A mempool entry chosen by the sender",
                ],
                "answer": 1,
                "explanation": "Inputs spend existing UTXOs by outpoint (txid and vout). There is no global account balance in the protocol.",
            },
            {
                "prompt": "Where is the transaction fee stored?",
                "choices": [
                    "In a dedicated fee field on every output",
                    "It is implied: input value minus output value",
                    "In the block header",
                    "Only inside the Lightning commitment transaction",
                ],
                "answer": 1,
                "explanation": "The fee is the leftover value not assigned to an output. Forgetting a change output donates that leftover to miners.",
            },
            {
                "prompt": "A change output is:",
                "choices": [
                    "An output that pays the leftover value back to the sender's wallet",
                    "A rewrite of an earlier confirmed transaction",
                    "The miner subsidy",
                    "Required by consensus on every transaction",
                ],
                "answer": 0,
                "explanation": "Change is a wallet construction so the unspent remainder is not consumed as fee. Consensus does not require it.",
            },
        ],
    },
    {
        "id": "transactions",
        "path_id": "bitcoin-fundamentals",
        "title": "Transactions",
        "order": 2,
        "summary": "The structure of a Bitcoin transaction, txids, and witness data.",
        "concepts": ["transaction", "txid", "wtxid", "witness", "locktime", "sequence"],
        "keywords": ["transaction", "transactions", "txid", "wtxid", "locktime", "sequence", "psbt"],
        "sources": [
            {"title": "BIP 141 — Segregated Witness", "url": "https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki"},
            {"title": "BIP 174 — PSBT", "url": "https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki"},
        ],
        "body": """A Bitcoin transaction is a message that spends old outputs and creates new ones. The fields you will meet in every implementation:

- **version** — currently used with relative locktime rules (BIP 68).
- **inputs** — each one points at an outpoint, carries a `sequence` number, and (before segwit, or alongside it) a `scriptSig`.
- **outputs** — value plus `scriptPubKey`.
- **locktime** — a block height or timestamp before which the transaction is not valid, when an input sequence is not final.
- **witness** — segwit unlocking data, stored outside the legacy serialization.

Two hashes matter:

- **txid** hashes the transaction *without* the witness. Segwit was designed this way so a third party cannot malleate the id by tweaking the witness.
- **wtxid** commits to the witness as well. Blocks commit to txids via the merkle root. A witness commitment in the coinbase commits to the wtxids.

**Segwit** (BIP 141) fixed txid malleability, which unblocked Lightning: a channel needs transaction ids that stay put while signatures are being exchanged. It also introduced **block weight**. Witness bytes are counted less heavily than base bytes. Fees are usually discussed in satoshis per virtual byte (sat/vB).

**PSBT** (BIP 174, plus later BIPs) is how software wallets, hardware wallets, and multisig coordinators pass a transaction around before it is fully signed. BDK and Bitcoin Core both speak PSBT. If you are contributing to wallet code, learn PSBT before you invent a new unsigned-transaction format.

When you read a codebase, separate three layers that people mix up:

1. **Consensus serialization** — what is valid in a block.
2. **Policy / standardness** — what a node will relay and keep in its mempool.
3. **Wallet representation** — PSBT, descriptors, address books.

A review comment that says "this is invalid" should say which layer it means.
""",
        "quiz": [
            {
                "prompt": "Why does the txid exclude the witness?",
                "choices": [
                    "So miners can compress blocks",
                    "So changing the witness does not change the transaction id",
                    "Because witness data is not hashed by SHA-256",
                    "So locktime can be edited after broadcast",
                ],
                "answer": 1,
                "explanation": "Segwit puts the witness outside the txid hash. That stops third-party malleation of the id, which Lightning depends on.",
            },
            {
                "prompt": "A PSBT is mainly used to:",
                "choices": [
                    "Replace the peer-to-peer protocol",
                    "Coordinate signing of a transaction across wallets and devices",
                    "Store the UTXO set on disk",
                    "Announce a block header",
                ],
                "answer": 1,
                "explanation": "Partially Signed Bitcoin Transactions are the standard handoff format for unsigned or partly signed transactions.",
            },
        ],
    },
    {
        "id": "scripts",
        "path_id": "bitcoin-fundamentals",
        "title": "Scripts and addresses",
        "order": 3,
        "summary": "Locking scripts, common output types, and why Taproot exists.",
        "concepts": ["script", "scriptpubkey", "p2pkh", "p2sh", "p2wpkh", "p2wsh", "p2tr", "taproot", "miniscript", "descriptor"],
        "keywords": ["script", "scripts", "p2pkh", "p2sh", "p2wpkh", "p2wsh", "p2tr", "taproot", "schnorr", "miniscript", "descriptor", "address"],
        "sources": [
            {"title": "BIP 341 — Taproot", "url": "https://github.com/bitcoin/bips/blob/master/bip-0341.mediawiki"},
            {"title": "BIP 380 — Output Script Descriptors", "url": "https://github.com/bitcoin/bips/blob/master/bip-0380.mediawiki"},
        ],
        "body": """Bitcoin Script is a small stack language. It is not a general smart-contract platform. An output's `scriptPubKey` locks the coins. Spending pushes inputs onto the stack (via `scriptSig` and/or the witness) and the script must finish with a true result. The interpreter in Bitcoin Core lives around `src/script/interpreter.cpp`. rust-bitcoin and rust-miniscript implement the same rules in Rust.

Output types you should recognize on sight:

| Name | What is locked | Typical use |
| --- | --- | --- |
| P2PKH | A public-key hash | Legacy addresses starting with `1` |
| P2SH | A hash of a redeem script | Legacy multisig, addresses starting with `3` |
| P2WPKH | A witness public-key hash | Native segwit `bc1q` |
| P2WSH | A witness script hash | Native segwit multisig |
| P2TR | A Taproot output key | `bc1p`, key-path or script-path spend |

**Taproot** (BIPs 340, 341, 342) uses Schnorr signatures. A P2TR output can be spent with a single key-path signature, or by revealing a script path committed in a merkle tree of scripts. The common case looks like a single-key spend, which is good for privacy and for fees.

**Descriptors** (BIP 380 and friends) are a human-readable way to say "how this wallet derives output scripts." They replaced the habit of importing a bare xpub and hoping every wallet interpreted it the same way. Bitcoin Core and BDK both use them.

**Miniscript** is a structured subset of Script. Instead of hand-writing opcodes, you compose fragments (`pk`, `and_v`, `older`, `thresh`, …) that can be analyzed for spending cost, malleability, and whether a sane satisfaction exists. rust-miniscript and Bitcoin Core's miniscript compiler are the projects to read.

Consensus will reject a script that breaks the rules (disabled opcodes, unclean stack, failed signature, resource limits). Policy may reject additional shapes as non-standard even though a miner could include them. When you change script code, say which one you are touching, and add vectors. Do not "clean up" the interpreter.
""",
        "quiz": [
            {
                "prompt": "A P2TR output (`bc1p`) can be spent by:",
                "choices": [
                    "Only a legacy scriptSig",
                    "A key-path Schnorr signature, or a revealed script path",
                    "Any miner, without a signature",
                    "The mempool, automatically after 100 blocks",
                ],
                "answer": 1,
                "explanation": "Taproot commits to an internal key and an optional tree of scripts. The spend is either the key path or one script leaf.",
            },
            {
                "prompt": "Miniscript is useful because it:",
                "choices": [
                    "Lets you analyze and compose Script policies instead of raw opcodes",
                    "Removes the need for signatures",
                    "Is a replacement for the peer-to-peer network",
                    "Sets the block subsidy",
                ],
                "answer": 0,
                "explanation": "Miniscript is a structured Script fragment language with known properties (satisfaction, malleability, cost).",
            },
        ],
    },
    {
        "id": "blocks",
        "path_id": "bitcoin-fundamentals",
        "title": "Blocks and proof of work",
        "order": 4,
        "summary": "What a block commits to, and how difficulty retargets.",
        "concepts": ["block", "proof of work", "merkle root", "difficulty", "subsidy"],
        "keywords": ["block", "blocks", "merkle", "difficulty", "proof of work", "subsidy", "coinbase", "header"],
        "sources": [
            {"title": "Bitcoin Developer Guide — Block chain", "url": "https://developer.bitcoin.org/devguide/block_chain.html"}
        ],
        "body": """A block is a header plus a list of transactions. The header is what proof-of-work covers:

- version
- hash of the previous block header
- merkle root of the transaction ids
- time
- compact difficulty target (`nBits`)
- nonce

The block hash is the double SHA-256 of that 80-byte header. A valid header's hash, interpreted as an integer, must be below the target. Miners vary the nonce, the coinbase transaction (which changes the merkle root), and other fields until they find one.

The **merkle root** commits to the txids in order. A node that has the header can later ask peers for the transactions and check they hash to that root. Segwit adds a witness commitment inside the coinbase so the witnesses are committed too.

The first transaction is the **coinbase**. It may create new bitcoin up to the subsidy for that height, plus the fees of the block. The subsidy started at 50 BTC and halves every 210,000 blocks. Coinbase outputs are immature for 100 blocks. Changing the subsidy schedule is a consensus change with economic consequences. It is not a good first issue. It is a thing you discuss in public for a long time, and most such proposals should be expected to fail.

**Difficulty** retargets every 2016 blocks so that the average interval stays near ten minutes. Nodes do not trust a miner's clock blindly: there are median-time-past rules and future-time limits. If you touch time or difficulty code, read the existing tests before you invent a new formula.

Blocks are a chain because each header names its parent. A reorganization happens when a competing chain has more work. Nodes reorg by disconnecting blocks and connecting the new ones. Wallet code that assumes "one confirmation is forever" is wrong. Reviewers of wallet and Lightning code ask what happens on reorg.
""",
        "quiz": [
            {
                "prompt": "What does proof of work commit to?",
                "choices": [
                    "Only the coinbase subsidy",
                    "The block header, which includes the merkle root of transaction ids",
                    "Every peer's mempool",
                    "The miner's domain name",
                ],
                "answer": 1,
                "explanation": "The hash covers the header. The merkle root inside the header commits to the txids.",
            },
            {
                "prompt": "The block subsidy:",
                "choices": [
                    "Is chosen by each miner independently",
                    "Follows a consensus schedule and halves every 210,000 blocks",
                    "Is paid through Lightning invoices",
                    "Is reset whenever the mempool is empty",
                ],
                "answer": 1,
                "explanation": "The maximum new coins in a coinbase are determined by height. Fees are extra. This is consensus, not policy.",
            },
        ],
    },
    {
        "id": "consensus",
        "path_id": "bitcoin-fundamentals",
        "title": "Consensus rules",
        "order": 5,
        "summary": "What every full node enforces, and why soft forks are slow on purpose.",
        "concepts": ["consensus", "soft fork", "hard fork", "full node", "validation"],
        "keywords": ["consensus", "soft fork", "hard fork", "validation", "full node", "chain split"],
        "sources": [
            {"title": "Bitcoin Core contributing guide", "url": "https://github.com/bitcoin/bitcoin/blob/master/CONTRIBUTING.md"}
        ],
        "body": """**Consensus rules** are the checks a full node runs before it accepts a block or a transaction into its view of the chain. They include the subsidy, the 21 million cap, script validity, block weight limits, signature rules, coinbase maturity, and the structure of transactions. If two honest nodes disagree on these rules, they can follow different chains. That is a chain split. Money that is valid on one side may be invalid on the other.

Bitcoin Core is the implementation most nodes run, but it is not the definition of Bitcoin by job title. The rules are whatever the economic majority of validating nodes actually enforce. A pull request does not change consensus when it is merged. It changes consensus when people run it.

Two words you must not mix up:

- A **soft fork** tightens rules. Old nodes still see new blocks as valid, if the fork is designed that way. Taproot and segwit were soft forks. They still need wide review because a bug is a consensus bug.
- A **hard fork** loosens or replaces a rule that old nodes reject. It requires every validating participant to upgrade in coordination.

**Policy** is everything else a node does: what it relays, what it keeps in the mempool, how it chooses packages, which addresses it hands out. Two nodes can have different policies and still agree on the chain. Standardness, default minimum relay fees, and replace-by-fee policy are policy.

Contributor rules of thumb:

- Do not open a drive-by consensus pull request. Write a design note, post it where the project actually talks (for protocol changes, the bitcoin-dev mailing list), and expect years, not days.
- In review, if a patch changes `validation`, `script`, or consensus constants, say so in the first paragraph of your review.
- Tests for consensus behavior are not optional. A refactor that "should not change behavior" still needs a reason, and often a test that pins the old vectors.
- Never tell a new contributor to ACK a consensus change they cannot explain.

`src/consensus/` in Bitcoin Core is small. Most consensus logic is spread through validation and the script interpreter. Do not assume a folder name is the whole rule set.
""",
        "quiz": [
            {
                "prompt": "Which statement is true?",
                "choices": [
                    "Mempool policy and consensus are the same thing",
                    "Consensus is what nodes must agree on to stay on one chain; policy is local relay and mining preference",
                    "A merged pull request immediately changes the network's consensus rules",
                    "Only miners validate scripts",
                ],
                "answer": 1,
                "explanation": "Full nodes enforce consensus independently. Policy can differ without splitting the chain. Merging code does not activate a rule by itself.",
            },
            {
                "prompt": "A soft fork is best described as:",
                "choices": [
                    "A tightening of rules that old nodes can still accept if it is constructed carefully",
                    "Any change to a wallet label",
                    "Deleting the mempool",
                    "A hard cutover where old nodes reject new blocks on purpose",
                ],
                "answer": 0,
                "explanation": "Soft forks restrict the set of valid blocks. They are still consensus changes and need careful review.",
            },
        ],
    },
    {
        "id": "p2p",
        "path_id": "bitcoin-fundamentals",
        "title": "The peer-to-peer network",
        "order": 6,
        "summary": "How nodes find each other and trade blocks and transactions.",
        "concepts": ["p2p", "peer-to-peer", "inv", "compact block", "addr"],
        "keywords": ["p2p", "peer", "peers", "inv", "getdata", "compact block", "addr", "gossip", "network"],
        "sources": [
            {"title": "BIP 152 — Compact Block Relay", "url": "https://github.com/bitcoin/bips/blob/master/bip-0152.mediawiki"}
        ],
        "body": """Bitcoin nodes talk a custom binary protocol over TCP. Peers are untrusted. Your node checks everything they send against consensus and policy. A peer can omit transactions, send junk, or lie about its peers. That is normal. Validation is local.

The handshake starts with `version` and `verack`. After that, the messages you will see in code and logs:

- `addr` / `addrv2` — gossip of peer addresses.
- `inv` — "I have these txids or block hashes."
- `getdata` — "Send me those."
- `tx` and `block` — the objects themselves.
- `ping` / `pong` — liveness.
- compact blocks (BIP 152) — a short block sketch so the receiver can rebuild the block from its mempool instead of downloading every transaction again.

In Bitcoin Core, connection management is mostly `src/net.cpp` and message handling is mostly `src/net_processing.cpp`. Those files are large because the protocol is stateful: each peer has a sync state, an inventory filter, and rate limits. A good first read is one message type, not the whole file.

Design habits that show up in review:

- Do not trust a peer's claim about fee, confirmations, or "this transaction is standard." Check it.
- Peer punishment (discouragement, disconnect) should match the offense. Over-punishing honest peers is a real bug.
- Extra round trips and extra allocations in the hot path get scrutiny. So do changes that make eclipse-style partitioning easier. You do not need to design an attack to review this code. You do need to ask "what if this peer is lying?"
- Protocol changes that are not backward compatible need a design discussion before a patch. Many changes ship as new messages negotiated in `version`, or via service bits.

Other projects speak related protocols. Lightning implementations speak BOLT peer messages on top of their own transports. Do not assume a Bitcoin `inv` and a Lightning `channel_announcement` are the same layer.
""",
        "quiz": [
            {
                "prompt": "Why does a node re-validate data from peers?",
                "choices": [
                    "Peers are trusted miners",
                    "Peers are untrusted and can lie or omit data",
                    "The mempool is consensus",
                    "Validation only happens on the miner who found the block",
                ],
                "answer": 1,
                "explanation": "The protocol assumes peers are hostile or broken. Local consensus checks are the source of truth.",
            },
            {
                "prompt": "Compact blocks (BIP 152) exist to:",
                "choices": [
                    "Raise the block subsidy",
                    "Send a short sketch so a node can rebuild a block from transactions it already has",
                    "Replace script verification",
                    "Remove the need for a merkle root",
                ],
                "answer": 1,
                "explanation": "Most transactions in a new block are already in the receiver's mempool, so the peer sends a compact encoding instead of the full block.",
            },
        ],
    },
    {
        "id": "mempool",
        "path_id": "bitcoin-fundamentals",
        "title": "Mempool and policy",
        "order": 7,
        "summary": "Unconfirmed transactions, fees, RBF, and why mempools disagree.",
        "concepts": ["mempool", "policy", "rbf", "fee", "package relay"],
        "keywords": ["mempool", "policy", "rbf", "replace-by-fee", "fee", "fees", "sat/vb", "cpfp", "package", "standardness", "dust"],
        "sources": [
            {"title": "BIP 125 — Opt-in Replace-by-Fee", "url": "https://github.com/bitcoin/bips/blob/master/bip-0125.mediawiki"}
        ],
        "body": """The **mempool** is one node's set of valid, unconfirmed transactions it is willing to relay or mine. It is not a global object. Your mempool and a miner's mempool can differ, and both can be "correct."

Before a transaction enters the mempool it must pass consensus checks (it could legally appear in a block) and policy checks. Policy includes:

- **standardness** — script forms the node is willing to relay, not the full set miners could accept.
- **dust** — outputs so small they cost more to spend than they are worth, which nodes refuse by default.
- **minimum relay fee** and the dynamic mempool fee floor — when the mempool is full, cheap transactions are evicted.
- **ancestor and descendant limits** — caps on unconfirmed chains of transactions, so one wallet cannot fill the mempool with a huge dependency graph.
- **replace-by-fee (RBF)** — BIP 125 opt-in replacement: a later transaction that spends the same inputs can replace an earlier one if it signals replacement and pays enough new fee.
- **child-pays-for-parent (CPFP)** — a child transaction with a high fee can make miners want the low-fee parent. Package relay is the ongoing work to evaluate such groups fairly.

Fees are usually measured in **sat/vB** (satoshis per virtual byte). Virtual size comes from segwit weight: `weight / 4`. Wallet fee estimation looks at recent blocks and the local mempool. It is a guess. Reviewers of fee code ask what happens when the guess is low, when a transaction is pinned by a descendant, and when a replacement is rejected.

Contributor notes:

- A policy change can have real effects on Lightning and on wallets even though it is not consensus. Treat it as a design change. Bitcoin Core expects discussion for policy changes.
- Do not write tests that assume every node has the same mempool.
- In Bitcoin Core, start with `src/policy/` and `src/txmempool.cpp`, then the functional tests under `test/functional` that cover `mempool_*` and `rpc_packages`.
- If your patch "just" changes relay, say so. Reviewers will ask whether it creates a pinning vector or a censorship footgun. Answer that in the pull request body.
""",
        "quiz": [
            {
                "prompt": "Two honest nodes can have different mempools because:",
                "choices": [
                    "The mempool is a consensus rule and one of them is on a fork",
                    "Mempool contents are local policy, not a single global set",
                    "UTXOs are optional",
                    "Only miners are allowed to store transactions",
                ],
                "answer": 1,
                "explanation": "Policy and propagation timing differ. Agreement is required on confirmed blocks, not on the set of unconfirmed transactions.",
            },
            {
                "prompt": "Opt-in RBF allows:",
                "choices": [
                    "A replacement transaction that spends the same inputs and pays a sufficient fee",
                    "Editing a confirmed block",
                    "Spending the same output twice inside one block",
                    "Removing the need for a signature",
                ],
                "answer": 0,
                "explanation": "BIP 125 replacement is a policy rule for unconfirmed transactions that signaled replaceability. It does not rewrite confirmed history.",
            },
        ],
    },
    {
        "id": "bips",
        "path_id": "bitcoin-fundamentals",
        "title": "BIPs and how Bitcoin changes",
        "order": 8,
        "summary": "What a BIP is for, and what it does not do by itself.",
        "concepts": ["bip", "bips", "bitcoin improvement proposal", "specification"],
        "keywords": ["bip", "bips", "improvement proposal", "bitcoin-dev", "specification", "spec"],
        "sources": [
            {"title": "BIP 2 — BIP process", "url": "https://github.com/bitcoin/bips/blob/master/bip-0002.mediawiki"},
            {"title": "Bitcoin BIPs repository", "url": "https://github.com/bitcoin/bips"},
        ],
        "body": """A **Bitcoin Improvement Proposal** is a document. It is not a software release and it is not a vote that binds miners or nodes. BIP 2 describes the process. Proposals are discussed, numbered, and given a status (draft, proposed, final, rejected, and so on).

BIPs come in flavors:

- **Standards track** — changes that want interoperability, such as a new script version or a new address format.
- **Informational** — descriptions and design notes.
- **Process** — changes to the process itself.

The path that actually changes the network is longer than the document:

1. Someone writes a clear problem statement. Often this starts on the **bitcoin-dev** mailing list, not as a pull request full of code.
2. People try to break the idea: incentive problems, upgrade pain, implementation cost, simpler alternatives.
3. A BIP number gets assigned once the idea is concrete enough to talk about precisely.
4. Implementations experiment. For consensus changes, that experiment is conservative and heavily reviewed.
5. Users run the code. Activation, if any, follows the mechanism in the BIP (flag day, miner signaling, or something else). None of this is automatic because a document was merged.

For a new contributor, BIPs are the reading list. When a review comment says "this violates BIP 341," open the BIP and quote the section. Do not paraphrase from memory if the text is short enough to check.

Good habits:

- Search closed BIPs and old mailing-list threads before proposing a new opcode or a new policy.
- A documentation typo in the BIPs repo is a real contribution. So is a missing test vector that the BIP already specifies.
- Do not open a Bitcoin Core pull request that "implements a BIP" you drafted last week. The BIP is the proposal. The implementation follows review, and many BIPs should not be implemented.
- Process proposals and consensus proposals have different audiences. A wallet descriptor BIP and a block-subsidy BIP are not reviewed the same way.

The Lightning equivalent of this culture is the **BOLT** specifications in `lightning/bolts`, discussed on the lightning-dev list. Same lesson: the spec is a document, the implementations (LDK, LND, Core Lightning, Eclair, and others) are where it becomes software, and they are allowed to lag or disagree until a feature is actually interoperable.
""",
        "quiz": [
            {
                "prompt": "Merging a BIP means:",
                "choices": [
                    "The network has activated a new consensus rule",
                    "A design document was accepted into the BIP repository, not that nodes enforce it",
                    "Miners must upgrade within one retarget period",
                    "Bitcoin Core will reject blocks that ignore it the next day",
                ],
                "answer": 1,
                "explanation": "A BIP is a specification document. Activation still depends on implementation, review, and what nodes actually run.",
            },
            {
                "prompt": "Where do Bitcoin protocol ideas usually get discussed before code?",
                "choices": [
                    "Only in a private chat with one maintainer",
                    "On the bitcoin-dev mailing list and in the relevant project forums",
                    "By force-pushing to master",
                    "Inside the mempool",
                ],
                "answer": 1,
                "explanation": "Protocol changes are public design discussions. A surprise pull request is a bad way to start one.",
            },
        ],
    },
]
