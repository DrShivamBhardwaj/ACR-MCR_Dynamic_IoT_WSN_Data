#!/usr/bin/env python3
"""Owner-run root-authorized Mac M1 *estimated* CPU package power capture.

Remote Desktop Commander cannot elevate the logged-in user. This helper
requires an actual local administrator action; it is NEVER run by ChatGPT.
Raw powermetrics subsystem watts are estimates, not a calibrated wattmeter.
"""
import argparse,csv,datetime,hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
DATA=Path(__file__).resolve().parents[1]
REPRO_SHA="3f134a8826525215f7cf2ff307bab3893c0d64b050f742bdc3c250b1c0302ea4"
VENVPY=DATA.parent/".venv"/"bin"/"python"
SCRIPTPATH=DATA/"host_energy"/"power_batch_worker.py"
POWER="/usr/bin/powermetrics"
def validate():
    if hashlib.sha256((DATA/"acr_mcr_v2.py").read_bytes()).hexdigest()!=REPRO_SHA:
        raise RuntimeError("Original model modified: abort energy measurement")
    if not VENVPY.exists() or not SCRIPTPATH.exists() or not Path(POWER).exists():
        raise RuntimeError("Missing frozen simulator virtualenv, worker, or Apple power tool")
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--preflight",action="store_true")
    p.add_argument("--repeats",type=int,default=5)
    a=p.parse_args()
    validate()
    if a.preflight:
        print("PREPARED_NOT_POWER_MEASURED: local administrator must execute this collector.")
        print("Original simulator SHA256",REPRO_SHA)
        print("User ID",os.geteuid(),"M1 package watts require root.")
        return
    if os.geteuid()!=0:
        raise PermissionError(
         "ACTUAL LOCAL ADMINISTRATION REQUIRED. Do not report host Joules. "
         "Open local trusted Mac Terminal and authorize the system power sampler.")
    if not 1<=a.repeats<=20:raise ValueError("Invalid workload repetitions")
    if platform.machine()!="arm64":
        raise RuntimeError("Unsupported platform: original M1 experiment must run on arm64")
    root=DATA/"host_energy"/"authorized_m1_power_runs"
    out=root/datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out.mkdir(parents=True,exist_ok=False)
    sequence=("IDLE","POINT-EA","ACR-MCR","ACR-MCR","POINT-EA","IDLE")
    study=dict(status="STARTED_NO_JOULE_ESTIMATE",original_sim_sha256=REPRO_SHA,
       board="Apple M1 MacBook Air",system_powermetrics=True,tool_installed=True,
       logged_in_as_root=True,methods=list(sequence),repeats_per_method=a.repeats,
       ics="No external calibrated wattmeter: CPU package power is estimated.",
       host_physical_joules_calibrated=False,raw_phases=[])
    (out/"registration.json").write_text(json.dumps(study,indent=2)+"\n")
    for index,method in enumerate(sequence):
        path=out/(f"phase_{index+1:02}_{method.replace('-','_')}")
        power_file=path.with_suffix(".powermetrics.txt")
        workload_file=path.with_suffix(".workload.json")
        with power_file.open("w") as fo:
            sampler=subprocess.Popen(
              [POWER,"--samplers","cpu_power","--sample-rate","1000",
               "--sample-count","-1"],
              stdout=fo,stderr=subprocess.STDOUT)
            start=time.monotonic()
            try:
                time.sleep(3)  # settle first power sample
                if method=="IDLE":
                    time.sleep(45)
                    process_result={"status":"CONTROLLED_IDLE","records":0}
                else:
                    p2=subprocess.run(
                      [str(VENVPY),str(SCRIPTPATH),
                       "--method",method,"--repeats",str(a.repeats)],
                      capture_output=True,text=True,timeout=3600)
                    if p2.returncode:
                        raise RuntimeError(method+" worker failed "+p2.stderr[-400:])
                    process_result=json.loads(p2.stdout)
                elapsed=time.monotonic()-start
                workload_file.write_text(json.dumps(
                    {"method":method,"phase_s":elapsed,**process_result},
                    indent=2)+"\n")
            finally:
                sampler.terminate()
                try:sampler.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    sampler.kill();sampler.wait()
        study["raw_phases"].append(dict(method=method,
           raw_power_file=power_file.name,worker_file=workload_file.name))
        (out/"registration.json").write_text(json.dumps(study,indent=2)+"\n")
        print("AUTHENTIC_POWERSAMPLER_PHASE",index+1,method,flush=True)
    study["status"]="RAW_POWER_SAMPLED_NOT_CALIBRATED_JOULES"
    study["source_sha256"]=REPRO_SHA
    (out/"registration.json").write_text(json.dumps(study,indent=2)+"\n")
    print("CAPTURE_COMPLETE_RAW_CPU_PACKAGE_POWER",out)
if __name__=="__main__":main()
