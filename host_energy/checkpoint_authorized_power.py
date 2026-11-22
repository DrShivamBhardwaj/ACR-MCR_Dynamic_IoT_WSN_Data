#!/usr/bin/env python3
"""Watch local Mac-authorized powermetrics collector and push finished phases.

Never classify a running phase as completed. Copy exact immutable bytes
only after the collector registration acknowledges phase completion.
Original simulator SHA must match. Preserve failed/incomplete captures.
"""
import argparse,datetime,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parent
REFERENCE="3f134a8826525215f7cf2ff307bab3893c0d64b050f742bdc3c250b1c0302ea4"
METHODS=["IDLE","POINT-EA","ACR-MCR","ACR-MCR","POINT-EA","IDLE"]
def hash_file(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def execute(cmd):
    p=subprocess.run(cmd,cwd=REPO,text=True,capture_output=True,timeout=70)
    if p.returncode:raise RuntimeError("Git failed "+repr(cmd)+"\n"+p.stdout[-600:]+"\n"+p.stderr[-900:])
    return p.stdout.strip()
def push(stage,dest):
    # Only stage the observation produced by this exact registered phase.
    execute(["git","add",str(dest.relative_to(REPO))])
    staged=execute(["git","diff","--cached","--name-only"]).splitlines()
    if staged:
        prefix=str(dest.relative_to(REPO))
        if any(not f.startswith(prefix+"/") for f in staged):
            raise RuntimeError("Unexpected staged files from a different research task: "+str(staged))
        execute(["git","commit","-m",f"Checkpoint M1 authorized Apple CPU-power phase {stage:02d}"])
    for attempt in range(5):
        try:
            execute(["git","-c","rebase.autoStash=true","pull","--rebase","origin","main"])
            execute(["git","push","origin","main"])
            sha=execute(["git","rev-parse","HEAD"])
            upstream=execute(["git","ls-remote","origin","refs/heads/main"]).split()[0]
            if sha!=upstream:raise RuntimeError("Remote SHA does not match local")
            print("GITHUB_PHASE_DURABLE",stage,sha,flush=True)
            return
        except Exception as exc:
            print("RETRY_PHASE_PUSH",attempt+1,str(exc)[:200],flush=True)
            time.sleep(4+4*attempt)
    raise RuntimeError("Five Git push attempts failed; source raw data remain on Mac")
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--run-dir",type=Path,required=True)
    args=a.parse_args()
    run=args.run_dir
    assert hash_file(REPO/"acr_mcr_v2.py")==REFERENCE
    assert run.is_dir()
    archive=HERE/"evidence"/("authorized_M1_"+run.name)
    archive.mkdir(exist_ok=True,parents=True)
    seen=set()
    print("POWER_MONITOR_STARTED",run,"ARCHIVE",archive,flush=True)
    deadline=time.monotonic()+1400
    while time.monotonic()<deadline:
        registration=run/"registration.json"
        if registration.exists():
            reg=json.loads(registration.read_text())
            if reg["original_sim_sha256"]!=REFERENCE or reg["methods"]!=METHODS:
                raise ValueError("Wrong power protocol; stop")
            complete=reg.get("raw_phases",[])
            for idx,item in enumerate(complete,1):
                if idx in seen:continue
                if item.get("method")!=METHODS[idx-1]:
                    raise ValueError("Mismatch method ordering")
                raw=run/item["raw_power_file"]
                worker=run/item["worker_file"]
                if not raw.is_file() or not worker.is_file():continue
                workerdata=json.loads(worker.read_text())
                assert workerdata["method"]==METHODS[idx-1]
                if raw.stat().st_size<1000:raise RuntimeError("Too few raw power bytes")
                dest=archive/f"phase_{idx:02d}_{METHODS[idx-1].replace('-','_')}"
                dest.mkdir(exist_ok=True)
                rfile=dest/raw.name
                wfile=dest/worker.name
                shutil.copy2(raw,rfile);shutil.copy2(worker,wfile)
                files={p.name:hash_file(p) for p in (rfile,wfile)}
                (dest/"checkpoint.json").write_text(json.dumps(dict(
                   phase=idx,method=METHODS[idx-1],original_sha256=REFERENCE,
                   result="CAPTURED_RAW_APPLE_ESTIMATED_CPU_SUBSYSTEM_POWER_NOT_CALIBRATED",
                   raw_original_directory=str(run),raw_files_sha256=files,
                   bytes={rfile.name:rfile.stat().st_size,wfile.name:wfile.stat().st_size},
                   collected_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
                ),indent=2)+"\n")
                push(idx,dest)
                seen.add(idx)
        if len(seen)==6:
            status=json.loads(registration.read_text())["status"]
            if status!="RAW_POWER_SAMPLED_NOT_CALIBRATED_JOULES":
                raise ValueError("All phase files present but root collection not complete")
            print("ALL_SIX_RAW_PHASES_DURABLY_ARCHIVED",flush=True)
            return
        time.sleep(4)
    raise TimeoutError("Power capture monitor timeout; existing completed phase checkpoints remain saved")
if __name__=="__main__":main()
