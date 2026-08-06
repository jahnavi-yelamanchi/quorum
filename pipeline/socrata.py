"""Automated NYC Open Data connector for Manhattan CB6 DOB filings.

Run: python3 -m pipeline.socrata --limit 20
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://data.cityofnewyork.us/resource/ic3t-wcy2.json"

def _date(value: str | None) -> str:
    if not value:
        return "1970-01-01"
    return datetime.strptime(value[:10], "%m/%d/%Y").date().isoformat() if "/" in value else value[:10]

def documents(records: list[dict]) -> list[dict]:
    output = []
    for record in records:
        job = record.get("job__") or record.get("job_s1_no")
        address = " ".join(part for part in (record.get("house__"), record.get("street_name")) if part)
        applicant = " ".join(part for part in (record.get("applicant_s_first_name"), record.get("applicant_s_last_name")) if part)
        owner = record.get("owner_s_business_name") or ""
        status = record.get("job_status_descrp") or record.get("job_status") or "unknown"
        source_url = ENDPOINT + "?" + urlencode({"$where": f"job__='{job}'"})
        output.append({
            "id": f"dob-{record.get('job_s1_no', job)}-{record.get('doc__', '01')}",
            "meeting_date": _date(record.get("latest_action_date") or record.get("dobrundate")),
            "source_url": source_url,
            "text": f"DOB filing {job}\n{address}\nApplicant: {applicant}\nOrganization: {owner}\nDOB Job {job}\nStatus: {status}\n{record.get('job_description', '')}",
            "bbl": record.get("bbl") or record.get("bin__"),
            "longitude": float(record["gis_longitude"]) if record.get("gis_longitude") else None,
            "latitude": float(record["gis_latitude"]) if record.get("gis_latitude") else None,
        })
    return output

def fetch(limit: int) -> list[dict]:
    query = urlencode({
        "$where": "community___board='106' AND borough='MANHATTAN'",
        "$order": "dobrundate DESC",
        "$limit": str(limit),
    })
    request = Request(f"{ENDPOINT}?{query}", headers={"User-Agent": "Quorum civic-data research/0.1"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read())

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--output", type=Path, default=ROOT / "var" / "extracted" / "dob-cb6-documents.json")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    docs = documents(fetch(args.limit))
    args.output.write_text(json.dumps(docs, indent=2) + "\n")
    print(f"Wrote {len(docs)} automated CB6 DOB documents to {args.output}")

if __name__ == "__main__":
    main()
