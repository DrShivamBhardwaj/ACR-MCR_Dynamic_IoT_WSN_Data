#!/usr/bin/env python3
"""Reserve exactly 40 Grenoble M3 sensors and one M3 sink for physical transport.

This is FIXED-head radio transport only. It is not an embedded execution of
the original conformal optimiser; it is a 41-board hardware integration test.
"""
import datetime,hashlib,json,subprocess,tarfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUT=ROOT/"logs"/"embedded_41node_smoke_v2_20261122"
OUT.mkdir(parents=True,exist_ok=True)
CLI=Path.home()/"Research/.iotlabcli-venv/bin/iotlab-experiment"
SSH=["ssh","-i",str(Path.home()/".ssh/id_ed25519_iotlab"),
    "-o","BatchMode=yes","-o","StrictHostKeyChecking=yes",
    "-o","ConnectTimeout=15","sbhardwa@grenoble.iot-lab.info"]
eid=None
def cmd(argv,timeout=90,stdin=None):
    p=subprocess.run(argv,text=True,capture_output=True,timeout=timeout,input=stdin)
    if p.returncode:raise RuntimeError(str(argv[:3])+" : "+p.stderr[-900:])
    return p.stdout
def api(*argv):
    return json.loads(cmd([str(CLI),*argv],timeout=90))
def audit_status(status,**extras):
    obj=dict(timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
      status=status,experiment_id=eid,**extras)
    (OUT/"status.json").write_text(json.dumps(obj,indent=2)+"\n")
    print(json.dumps(obj),flush=True)
def remote_install(remote_path,content):
    for attempt in range(1,4):
        try:
            cmd(SSH+["cat > "+remote_path],timeout=100,stdin=content)
            return
        except Exception:
            if attempt==3:raise
            time.sleep(5)
try:
    manifest=json.loads((HERE/"41_firmware_manifest_v2.json").read_text())
    physical=json.loads((HERE/"41node_physical_layout_v2.json").read_text())
    firmware=manifest["firmware"]
    assert len(firmware)==41 and len({z["physical_board"] for z in firmware.values()})==41
    assert api("get","-e","--active")=={}, "Another account reservation is active"
    images={}
    for logical in range(1,42):
        info=firmware[str(logical)]
        image=HERE/"firmware_41"/info["filename"]
        if hashlib.sha256(image.read_bytes()).hexdigest()!=info["sha256"]:
            raise ValueError("Firmware hash mismatch: "+str(image))
        images[logical]=image
    audit_status("source_firmware_and_41_board_map_verified",
                 source_sha256=manifest["source_sha256"])
    cmd(SSH+["mkdir -p ~/acr_m3_transport_41"],timeout=30)
    remote_install("~/acr_m3_transport_41/physical_layout.json",
                   (HERE/"41node_physical_layout_v2.json").read_text())
    remote_install("~/acr_m3_transport_41/capture_41_frontend_v2.py",
                   (HERE/"capture_41_frontend_v2.py").read_text())
    request=["submit","-d","15","-n","ACR-MCR-41M3-500B-static-overair-control-smoke"]
    for logical in range(1,42):
        board=firmware[str(logical)]["physical_board"]
        request.extend(("-l",f"grenoble,m3,{board},{images[logical]}"))
    tested=api(*(request[:1]+["-p"]+request[1:]))
    (OUT/"preflight.json").write_text(json.dumps(tested,indent=2)+"\n")
    audit_status("scheduler_preflight_accepted")
    submitted=api(*request)
    eid=int(submitted["id"])
    (OUT/"reservation.json").write_text(json.dumps(submitted,indent=2)+"\n")
    audit_status("reserved")
    # Start all 41 UART connections at firmware LAUNCH instead of after
    # every node is Running; this avoids missing early source round 0.
    capture_out=(OUT/"capture_stdout.log").open("w")
    capture_err=(OUT/"capture_stderr.log").open("w")
    early_capture=subprocess.Popen(
      SSH+["python3 -u ~/acr_m3_transport_41/capture_41_frontend_v2.py "+str(eid)],
      stdout=capture_out,stderr=capture_err)
    audit_status("early_uart_collection_started",capture_pid=early_capture.pid)
    deadline=time.monotonic()+260
    while time.monotonic()<deadline:
        state=api("get","-i",str(eid),"-p")
        (OUT/"site_state.json").write_text(json.dumps(state,indent=2)+"\n")
        if state.get("state")=="Running":break
        if state.get("state") in ("Stopped","Error","Terminated"):
            raise RuntimeError("IoT-LAB reservation terminated before UART capture")
        time.sleep(5)
    else:raise RuntimeError("Physical reservation did not start within bounded window")
    deploy=api("get","-i",str(eid),"-d")
    (OUT/"deployment.json").write_text(json.dumps(deploy,indent=2)+"\n")
    audit_status("physical_41_serial_capture")
    capture_result=early_capture.wait(timeout=315)
    capture_out.close();capture_err.close()
    audit_status("serial_capture_finished",capture_exit=capture_result)
    with (OUT/"raw_uart.tar.gz").open("wb") as archive:
        download=subprocess.run(SSH+["tar -czf - -C ~/acr_m3_transport_41 "+str(eid)],
                                stdout=archive,stderr=subprocess.PIPE,timeout=180)
    if download.returncode:
        raise RuntimeError("Could not preserve all raw UART: "+download.stderr.decode()[-600:])
    with tarfile.open(OUT/"raw_uart.tar.gz") as tar:
        tar.extractall(OUT/"capture",filter="data")
    summary=json.loads((OUT/"capture"/str(eid)/"capture_summary.json").read_text())
    (OUT/"physical_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    audit_status("raw_data_archived",scientific_scope="physical static transport, NOT embedded ACR",
                 captured_serial_nodes=summary["captured_serial_nodes"],
                 reassembled_500B=summary["full_500B_sink_reassemblies"],
                 site_complete=summary["sink_reported_experiment_finished"])
except Exception as error:
    audit_status("failed",error=str(error))
    raise
finally:
    if "early_capture" in globals() and early_capture.poll() is None:
        early_capture.terminate()
    if eid is not None:
        try:
            stopped=api("stop","-i",str(eid))
            audit_status("own_experiment_stopped",stop_result=stopped)
        except Exception as error:
            print("STOP_RETURNED_NONZERO",repr(error),flush=True)
