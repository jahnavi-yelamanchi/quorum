# Quorum gold set

`gold_set.json` is the hand-correctable source of truth for the civic document fixtures. Each row binds one source document to its canonical item, resolved address, and lifecycle state.

Run `python3 -m training.evaluate` after changing the resolver, documents, or labels. Expand this file with real CB6 corrections before training; do not train from LLM labels alone.

The first trainable artifacts should be:

- Civic NER: document text → address, case ID, named project, organization spans.
- Entity linker: positive alias pairs from the same `item_id`; hard negatives from same-neighborhood but distinct items.
- Interest classifier: saved-address/item pairs labeled alert or suppress.
