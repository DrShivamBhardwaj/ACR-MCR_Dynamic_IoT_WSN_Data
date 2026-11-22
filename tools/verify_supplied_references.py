#!/usr/bin/env python3
"""Check *only* the 18 citations supplied in references.json.

No new paper is discovered or added. The DOI metadata requests are only for
verification of existing supplied DOI records. A nonmatch or network error is
marked as pending, not corrected with a guessed citation.
"""
import argparse
import json
import re
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import quote, urlsplit
from urllib.request import Request,urlopen

BASE=Path(__file__).resolve().parents[1]
def compact(s):
    return " ".join(re.findall(r"[a-z0-9]+",str(s).casefold()))
def doi_from(url):
    u=urlsplit(url)
    if u.hostname in {"doi.org","www.doi.org","dx.doi.org"}:
        return u.path.lstrip("/")
    return None
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",default="recovery_reports/supplied_reference_check.json")
    ap.add_argument("--offline",action="store_true")
    args=ap.parse_args()
    refs=json.loads((BASE/"references.json").read_text())
    if len(refs)!=18:
        raise ValueError("Reference ledger is not the 18-entry supplied source record")
    records=[]
    for key,entry in refs.items():
        for field in ("text","url","supports"):
            if not entry.get(field):
                raise ValueError(f"{key} is missing {field}")
        record=dict(
            key=key,claimed_text=entry["text"],supplied_url=entry["url"],
            support_scope=entry["supports"], doi=doi_from(entry["url"]),
            status="metadata_not_checked",metadata_source=None
        )
        if record["doi"] and not args.offline:
            endpoint="https://api.crossref.org/works/"+quote(record["doi"],safe="/")
            try:
                req=Request(endpoint,headers={"User-Agent":"ACR-MCR-DOI-verifier/1.0"})
                with urlopen(req,timeout=9) as f:
                    result=json.loads(f.read().decode("utf-8"))
                meta=result["message"]
                title=(meta.get("title") or [""])[0]
                year=((meta.get("published",{}).get("date-parts") or [[None]])[0][0])
                record.update(
                    metadata_source=endpoint,returned_title=title,
                    returned_year=year,
                    title_verification=bool(title and compact(title) in compact(entry["text"])),
                    year_verification=bool(year is not None and str(year) in entry["text"])
                )
                if record["title_verification"] and record["year_verification"]:
                    record["status"]="doi_title_year_matched"
                else:
                    record["status"]="DOI_METADATA_MISMATCH_NEEDS_REVIEW"
            except Exception as exc:
                record["status"]="DOI_VERIFICATION_UNAVAILABLE"
                record["error"]=str(exc)[:240]
        elif not record["doi"]:
            record["status"]="NON_DOI_ORIGINAL_URL_NEEDS_MANUAL_VERIFICATION"
        records.append(record)
    stats={}
    for r in records:stats[r["status"]]=stats.get(r["status"],0)+1
    out=dict(
        status="source_limited_reference_audit",
        verified_at_utc=datetime.now(timezone.utc).isoformat(),
        supplied_reference_count=len(records),
        status_counts=stats,
        caveat="DOI title/year match is metadata validation, not full-text analysis or proof of the manuscript's claim.",
        records=records
    )
    dest=Path(args.out); dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(dict(count=len(records),status_counts=stats),indent=2))
if __name__=="__main__": main()
