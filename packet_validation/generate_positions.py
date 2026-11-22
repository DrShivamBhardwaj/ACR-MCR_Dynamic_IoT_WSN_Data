#!/usr/bin/env python3
"""Generate original 40-sensor positions without running synthetic transactions."""
import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P))
from acr_mcr_v2 import Simulator,Config
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--seed",type=int,required=True)
    ap.add_argument("--scenario",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    # Construct topology only. No data/probe/route transactions are run.
    sim=Simulator(a.seed,a.scenario,"POINT-EA",Config(nodes=40,rounds=160))
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"sensors":sim.pos.tolist(),"sink":sim.sink.tolist(),
                              "source":"Original topology initialization only",
                              "packet_outcomes_generated":False},indent=2)+"\n")
    print(f"FORTY_NODE_TOPOLOGY_ONLY seed={a.seed} -> {out}")
if __name__=="__main__":main()
