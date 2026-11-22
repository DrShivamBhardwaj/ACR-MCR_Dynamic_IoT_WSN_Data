#!/usr/bin/env python3
"""Fresh ACR-MCR 500-byte physical transport pilot, with owned reservation only.

All failures retained; no older study's IoT-LAB outputs reused.
M3 radio driver lacks calibrated RSSI/TX power; does not claim SNR-PER.
"""
import subprocess,hashlib,json,time,datetime,shutil,tarfile,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
OUT=ROOT/"logs"/"physical_m3_power_grenoble_20261122"
OUT.mkdir(parents=True,exist_ok=True)
CLI=Path.home()/"Research/.iotlabcli-venv/bin/iotlab-experiment"
SKEY=Path.home()/".ssh/id_ed25519_iotlab"
SSH=["ssh","-i",str(SKEY),"-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=15",
     "sbhardwa@grenoble.iot-lab.info"]
FIRMWARE=Path.home()/"Research/iot-lab-contiki-ng/contiki-ng/examples/acr_phy_m3"
eid=None

def cmd(*args,timeout=50,**kwargs):
    p=subprocess.run(args,capture_output=True,text=True,timeout=timeout,**kwargs)
    if p.returncode:
        raise RuntimeError("Command failed "+str(args[:3])+" : "+p.stderr[-500:])
    return p.stdout
def api(*args):
    return json.loads(cmd(str(CLI),*args,timeout=45))
def state(label,**kw):
    record=dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                state=label,**kw)
    (OUT/"progress.json").write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps(record),flush=True)
try:
    current=api("get","-e","--active")
    if current:
        raise RuntimeError("A reservation is already active for this account; no conflicting experiment submitted")
    for name in ("acr_phy_tx.iotlab","acr_phy_rx.iotlab"):
        if not (FIRMWARE/name).is_file():
            raise FileNotFoundError("Fresh firmware binary missing: "+name)
    sshcheck=cmd(*SSH,"mkdir -p ~/acr_phy_m3",timeout=25)
    capture=(BASE/"capture_frontend.py").read_text()
    upload=subprocess.run(SSH+["cat > ~/acr_phy_m3/capture_frontend.py"],
        input=capture,text=True,capture_output=True,timeout=25)
    if upload.returncode:
        raise RuntimeError("Frontend capture installer failed: "+upload.stderr[-500:])
    fsha={name:hashlib.sha256((FIRMWARE/name).read_bytes()).hexdigest()
          for name in ("acr_phy_tx.iotlab","acr_phy_rx.iotlab")}
    (OUT/"firmware_sha256.json").write_text(json.dumps(fsha,indent=2)+"\n")
    result=api("submit","-d","10","-n","ACR-MCR-500B-Grenoble-REAL-power",
        "-l","grenoble,m3,14,"+str(FIRMWARE/"acr_phy_tx.iotlab")+",acr_m3_active_power_20261122",
        "-l","grenoble,m3,15,"+str(FIRMWARE/"acr_phy_rx.iotlab")+",acr_m3_active_power_20261122")
    eid=result["id"]
    (OUT/"reservation.json").write_text(json.dumps(result,indent=2)+"\n")
    state("reserved",experiment=eid,firmware_sha256=fsha)
    until=time.monotonic()+155
    while time.monotonic()<until:
        info=api("get","-i",str(eid),"-p")
        (OUT/"experiment.json").write_text(json.dumps(info,indent=2)+"\n")
        if info.get("state")=="Running":break
        if info.get("state") in ("Stopped","Error","Terminated"):
            raise RuntimeError("Reservation ended without physical capture: "+str(info["state"]))
        time.sleep(4)
    else:raise RuntimeError("IoT-LAB reservation did not enter Running state within 155 seconds")
    deployment=api("get","-i",str(eid),"-d")
    (OUT/"deployment.json").write_text(json.dumps(deployment,indent=2)+"\n")
    state("capturing_physical_uart",experiment=eid,observed_deployment=deployment)
    with (OUT/"capture_stdout.log").open("w") as output,(OUT/"capture_stderr.log").open("w") as errors:
        cap=subprocess.run(SSH+["python3 -u ~/acr_phy_m3/capture_frontend.py "+str(eid)],
                           stdout=output,stderr=errors,timeout=240)
    if cap.returncode:
        raise RuntimeError("Fresh M3 physical capture failed; logs retained at "+str(OUT))
    with (OUT/"capture.tar.gz").open("wb") as blob:
        fetched=subprocess.run(SSH+["tar -czf - -C ~/acr_phy_m3 "+str(eid)],
                               stdout=blob,stderr=subprocess.PIPE,timeout=110)
    if fetched.returncode:
        raise RuntimeError("Cannot retrieve physical trace: "+fetched.stderr.decode()[-500:])
    with tarfile.open(OUT/"capture.tar.gz") as archive:
        archive.extractall(OUT/"capture",filter="data")
    summary_path=OUT/"capture"/str(eid)/"summary.json"
    summary=json.loads(summary_path.read_text())
    (OUT/"validated_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    state("physically_captured" if summary["sender_completed"] and not summary["error"] else "incomplete",
          experiment=eid,observed=summary)
except Exception as exc:
    state("failed",experiment=eid,error=str(exc))
    raise
finally:
    if eid is not None:
        try:
            result=api("stop","-i",str(eid))
            state("own_reservation_stopped",experiment=eid,stop_result=result)
        except Exception as exc:
            print("OWN_RESERVATION_STOP_FAILED",repr(exc),flush=True)
