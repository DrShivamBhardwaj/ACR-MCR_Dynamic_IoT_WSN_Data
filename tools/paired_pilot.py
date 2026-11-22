#!/usr/bin/env python3
"""A bounded, explicitly exploratory paired cloud smoke test.

Uses fresh pilot seed blocks and the frozen 40-node/160-round configuration.
Does not replace or overwrite the 1,280-run released results.
"""
import argparse
import csv
import hashlib
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path

from acr_mcr_v2 import Config, Simulator

METHODS = ("POINT-EA", "ACR-MCR")
SCENARIOS = {"S1", "S2", "S3", "S4", "S5"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--scenario", required=True, choices=sorted(SCENARIOS))
    p.add_argument("--block", type=int, required=True)
    p.add_argument("--seeds", type=int, default=1)
    p.add_argument("--out", default="recovery_reports/pilot")
    args=p.parse_args()
    if args.block not in range(6) or args.seeds not in range(1,6):
        p.error("block must be 0..5 and seeds must be 1..5")
    if not os.path.isfile("acr_mcr_v2.py"):
        raise RuntimeError("Run from the dataset repository root.")
    conf=Config()
    out=Path(args.out)
    out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for j in range(args.seeds):
        seed=9100 + args.block*5 + j
        for method in METHODS:
            print(f"pilot {args.scenario} seed={seed} method={method}",flush=True)
            sim=Simulator(seed,args.scenario,method,conf,False)
            result=sim.run()
            result["group"]="recovery_pilot_exploratory"
            result["source_seed_block"]=args.block
            rows.append(result)
    out_file=out/f"pilot_{args.scenario}_block{args.block}.csv"
    with out_file.open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    meta=dict(
        status="exploratory_only",
        scenario=args.scenario,
        seeds=[9100+args.block*5+j for j in range(args.seeds)],
        methods=list(METHODS),
        baseline_data_commit="7dceb22340677ee78a9f36c8dd4c96ad5988509c",
        code_sha256=hashlib.sha256(Path("acr_mcr_v2.py").read_bytes()).hexdigest(),
        protocol_sha256=hashlib.sha256(Path("PROTOCOL.md").read_bytes()).hexdigest(),
        github_run_id=os.getenv("GITHUB_RUN_ID","local"),
        python=platform.python_version(),
        completed_utc=datetime.now(timezone.utc).isoformat(),
        warning="Pilot results are exploratory; no inferential claims or novelty claim."
    )
    out_file.with_suffix(".json").write_text(json.dumps(meta,indent=2)+"\n")
    print(f"Saved {len(rows)} matched runs at {out_file}")

if __name__ == "__main__":
    main()
