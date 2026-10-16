"""Launch a LoRA fine-tuning job for the OSMA Mentor model on Together.ai.

Steps:
  1. Upload train.jsonl (and val.jsonl if present).
  2. Create a LoRA fine-tuning job from the configured base model.
  3. Optionally poll until it finishes and print the resulting model name.

Usage (run from services/agent-api, after `python -m finetune.build_dataset`):
    python -m finetune.finetune_together --wait
Requires TOGETHER_API_KEY. The base model comes from TOGETHER_BASE_MODEL.

When the job completes, set TOGETHER_MODEL to the printed output name and
LLM_PROVIDER=together to serve the fine-tuned model in the app.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from app.core.config import settings

DATA_DIR = Path(__file__).parent / "data"


def _attr(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _client():
    if not settings.together_api_key:
        raise SystemExit("TOGETHER_API_KEY is not set.")
    from together import Together

    return Together(api_key=settings.together_api_key)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default=str(DATA_DIR / "train.jsonl"))
    parser.add_argument("--val", default=str(DATA_DIR / "val.jsonl"))
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--suffix", default="osma-mentor")
    parser.add_argument("--base-model", default=settings.together_base_model)
    parser.add_argument("--wait", action="store_true", help="Poll until finished")
    args = parser.parse_args()

    train_path = Path(args.train)
    if not train_path.exists():
        raise SystemExit(
            f"{train_path} not found. Run `python -m finetune.build_dataset` first."
        )

    client = _client()

    print(f"Uploading {train_path} ...")
    train_file = client.files.upload(file=str(train_path))
    train_id = _attr(train_file, "id")
    print(f"  training_file={train_id}")

    kwargs = dict(
        training_file=train_id,
        model=args.base_model,
        n_epochs=args.epochs,
        lora=True,
        suffix=args.suffix,
    )

    val_path = Path(args.val)
    if val_path.exists():
        print(f"Uploading {val_path} ...")
        val_file = client.files.upload(file=str(val_path))
        kwargs["validation_file"] = _attr(val_file, "id")
        kwargs["n_evals"] = args.epochs

    print(f"Creating fine-tune job on {args.base_model} (LoRA) ...")
    job = client.fine_tuning.create(**kwargs)
    job_id = _attr(job, "id")
    print(f"  job_id={job_id}  status={_attr(job, 'status')}")

    if not args.wait:
        print(
            "Job submitted. Check progress with:\n"
            f"  python -m finetune.finetune_together --status {job_id}\n"
            "or in the Together dashboard."
        )
        return

    print("Waiting for completion (this can take a while)...")
    terminal = {"completed", "error", "cancelled", "failed"}
    while True:
        job = client.fine_tuning.retrieve(job_id)
        status = str(_attr(job, "status"))
        print(f"  status={status}")
        if status.lower() in terminal:
            break
        time.sleep(30)

    output = _attr(job, "output_name") or _attr(job, "model_output_name")
    if output:
        print("\nFine-tuned model is ready. To use it:")
        print(f"  LLM_PROVIDER=together")
        print(f"  TOGETHER_MODEL={output}")
    else:
        print("Job finished; check the Together dashboard for the model name.")


if __name__ == "__main__":
    main()
