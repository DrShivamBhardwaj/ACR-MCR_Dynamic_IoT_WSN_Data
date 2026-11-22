#!/usr/bin/env python3
"""Export exact frozen original Python ACR-MCR/POINT state to immutable Flash.

All original model matrices, NumPy-generated candidate genotypes and exact
risk resampling indices are stored as a test fixture, not observed from a
physical 40-node network. M3 executes the portable C deterministic kernel.
"""
import argparse,copy,hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from acr_mcr_v2 import Simulator,Config,rng_for
from test_optimizer_parity import python_trace
def scalar(x):
    x=float(x)
    return "INFINITY" if np.isposinf(x) else ("-INFINITY" if np.isneginf(x) else x.hex())
def declare(name,values,ctype="double",perline=8):
    values=list(values)
    items=[str(int(v)) if ctype=="uint8_t" else scalar(v) for v in values]
    rows=[", ".join(items[i:i+perline]) for i in range(0,len(items),perline)]
    return f"static const {ctype} {name}[{len(items)}] = {{\n  "+",\n  ".join(rows)+"\n};\n"
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--method",choices=("ACR-MCR","POINT-EA"),required=True)
    p.add_argument("--seed",type=int,default=9401)
    p.add_argument("--scenario",choices=("S1","S5"),default="S1")
    p.add_argument("--round",type=int,default=20)
    p.add_argument("--tag",default="")
    args=p.parse_args()
    s=Simulator(args.seed,args.scenario,args.method,Config(nodes=40,rounds=45))
    for t in range(args.round+1):
        s.fail_nodes(t);s.environment(t);s.predictions(t)
        if t==args.round:break
        plan,_=s.select(t)
        s.data_phase(t,plan);s.probe_phase(t)
    ref=copy.deepcopy(s)
    pybest,trace=python_trace(ref,args.round)
    risk=ref.stress_c is not None
    scores=np.asarray(ref.cal.scores,dtype=float)
    idx=None
    if risk:
        idx=rng_for(args.seed,41,args.round).integers(0,len(scores),
                        (ref.cfg.tail_samples,ref.n,ref.n+1))
        np.testing.assert_allclose(ref.stress_c,
          np.clip(ref.cost_pred[None]+ref.cost_scale[None]*scores[idx][...,0],1.,5.),
          atol=0,rtol=1e-14)
        np.testing.assert_allclose(ref.stress_d,
          np.maximum(1.,ref.delay_pred[None]+ref.delay_scale[None]*scores[idx][...,1]),
          atol=0,rtol=1e-14)
        if len(scores)>512:raise ValueError("Score index exceeds 9-bit storage")
    name="m3fixture_"+args.method.replace("-","_").lower()+("_"+args.tag if args.tag else "")
    out=HERE/"m3_kernel_fixtures"/name
    out.mkdir(exist_ok=True,parents=True)
    arrays={
       "edge_cost":ref.edge_cost,"attempt_mean":ref.attempt_mean,
       "tx_energy":ref.tx_energy,"distance":ref.distance,
       "d_used":ref.d_used,"energy":ref.energy,
       "cost_pred":ref.cost_pred,"cost_scale":ref.cost_scale,
       "delay_pred":ref.delay_pred,"delay_scale":ref.delay_scale}
    pieces=["/* Generated source from original acr_mcr_v2.py, read-only M3 test fixture.",
            "   No empirical physical feedback is included in these source matrices. */",
            "#include <math.h>","#include <stdint.h>"]
    for key,values in arrays.items():
        pieces.append(declare("fx_"+key,np.asarray(values).ravel()))
    if risk:
        pieces.append(declare("fx_scores",scores.ravel()))
        # Exact compact 9-bit index encoding: 512-score window requires
        # 9 bits, 64*40*41 entries => 118080 flash bytes, not 210k bytes.
        packed=bytearray((idx.size*9+7)//8+2)
        for at,x in enumerate(idx.ravel()):
            bit=at*9
            by=bit//8
            v=int(x)<<(bit%8)
            packed[by]|=v&255
            packed[by+1]|=(v>>8)&255
            packed[by+2]|=(v>>16)&255
        pieces.append(declare("fx_idx_packed",packed,"uint8_t",perline=32))
        pieces.append(f"#define FX_N_IDX {idx.size}")
    else:
        pieces.append("static const double fx_scores[2]={0.,0.};\n")
        pieces.append("static const uint8_t fx_idx_packed[3]={0,0,0};\n")
        pieces.append("#define FX_N_IDX 0")
    heads=[list(trace.heads[a][:trace.nheads])+[0]*(8-trace.nheads)
           for a in range(32)]
    pieces.append(f"static const int fx_trace_heads[32][8]={{\n"+",\n".join(
        "{"+",".join(str(int(v)) for v in row)+"}" for row in heads)+"\n};\n")
    active=np.asarray(ref.alive(),dtype=int)
    pieces.append("static const uint8_t fx_active[40]={"+
                  ",".join(str(int(v)) for v in active)+"};\n")
    pieces.append(f"#define FX_METHOD_RISK {int(risk)}")
    pieces.append(f"#define FX_N_SCORES {len(scores)}")
    pieces.append(f"#define FX_K {trace.nheads}")
    pieces.append(f"#define FX_LOAD {ref.load}")
    pieces.append(f"#define FX_EXPECTED {scalar(pybest.fitness)}")
    pieces.append(f"#define FX_ID \"{args.method}_{args.seed}_{args.scenario}_r{args.round}\"")
    pieces.append(f"#define FX_EXPECTED_H0 {int(pybest.heads[0])}")
    path=out/"generated_fixture.h"
    path.write_text("\n".join(pieces)+"\n")
    report=dict(
       fixture_id=f"{args.method}_{args.seed}_{args.scenario}_r{args.round}",
       original_simulator_sha256=hashlib.sha256((ROOT/"acr_mcr_v2.py").read_bytes()).hexdigest(),
       original_method=args.method,seed=args.seed,scenario=args.scenario,
       t=args.round,source="Synthetic original simulator state (NOT physical observations)",
       n_sensors=40,n_heads=trace.nheads,stress_samples=ref.cfg.tail_samples if risk else 0,
       score_window_records=len(scores),selected_head_ids=pybest.heads.tolist(),
       selected_objective=pybest.fitness,
       tail_risk_enabled=risk,
       frozen_risk_index_tensor_9bit=(64*40*41 if risk else 0),
       fixture_h_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
       interpretation="Original NumPy candidate and risk-index sequences are frozen in firmware FLASH. This tests M3 deterministic decision kernel only.")
    (out/"reference.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
