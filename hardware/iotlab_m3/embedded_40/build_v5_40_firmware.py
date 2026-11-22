#!/usr/bin/env python3
"""Rebuild 40 control-reception-triggered M3 members, preserve all V3 binaries."""
from pathlib import Path
import hashlib,json,os,subprocess,tarfile
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
PORT=Path.home()/"Research/iot-lab-contiki-ng/contiki-ng/examples/acr_m3_transport"
SOURCE=HERE/"acr_m3_transport_control_triggered_v5.c"
OUT=HERE/"firmware_41_v5"
OUT.mkdir(parents=True,exist_ok=True)
layout=json.loads((HERE/"41node_physical_layout_v4.json").read_text())
old=json.loads((HERE/"41_firmware_manifest_v3.json").read_text())
manifest=dict(old)
manifest["source_sha256"]=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
manifest["algorithm"]="STATIC members' real over-air control-triggered timing. Sink on-M3 ORIGINAL frozen method-specific Python-equivalent search."
manifest["firmware"]={}
manifest["logical_to_physical"]={**{str(k):int(v["board"]) for k,v in layout["nodes"].items()},"41":int(layout["sink_physical_board"])}
LOG=ROOT/"logs"/"m3_member_v5_compilation"
LOG.mkdir(parents=True,exist_ok=True)
PORT.mkdir(parents=True,exist_ok=True)
(PORT/"acr_m3_transport.c").write_bytes(SOURCE.read_bytes())
for i in range(1,41):
  command=["gmake","-B","TARGET=iotlab","BOARD=m3","WERROR=0",
    "ARCH_PATH=../../../arch",f"ACR_NODE_ID={i}","CL_ROUNDS=3","ACR_START_DELAY_S=25",
    "acr_m3_transport.iotlab"]
  env=os.environ.copy()
  env["PATH"]="/opt/homebrew/opt/make/libexec/gnubin:"+env["PATH"]
  p=subprocess.run(command,cwd=PORT,capture_output=True,text=True,env=env)
  (LOG/f"member_{i:02d}.log").write_text(p.stdout+"\n"+p.stderr)
  if p.returncode:raise RuntimeError(f"M3 source {i} compiler error, see {LOG}")
  filename=f"node_{i:02d}.iotlab"
  binary=PORT/"acr_m3_transport.iotlab"
  result=OUT/filename
  result.write_bytes(binary.read_bytes())
  manifest["firmware"][str(i)]=dict(
      logical_id=i,physical_board=manifest["logical_to_physical"][str(i)],
      filename=filename,sha256=hashlib.sha256(result.read_bytes()).hexdigest(),
      bytes=result.stat().st_size)
  (HERE/"41_firmware_manifest_v5.json").write_text(json.dumps(manifest,indent=2)+"\n")
  print("V5_MEMBER_COMPILED",i,"/40",flush=True)
# Original source-locked method-specific S5 frozen sink firmware is retained separately.
manifest["firmware"]["41"]=dict(old["firmware"]["41"])
manifest["firmware"]["41"]["physical_board"]=int(layout["sink_physical_board"])
(HERE/"41_firmware_manifest_v5.json").write_text(json.dumps(manifest,indent=2)+"\n")
assert len(manifest["firmware"])==41
assert len({z["physical_board"] for z in manifest["firmware"].values()})==41
archive=HERE/"firmware_41_v5.tar.gz"
with tarfile.open(archive,"w:gz") as t:
  for f in sorted(OUT.glob("node_*.iotlab")):t.add(f,arcname=f.name)
print("V5_COMPLETE",len(manifest["firmware"]),archive.stat().st_size,flush=True)
