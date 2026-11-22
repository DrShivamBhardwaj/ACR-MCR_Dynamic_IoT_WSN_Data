#!/usr/bin/env python3
"""Run one owned, fresh Grenoble three-M3 radio-control/500B smoke test."""
import datetime,hashlib,json,subprocess,tarfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
DEST=ROOT/"logs"/"real_probe_feedback_v9/experiment_second"
DEST.mkdir(parents=True,exist_ok=True)
CLI=Path.home()/"Research/.iotlabcli-venv/bin/iotlab-experiment"
SSH=["ssh","-i",str(Path.home()/".ssh/id_ed25519_iotlab"),
     "-o","BatchMode=yes","-o","StrictHostKeyChecking=yes",
     "-o","ConnectTimeout=15","sbhardwa@grenoble.iot-lab.info"]
ROLES=((16,"sensor_01"),(15,"sensor_02"),(18,"sink_41"))
exp=None
def command(argv,timeout=45,stdin=None):
    p=subprocess.run(argv,capture_output=True,text=True,input=stdin,timeout=timeout)
    if p.returncode:raise RuntimeError("Command failed: "+str(argv[:4])+" "+p.stderr[-500:])
    return p.stdout
def api(*args):
    return json.loads(command([str(CLI),*args],timeout=55))
def mark(status,**kw):
    doc=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status=status,**kw)
    (DEST/"status.json").write_text(json.dumps(doc,indent=2)+"\n")
    print(json.dumps(doc),flush=True)
try:
    current=api("get","-e","--active")
    if current:raise RuntimeError("Another experiment is active on the account")
    images={str(n):HERE/"firmware_smoke"/(label+".iotlab") for n,label in ROLES}
    for path in images.values():
        if not path.is_file():raise FileNotFoundError(str(path))
    digest={n:hashlib.sha256(path.read_bytes()).hexdigest() for n,path in images.items()}
    (DEST/"firmware_sha256.json").write_text(json.dumps(digest,indent=2)+"\n")
    # Verify authorized frontend host, preserving strict SSH host key checks.
    command(SSH+["mkdir -p ~/acr_m3_telemetry_v9_second"],timeout=25)
    payload=(HERE/"capture_3node_frontend_second.py").read_text()
    for upload_attempt in range(1,4):
        try:
            command(SSH+["cat > ~/acr_m3_telemetry_v9_second/capture_3node_frontend_second.py"],
                    timeout=70,stdin=payload)
            break
        except Exception:
            if upload_attempt==3:raise
            time.sleep(3)
    request=["submit","-d","10","-n","ACR-3-M3-physical-probe-ACK-telemetry-v9-second"]
    for board,label in ROLES:
        request+=["-l","grenoble,m3,"+str(board)+","+str(images[str(board)])]
    preflight=api(*(request[:1]+["-p"]+request[1:]))
    (DEST/"reservation_preflight.json").write_text(json.dumps(preflight,indent=2)+"\n")
    booked=api(*request)
    exp=int(booked["id"])
    (DEST/"reservation.json").write_text(json.dumps(booked,indent=2)+"\n")
    mark("reserved",experiment=exp,roles=dict((str(n),label) for n,label in ROLES))
    until=time.monotonic()+450
    while time.monotonic()<until:
        status=api("get","-i",str(exp),"-p")
        (DEST/"status_from_iotlab.json").write_text(json.dumps(status,indent=2)+"\n")
        if status.get("state")=="Running":break
        if status.get("state") in ("Stopped","Terminated","Error"):
            raise RuntimeError("Reservation ended without live experiment")
        time.sleep(4)
    else:raise RuntimeError("Reservation did not reach Running state")
    dep=api("get","-i",str(exp),"-d")
    (DEST/"deployment.json").write_text(json.dumps(dep,indent=2)+"\n")
    expected={f"m3-{board}.grenoble.iot-lab.info" for board,label in ROLES}
    assert set(dep)=={"0"} and set(dep["0"])==expected, "NOT_ALL_3_PHYSICAL_FIRMWARE_FLASH_SUCCEEDED"
    mark("physical_flash_success",experiment=exp,native_firmware_verified_nodes=3)
    mark("physical_serial_capture",experiment=exp)
    with (DEST/"capture_stdout.log").open("w") as fo,(DEST/"capture_stderr.log").open("w") as fe:
        completed=subprocess.run(SSH+["python3 -u ~/acr_m3_telemetry_v9_second/capture_3node_frontend_second.py "+str(exp)],
             stdout=fo,stderr=fe,timeout=220)
    if completed.returncode:
        mark("physical_capture_incomplete",experiment=exp,capture_exit=completed.returncode)
    else:mark("physical_capture_complete",experiment=exp)
    with (DEST/"capture.tar.gz").open("wb") as f:
        p=subprocess.run(SSH+["tar -czf - -C ~/acr_m3_telemetry_v9_second "+str(exp)],
                         stdout=f,stderr=subprocess.PIPE,timeout=80)
    if p.returncode:raise RuntimeError("Could not export original UART traces: "+p.stderr.decode()[-500:])
    with tarfile.open(DEST/"capture.tar.gz") as t:
        t.extractall(DEST/"capture",filter="data")
    x=json.loads((DEST/"capture"/str(exp)/"capture_summary.json").read_text())
    (DEST/"physical_smoke_summary.json").write_text(json.dumps(x,indent=2)+"\n")
    mark("raw_captured" if x["sink_reported_done"] else "not_fully_captured",
         experiment=exp,summary=x)
except Exception as e:
    mark("failed",experiment=exp,error=str(e))
    raise
finally:
    if exp is not None:
        try:
            stopped=api("stop","-i",str(exp))
            mark("own_reservation_stopped",experiment=exp,stop_result=stopped)
        except Exception as e:
            print("STOP_ALREADY_ENDED_OR_ERROR",repr(e),flush=True)
