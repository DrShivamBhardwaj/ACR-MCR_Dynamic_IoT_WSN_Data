#!/usr/bin/env python3
"""Independent original-simulator generalisation run; no source modifications."""
import argparse,hashlib,json,platform,sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from acr_mcr_v2 import Simulator,Config
SCENARIOS=("S0","S1","S2","S3","S4","S5")
SIZES=(40,80,120)
SEEDS=tuple(range(9701,9711))
METHODS=("POINT-EA","ACR-MCR")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--scenario",choices=SCENARIOS,required=True)
    p.add_argument("--nodes",type=int,choices=SIZES,required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    sha=hashlib.sha256((ROOT/"acr_mcr_v2.py").read_bytes()).hexdigest()
    protocol_sha=hashlib.sha256((ROOT/"recovery_generalisation/REGISTERED_PROTOCOL_20261122.md").read_bytes()).hexdigest()
    records=[]
    for seed in SEEDS:
        for method in METHODS:
            cfg=Config(nodes=a.nodes,rounds=160,probes=1)
            sim=Simulator(seed,a.scenario,method,cfg=cfg,diagnostics=False)
            r=sim.run()
            if int(r["seed"])!=seed or int(r["nodes"])!=a.nodes:
                raise RuntimeError("Simulator returned mismatched data")
            row=dict(r,
                group="rejection_recovery_20261122_generalisation",
                original_code_sha256=sha,
                registered_protocol_sha256=protocol_sha,
                independent_seed_unit=seed,
                python_version=platform.python_version(),numpy_version=np.__version__,
                limitations="Synthetic half-duplex transaction model; not Cooja or hardware")
            records.append(row)
            print(f"COMPLETE {a.scenario} N={a.nodes} seed={seed} method={method} timely={r['timely_ratio']:.6f}",flush=True)
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text("\n".join(json.dumps(r,allow_nan=False) for r in records)+"\n")
    print(f"OUTPUT {out}: {len(records)} immutable original-controller runs",flush=True)
if __name__=="__main__": main()
