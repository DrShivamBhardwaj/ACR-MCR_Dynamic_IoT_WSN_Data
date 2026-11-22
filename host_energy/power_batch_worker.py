#!/usr/bin/env python3
"""Original, frozen ACR-MCR vs POINT-EA computation in dedicated process."""
import argparse,hashlib,json,time,sys
from pathlib import Path
DATA=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(DATA))
from acr_mcr_v2 import Simulator,Config
SEEDS=tuple(range(10301,10311))
SC=("S1","S5")
SHA="3f134a8826525215f7cf2ff307bab3893c0d64b050f742bdc3c250b1c0302ea4"
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--method",choices=("POINT-EA","ACR-MCR"),required=True)
    parser.add_argument("--repeats",type=int,default=5)
    a=parser.parse_args()
    assert hashlib.sha256((DATA/"acr_mcr_v2.py").read_bytes()).hexdigest()==SHA
    t0=time.perf_counter()
    controller=0.;n=0;fitness=0
    for rep in range(a.repeats):
        for scenario in SC:
            for seed in SEEDS:
                s=Simulator(seed,scenario,a.method,Config(nodes=40,rounds=160,probes=1))
                r=s.run()
                controller+=float(r["controller_seconds"])
                fitness+=int(r["fitness_evaluations"])
                n+=1
    elapsed=time.perf_counter()-t0
    print(json.dumps(dict(method=a.method,cases=n,seeds=list(SEEDS),
      source_sha256=SHA,scenarios=list(SC),
      controller_wall_seconds_sum=controller,
      whole_program_wall_seconds=elapsed,
      fitness_evaluations_sum=fitness,
      physical_Apple_M1_electrical_energy_joules=None)))
if __name__=="__main__":main()
