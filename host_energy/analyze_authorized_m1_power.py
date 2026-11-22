#!/usr/bin/env python3
"""Fail-closed Apple powermetrics CPU-subsystem estimate and raw-claim audit.

It does NOT yield calibrated electrical wall-plug or per-process Joules.
Apple powermetrics reports estimated package/subsystem power, not a meter.
"""
import argparse,datetime,hashlib,json,math,re,statistics,sys
from pathlib import Path
SOURCE_SHA="3f134a8826525215f7cf2ff307bab3893c0d64b050f742bdc3c250b1c0302ea4"
REGEX=re.compile(r"(?im)^\s*CPU Power\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*(mW|W)\s*$")
def parse_power(path):
    content=path.read_text(errors="replace")
    matches=REGEX.findall(content)
    result=[float(n)*(0.001 if u.lower()=="mw" else 1.) for n,u in matches]
    return result,hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run-dir",type=Path)
    p.add_argument("--latest",action="store_true")
    a=p.parse_args()
    home=Path(__file__).resolve().parent
    original=home.parent/"acr_mcr_v2.py"
    if hashlib.sha256(original.read_bytes()).hexdigest()!=SOURCE_SHA:
        raise RuntimeError("Original simulator SHA256 mismatch")
    root=home/"authorized_m1_power_runs"
    if a.latest:
        candidates=sorted((x for x in root.iterdir() if x.is_dir() and (x/"registration.json").exists()),reverse=True)
        if not candidates:
            print("NO_ROOT_APPROVED_POWER_TRACES_EXIST")
            raise SystemExit(3)
        folder=candidates[0]
    else:
        if a.run_dir is None:p.error("Pass --latest or --run-dir")
        folder=a.run_dir
    reg=json.loads((folder/"registration.json").read_text())
    methods=["IDLE","POINT-EA","ACR-MCR","ACR-MCR","POINT-EA","IDLE"]
    if reg.get("original_sim_sha256")!=SOURCE_SHA or reg.get("methods")!=methods:
        raise RuntimeError("Protocol registration is not the locked six-phase design")
    if reg.get("status")!="RAW_POWER_SAMPLED_NOT_CALIBRATED_JOULES":
        raise RuntimeError("Power collection incomplete; no energy inference")
    phases=[]
    for ix,method in enumerate(methods):
        base=folder/f"phase_{ix+1:02}_{method.replace('-','_')}"
        power=base.with_suffix(".powermetrics.txt")
        worker=base.with_suffix(".workload.json")
        if not power.is_file() or not worker.is_file():
            raise RuntimeError(f"Missing raw phase {ix+1}: no evidence")
        vals,sha=parse_power(power)
        w=json.loads(worker.read_text())
        if w["method"]!=method:raise RuntimeError("Wrong method aligned with power trace")
        phase=float(w["phase_s"])
        if not math.isfinite(phase) or phase<=0:raise ValueError("Bad duration")
        if method!="IDLE":
            if w.get("source_sha256")!=SOURCE_SHA or w.get("cases")!=int(reg["repeats_per_method"])*20:
                raise RuntimeError("Incomplete controlled method workload")
        if len(vals)<max(10,int(0.55*phase)) or len(vals)>int(1.8*phase)+5:
            raise RuntimeError(f"Invalid power sampling density phase {ix+1}: {len(vals)} samples for {phase}s")
        if any(not math.isfinite(v) or v<0 or v>25 for v in vals):
            raise RuntimeError(f"Unphysical estimated CPU watts in phase {ix+1}")
        phases.append(dict(phase_index=ix+1,method=method,
          run_seconds=phase,parsed_cpu_watt_samples=len(vals),
          cpu_power_mean_W=statistics.mean(vals),cpu_power_std_W=(statistics.stdev(vals) if len(vals)>1 else 0.),
          estimated_cpu_subsystem_energy_J=sum(vals),
          sampler_interval_s=1.0,
          source_file_sha256=sha,
          estimated_CPU_energy_not_calibrated=True))
    idle_mean=statistics.mean((phases[0]["cpu_power_mean_W"],phases[-1]["cpu_power_mean_W"]))
    est={}
    for method in ("POINT-EA","ACR-MCR"):
        pair=[z for z in phases if z["method"]==method]
        # Baseline varies over time. Use linear interpolation between
        # measured start and end idle phases, not a fixed guessed wattage.
        rows=[]
        for z in pair:
            f=(z["phase_index"]-1)/5
            b=(1-f)*phases[0]["cpu_power_mean_W"]+f*phases[-1]["cpu_power_mean_W"]
            # Remove first 3 seconds of sampler warmup; one-second sample
            # intervals and exact sample timestamps are not available.
            work_duration=z["run_seconds"]-3
            rows.append(dict(phase=z["phase_index"],estimated_cpu_watts=z["cpu_power_mean_W"],
                interpolated_idle_cpu_watts=b,excess_CPU_watts=z["cpu_power_mean_W"]-b,
                net_CPU_subsystem_energy_J=(z["cpu_power_mean_W"]-b)*work_duration,
                estimated_work_seconds=work_duration,
                uncertainty_note="No per-process attribution. One-second sample timing approximated from phase duration."))
        est[method]=rows
    report=dict(
      verdict="APPLE_REPORTED_CPU_SUBSYSTEM_ESTIMATES_ONLY",
      scientific_scope="CPU subsystem power estimate in watts from root-authorized Mac powermetrics; baseline-subtracted J are estimates, NOT calibrated electricity or exclusive optimizer Joules.",
      original_model_sha256=SOURCE_SHA,
      root_authorized_trace_collected=True,
      raw_run_directory=str(folder),phases=phases,
      method_comparisons=est,
      wallplug_joules_measured=False,
      independent_calibrated_energy_meter_used=False,
      permitted_publication_claim="estimated M1 CPU-subsystem energy expenditure under paired programs, not physical per-process or whole-host electricity",
      caveats=["Powermetrics Apple SoC power is explicitly estimated and may be inaccurate.",
               "Other Mac processes influence measured aggregate CPU power.",
               "Only two computational phases per method and two idle phases; this is not a large independent power study.",
               "Without exact per-sample timestamps, integration uses nominal 1-second sampler intervals.",
               "The original Python simulator is included in each method's process.",
               "Do not interpret these estimates as measured calibrated ACR-MCR host Joules or M3 sensor-node Joules."])
    target=folder/"estimated_cpu_power_audit.json"
    target.write_text(json.dumps(report,indent=2)+"\n")
    print("ROOT_AUTHORIZED_ESTIMATED_CPU_POWER_AUDIT",target)
    for label,rows in est.items():
        print(label,[round(a["net_CPU_subsystem_energy_J"],4) for a in rows])
    print("CLAIM_RESTRICTION: not measured calibrated CPU/optimizer electrical Joules")
if __name__=="__main__":main()
