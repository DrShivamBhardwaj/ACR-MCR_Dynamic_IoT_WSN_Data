#!/usr/bin/env python3
"""Held-out component ablations using only ORIGINAL methods."""
import argparse,hashlib,json,math,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from acr_mcr_v2 import Simulator,Config
METHODS=("POINT-EA","ACI-PER","ACI-EVENT","ACR-MCR")
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scenario",choices=["S0","S1","S2","S3","S4","S5"],required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    sha=hashlib.sha256((ROOT/"acr_mcr_v2.py").read_bytes()).hexdigest()
    protocol=hashlib.sha256((ROOT/"recovery_generalisation/REGISTERED_COMPONENT_ABLATION_20261122.md").read_bytes()).hexdigest()
    rows=[]
    for seed in range(9971,9981):
        for method in METHODS:
            s=Simulator(seed,a.scenario,method,Config(nodes=120,rounds=160,probes=1))
            r=s.run()
            rec=dict(r,heldout_ablation="original_components_9971_9980",original_sha256=sha,
                     registered_protocol_sha256=protocol)
            for k,v in list(rec.items()):
                if isinstance(v,(float,np.floating)) and not math.isfinite(float(v)):
                    if k in ("timely_ratio","PDR"):raise ValueError("Undefined primary experiment outcome")
                    rec[k]=None
            rows.append(rec)
            print(f"FINISHED component {a.scenario} seed={seed} method={method} timely={r['timely_ratio']:.5f}",flush=True)
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text("\n".join(json.dumps(x,allow_nan=False) for x in rows)+"\n")
if __name__=="__main__":main()
