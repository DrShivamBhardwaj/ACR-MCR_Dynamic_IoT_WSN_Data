#!/usr/bin/env python3
"""Boundary-case parity beyond normally successful network-state candidates."""
import hashlib,json,math,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from acr_mcr_v2 import Simulator,Config
from test_optimizer_parity import get_lib,make_ctx,compare
def build_state(seed,method):
    sim=Simulator(seed,"S5",method,Config(nodes=40,rounds=45))
    for t in range(25):
        sim.fail_nodes(t);sim.environment(t);sim.predictions(t)
        if t==24:break
        p,_=sim.select(t);sim.data_phase(t,p);sim.probe_phase(t)
    assert sim.disabled.any(), "Expected explicit S5 node failure"
    assert not sim.alive().all()
    sim.stress_fields(24)
    return sim
def main():
    lib=get_lib()
    rows=[]
    maxerr=0.
    for seed in range(9411,9416):
      for method in ("POINT-EA","ACR-MCR"):
        s=build_state(seed,method)
        alive=s.active
        heads_sets=[list(alive[:4]),list(alive[-4:])]
        if s.heads is not None:
            heads_sets.append([int(x) for x in s.heads])
        for j,heads in enumerate(heads_sets):
            ctx,keep=make_ctx(s);err=[]
            compare(s,lib,ctx,heads,f"{seed}/{method}/failed_nodes_{j}",err)
            maxerr=max(maxerr,*err)
            rows.append(dict(seed=seed,method=method,
                case="explicit_S5_failed_nodes",candidate=j,
                dead_nodes=int(s.disabled.sum()),error=max(err)))
        # No sink path case is separate from total node failure.
        saved=s.edge_cost.copy()
        s.edge_cost[:,s.n]=np.inf
        ctx,keep=make_ctx(s);err=[]
        compare(s,lib,ctx,list(alive[:4]),f"{seed}/{method}/no_sink_path",err)
        maxerr=max(maxerr,*err)
        rows.append(dict(seed=seed,method=method,
             case="all_sink_edges_removed",error=max(err)))
        s.edge_cost=saved
    assert maxerr<1e-9
    result=dict(status="PASS_ORIGINAL_C_BOUNDARY_PARITY",cases=len(rows),
       seed_count=5,method_count=2,unique_fail_cases=10,
       max_objective_absolute_error=maxerr,
       source_sha256=hashlib.sha256((ROOT/"acr_mcr_v2.py").read_bytes()).hexdigest(),
       limitations="Explicit failed-node and no-sink-path fixed-state objective parity only; no hardware controller integration, no stochastic NumPy RNG port.",
       records=rows)
    (HERE/"optimizer_failure_parity.json").write_text(json.dumps(result,indent=2)+"\n")
    print("FAILURE_AND_DISCONNECT_PARITY_PASS",result["cases"],maxerr)
if __name__=="__main__":main()
