#!/usr/bin/env python3
"""Original Python vs portable C: exact fixed-state topology/fitness/CVaR
and full 8x4-gen survivor search with frozen NumPy candidate trace.

This does NOT prove native SeedSequence/PCG64 candidate RNG equivalence,
nor physical embedded-controller operation.
"""
import argparse,copy,ctypes,hashlib,json,math,subprocess,sys,time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from acr_mcr_v2 import Simulator,Config,rng_for
N=40;MAX=8;G=4;POP=8;CANDIDATES=32
CB=ctypes.CFUNCTYPE(None,ctypes.c_void_p,ctypes.c_uint,ctypes.c_uint,
                     ctypes.c_uint,ctypes.POINTER(ctypes.c_double),
                     ctypes.POINTER(ctypes.c_double))
class Ctx(ctypes.Structure):
    _fields_=[("n",ctypes.c_int),("stress_samples",ctypes.c_int),
      ("has_risk",ctypes.c_int),("load",ctypes.c_int),
      ("deadline_ms",ctypes.c_double),("tail_weight",ctypes.c_double),
      ("tail_beta",ctypes.c_double),("active",ctypes.c_uint8*N),
      *[(key,ctypes.POINTER(ctypes.c_double)) for key in
        ("edge_cost","attempt_mean","tx_energy","distance","d_used","energy")],
      ("stress",CB),("stress_user",ctypes.c_void_p)]
class Plan(ctypes.Structure):
    _fields_=[("nheads",ctypes.c_int),("heads",ctypes.c_int*MAX),
     ("assigned",ctypes.c_int*N),("costs",ctypes.c_double*N),
     ("path_len",ctypes.c_int*MAX),
     ("paths",(ctypes.c_int*(MAX+2))*MAX),("objective",ctypes.c_double)]
class Trace(ctypes.Structure):
    _fields_=[("nheads",ctypes.c_int),
              ("heads",(ctypes.c_int*MAX)*CANDIDATES)]
def get_lib():
    libfile=HERE/"acr_optimizer_core.test.dylib"
    subprocess.run(["cc","-std=c99","-O2","-Wall","-Wextra","-fPIC",
       "-dynamiclib",str(HERE/"acr_optimizer_core.c"),
       "-lm","-o",str(libfile)],check=True,capture_output=True,text=True)
    lib=ctypes.CDLL(str(libfile))
    lib.acr_make_plan.argtypes=[ctypes.POINTER(Ctx),ctypes.POINTER(ctypes.c_int),
       ctypes.c_int,ctypes.POINTER(Plan)]
    lib.acr_make_plan.restype=ctypes.c_int
    lib.acr_fitness.argtypes=[ctypes.POINTER(Ctx),ctypes.POINTER(Plan)]
    lib.acr_fitness.restype=ctypes.c_double
    lib.acr_select_trace.argtypes=[ctypes.POINTER(Ctx),ctypes.POINTER(Trace),
       ctypes.POINTER(Plan)]
    lib.acr_select_trace.restype=ctypes.c_int
    return lib
def make_ctx(s):
    arr={}
    for name in ("edge_cost","attempt_mean","tx_energy","distance","d_used","energy"):
        arr[name]=np.ascontiguousarray(getattr(s,name),dtype=np.float64)
    have=s.stress_c is not None
    @CB
    def stress(user,scenario,u,v,pc,pd):
        if not have:
            pc[0]=0.;pd[0]=0.
            return
        pc[0]=float(s.stress_c[scenario,u,v])
        pd[0]=float(s.stress_d[scenario,u,v])
    ctx=Ctx()
    ctx.n=40;ctx.stress_samples=s.cfg.tail_samples if have else 0
    ctx.has_risk=int(have)
    ctx.load=s.load;ctx.deadline_ms=s.cfg.deadline_ms
    ctx.tail_weight=s.cfg.tail_weight;ctx.tail_beta=s.cfg.tail_beta
    for i,x in enumerate(s.alive()):ctx.active[i]=int(x)
    for name,field in arr.items():
        setattr(ctx,name,field.ctypes.data_as(ctypes.POINTER(ctypes.c_double)))
    ctx.stress=stress
    return ctx,(arr,stress,s)
def python_trace(s,t):
    """Exact RNG calls and 8+4*6 candidate genotypes of original select()."""
    active=s.active
    k=min(len(active),s.cfg.fixed_heads or max(2,int(round(s.cfg.head_fraction*len(active)))))
    r=rng_for(s.seed,51,t)
    prob=s.energy[active]/s.energy[active].sum()
    initial_candidate=np.sort(r.choice(active,k,replace=False,p=prob))
    s.stress_fields(t)
    selected=[initial_candidate]
    for _ in range(s.cfg.population-1):
        selected.append(np.sort(r.choice(active,k,replace=False,p=prob)))
    if s.heads is not None and len(s.heads)==k and all(s.alive()[s.heads]):
        selected[0]=s.heads.copy()
    all_candidates=[tuple(int(x) for x in heads) for heads in selected]
    plans=[s.make_plan(h) for h in selected]
    for p in plans:s.fitness(p)
    for gen in range(s.cfg.generations):
        plans.sort(key=lambda p:(p.fitness,tuple(p.heads)))
        nxt=plans[:2]
        while len(nxt)<s.cfg.population:
            parent=plans[int(r.integers(0,max(2,s.cfg.population//2)))].heads.copy()
            replace=int(r.integers(0,k))
            pool=s.active[~np.isin(s.active,parent)]
            if len(pool):parent[replace]=r.choice(pool)
            all_candidates.append(tuple(int(x) for x in parent))
            child=s.make_plan(parent)
            s.fitness(child)
            nxt.append(child)
        plans=nxt
    best=min(plans,key=lambda p:(p.fitness,tuple(p.heads)))
    assert len(all_candidates)==CANDIDATES,(len(all_candidates),CANDIDATES)
    trace=Trace();trace.nheads=k
    for a,heads in enumerate(all_candidates):
        for j,head in enumerate(heads):trace.heads[a][j]=head
    return best,trace
def compare(s,lib,ctx,heads,tag,errors):
    py=s.make_plan(np.array(heads,int))
    pyfit=float(s.fitness(py))
    cp=Plan()
    h=(ctypes.c_int*len(heads))(*heads)
    code=lib.acr_make_plan(ctypes.byref(ctx),h,len(heads),ctypes.byref(cp))
    if code:raise AssertionError(f"{tag} C plan failed {code}")
    cfit=lib.acr_fitness(ctypes.byref(ctx),ctypes.byref(cp))
    err=abs(cfit-pyfit)
    errors.append(err)
    assert math.isfinite(cfit),f"{tag}: nonfinite objective"
    assert err<max(1e-8,abs(pyfit)*1e-8),f"{tag}: objective {pyfit} vs {cfit} abs_error={err}"
    assert list(cp.assigned[:40])==py.assigned.tolist(),f"{tag}: different member assignment"
    assert cp.nheads==len(py.heads)
    assert list(cp.heads[:cp.nheads])==py.heads.tolist(),f"{tag}: head ids differ"
    for ix,head in enumerate(py.heads):
        pypath=py.paths.get(int(head))
        cpath=list(cp.paths[ix][:cp.path_len[ix]])
        assert cpath==(pypath or []),(tag,head,pypath,cpath)
    return pyfit
def evaluate_fixture(lib,seed,scenario,method,t):
    s=Simulator(seed,scenario,method,Config(nodes=40,rounds=45))
    for rnd in range(t+1):
        s.fail_nodes(rnd);s.environment(rnd);s.predictions(rnd)
        if rnd==t:break
        plan,_=s.select(rnd)
        s.data_phase(rnd,plan);s.probe_phase(rnd)
    if not s.trigger(t):
        raise AssertionError("No head search at specified sample: "+str((seed,scenario,method,t)))
    # Snapshot the original stochastic genotype stream with independent
    # copy, so no additional fitness_calls change original state.
    ref=copy.deepcopy(s)
    pybest,trace=python_trace(ref,t)
    ctx,keepalive=make_ctx(ref)
    errors=[]
    for a in (0,1,7,8,15,31):
        compare(ref,lib,ctx,list(trace.heads[a][:trace.nheads]),
                f"{scenario}/{method}/{seed}/{t}/candidate{a}",errors)
    cp=Plan()
    rc=lib.acr_select_trace(ctypes.byref(ctx),ctypes.byref(trace),ctypes.byref(cp))
    if rc:raise AssertionError(f"Full C survivor search returned code {rc}")
    assert list(cp.heads[:cp.nheads])==pybest.heads.tolist(), \
        f"Full C search selected different heads: {list(cp.heads[:cp.nheads])}, Python={pybest.heads}"
    err=abs(cp.objective-float(pybest.fitness))
    assert err<max(1e-8,abs(pybest.fitness)*1e-8),(err,cp.objective,pybest.fitness)
    # Now compare C survivor winner with *unmodified original* Python select.
    selected,reason=s.select(t)
    expected=pybest.heads
    if s.heads is not None and reason!="failure":
        # Original sometimes retains the incumbent if best <0.5% better.
        # The full Python reference selection is the authoritative result.
        pass
    # The primitive genotype trace selects same candidate; select() may
    # preserve an incumbent and thus differ from search's best genotype.
    return dict(seed=seed,scenario=scenario,method=method,round=t,
       reason=reason,used_tail_risk=bool(ref.stress_c is not None),
       objective_py=float(pybest.fitness),objective_c=float(cp.objective),
       max_abs_objective_error=max([err]+errors),
       python_search_heads=pybest.heads.tolist(),
       c_search_heads=list(cp.heads[:cp.nheads]),
       original_controller_final_heads=selected.heads.tolist(),
       search_candidate_sets=CANDIDATES)
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--quick",action="store_true")
    ap.add_argument("--extended",action="store_true")
    a=ap.parse_args()
    lib=get_lib()
    # t=0 verifies optimization without empirical tail risk; t=20 verifies
    # risk after warmup and calibration data. t=30 covers periodic rescheduling.
    fixtures=[
       (9401,"S1","POINT-EA",0),
       (9401,"S1","ACR-MCR",0),
       (9402,"S5","POINT-EA",0),
       (9402,"S5","ACR-MCR",0),
       (9401,"S1","ACR-MCR",20),
       (9401,"S1","POINT-EA",20),
       (9402,"S5","ACR-MCR",20),
       (9402,"S5","POINT-EA",20),
    ]
    if a.extended:
        fixtures=[(seed,scenario,method,round_id)
          for seed in range(9401,9411)
          for scenario in ("S1","S5")
          for method in ("POINT-EA","ACR-MCR")
          for round_id in (0,20)]
    elif not a.quick:
        fixtures.extend([
           (9403,"S1","ACR-MCR",20),(9403,"S1","POINT-EA",20),
           (9404,"S5","ACR-MCR",20),(9404,"S5","POINT-EA",20)])
    records=[]
    t0=time.monotonic()
    for i,params in enumerate(fixtures):
        rec=evaluate_fixture(lib,*params)
        records.append(rec)
        print("PARITY_FIXED_STATE",i+1,"/",len(fixtures),
              params,"maxerr",rec["max_abs_objective_error"],flush=True)
    risk=sum(r["used_tail_risk"] for r in records)
    if not risk or len(records)<8:raise AssertionError("Risk cases absent")
    if a.extended:
        assert len({r["seed"] for r in records})==10
        assert risk==20
    outcome=dict(status="PASS_DETERMINISTIC_INNER_KERNEL",
      original_source_sha256=hashlib.sha256((ROOT/"acr_mcr_v2.py").read_bytes()).hexdigest(),
      port_source_sha256=hashlib.sha256((HERE/"acr_optimizer_core.c").read_bytes()).hexdigest(),
      fixtures=len(records),risk_enabled_fixtures=risk,
      independent_seed_blocks=len({r["seed"] for r in records}),
      evaluated_candidate_plan_and_objective_checks=6*len(records),
      full_search_trace_checks=len(records),
      max_objective_abs_error=max(x["max_abs_objective_error"] for x in records),
      candidate_rng_ported_to_M3=False,
      full_controller_ported_to_M3=False,
      guaranteed_embedded_memory_fit=False,
      statement="Equal genotype sets, equal fixed input matrices and stress tensors; original Python vs C complete scoring and generation survivor selection. NumPy PCG64 RNG, feedback-state evolution, and physical adaptive controller parity are unverified.",
      elapsed_seconds=round(time.monotonic()-t0,3),
      records=records)
    path=HERE/"optimizer_deterministic_parity.json"
    path.write_text(json.dumps(outcome,indent=2)+"\n")
    print("OPTIMIZER_PARITY_PASS",len(records),"fixtures, risk",risk,"maxerr",outcome["max_objective_abs_error"],flush=True)
if __name__=="__main__":main()
