#!/usr/bin/env python3
"""Held-out signed policy-by-size interaction; no cherry-picking."""
import argparse,json,math
from pathlib import Path
import numpy as np
from scipy import stats
SEEDS=range(9901,9911)
SCENARIOS=("S0","S1","S2","S3","S4","S5")
SIZES=(40,120)
METHODS=("POINT-EA","ACR-MCR")
METRICS=("timely_ratio","service_violation_rate")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--directory",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    files=sorted(Path(a.directory).rglob("size_*.jsonl"))
    if len(files)!=12:raise ValueError(f"Expected 12 cell files, got {len(files)}")
    rows=[json.loads(line) for f in files for line in f.read_text().splitlines() if line.strip()]
    expected={(sc,n,s,m) for sc in SCENARIOS for n in SIZES for s in SEEDS for m in METHODS}
    indexed={(r["scenario"],r["nodes"],r["seed"],r["method"]):r for r in rows}
    if len(rows)!=240 or len(indexed)!=240 or set(indexed)!=expected:
        raise ValueError("Incomplete registered 240-run matrix")
    if len({r["original_source_sha256"] for r in rows})!=1 or len({r["registered_protocol_sha256"] for r in rows})!=1:
        raise ValueError("Mixed source/protocol hashes")
    result={}
    for metric in METRICS:
        vals=[]
        details=[]
        for seed in SEEDS:
            diffs=[]
            for sc in SCENARIOS:
                by_size={}
                for size in SIZES:
                    ac=indexed[(sc,size,seed,"ACR-MCR")][metric]
                    po=indexed[(sc,size,seed,"POINT-EA")][metric]
                    if ac is None or po is None:raise ValueError("Undefined primary endpoint")
                    by_size[size]=float(ac)-float(po)
                diff=by_size[120]-by_size[40]
                diffs.append(diff)
                details.append(dict(seed=seed,scenario=sc,delta_at40=by_size[40],
                                    delta_at120=by_size[120],interaction=diff))
            vals.append(float(np.mean(diffs)))
        arr=np.asarray(vals,float)
        mean=float(arr.mean());sd=float(arr.std(ddof=1))
        if sd<1e-14:
            ci=[mean,mean];p=1.0 if abs(mean)<1e-14 else None
        else:
            t=float(stats.t.ppf(.975,9))
            ci=[mean-t*sd/math.sqrt(10),mean+t*sd/math.sqrt(10)]
            p=float(stats.ttest_1samp(arr,0).pvalue)
        if p is None:raise ValueError("Zero variance with nonzero effect")
        result[metric]=dict(
          interaction_N120_minus_N40=mean,ci95=ci,two_sided_p=p,
          paired_independent_seed_count=10,by_seed={str(i):v for i,v in zip(SEEDS,vals)},
          exploratory_per_scenario=details)
    ranking=sorted(METRICS,key=lambda m:result[m]["two_sided_p"])
    carry=0
    for i,m in enumerate(ranking):
        carry=max(carry,min(1.0,(2-i)*result[m]["two_sided_p"]))
        result[m]["holm_adjusted_p"]=carry
    report=dict(
      status="PASS",confirmatory_interaction=True,
      source_360_run_discovery_not_pooled=True,independent_seeds=list(SEEDS),
      registered_cases=240,regimes=list(SCENARIOS),nodes=list(SIZES),
      tests=result,scientific_scope="Original synthetic simulator only",
      novelty_limit="A confirmed effect modification is not proof the controller integration is previously unknown.",
      physical_validation=False)
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:{z:v for z,v in t.items() if z not in ("by_seed","exploratory_per_scenario")} for k,t in result.items()},indent=2))
if __name__=="__main__":main()
