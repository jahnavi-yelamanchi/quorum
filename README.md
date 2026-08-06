# Quorum

Map-first civic decision intelligence for a Manhattan Community Board 6 demo snapshot.

## Run the web demo

```bash
npm install
npm run dev
```

## Run the API

```bash
python3 -m venv .venv
.venv/bin/pip install -r api/requirements.txt
.venv/bin/uvicorn main:app --reload --app-dir api
```

The UI is self-contained so it can be previewed without the API. The API exposes evidence-backed demo items at `GET /items` and validates saved-place input at `POST /saved-places`.
Set `VITE_API_URL` to the deployed API URL to hydrate the map from the snapshot; without it, the presentation fallback remains usable.

## Build the civic snapshot

```bash
python3 -m pipeline.build_snapshot
python3 -m pipeline.check
```

The resolver groups agenda aliases by civic ID, address, and title similarity, retains the original document evidence, and turns each item into a lifecycle. It only permits an alert for a high-confidence address match at an approved, denied, or closed decision state.

The checked-in documents are versioned development fixtures pointing to the CB6 public source. The production adapter should replace only `data/cb6_documents.json`; the resolver and API contract remain unchanged.
