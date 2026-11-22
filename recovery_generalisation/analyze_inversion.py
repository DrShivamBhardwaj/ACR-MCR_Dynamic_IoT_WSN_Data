#!/usr/bin/env python3
"""Preregistered two-primary reliability/deadline heldout test."""
import argparse,json,math
from pathlib import Path
from collections import defaultdict
import numpy as np
from scipy import stats
SEEDS=range(9951,9961)
SCENARIOS=("S0","S1","S2","S3","S4","S5")
PRIMARY=("PDR","timely_ratio")
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--directory",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    files=sorted(Path(a.directory).rglob("inversion_*.jsonl"))
    if len(files)!=6: raise ValueError("Six registered scenario files required")
    rows=[json.loads(l) for f in files for l in f.read_text().splitlines() if l.strip()]
    expected={(sc,s,m) for sc in SCENARIOS for s in SEEDS for m in ("POINT-EA","ACR-MCR")}
    index={(r["scenario"],r["seed"],r["method"]):r for r in rows}
    if len(rows)!=120 or len(index)!=120 or set(index)!=expected:
        raise ValueError("Incomplete 120-run registered cohort")
    if len({x["source_sha256"] for x in rows})!=1 or len({x["registered_protocol_sha256"] for x in rows})!=1:
        raise ValueError("Mixed frozen source/protocol")
    if any(r["nodes"]!=120 or r["rounds"]!=160 or r["probes"]!=1 for r in rows):
        raise ValueError("Registered configuration mismatch")
    results={}
    for m in PRIMARY:
        values=[]
        for seed in SEEDS:
            dd=[float(index[(sc,seed,"ACR-MCR")][m])-float(index[(sc,seed,"POINT-EA")][m]) for sc in SCENARIOS]
            values.append(sum(dd)/len(dd))
        a0=np.asarray(values,float)
        mean=float(a0.mean())
        std=float(a0.std(ddof=1))
        if std<1e-14:
            low=high=mean;p=1. if abs(mean)<1e-14 else None
        else:
            delta=float(stats.t.ppf(.975,len(a0)-1))*std/math.sqrt(len(a0))
            low,high=mean-delta,mean+delta
            p=float(stats.ttest_1samp(a0,0).pvalue)
        if p is None:raise ValueError("Zero variance and nonzero effect")
        results[m]=dict(effect_acr_minus_point=mean,ci95=[low,high],
                        p_two_sided=p,by_independent_seed=dict(zip(map(str,SEEDS),values)))
    rolling=0.
    for i,m in enumerate(sorted(PRIMARY,key=lambda k:results[k]["p_two_sided"])):
        rolling=max(rolling,min(1.0,(2-i)*results[m]["p_two_sided"]))
        results[m]["holm_adjusted_p"]=rolling
    is_inversion=(results["PDR"]["effect_acr_minus_point"]>0
        and results["timely_ratio"]["effect_acr_minus_point"]<0
        and results["PDR"]["holm_adjusted_p"]<.05
        and results["timely_ratio"]["holm_adjusted_p"]<.05)
    report=dict(status="PASS",registered_cohort_runs=120,independent_seed_count=10,
                studied_nodes=120,regimes=list(SCENARIOS),effects=results,
                independently_confirmed_inversion=bool(is_inversion),
                scientific_boundary="Within original synthetic simulator only; no causal source for effect established.",
                code_sha256=rows[0]["source_sha256"],protocol_sha256=rows[0]["registered_protocol_sha256"])
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:{q:v for q,v in x.items() if q!="by_independent_seed"} for k,x in results.items()},indent=2))
    print("CONFIRMED_RELIABILITY_DEADLINE_INVERSION",is_inversion)
if __name__=="__main__":main()
