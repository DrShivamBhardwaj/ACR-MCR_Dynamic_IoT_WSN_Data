#!/usr/bin/env python3
"""Independent size-interaction confirmation cohort, not discovery cohort."""
import argparse,hashlib,json,math,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from acr_mcr_v2 import Simulator,Config
SEEDS=range(9901,9911)
SCENARIOS=("S0","S1","S2","S3","S4","S5")
SIZES=(40,120)
METHODS=("POINT-EA","ACR-MCR")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--scenario",choices=SCENARIOS,required=True)
    p.add_argument("--nodes",type=int,choices=SIZES,required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    script=hashlib.sha256((ROOT/"acr_mcr_v2.py").read_bytes()).hexdigest()
    protocol=hashlib.sha256((ROOT/"recovery_generalisation/REGISTERED_SCALE_INTERACTION_20261122.md").read_bytes()).hexdigest()
    records=[]
    for seed in SEEDS:
        for method in METHODS:
            sim=Simulator(seed,a.scenario,method,Config(nodes=a.nodes,rounds=160,probes=1))
            r=sim.run()
            record=dict(r,independent_confirmation_cohort="scale_9901_9910",
                        original_source_sha256=script,registered_protocol_sha256=protocol)
            for k,v in list(record.items()):
                if isinstance(v,(float,np.floating)) and not math.isfinite(float(v)):
                    if k in ("timely_ratio","service_violation_rate"):raise ValueError(f"Undefined primary metric {k}")
                    record[k]=None
            records.append(record)
            print(f"COMPLETED size confirmation S={a.scenario} N={a.nodes} seed={seed} method={method}",flush=True)
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text("\n".join(json.dumps(r,allow_nan=False) for r in records)+"\n")
if __name__=="__main__":main()
