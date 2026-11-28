"""Per-repository IDE settings.

Bitcoin Core is cloned sparse so the working tree stays on the files a new
contributor actually reads. The file and history caps keep a 1.5B or 3B local
model inside a short prompt. qwen2.5-coder:1.5b and 3b are about 32k tokens;
long files crowd out the contributing rules.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IdeProfile:
    slug: str
    sparse_dirs: tuple[str, ...] = ()
    skip_prefixes: tuple[str, ...] = ()
    tree_first: tuple[str, ...] = ()
    timeout_seconds: int = 180
    file_chars: int = 12_000
    history_messages: int = 12
    history_chars: int = 8_000
    clone_note: str = ""
    issue_hint: str = ""
    context_note: str = ""
    learn_links: tuple[tuple[str, str], ...] = ()


_CORE_NOTE = (
    "Bitcoin Core is large. This clone is shallow and sparse: source, docs, "
    "functional tests, and CI files, without git history or the depends/ tree. "
    "The download can take several minutes and use a few hundred megabytes."
)

_LDK_NOTE = (
    "LDK is a shallow clone. It is much smaller than Bitcoin Core. "
    "The first download still comes from GitHub and can take a minute."
)

_CORE_CONTEXT = (
    "Context budget for qwen2.5-coder:1.5b or 3b: read_workspace_file returns "
    "at most 4000 characters, and only the last few chat turns are sent. "
    "Read one file, then answer. Do not load several large files in one turn."
)

_LDK_CONTEXT = (
    "Context budget for qwen2.5-coder:1.5b or 3b: read_workspace_file returns "
    "at most 6000 characters. Read one file, then answer."
)

IDE_PROFILES: dict[str, IdeProfile] = {
    "bdk": IdeProfile(
        slug="bdk",
        learn_links=(
            ("/projects/bdk", "BDK project guide"),
            ("/learn/contribution-craft", "Contribution craft"),
        ),
        issue_hint=(
            "Good first issues use the label good first issue on "
            "https://github.com/bitcoindevkit/bdk/labels/good%20first%20issue. "
            "Comment on the issue before you start."
        ),
    ),
    "rust-bitcoin": IdeProfile(
        slug="rust-bitcoin",
        learn_links=(
            ("/projects/rust-bitcoin", "rust-bitcoin project guide"),
            ("/learn/bitcoin-fundamentals", "Bitcoin fundamentals"),
            ("/learn/contribution-craft", "Contribution craft"),
        ),
        issue_hint=(
            "Good first issues use the label good first issue on "
            "https://github.com/rust-bitcoin/rust-bitcoin/labels/good%20first%20issue."
        ),
    ),
    "bitcoin-core": IdeProfile(
        slug="bitcoin-core",
        sparse_dirs=("src", "doc", "test/functional", "ci", ".github"),
        skip_prefixes=(
            "depends",
            "src/qt",
            "src/leveldb",
            "src/secp256k1",
            "src/minisketch",
            "src/crc32c",
            "src/univalue",
        ),
        tree_first=("doc", "test/functional", "src", "ci", ".github"),
        timeout_seconds=600,
        file_chars=4_000,
        history_messages=4,
        history_chars=2_000,
        clone_note=_CORE_NOTE,
        context_note=_CORE_CONTEXT,
        issue_hint=(
            "Bitcoin Core often has few good first issues. Look for that label on "
            "https://github.com/bitcoin/bitcoin/labels/good%20first%20issue. "
            "Reviewing an existing pull request is the better first contribution. "
            "Do not start with consensus changes."
        ),
        learn_links=(
            ("/projects/bitcoin-core", "Bitcoin Core project guide"),
            ("/learn/bitcoin-fundamentals", "Bitcoin fundamentals"),
            ("/learn/contribution-craft", "Contribution craft"),
        ),
    ),
    "ldk": IdeProfile(
        slug="ldk",
        timeout_seconds=300,
        file_chars=6_000,
        history_messages=6,
        history_chars=3_000,
        clone_note=_LDK_NOTE,
        context_note=_LDK_CONTEXT,
        issue_hint=(
            "Look for the label good first issue on "
            "https://github.com/lightningdevkit/rust-lightning/labels/good%20first%20issue. "
            "Read the channel state machine before changing it."
        ),
        learn_links=(
            ("/projects/ldk", "LDK project guide"),
            ("/learn/lightning", "Lightning lessons"),
            ("/learn/contribution-craft", "Contribution craft"),
        ),
    ),
}

IDE_SLUGS: tuple[str, ...] = tuple(IDE_PROFILES)


def profile_for(slug: str) -> IdeProfile | None:
    return IDE_PROFILES.get(slug)
