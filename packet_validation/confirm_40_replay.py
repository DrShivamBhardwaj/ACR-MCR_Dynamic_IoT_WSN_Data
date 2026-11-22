#!/usr/bin/env python3
"""Preregistered independent 40-node open-loop Cooja transport confirmation.

Do not call this a closed-loop ACR-MCR confirmation. Source: the registered
packet_validation/CONFIRMATION_40NODE_PROTOCOL_20261122.md.
"""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from scipy import stats
import numpy as np

SEEDS=list(range(8201,8211))
SCENARIOS=("S1","S5")
ENDPOINTS=("PDR_delta_ACR_minus_POINT","timely_delta_ACR_minus_POINT")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    data=json.loads(Path(args.input).read_text())
    if data["n_pairs"]!=20 or data["n_runs"]!=40:
        raise ValueError("Incomplete prespecified 40-cell confirmation")
    if data.get("closed_loop_packet_observation_used_by_controller") is not False:
        raise ValueError("Claim boundary changed")
    found={(x["scenario"],x["seed"]):x for x in data["paired_differences"]}
    expected={(sc,s) for sc in SCENARIOS for s in SEEDS}
    if set(found)!=expected:
        raise ValueError("Confirmation seeds or scenarios missing/incorrect")
    tests={}
    for endpoint in ENDPOINTS:
        by_seed=[]
        for seed in SEEDS:
            value=float(np.mean([found[(sc,seed)][endpoint] for sc in SCENARIOS]))
            by_seed.append(value)
        vals=np.asarray(by_seed,dtype=float)
        estimate=float(np.mean(vals))
        deviation=float(np.std(vals,ddof=1))
        if deviation<1e-15:
            ci=[estimate,estimate]
            raw_p=1.0 if abs(estimate)<1e-15 else None
            test_status=("all_pairs_tied" if raw_p==1.0 else
                         "zero_variance_nonzero_effect_requires_review")
        else:
            critical=float(stats.t.ppf(.975,len(vals)-1))
            margin=critical*deviation/math.sqrt(len(vals))
            ci=[estimate-margin,estimate+margin]
            raw_p=float(stats.ttest_1samp(vals,0.0,alternative="two-sided").pvalue)
            test_status="paired_t_test"
        tests[endpoint]=dict(n_seed_blocks=10,
            estimate_acr_minus_point=estimate,
            ci95=ci,
            two_sided_p_unadjusted=raw_p,
            by_seed=[{"seed":int(s),"paired_effect":float(v)} for s,v in zip(SEEDS,vals)],
            test_status=test_status)
    if any(t["two_sided_p_unadjusted"] is None for t in tests.values()):
        raise ValueError("Degenerate nonzero effect: human statistical audit required")
    ordering=sorted(ENDPOINTS,key=lambda e:tests[e]["two_sided_p_unadjusted"])
    adj=0.0
    for rank,endpoint in enumerate(ordering):
        value=min(1.0,(len(ENDPOINTS)-rank)*tests[endpoint]["two_sided_p_unadjusted"])
        adj=max(adj,value)
        tests[endpoint]["holm_adjusted_p"]=adj
    result=dict(
        protocol="CONFIRMATION_40NODE_PROTOCOL_20261122.md",
        scope="Independent fresh seeds for OPEN-LOOP controller schedule replay",
        independent_seed_count=10,
        scenarios=list(SCENARIOS),
        fixed_demand_per_scenario=40*160,
        methods=["POINT-EA","ACR-MCR"],
        sample_size_note="Seeds are units; S1 and S5 mean effects are aggregated within each seed.",
        tests=tests,
        confirmatory_packet_transport_complete=True,
        original_controller_closed_loop_validated=False,
        payload_fragmentation_500_bytes_implemented=False,
        claim="Evidence is limited to MAC transport given synthetic-policy replay; not an ACR-MCR full-controller performance claim.",
    )
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:{q:v for q,v in t.items() if q!="by_seed"} for k,t in tests.items()},indent=2))
if __name__=="__main__":main()
