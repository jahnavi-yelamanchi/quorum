# Quorum gold set

`gold_set.json` is the hand-correctable source of truth for the civic document fixtures. Each row binds one source document to its canonical item, resolved address, and lifecycle state.

Run `python3 -m training.evaluate` after changing the resolver, documents, or labels. Expand this file with real CB6 corrections before training; do not train from LLM labels alone.

The first trainable artifacts should be:

- Civic NER: document text → address, case ID, named project, organization spans.
- Entity linker: positive alias pairs from the same `item_id`; hard negatives from same-neighborhood but distinct items.
- Interest classifier: saved-address/item pairs labeled alert or suppress.

## Automated linker baseline

The DOB connector can create silver labels from recurring job records, so no manual labeling is needed for the first linker baseline:

```bash
python3 -m training.bootstrap --documents var/extracted/dob-cb6-documents.json
python3 -m pip install -r training/requirements.txt
python3 -m training.train_linker --pairs var/training/linker-silver.jsonl
```

The report is explicitly labeled `silver`: use it to find pipeline regressions, not as a claim of human-verified model quality. Keep the deterministic resolver and alert gate authoritative until a corrected gold set is larger.
