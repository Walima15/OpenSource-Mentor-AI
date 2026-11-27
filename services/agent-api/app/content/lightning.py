"""Lightning lessons for contributors who will read LDK, LND, or Core Lightning."""

from __future__ import annotations

LESSONS: list[dict] = [
    {
        "id": "lightning-channels",
        "path_id": "lightning",
        "title": "Payment channels",
        "order": 1,
        "summary": "A Lightning channel is a 2-of-2 Bitcoin contract with an off-chain balance sheet.",
        "concepts": ["lightning channel", "commitment transaction", "htlc", "funding transaction"],
        "keywords": ["channel", "channels", "commitment", "htlc", "funding", "penalty", "justice"],
        "sources": [
            {
                "title": "BOLT 2 — Peer protocol",
                "url": "https://github.com/lightning/bolts/blob/master/02-peer-protocol.md",
            },
            {
                "title": "BOLT 3 — Transactions",
                "url": "https://github.com/lightning/bolts/blob/master/03-transactions.md",
            },
        ],
        "body": """Lightning moves payments off the global chain without giving up Bitcoin's settlement. Two peers lock bitcoin in a **funding transaction** they both must sign to spend (a 2-of-2). They then exchange **commitment transactions**: each side holds a transaction that spends the funding output and pays the current balances. Those commitment transactions are valid Bitcoin transactions. They are just not broadcast while both peers cooperate.

When the balance changes, the peers revoke the old commitment. In the LN-Penalty design used by the original BOLTs, broadcasting a revoked commitment lets the honest peer take the funds with a **penalty** (or "justice") transaction. That only works if someone notices in time. A node that is offline can hire a **watchtower** to watch for cheating commitments.

Payments across a channel use **HTLCs** (hash time locked contracts). An HTLC pays the receiver if they reveal a preimage before a timeout, and refunds the sender after that timeout. The timeout is expressed in Bitcoin blocks, so a Lightning timeout is only as good as the chain data the node is watching.

Things contributors get wrong, and reviewers will ask about:

- **Who holds which transaction.** Each peer's commitment transaction is different. A bug that swaps them can look fine in a unit test and fail on mainnet.
- **CSV and CLTV delays.** `to_self_delay` gives the honest peer time to punish a revoked commitment. Shortening it casually is a funds-loss bug.
- **Fee estimation on commitment transactions.** Anchor channels and zero-fee commitment designs exist because on-chain fees move. Read the project's current channel type before you copy an old blog post.
- **Reorgs.** A funding transaction that loses its confirmations unfunds the channel. Implementations track confirmation depth on purpose.

Read BOLT 3 with the code, not instead of the code. The spec is the contract between implementations. Your patch has to keep that contract or explicitly propose a spec change.
""",
        "quiz": [
            {
                "prompt": "A Lightning channel's bitcoin is locked by:",
                "choices": [
                    "An account balance on a Lightning server",
                    "A Bitcoin funding output that the peers update with off-chain commitment transactions",
                    "The mempool policy of a single miner",
                    "A BIP that replaces proof of work",
                ],
                "answer": 1,
                "explanation": "The funding transaction is on-chain. Balance updates are commitment transactions that could be broadcast but usually are not.",
            },
            {
                "prompt": "A penalty (justice) transaction exists so that:",
                "choices": [
                    "Miners can claim every HTLC",
                    "An honest peer can take funds if the other broadcasts a revoked commitment",
                    "The mempool can drop dust",
                    "Watchtowers can mine blocks",
                ],
                "answer": 1,
                "explanation": "Revocation is what makes old commitment transactions unsafe to broadcast. Someone must be online, or a watchtower must be, to use it.",
            },
        ],
    },
    {
        "id": "lightning-network",
        "path_id": "lightning",
        "title": "Routing, invoices, and trust",
        "order": 2,
        "summary": "How a payment crosses several channels, and what Lightning does not promise.",
        "concepts": ["lightning routing", "invoice", "bolt11", "bolt12", "liquidity"],
        "keywords": ["routing", "invoice", "bolt11", "bolt12", "offers", "liquidity", "mpp", "onion"],
        "sources": [
            {
                "title": "BOLT 4 — Onion routing",
                "url": "https://github.com/lightning/bolts/blob/master/04-onion-routing.md",
            },
            {
                "title": "BOLT 11 — Invoices",
                "url": "https://github.com/lightning/bolts/blob/master/11-invoice-protocol.md",
            },
        ],
        "body": """A Lightning payment is a chain of HTLCs that share a secret. The sender builds an **onion**: each hop can read only its own forwarding instructions (amount, next channel, timelock). Intermediate nodes do not learn the final recipient from the onion. They do learn that they forwarded a payment of some size at some time. Privacy is better than a plain on-chain payment and it is not magic.

The receiver generates a **payment hash** and, in BOLT 11, an invoice that names the hash, an amount, an expiry, and a route hint if needed. The payment succeeds when the receiver releases the **preimage**. The preimage flows back along the path and each hop claims its HTLC. If something fails, the error propagates back and the sender tries another route.

**BOLT 12 offers** improve on invoices: reusable offers, blinded paths, and invoices fetched over Lightning rather than copied out of band. Support is not uniform across implementations. Check the project before you assume an offer feature exists.

Practical limits reviewers expect you to understand:

- **Liquidity** is local. A channel can have capacity and still be unable to forward in the direction you need.
- **Timelocks decrease** toward the receiver so an intermediate hop always has time to settle or fail before its upstream HTLC expires. Getting the deltas wrong can stick funds.
- **MPP** (multi-part payments) splits one payment across several paths. Partial success and timeout handling is a common source of bugs.
- **Fees** on Lightning are forwarding fees set by each node, separate from Bitcoin transaction fees. Both show up in real systems. Say which one you mean.

Lightning is not a custody upgrade by slogan. The node that signs channel state can lose funds if it is backed up badly, if it forgets revocation state, or if it watches the wrong chain. Wallet projects (LDK is often embedded in wallets) get reviewed with that threat in mind.
""",
        "quiz": [
            {
                "prompt": "An intermediate Lightning node can typically see:",
                "choices": [
                    "The full invoice and the sender's xpub",
                    "Its own forwarding instructions, not the entire route unwrapped",
                    "The Bitcoin mempool of every peer",
                    "The preimage before the receiver releases it",
                ],
                "answer": 1,
                "explanation": "Onion routing gives each hop only its layer. Nodes still learn amounts and timing of payments they forward.",
            },
            {
                "prompt": "A BOLT 11 invoice commits to a payment hash so that:",
                "choices": [
                    "Any hop can settle the HTLC without a secret",
                    "The receiver can claim the funds by revealing the preimage, and forwarders can verify it",
                    "The funding transaction does not need signatures",
                    "The channel never needs an on-chain close",
                ],
                "answer": 1,
                "explanation": "The hash locks every HTLC on the path. The preimage is the proof that lets each hop claim the outgoing HTLC.",
            },
        ],
    },
    {
        "id": "lightning-implementations",
        "path_id": "lightning",
        "title": "Lightning implementations",
        "order": 3,
        "summary": "LDK, LND, Core Lightning, and the BOLTs are different layers of one network.",
        "concepts": ["ldk", "lnd", "core lightning", "bolts", "eclair"],
        "keywords": ["ldk", "lnd", "core lightning", "cln", "bolts", "eclair", "implementation"],
        "sources": [
            {"title": "Lightning BOLTs", "url": "https://github.com/lightning/bolts"},
            {"title": "Lightning Dev Kit", "url": "https://github.com/lightningdevkit/rust-lightning"},
            {"title": "LND", "url": "https://github.com/lightningnetwork/lnd"},
            {"title": "Core Lightning", "url": "https://github.com/ElementsProject/lightning"},
        ],
        "body": """The Lightning network is specified by the **BOLTs** (`lightning/bolts`) and implemented by more than one codebase. They interoperate when they follow the same bolt. They diverge when a feature is still experimental.

| Project | Language | How to think about it |
| --- | --- | --- |
| BOLTs | Markdown spec | The contract. Changes need cross-implementation review. |
| LDK (`rust-lightning`) | Rust library | Embeddable Lightning node logic. You bring the chain source, keys, storage, and network. |
| LND | Go daemon | A full node with a gRPC API, widely deployed, its own wallet and channel graph. |
| Core Lightning | C daemon | A modular daemon (`lightningd` plus subdaemons). Plugins are a normal extension path. |
| Eclair | Scala | ACINQ's implementation, often relevant when you are checking interoperability. |

LDK is a library on purpose. A pull request that shells out to bitcoind or opens a socket inside the core crate is probably in the wrong layer. LND and Core Lightning are daemons. A pull request that changes their RPC is user-facing and needs release notes and tests.

Contribution shape:

- **Spec work** belongs in `lightning/bolts` and on the lightning-dev mailing list. Implementers will ask you to show that at least two implementations can speak the change.
- **Interop bugs** need a log from both sides, the BOLT section you think was violated, and a minimal test if the project has one.
- **Do not "fix" a spec violation in one node by making it more lenient** unless the spec is wrong. Lenience becomes the new protocol.
- Read the project's own contributing file. LND wants `make check` and often integration tests. LDK wants `cargo test` and careful API stability. Core Lightning wants `make check` and a changelog line.

Bitcoin on-chain code and Lightning code meet at the funding transaction, the commitment format, feerates, and reorg handling. When you cross that boundary, name both sides in the pull request.
""",
        "quiz": [
            {
                "prompt": "LDK differs from LND in that LDK is:",
                "choices": [
                    "A specification repository with no code",
                    "A Rust library you embed, not a standalone daemon",
                    "The only implementation allowed to open channels",
                    "A replacement for Bitcoin consensus",
                ],
                "answer": 1,
                "explanation": "LDK implements Lightning logic as a library. The host application supplies chain data, persistence, keys, and I/O.",
            },
            {
                "prompt": "A BOLT change should be treated as:",
                "choices": [
                    "A private patch to one daemon",
                    "A spec change that other implementations have to be able to follow",
                    "A mempool policy tweak",
                    "An automatic hard fork",
                ],
                "answer": 1,
                "explanation": "BOLTs are the interoperability contract. One implementation merging a behavior does not define the network.",
            },
        ],
    },
]
