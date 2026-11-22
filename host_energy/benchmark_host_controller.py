#!/usr/bin/env python3
"""Host CPU timing only: CPU seconds do not establish measured Joules."""
import argparse,csv,hashlib,json,platform,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from acr_mcr_v2 import Simulator,Config
SEEDS=range(10301,10311)
SCENARIOS=("S1","S5")
METHODS=("POINT-EA","ACR-MCR")
def sha():
    return hashlib.sha256((ROOT/"acr_mcr_v2.py").read_bytes()).hexdigest()
def worker(sc,seed,method):
    r0=resource.getrusage(resource.RUSAGE_SELF);t0=time.perf_counter()
    sim=Simulator(seed,sc,method,Config(nodes=40,rounds=160,probes=1))
    out=sim.run()
    dt=time.perf_counter()-t0;r1=resource.getrusage(resource.RUSAGE_SELF)
    return dict(seed=seed,scenario=sc,method=method,original_sha256=sha(),
      machine=platform.machine(),python=platform.python_version(),
      controller_wall_seconds=out["controller_seconds"],
      total_wall_seconds=dt,process_user_seconds=r1.ru_utime-r0.ru_utime,
      process_system_seconds=r1.ru_stime-r0.ru_stime,
      process_cpu_seconds=r1.ru_utime-r0.ru_utime+r1.ru_stime-r0.ru_stime,
      searches=out["searches"],fitness_evaluations=out["fitness_evaluations"],
      PDR=out["PDR"],timely=out["timely_ratio"],physical_joules=None)
def main(out_path):
    out=Path(out_path);out.parent.mkdir(parents=True,exist_ok=True)
    protocol=dict(code_sha256=sha(),scenarios=list(SCENARIOS),seeds=list(SEEDS),
       methods=list(METHODS),nodes=40,rounds=160,probes=1,
       registered_outcome="Controller wall-clock CPU timing, not physical energy",
       energy_joules_available=False,root_permission_for_powermetrics=False)
    out.with_suffix(".protocol.json").write_text(json.dumps(protocol,indent=2)+"\n")
    rows=[]
    with out.with_suffix(".jsonl").open("w") as trace:
        for sc in SCENARIOS:
            for seed in SEEDS:
                for method in (METHODS if seed%2 else METHODS[::-1]):
                    p=subprocess.run([sys.executable,__file__,"--worker",
                      "--scenario",sc,"--seed",str(seed),"--method",method],
                      capture_output=True,text=True)
                    if p.returncode:
                        raise RuntimeError("Registered run failed: "+p.stderr[-700:])
                    rec=json.loads(p.stdout);rows.append(rec)
                    trace.write(json.dumps(rec)+"\n");trace.flush()
                    print(f"RUN {len(rows)}/40 {sc} {seed} {method} "
                          f"controller={rec['controller_wall_seconds']:.5f}s "
                          f"process_cpu={rec['process_cpu_seconds']:.5f}s",flush=True)
    expected={(sc,seed,m) for sc in SCENARIOS for seed in SEEDS for m in METHODS}
    if len(rows)!=40 or {(r["scenario"],r["seed"],r["method"]) for r in rows}!=expected:
        raise ValueError("Incomplete paired host benchmark")
    from statistics import mean
    measures=("controller_wall_seconds","process_cpu_seconds","total_wall_seconds",
              "process_user_seconds","process_system_seconds","fitness_evaluations")
    result=dict(status="PASS_RUNTIME_NOT_JOULES",original_sha256=sha(),runs=40,
        independent_seed_blocks=10,calibrated_host_energy_joules=None,
        by_method={m:{k:mean(r[k] for r in rows if r["method"]==m) for k in measures}
                   for m in METHODS},
        paired_controller_differences=[
          dict(scenario=sc,seed=seed,
          delta_acr_minus_point=next(r["controller_wall_seconds"] for r in rows if (r["scenario"],r["seed"],r["method"])==(sc,seed,"ACR-MCR"))-
                                next(r["controller_wall_seconds"] for r in rows if (r["scenario"],r["seed"],r["method"])==(sc,seed,"POINT-EA")))
          for sc in SCENARIOS for seed in SEEDS],
        caveat="Original simulator itself uses CPU; even isolated controller wall time is not Joules. powermetrics needs administrator rights; no external calibrated wattmeter available.")
    out.write_text(json.dumps(result,indent=2)+"\n")
    with out.with_suffix(".csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print("HOST_BENCHMARK_COMPLETE",out,flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--worker",action="store_true")
    p.add_argument("--scenario",choices=SCENARIOS)
    p.add_argument("--seed",type=int)
    p.add_argument("--method",choices=METHODS)
    p.add_argument("--out")
    a=p.parse_args()
    if a.worker: print(json.dumps(worker(a.scenario,a.seed,a.method)))
    else:
        if not a.out:p.error("--out required")
        main(a.out)
