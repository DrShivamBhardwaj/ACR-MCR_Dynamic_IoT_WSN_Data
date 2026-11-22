#!/usr/bin/env python3
"""Original-source held-out 120-node reliability/deadline replication."""
import argparse,hashlib,json,math,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from acr_mcr_v2 import Simulator,Config
SCENARIOS=("S0","S1","S2","S3","S4","S5")
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--scenario",choices=SCENARIOS,required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    sha=hashlib.sha256((ROOT/"acr_mcr_v2.py").read_bytes()).hexdigest()
    proto=hashlib.sha256((ROOT/"recovery_generalisation/REGISTERED_INVERSION_20261122.md").read_bytes()).hexdigest()
    rows=[]
    for seed in range(9951,9961):
        for method in ("POINT-EA","ACR-MCR"):
            s=Simulator(seed,a.scenario,method,Config(nodes=120,rounds=160,probes=1))
            r=s.run()
            row=dict(r,cohort="heldout_reliability_deadline_inversion",source_sha256=sha,
                     registered_protocol_sha256=proto)
            for key,value in list(row.items()):
                if isinstance(value,(float,np.floating)) and not math.isfinite(float(value)):
                    if key in ("PDR","timely_ratio"):raise ValueError("Non-finite co-primary outcome")
                    row[key]=None
            rows.append(row)
            print(f"FINISHED inversion {a.scenario} seed={seed} method={method} PDR={r['PDR']:.6f} timely={r['timely_ratio']:.6f}",flush=True)
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text("\n".join(json.dumps(row,allow_nan=False) for row in rows)+"\n")
if __name__=="__main__":main()
