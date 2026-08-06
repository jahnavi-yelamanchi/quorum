"""Download/cache civic sources, extract text, and write resolver-ready documents.

Run: python3 -m pipeline.ingest --manifest data/cb6_sources.json
Audio uses QUORUM_ASR_COMMAND, which must print a transcript to stdout and may
contain {input}. Example: QUORUM_ASR_COMMAND='whisper-cli -f {input}'
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import shlex
import subprocess
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]

@dataclass
class IngestResult:
    id: str
    status: str
    sha256: str | None = None
    detail: str | None = None

def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _download(source: dict, raw_dir: Path) -> Path:
    if source.get("path"):
        path = ROOT / source["path"]
        if not path.is_file():
            raise FileNotFoundError(path)
        return path
    request = Request(source["url"], headers={"User-Agent": "Quorum civic-data research/0.1"})
    with urlopen(request, timeout=30) as response:
        suffix = Path(response.headers.get_filename() or urlparse(source["url"]).path).suffix or ".bin"
        destination = raw_dir / f"{source['id']}{suffix.lower()}"
        with destination.open("wb") as output:
            shutil.copyfileobj(response, output)
    return destination

def _extract_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
        text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    except ImportError as error:
        raise RuntimeError("Install pipeline/requirements.txt for PDF extraction") from error
    if len(text.strip()) >= 80:
        return text
    return _ocr_pdf(path)

def _ocr_pdf(path: Path) -> str:
    try:
        import fitz
    except ImportError as error:
        raise RuntimeError("Install pipeline/requirements.txt for scanned-PDF OCR") from error
    with tempfile.TemporaryDirectory() as temp_dir:
        document = fitz.open(path)
        pages: list[str] = []
        for number, page in enumerate(document):
            image = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            target = Path(temp_dir) / f"page-{number}.png"
            image.save(target)
            result = subprocess.run(["tesseract", str(target), "stdout"], text=True, capture_output=True, check=True)
            pages.append(result.stdout)
        return "\n".join(pages)

def _extract_audio(path: Path) -> str:
    sidecar = path.with_suffix(path.suffix + ".txt")
    if sidecar.is_file():
        return sidecar.read_text()
    command = os.getenv("QUORUM_ASR_COMMAND")
    if not command:
        raise RuntimeError("No transcript sidecar or QUORUM_ASR_COMMAND configured")
    result = subprocess.run(shlex.split(command.format(input=str(path))), text=True, capture_output=True, check=True)
    if not result.stdout.strip():
        raise RuntimeError("ASR command returned no transcript on stdout")
    return result.stdout

def _extract(path: Path, kind: str) -> str:
    if kind == "audio":
        return _extract_audio(path)
    if path.suffix.lower() == ".pdf":
        return _extract_pdf(path)
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tiff"}:
        return subprocess.run(["tesseract", str(path), "stdout"], text=True, capture_output=True, check=True).stdout
    return path.read_text(encoding="utf-8", errors="replace")

def run(manifest_path: Path, output_path: Path, raw_dir: Path) -> list[IngestResult]:
    manifest = json.loads(manifest_path.read_text())
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    documents, results = [], []
    for source in manifest["sources"]:
        try:
            raw = _download(source, raw_dir)
            text = _extract(raw, source.get("kind", "document"))
            digest = _sha256(raw)
            documents.append({
                "id": source["id"], "meeting_date": source["meeting_date"],
                "source_url": source.get("url", f"file://{source['path']}"), "text": text,
            })
            results.append(IngestResult(source["id"], "ingested", digest))
        except (FileNotFoundError, HTTPError, URLError, RuntimeError, subprocess.CalledProcessError) as error:
            results.append(IngestResult(source["id"], "blocked", detail=str(error)))
    output_path.write_text(json.dumps(documents, indent=2) + "\n")
    (output_path.parent / "ingest-report.json").write_text(json.dumps([asdict(result) for result in results], indent=2) + "\n")
    return results

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "var" / "extracted" / "documents.json")
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "var" / "raw")
    args = parser.parse_args()
    results = run(args.manifest, args.output, args.raw_dir)
    print("; ".join(f"{result.id}: {result.status}" for result in results))
    if not any(result.status == "ingested" for result in results):
        raise SystemExit("No sources were ingested; see ingest-report.json")

if __name__ == "__main__":
    main()
