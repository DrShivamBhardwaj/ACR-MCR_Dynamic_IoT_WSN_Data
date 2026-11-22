#!/usr/bin/env python3
"""Registered independent 40-node radio-control / 500B fragmentation analysis."""
import argparse,json,math,csv
from pathlib import Path
import numpy as np
from scipy import stats

SEEDS=tuple(range(9201,9211))
SCENARIOS=("S1","S5")
METHODS=("POINT-EA","ACR-MCR")
PRIMARY=("PDR_nominal","timely_ratio_nominal")
EXPLORATORY=("control_receptions","controller_control_radio_packets",
             "data_fragment_radio_callbacks","total_MAC_callbacks")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    files=sorted(Path(args.source).rglob("distributed_audit.json"))
    if len(files)!=40:raise ValueError(f"Expected all 40 registered audit reports, found {len(files)}")
    rows=[json.loads(f.read_text()) for f in files]
    expected={(sc,seed,m) for sc in SCENARIOS for seed in SEEDS for m in METHODS}
    index={(r["scenario"],int(r["seed"]),r["method"]):r for r in rows}
    if len(index)!=40 or set(index)!=expected:
        raise ValueError("Duplicate or missing scenario/seed/method cell")
    if len({r["code_source_sha256"] for r in rows})!=1:
        raise ValueError("Different transport-controller source hashes")
    for r in rows:
        if (r["verification"]!="PASS" or r["nodes"]!=40 or r["rounds"]!=160 or
            r["nominal_demand"]!=6400 or r["payload_integrity_errors"]!=0 or
            not r["complete_8_fragment_payload_verified"] or
            not r["sensor_routes_received_as_actual_control_packets"] or
            not r["controller_plans_through_sink_memory_only"]):
            raise ValueError("Incomplete 160-round fragment/control audit")
        if r["control_receptions"]>r["control_reception_opportunities"]:
            raise ValueError("Impossible control count")
        for m in PRIMARY:
            if not math.isfinite(r[m]): raise ValueError("Non-finite co-primary outcome")
    effect={}
    by_sc={}
    for sc in SCENARIOS:
        by_sc[sc]={}
        for m in PRIMARY:
            by_sc[sc][m]=sum(index[(sc,seed,"ACR-MCR")][m]-
                             index[(sc,seed,"POINT-EA")][m] for seed in SEEDS)/len(SEEDS)
    for metric in PRIMARY:
        vals=np.asarray([sum(index[(sc,seed,"ACR-MCR")][metric]-
                         index[(sc,seed,"POINT-EA")][metric] for sc in SCENARIOS)/len(SCENARIOS)
                         for seed in SEEDS],float)
        mean=float(vals.mean());std=float(vals.std(ddof=1))
        if std<1e-14:
            ci=[mean,mean];p=1. if abs(mean)<1e-14 else None
        else:
            margin=float(stats.t.ppf(.975,len(vals)-1))*std/math.sqrt(len(vals))
            ci=[mean-margin,mean+margin]
            p=float(stats.ttest_1samp(vals,0).pvalue)
        if p is None:raise ValueError("Degenerate nonzero primary effects")
        effect[metric]=dict(estimated_acr_minus_point=mean,ci95=ci,
            p_unadjusted=p,by_independent_seed=dict(zip(map(str,SEEDS),vals.tolist())))
    rolling=0
    for i,m in enumerate(sorted(PRIMARY,key=lambda k:effect[k]["p_unadjusted"])):
        rolling=max(rolling,min(1.0,(2-i)*effect[m]["p_unadjusted"]))
        effect[m]["holm_adjusted_p"]=rolling
    result=dict(
       status="PASS",registered_runs=40,independent_seed_blocks=len(SEEDS),
       seeds=list(SEEDS),scenarios=list(SCENARIOS),
       estimates=effect,scenario_descriptive_effects=by_sc,
       original_payload_bytes=500,
       route_installed_only_by_radio=True,
       original_optimizer_feedback_from_cooja_MAC=True,
       external_controller_at_sink=True,
       physical_radio_energy=False,external_SNR_PER_calibration=False,
       original_frozen_model_unmodified=True,
       important_limitations=[
         "Packet observations and sensor control use Cooja, not a physical testbed",
         "Centralized Python optimizer plans are written to sink memory without measured CPU cost",
         "ENDERGEST ticks are durations, not calibrated Joules",
         "Static Cooja loss parameters are not observed RSSI/noise/physical PER",
         "Original offered-load timing and full interference law not reproduced"
       ],all_run_audits=rows)
    out=Path(args.out);out.parent.mkdir(exist_ok=True,parents=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    with out.with_suffix(".csv").open("w",newline="") as f:
        cols=["scenario","seed","method","PDR_nominal","timely_ratio_nominal",
              "source_requests","valid_500byte_reassemblies","control_receptions",
              "controller_control_radio_packets","total_MAC_callbacks"]
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        w.writerows([{k:r[k] for k in cols} for r in rows])
    print(json.dumps({k:{q:v for q,v in e.items() if q!="by_independent_seed"} for k,e in effect.items()},indent=2))
if __name__=="__main__":main()
