#!/usr/bin/env python3
"""Aggregate fresh paired pilot logs without hypothesis testing or model tuning."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dir",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    results=defaultdict(dict)
    seen=set()
    files=sorted(Path(args.dir).glob("pilot_*.csv"))
    if not files:
        raise ValueError("No pilot CSV inputs")
    for file in files:
        with file.open(newline="") as stream:
            for row in csv.DictReader(stream):
                key=(row["scenario"],int(row["seed"]))
                if (key,row["method"]) in seen:
                    raise ValueError("Duplicate method/seed/scenario")
                seen.add((key,row["method"]))
                results[key][row["method"]]=row
    outcomes=("timely_ratio","service_violation_rate","radio_energy_J","energy_probe_J")
    scenarios=defaultdict(lambda:defaultdict(list))
    for (scenario,seed),pair in sorted(results.items()):
        if set(pair) != {"ACR-MCR","POINT-EA"}:
            raise ValueError(f"Unmatched comparison in {scenario}/{seed}")
        for metric in outcomes:
            d=float(pair["ACR-MCR"][metric])-float(pair["POINT-EA"][metric])
            scenarios[scenario][metric].append(d)
    summary={}
    for sc,metrics in scenarios.items():
        summary[sc]={
            "matched_seed_blocks":len(metrics["timely_ratio"]),
            "mean_difference_acr_minus_point":{m:sum(xs)/len(xs) for m,xs in metrics.items()}
        }
    result=dict(
        label="Exploratory code smoke test only, no inferential interpretation",
        matched_scenario_seed_pairs=len(results),
        primary_inference_unchanged=True,
        scenarios=summary
    )
    out=Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
