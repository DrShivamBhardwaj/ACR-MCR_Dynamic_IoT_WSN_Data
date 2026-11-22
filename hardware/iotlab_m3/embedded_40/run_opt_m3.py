#!/usr/bin/env python3
"""Physically flash/read deterministic native risk or point kernel on M3-14.

Own reservation only. A power profile measures TOTAL M3 board supply power,
not host Mac Joules or CPU energy of original network controller.
"""
import argparse,datetime,hashlib,json,subprocess,time,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
CLI=Path.home()/"Research/.iotlabcli-venv/bin/iotlab-experiment"
SSH=["ssh","-i",str(Path.home()/".ssh/id_ed25519_iotlab"),
     "-o","BatchMode=yes","-o","StrictHostKeyChecking=yes",
     "-o","ConnectTimeout=15","sbhardwa@grenoble.iot-lab.info"]
SCP=["scp","-i",str(Path.home()/".ssh/id_ed25519_iotlab"),
     "-o","BatchMode=yes","-o","StrictHostKeyChecking=yes",
     "-o","ConnectTimeout=15"]
def command(args,timeout=90,stdin=None):
    p=subprocess.run(args,timeout=timeout,text=True,capture_output=True,input=stdin)
    if p.returncode:raise RuntimeError(str(args[:3])+" exited "+str(p.returncode)+" : "+p.stderr[-600:])
    return p.stdout
def api(*args):
    return json.loads(command([str(CLI),*args],timeout=90))
def run(method):
    label="m3fixture_acr_mcr" if method=="ACR-MCR" else "m3fixture_point_ea"
    fixture=HERE/"m3_kernel_fixtures"/label
    elf=fixture/"firmware.iotlab"
    reference=json.loads((fixture/"reference.json").read_text())
    if hashlib.sha256(elf.read_bytes()).hexdigest()!=reference["m3_firmware_sha256"]:
        raise ValueError("Firmware binary does not match preregistered SHA256")
    out=ROOT/"logs"/"m3_optimizer_kernel_20261122"/label
    out.mkdir(exist_ok=True,parents=True)
    (out/"reference.json").write_text(json.dumps(reference,indent=2)+"\n")
    eid=None
    def status(stage,**extra):
        x=dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               stage=stage,method=method,experiment=eid,**extra)
        (out/"progress.json").write_text(json.dumps(x,indent=2)+"\n")
        print(json.dumps(x),flush=True)
    try:
        if api("get","-e","--active")!={}:
            raise RuntimeError("Another user's reservation is active on this account")
        command(SSH+["mkdir -p ~/acr_opt_m3"],timeout=25)
        capture=(HERE/"capture_opt_frontend.py").read_text()
        for attempt in range(3):
            try:
                command(SSH+["cat > ~/acr_opt_m3/capture_opt_frontend.py"],
                        timeout=70,stdin=capture)
                break
            except Exception:
                if attempt==2:raise
                time.sleep(3)
        short=method.replace("-","")
        submit=["submit","-d","10","-n","ACR-native-M3-"+short+"-CVaR-kernel-9401",
            "-l",f"grenoble,m3,14,{elf},acr_m3_active_power_20261122"]
        check=api(*(submit[:1]+["-p"]+submit[1:]))
        (out/"preflight.json").write_text(json.dumps(check,indent=2)+"\n")
        status("preflight_pass")
        registered=api(*submit)
        eid=int(registered["id"])
        (out/"reservation.json").write_text(json.dumps(registered,indent=2)+"\n")
        status("reserved")
        capture_stdout=(out/"capture_stdout.log").open("w")
        capture_stderr=(out/"capture_stderr.log").open("w")
        live=subprocess.Popen(SSH+["python3 -u ~/acr_opt_m3/capture_opt_frontend.py "+str(eid)],
                              stdout=capture_stdout,stderr=capture_stderr)
        status("early_uart_capture",capture_pid=live.pid)
        until=time.monotonic()+300
        while time.monotonic()<until:
            current=api("get","-i",str(eid),"-p")
            (out/"site_state.json").write_text(json.dumps(current,indent=2)+"\n")
            if current.get("state")=="Running":break
            if current.get("state") in ("Stopped","Terminated","Error"):
                raise RuntimeError("Testbed reservation stopped before firmware could run")
            time.sleep(4)
        else:raise RuntimeError("Reservation never entered Running")
        deploy=api("get","-i",str(eid),"-d")
        (out/"deployment.json").write_text(json.dumps(deploy,indent=2)+"\n")
        status("running_real_m3")
        rc=live.wait(timeout=500)
        capture_stdout.close();capture_stderr.close()
        status("m3_capture_completed",returncode=rc)
        with (out/"raw_original_uart.tar.gz").open("wb") as file:
            tar=subprocess.run(SSH+["tar -czf - -C ~/acr_opt_m3 "+str(eid)],
                               stdout=file,stderr=subprocess.PIPE,timeout=120)
        if tar.returncode:
            raise RuntimeError("Could not retrieve original real UART "+tar.stderr.decode()[-500:])
        with tarfile.open(out/"raw_original_uart.tar.gz") as archive:
            archive.extractall(out/"raw",filter="data")
        (out/"capture_summary.json").write_text((out/"raw"/str(eid)/"capture_summary.json").read_text())
        summary=json.loads((out/"capture_summary.json").read_text())
        status("real_m3_uart_archived",complete=summary["complete"],
               source_fixture_id=reference["fixture_id"])
    except Exception as exc:
        status("failed",error=repr(exc))
        raise
    finally:
        if "live" in locals() and live.poll() is None:
            live.terminate()
        if eid is not None:
            try:
                result=api("stop","-i",str(eid))
                status("own_reservation_stopped",stop_result=result)
            except Exception as exc:status("stop_problem",error=str(exc))
            time.sleep(8)
            from_remote=f"sbhardwa@grenoble.iot-lab.info:.senslab/{eid}/consumption/m3_14.oml"
            try:
                command(SCP+[from_remote,str(out/"m3_14.oml")],timeout=100)
                status("physical_power_oml_archived",bytes=(out/"m3_14.oml").stat().st_size)
            except Exception as exc:status("power_oml_export_problem",error=str(exc))
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--method",choices=("ACR-MCR","POINT-EA"),required=True)
    args=p.parse_args();run(args.method)
