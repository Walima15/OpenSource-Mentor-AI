"""Build the fine-tuning dataset for Together.ai.

Combines the curated seed examples with any distilled examples, validates the
chat format, shuffles, splits into train/val, and writes JSONL files that
Together's fine-tuning API accepts (one JSON object per line with a top-level
``messages`` array).

Usage:
    python -m finetune.build_dataset
    python -m finetune.build_dataset --distilled finetune/data/distilled.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from finetune.seed_examples import SEED

DATA_DIR = Path(__file__).parent / "data"
VALID_ROLES = {"system", "user", "assistant", "tool"}


def _valid_record(rec: dict) -> bool:
    msgs = rec.get("messages")
    if not isinstance(msgs, list) or len(msgs) < 2:
        return False
    has_user = has_assistant = False
    for m in msgs:
        if not isinstance(m, dict):
            return False
        if m.get("role") not in VALID_ROLES:
            return False
        if not isinstance(m.get("content"), str) or not m["content"].strip():
            return False
        has_user = has_user or m["role"] == "user"
        has_assistant = has_assistant or m["role"] == "assistant"
    return has_user and has_assistant


def _load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"Skipping malformed line in {path}")
    return records


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--distilled",
        default=str(DATA_DIR / "distilled.jsonl"),
        help="Optional JSONL of distilled examples to merge in.",
    )
    parser.add_argument("--val-split", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    records = list(SEED) + _load_jsonl(Path(args.distilled))

    valid = [r for r in records if _valid_record(r)]
    dropped = len(records) - len(valid)
    if dropped:
        print(f"Dropped {dropped} invalid record(s).")

    random.seed(args.seed)
    random.shuffle(valid)

    n_val = max(1, int(len(valid) * args.val_split)) if len(valid) > 5 else 0
    val, train = valid[:n_val], valid[n_val:]

    _write_jsonl(DATA_DIR / "train.jsonl", train)
    if val:
        _write_jsonl(DATA_DIR / "val.jsonl", val)

    print(f"Wrote {len(train)} train and {len(val)} val examples to {DATA_DIR}")


if __name__ == "__main__":
    main()
