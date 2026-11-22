#!/usr/bin/env python3
"""Prespecified held-out component ablation, Holm family size=3."""
import argparse,json,math
from pathlib import Path
import numpy as np
from scipy import stats
S=("S0","S1","S2","S3","S4","S5")
SEEDS=range(9971,9981)
METHODS=("POINT-EA","ACI-PER","ACI-EVENT","ACR-MCR")
CONTRASTS=(
  ("ACI-PER","POINT-EA","conformal_bounds_vs_point"),
  ("ACI-EVENT","ACI-PER","event_search_increment"),
  ("ACR-MCR","ACI-EVENT","tail_regularizer_increment"),
)
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--directory",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    fs=sorted(Path(a.directory).rglob("ablation_*.jsonl"))
    if len(fs)!=6:raise ValueError("Six registered scenario artifacts required")
    rows=[json.loads(l) for f in fs for l in f.read_text().splitlines() if l.strip()]
    d={(r["scenario"],r["seed"],r["method"]):r for r in rows}
    exp={(sc,seed,m) for sc in S for seed in SEEDS for m in METHODS}
    if len(rows)!=240 or len(d)!=240 or set(d)!=exp:
        raise ValueError("Incomplete or duplicate registered component matrix")
    if len({r["original_sha256"] for r in rows})!=1 or len({r["registered_protocol_sha256"] for r in rows})!=1:
        raise ValueError("Mixed source/protocol")
    if any(r["nodes"]!=120 or r["rounds"]!=160 or r["probes"]!=1 for r in rows):
        raise ValueError("Input config drift")
    tests={}
    for a_name,b_name,title in CONTRASTS:
        values=np.asarray([np.mean([
           float(d[(sc,seed,a_name)]["timely_ratio"])-float(d[(sc,seed,b_name)]["timely_ratio"])
           for sc in S]) for seed in SEEDS],float)
        mean=float(values.mean()); sd=float(values.std(ddof=1))
        if sd<1e-14:
            ci=[mean,mean];pval=1.0 if abs(mean)<1e-14 else None
        else:
            margin=float(stats.t.ppf(.975,9))*sd/math.sqrt(10)
            ci=[mean-margin,mean+margin]
            pval=float(stats.ttest_1samp(values,0).pvalue)
        if pval is None:raise ValueError("Zero variance nonzero test")
        tests[title]=dict(
          intervention=a_name,comparator=b_name,outcome="timely_ratio",
          signed_difference=mean,ci95=ci,p_two_sided=pval,
          per_independent_seed=dict(zip(map(str,SEEDS),values.tolist())))
    order=sorted(tests,key=lambda k:tests[k]["p_two_sided"])
    rolling=0.
    for i,name in enumerate(order):
        rolling=max(rolling,min(1.,(3-i)*tests[name]["p_two_sided"]))
        tests[name]["holm_adjusted_p"]=rolling
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    payload=dict(status="PASS",registered_outcome_runs=240,independent_seeds=list(SEEDS),
       methods=list(METHODS),regimes=list(S),test_family=tests,
       scientific_scope="Original simulation only; component isolation is conditional on the frozen model",
       physical_or_cooja_validation=False,original_source_sha256=rows[0]["original_sha256"])
    out.write_text(json.dumps(payload,indent=2)+"\n")
    print(json.dumps({k:{q:v for q,v in t.items() if q!="per_independent_seed"} for k,t in tests.items()},indent=2))
if __name__=="__main__":main()
