#!/usr/bin/env python3
"""Audit 360-cell registered independent paired generalisation evidence."""
import argparse,csv,json,math
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy import stats

SEEDS=tuple(range(9701,9711))
SCENARIOS=("S0","S1","S2","S3","S4","S5")
SIZES=(40,80,120)
METHODS=("POINT-EA","ACR-MCR")
PRIMARY=("timely_ratio","service_violation_rate")
EXPLORATORY=("PDR","radio_energy_J","energy_probe_J","energy_per_delivered_mJ")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--directory",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    rows=[]
    files=sorted(Path(a.directory).rglob("cell_*.jsonl"))
    if len(files)!=18:raise ValueError(f"Expected 18 scenario x size cell files; got {len(files)}")
    for file in files:
        rows.extend(json.loads(line) for line in file.read_text().splitlines() if line.strip())
    expected={(sc,n,seed,method) for sc in SCENARIOS for n in SIZES for seed in SEEDS for method in METHODS}
    got={(r["scenario"],r["nodes"],r["seed"],r["method"]) for r in rows}
    if len(rows)!=360 or got!=expected:
        raise ValueError(f"Registered matrix incomplete/duplicated {len(rows)} vs {len(expected)}")
    if len({r["original_code_sha256"] for r in rows})!=1 or len({r["registered_protocol_sha256"] for r in rows})!=1:
        raise ValueError("Mixed controller/protocol source hashes")
    if any(r["rounds"]!=160 or r["probes"]!=1 for r in rows):
        raise ValueError("Unregistered simulator config")
    for r in rows:
        for m in PRIMARY:
            if r[m] is None or not math.isfinite(float(r[m])):
                raise ValueError(f"Undefined primary outcome {m}")
    idx={(r["scenario"],r["nodes"],r["seed"],r["method"]):r for r in rows}
    diffs={}
    for sc in SCENARIOS:
        for n in SIZES:
            for seed in SEEDS:
                arow,brow=(idx[(sc,n,seed,m)] for m in METHODS)
                diffs[(sc,n,seed)]={k:(float(brow[k])-float(arow[k]) if
                    brow[k] is not None and arow[k] is not None else None)
                    for k in PRIMARY+EXPLORATORY}
    results={}
    for m in PRIMARY:
        per_seed=np.array([np.mean([diffs[(sc,n,s)][m] for sc in SCENARIOS for n in SIZES]) for s in SEEDS],float)
        estimate=float(per_seed.mean())
        sd=float(per_seed.std(ddof=1))
        if sd<1e-14:
            ci=[estimate,estimate]
            pvalue=1.0 if abs(estimate)<1e-14 else None
        else:
            delta=float(stats.t.ppf(.975,9))*sd/math.sqrt(10)
            ci=[estimate-delta,estimate+delta]
            pvalue=float(stats.ttest_1samp(per_seed,0).pvalue)
        if pvalue is None: raise ValueError("Degenerate nonzero primary effect needs manual review")
        results[m]=dict(
            signed_effect_acr_minus_point=estimate,
            ci95=ci,two_sided_p=pvalue,
            by_independent_seed={str(s):float(v) for s,v in zip(SEEDS,per_seed)},
            independent_n=10)
    rank=sorted(PRIMARY,key=lambda m:results[m]["two_sided_p"])
    running=0
    for i,m in enumerate(rank):
        running=max(running,min(1.0,(len(rank)-i)*results[m]["two_sided_p"]))
        results[m]["holm_adjusted_p"]=running
    cells=[]
    for sc in SCENARIOS:
        for n in SIZES:
            cell=dict(scenario=sc,nodes=n,n=10)
            for metric in PRIMARY+EXPLORATORY:
                vv=[diffs[(sc,n,s)][metric] for s in SEEDS]
                cell[metric+"_mean_acr_minus_point"]=None if any(v is None for v in vv) else sum(vv)/10
            cells.append(cell)
    summary=dict(
        scientific_scope="Generalisation across original SYNTHETIC model, not external packet/hardware evidence",
        status="PASS",registered_cell_count=360,
        independent_seeds=list(SEEDS),model_sizes=list(SIZES),
        scenarios=list(SCENARIOS),
        code_sha256=rows[0]["original_code_sha256"],
        registered_protocol_sha256=rows[0]["registered_protocol_sha256"],
        primary_effects=results,
        exploratory_by_condition=cells,
        limitations="Same simulator assumptions across all 360 runs. Not independent physical communication calibration.")
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(summary,indent=2)+"\n")
    with out.with_suffix(".csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(cells[0]))
        w.writeheader();w.writerows(cells)
    print(json.dumps({m:results[m] for m in PRIMARY},indent=2))
if __name__=="__main__": main()
