#!/usr/bin/env python3
"""Paired, source-locked exploratory probe-budget audit for the S5 study.

Existing results only. Does not run or re-label a new experiment.
"""
from pathlib import Path
import argparse
import json
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
METRICS=[
    "PDR","timely_ratio","service_violation_rate","radio_energy_J",
    "energy_probe_J","energy_control_J","energy_per_delivered_mJ",
    "data_cost_coverage"
]
BUDGETS=[0,1,2]
METHODS=["POINT-EA","ACR-MCR"]

def analyze():
    df=pd.read_csv(ROOT/"results/raw_results.csv")
    subset=df[df.group.eq("probes")].copy()
    if len(subset)!=60 or set(subset.probes)!=set(BUDGETS) or set(subset.method)!=set(METHODS):
        raise ValueError("Probe-budget sample set differs from frozen protocol")
    expected_seeds=set(range(3000,3010))
    if set(subset.seed)!=expected_seeds or set(subset.scenario)!={"S5"}:
        raise ValueError("Probe-budget seeds/scenarios changed")
    if subset.duplicated(["seed","method","probes"]).any():
        raise ValueError("Repeated seed/method/budget")
    groups=[]
    for method in METHODS:
        for budget in BUDGETS:
            g=subset[(subset.method==method)&(subset.probes==budget)].sort_values("seed")
            if len(g)!=10:
                raise ValueError("Missing paired seed")
            r={"method":method,"probes":budget,"n_seed_blocks":len(g)}
            for m in METRICS:
                vals=g[m].astype(float).to_numpy()
                r[m+"_mean"]=None if np.all(np.isnan(vals)) else float(np.nanmean(vals))
            r["modelled_probe_energy_fraction"]=(r["energy_probe_J_mean"] / r["radio_energy_J_mean"])
            groups.append(r)
    paired=[]
    for method in METHODS:
        x=subset[subset.method==method]
        for b0,b1 in [(0,1),(1,2),(0,2)]:
            pair={"method":method,"probe_budget_change":f"{b0} to {b1}","n":10}
            for metric in METRICS:
                p=x.pivot(index="seed",columns="probes",values=metric)
                delta=p[b1]-p[b0]
                pair[metric+"_paired_mean_delta"]=None if delta.isna().all() else float(delta.mean())
            paired.append(pair)
    paired_comparators=[]
    for budget in BUDGETS:
        x=subset[subset.probes==budget]
        pair={"probe_budget":budget,"n":10,"contrast":"ACR-MCR minus POINT-EA"}
        for metric in METRICS:
            p=x.pivot(index="seed",columns="method",values=metric)
            delta=p["ACR-MCR"]-p["POINT-EA"]
            pair[metric+"_paired_mean_delta"]=None if delta.isna().all() else float(delta.mean())
        paired_comparators.append(pair)
    return dict(
        status="PASS",
        release="Frozen 1,280-run study, subset: S5 telemetry sensitivity",
        original_confirmatory_family_unchanged=True,
        n_paired_seed_blocks=10,
        named_seeds=sorted(expected_seeds),
        descriptive_groups=groups,
        paired_probe_budget_effects=paired,
        paired_controller_effects_by_budget=paired_comparators,
        interpretation="Exploratory paired means only, no superiority test; probes consume energy and can reduce timely service.",
        boundary="No CPU energy, idle listening, sensing, distributed probe protocol or physical calibration."
    )

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",default="recovery_reports/telemetry_tradeoff.json")
    args=ap.parse_args()
    result=analyze()
    out=Path(args.out);out.parent.mkdir(exist_ok=True,parents=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print("PASS telemetry trade-off: 60 frozen runs, 10 paired seeds, 3 budgets")
    for item in result["descriptive_groups"]:
        print(item["method"],item["probes"],"timely",item["timely_ratio_mean"],"radio",item["radio_energy_J_mean"])
