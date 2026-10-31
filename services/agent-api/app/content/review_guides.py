"""Review checklists shared by the mentor and the review tools."""

from __future__ import annotations

GENERAL_CHECKLIST: list[str] = [
    "Can you explain the change without reading the diff line by line?",
    "Is the pull request one logical change, without drive-by refactors?",
    "Does the description say why, what changed, and how it was tested?",
    "Are there tests that fail before the fix and pass after it?",
    "Does any behavior change at the consensus, policy, or wire layer? If yes, slow down and name the layer.",
    "Are error paths explicit, or do they swallow a failed signature, a failed read, or a failed payment?",
    "Are amounts, weights, and sizes converted in one direction only, with tests at the boundaries?",
    "Is the commit message accurate, and does it avoid hiding a behavior change inside a cleanup?",
    "Would a reorg, a malicious peer, or a replaced unconfirmed transaction embarrass this patch?",
    "Did you review this commit yourself? Do not ACK work you did not read.",
]

PROJECT_CHECKLIST: dict[str, list[str]] = {
    "bitcoin-core": [
        "Use Concept ACK, Approach ACK, ACK, utACK, NACK, and nit precisely.",
        "Name the commit you reviewed and whether you ran unit or functional tests.",
        "Consensus logic is spread beyond src/consensus/. Check validation and script too.",
        "Node behavior wants a functional test under test/functional.",
        "History should rebase cleanly. Merge commits are not the project style.",
    ],
    "secp256k1": [
        "Secret-dependent branches and memory access are correctness bugs.",
        "Do not treat a benchmark win as a review approval.",
        "API and consensus-signature changes need vectors.",
    ],
    "rust-bitcoin": [
        "Run tests with the features CI enables, not only the default set.",
        "Consensus encoding must stay compatible with Bitcoin Core.",
        "Public API changes need a migration note.",
    ],
    "rust-miniscript": [
        "A policy that compiles to a malleable or insane script is a failed patch.",
        "Resource limits should reject, not truncate, an oversized script.",
    ],
    "bdk": [
        "Walk a multi-input transaction and check the change output and the fee.",
        "Reorgs and conflicting unconfirmed transactions need a stated behavior.",
        "Keep PSBT roles from collapsing into one untestable function.",
    ],
    "ldk": [
        "Cite the BOLT section.",
        "The core crate should not grow a hidden dependency on bitcoind or a socket.",
        "Trace the channel state machine, including a peer who misbehaves.",
        "Show the timelock math with numbers.",
    ],
    "lnd": [
        "RPC and protobuf changes need docs, release notes, and compatibility.",
        "Persistence changes need an upgrade path.",
        "Protocol changes need an integration test, not only a mocked unit test.",
    ],
    "core-lightning": [
        "User-visible changes need a changelog fragment.",
        "Protocol changes cite a BOLT.",
        "Check both sides of a subdaemon boundary.",
    ],
    "btcpay": [
        "State which invoice or payment statuses change.",
        "Secrets, seeds, and connection strings must not be logged.",
        "Describe the merchant-facing migration if configuration changed.",
    ],
    "bolts": [
        "Say whether the edit clarifies or changes behavior.",
        "Update test vectors when bytes change.",
        "Note what LDK, LND, and Core Lightning do today.",
        "MUST and SHOULD should be unambiguous.",
    ],
}


def checklist_for(slug: str | None) -> list[str]:
    items = list(GENERAL_CHECKLIST)
    if slug:
        items.extend(PROJECT_CHECKLIST.get(slug, []))
    return items
