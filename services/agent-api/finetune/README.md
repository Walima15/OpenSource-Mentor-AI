# OSMA Mentor - fine-tuning pipeline (Together.ai)

Fine-tune an open-source model into a custom **OSMA Mentor** model that speaks in
OSMA's voice across all its capabilities (explain repo/issue, plan, recommend
files, suggest code/tests, commit messages, PR descriptions, summaries, chat),
then serve it in the app via the Together provider.

## Pipeline

```
seed_examples.py ─┐
                  ├─> build_dataset.py ─> data/train.jsonl (+ val.jsonl) ─> finetune_together.py ─> fine-tuned model
distill.py ───────┘            (merge + validate + split)                        (upload + LoRA job)
```

## 1. Build the dataset

Seed only (no API keys needed):

```bash
cd services/agent-api
python -m finetune.build_dataset
```

Scale up by distilling from a teacher model over real repos/issues (needs
`ANTHROPIC_API_KEY` or `OPENAI_API_KEY`, and ideally `GITHUB_FALLBACK_TOKEN`):

```bash
python -m finetune.distill --teacher anthropic --repos pallets/flask,psf/requests
python -m finetune.build_dataset   # re-run to merge distilled examples
```

Output: `finetune/data/train.jsonl` and `finetune/data/val.jsonl` in Together's
chat format (`{"messages": [...]}` per line).

## 2. Fine-tune on Together

Set `TOGETHER_API_KEY`, then:

```bash
python -m finetune.finetune_together --wait
```

This uploads the dataset, starts a **LoRA** fine-tune from `TOGETHER_BASE_MODEL`,
and (with `--wait`) prints the resulting model name when done.

## 3. Serve the fine-tuned model

Set these (in `.env`) and restart the API:

```
LLM_PROVIDER=together
TOGETHER_MODEL=<your fine-tuned model name from step 2>
```

The agent system ([app/agents/llm.py](../app/agents/llm.py)) routes all nodes
through this model via Together's OpenAI-compatible API. Nothing else in the
agent graph changes - the mentor now runs on your own model.

## Notes

- Keep the seed set small and high-quality; distillation scales volume.
- The `data/` JSONL files are git-ignored (regenerate them); `seed_examples.py`
  is the source of truth for curated examples.
- Costs: a small LoRA run on an 8B model is typically inexpensive, but check
  Together's current pricing before launching.
