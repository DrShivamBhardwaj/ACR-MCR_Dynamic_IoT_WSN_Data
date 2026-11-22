#!/usr/bin/env python3
"""Pre-registered paired 10-seed Cooja packet-feedback closed-loop analysis."""
import argparse,csv,json,math
from pathlib import Path
from scipy import stats
import numpy as np
SEEDS=range(8901,8911)
SCENARIOS=("S1","S5")
METHODS=("POINT-EA","ACR-MCR")
PRIMARY=("PDR_on_all_demand","timely_ratio_on_all_demand")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--directory",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    files=sorted(Path(a.directory).rglob("closedloop_audit.json"))
    if len(files)!=40: raise ValueError(f"Expected 40 unique auditor outputs, got {len(files)}")
    rows=[json.loads(f.read_text()) for f in files]
    indexed={(r["scenario"],r["seed"],r["method"]):r for r in rows}
    expected={(sc,s,m) for sc in SCENARIOS for s in SEEDS for m in METHODS}
    if len(indexed)!=40 or set(indexed)!=expected:raise ValueError("Missing or duplicated registered cases")
    for r in rows:
        if r["verification"]!="PASS" or r["feedback_rounds"]!=160 or r["nominal_demand"]!=6400:
            raise ValueError("Incomplete closed-loop case")
        if r["external_control"]!="simulator-memory injection (no actual control packets)" or r["original_payload_500B"]:
            raise ValueError("Scope changed: incorrect distribution/fragmentation claim")
    paired={}
    for sc in SCENARIOS:
        for seed in SEEDS:
            a0=indexed[(sc,seed,"POINT-EA")]
            b0=indexed[(sc,seed,"ACR-MCR")]
            paired[(sc,seed)]={m:b0[m]-a0[m] for m in PRIMARY}
    tests={}
    for m in PRIMARY:
        vals=np.asarray([np.mean([paired[(sc,s)][m] for sc in SCENARIOS]) for s in SEEDS],float)
        est=float(vals.mean());sd=float(vals.std(ddof=1))
        if sd<1e-14:
            ci=[est,est];pvalue=1.0 if abs(est)<1e-14 else None
        else:
            delta=float(stats.t.ppf(.975,len(vals)-1))*sd/math.sqrt(len(vals))
            ci=[est-delta,est+delta]
            pvalue=float(stats.ttest_1samp(vals,0.).pvalue)
        if pvalue is None:raise ValueError("Zero variance nonzero effect requires manual review")
        tests[m]=dict(estimate_acr_minus_point=est,ci95=ci,p_unadjusted=pvalue,
                      by_seed=[{"seed":int(s),"effect":float(v)} for s,v in zip(SEEDS,vals)])
    running=0.
    for i,m in enumerate(sorted(PRIMARY,key=lambda x:tests[x]["p_unadjusted"])):
        running=max(running,min(1.,(2-i)*tests[m]["p_unadjusted"]))
        tests[m]["p_holm"]=running
    report=dict(
        status="PASS",
        n_independent_seed_blocks=10,n_cases=40,n_paired_scenario_seed_cells=20,
        source="Continuous Cooja MAC simulation with round-by-round feedback to original Python optimizer",
        controller_feedback_from_cooja=True,
        centralized_memory_injection=True,
        distributed_control_validated=False,
        original_payload_fragmentation_validated=False,
        physical_RF_calibration=False,
        original_frozen_1280_run_study_unchanged=True,
        main_results=tests,
        exploratory_by_scenario=[
            dict(scenario=sc,metric=m,mean_acr_minus_point=float(np.mean([paired[(sc,s)][m] for s in SEEDS])))
            for sc in SCENARIOS for m in PRIMARY
        ],
        warning="Does not establish full distributed original ACR-MCR or field generalisation."
    )
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    with out.with_suffix(".csv").open("w",newline="") as f:
        keys=["scenario","seed","method","PDR_on_all_demand","timely_ratio_on_all_demand",
              "requests_queued","unique_sink","timely500","observed_MAC_callbacks",
              "actual_probe_callbacks","controller_searches"]
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
        w.writerows([{k:r[k] for k in keys} for r in rows])
    print(json.dumps({m:{k:v for k,v in t.items() if k!="by_seed"} for m,t in tests.items()},indent=2))
if __name__=="__main__":main()
