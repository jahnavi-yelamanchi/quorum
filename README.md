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

## Add MapPLUTO parcels

Export the relevant MapPLUTO parcels as GeoJSON, or provide a CSV with `BBL`, `Address`, `Longitude`, and `Latitude` columns. Then build with `python3 -m pipeline.build_snapshot --parcels var/parcels/cb6.geojson`. Exact addresses attach a BBL and map point at 99% confidence; weak matches remain unresolved and never become alert-eligible.

## Ingest source files

```bash
python3 -m pip install -r pipeline/requirements.txt
python3 -m pipeline.ingest --manifest data/cb6_sources.json
python3 -m pipeline.build_snapshot --documents var/extracted/documents.json
```

The ingestion job caches raw files under `var/raw/`, writes extracted resolver-ready records under `var/extracted/`, hashes every input, and records blocked sources in `ingest-report.json`. Text PDFs are extracted directly; scanned PDFs render locally and pass through Tesseract. Audio accepts a `*.audio-extension.txt` transcript sidecar or a local `QUORUM_ASR_COMMAND` that prints the transcript to stdout. Keep raw CB6 PDFs/audio outside git and add their direct URLs or local paths to `data/cb6_sources.json`.
