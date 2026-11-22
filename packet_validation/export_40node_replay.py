#!/usr/bin/env python3
"""Export actual 40-node original Python controller decisions for packet-level Cooja replay.

IMPORTANT: controller observations still come from synthetic source transactions.
Cooja reports genuinely simulated packet transmissions/receptions of frozen decisions;
this is an open-loop transport/scheduler stress test, NOT a closed-loop ACR-MCR port.
"""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
from acr_mcr_v2 import Simulator,Config

def write_arrays(name,rows,n=40):
    return f"static const unsigned char {name}[REPLAY_ROUNDS][REPLAY_NODES] = {{\n"+ "".join(
        " {"+",".join(str(int(v)) for v in row)+"},\n" for row in rows
    )+"};\n"

def export(seed,method,scenario,rounds,output):
    if method not in ("POINT-EA","ACR-MCR"):
        raise ValueError("Both methods must use the exact original optimizer")
    if scenario not in ("S1","S5"):
        raise ValueError("Initial replay study restricts to S1 and S5")
    cfg=Config(rounds=rounds,nodes=40)
    sim=Simulator(seed,scenario,method,cfg,False)
    n=cfg.nodes
    records=[]
    assigns, nexthops, probes, enabled = [],[],[],[]
    reasons=[]
    for t in range(rounds):
        sim.fail_nodes(t)
        sim.environment(t)
        sim.predictions(t)
        plan,reason=sim.select(t)
        scheduled=dict((int(i),int(v)) for i,v,q in sim.probe_schedule(t) if q==0)
        is_active=sim.alive().astype(int).tolist()
        dest=[]
        nxt=[]
        probe=[]
        for i in range(n):
            ch=int(plan.assigned[i])
            if is_active[i] and ch>=0:
                dest.append(ch+1)
                if ch!=i:
                    step=ch+1
                else:
                    path=plan.paths.get(ch,[])
                    step=(path[1]+1) if len(path)>1 else 0
                nxt.append(step)
            else:
                dest.append(0)
                nxt.append(0)
            peer=scheduled.get(i)
            probe.append((peer+1) if peer is not None and is_active[i] else 0)
            records.append(dict(round=t+1, node=i+1, active=is_active[i],
                                assigned_head=dest[-1], next_hop=nxt[-1],
                                probe_target=probe[-1], trigger=reason))
        assigns.append(dest)
        nexthops.append(nxt)
        probes.append(probe)
        enabled.append(is_active)
        reasons.append(reason)
        # Compute the NEXT round's policy input using the ORIGINAL source
        # transaction model. This is not Cooja ACK feedback.
        sim.data_phase(t,plan)
        sim.probe_phase(t)
    output.mkdir(parents=True,exist_ok=True)
    header=("#ifndef ACR_40_REPLAY_HEADER\n#define ACR_40_REPLAY_HEADER\n"
            f"#define REPLAY_NODES 40\n#define REPLAY_ROUNDS {rounds}\n"
            f"#define REPLAY_SEED {seed}\n"
            f"#define REPLAY_METHOD {1 if method=='ACR-MCR' else 0}\n"
            f"#define REPLAY_SCENARIO {5 if scenario=='S5' else 1}\n"
            +write_arrays("route_heads",assigns)+write_arrays("route_next",nexthops)
            +write_arrays("probe_to",probes)+write_arrays("active_node",enabled)
            +"#endif\n")
    (output/"acr_40_plan.h").write_text(header)
    with (output/"plan.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]))
        w.writeheader()
        w.writerows(records)
    provenance=dict(
        seed=seed,method=method,scenario=scenario,nodes=40,rounds=rounds,
        source_sha256=hashlib.sha256((BASE/"acr_mcr_v2.py").read_bytes()).hexdigest(),
        protocol_sha256=hashlib.sha256((BASE/"PROTOCOL.md").read_bytes()).hexdigest(),
        schedule_sha256=hashlib.sha256(header.encode()).hexdigest(),
        controller_full_original_optimizer=True,
        controller_packet_feedback=False,
        transport_validation_only=True,
        controller_update_source="original Python synthetic model, never Cooja",
        original_default_rounds=160,
        frozen_original_source_not_modified=True,
        observed_searches=sim.searches,
        observed_fitness_evaluations=sim.fitness_calls,
        triggered={kind:reasons.count(kind) for kind in set(reasons)},
        limitation="Open-loop 40-node replay: not a full closed-loop packet-level ACR-MCR implementation",
    )
    (output/"positions.json").write_text(json.dumps({"sensors":sim.pos.tolist(),"sink":sim.sink.tolist()},indent=2)+"\n")
    (output/"provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
    print(json.dumps(provenance,indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--method",choices=["ACR-MCR","POINT-EA"],required=True)
    p.add_argument("--scenario",choices=["S1","S5"],required=True)
    p.add_argument("--rounds",type=int,choices=[16,40,160],default=40)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    export(a.seed,a.method,a.scenario,a.rounds,a.out)
