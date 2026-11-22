#!/usr/bin/env python3
"""Read-only checks against the immutable 1,280-run research record."""
import argparse
import csv
import hashlib
import json
import os
import platform
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CO_PRIMARY = {"timely_ratio", "service_violation_rate"}
GROUPS = {"main": 1050, "stationary": 70, "scale": 40, "probes": 60, "heads": 60}

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def check():
    man = json.loads((BASE / "results/manifest.json").read_text())
    saved = json.loads((BASE / "analysis/analysis_verification.json").read_text())
    release = json.loads((BASE / "release_validation.json").read_text())
    for name in ("acr_mcr_v2.py", "run_study.py", "PROTOCOL.md"):
        expected = man.get("source_sha256", {}).get(name)
        if expected is None or digest(BASE / name) != expected:
            raise ValueError("Locked protocol/source hash mismatch: " + name)
    if len(man["jobs"]) != 1280:
        raise ValueError("Unexpected manifest count")
    counter = Counter()
    matched = set()
    with (BASE / "results/raw_results.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            counter[row["group"]] += 1
            if row["group"] == "main":
                matched.add((row["seed"], row["scenario"], row["method"]))
    if dict(counter) != GROUPS:
        raise ValueError("Mismatch in run categories: " + str(counter))
    if len(matched) != 1050:
        raise ValueError("Missing or repeated primary seed/scenario/method combinations")
    if not saved.get("locked_source_hashes_verified") or saved.get("primary_seed_blocks") != 30:
        raise ValueError("Saved verification invalid")
    if not release.get("tables_match_saved_analyses") or release.get("verified_mechanisms") != 13:
        raise ValueError("Saved release verification invalid")
    with (BASE / "analysis/primary_effects.csv").open(newline="") as f:
        primary = list(csv.DictReader(f))
    if len(primary) != 2 or {r["metric"] for r in primary} != CO_PRIMARY:
        raise ValueError("Unexpected primary comparison family")
    effects = {}
    for row in primary:
        if row["contrast"] != "ACR-MCR minus POINT-EA" or int(row["n"]) != 30:
            raise ValueError("Unexpected primary contrast/n")
        lo, hi, p = [float(row[k]) for k in ("ci_low", "ci_high", "p_holm")]
        if lo > hi or not 0 <= p <= 1:
            raise ValueError("Invalid CI/p-value")
        effects[row["metric"]] = dict(
            difference=float(row["difference"]), ci95=[lo, hi],
            adjusted_p=p, interval_includes_zero=lo <= 0 <= hi
        )
    with (BASE / "analysis/method_summary.csv").open(newline="") as f:
        summary = list(csv.DictReader(f))
    totals = {(r["method"],r["metric"]): float(r["mean"]) for r in summary}
    telemetry = {}
    for m in ("POINT-EA", "ACR-MCR"):
        e = totals[m, "radio_energy_J"]
        probe = totals[m, "energy_probe_J"]
        telemetry[m] = dict(radio_energy_J=e, probe_energy_J=probe, probe_share=probe/e)
    return dict(
        status="PASS", timestamp_utc=datetime.now(timezone.utc).isoformat(),
        baseline_data_commit="7dceb22340677ee78a9f36c8dd4c96ad5988509c",
        outcome_runs=sum(counter.values()), main_seed_blocks=30,
        runs_by_group=dict(counter), co_primary=effects,
        telemetry=telemetry,
        warning="No significant co-primary improvement is established; simulator is not packet-level or physical validation.",
        runner=platform.platform(), github_run_id=os.getenv("GITHUB_RUN_ID","local")
    )

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out", default="recovery_reports/frozen_record_audit.json")
    args=ap.parse_args()
    report=check()
    dest=Path(args.out)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
