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

The current records are a curated presentation seed. Replacing them with a real snapshot is intentionally isolated to the ingestion/resolution layer, so the public UI and API contract remain stable.
