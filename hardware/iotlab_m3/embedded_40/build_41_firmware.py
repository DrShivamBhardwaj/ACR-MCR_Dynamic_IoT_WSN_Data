#!/usr/bin/env python3
"""Reproducibly compile source-locked 40 M3 member plus one sink binary.

All binaries are STATIC four-head packet transport; not ACR-MCR optimizer.
"""
import hashlib,json,os,subprocess,sys,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
R=HERE.parents[3]
PORT=Path.home()/"Research/iot-lab-contiki-ng/contiki-ng/examples/acr_m3_transport"
OUT=HERE/"firmware_41"
OUT.mkdir(exist_ok=True)
SITE=json.loads((HERE/"41node_physical_layout.json").read_text())
logdir=R/"logs"/"embedded_41_build";logdir.mkdir(parents=True,exist_ok=True)
manifest=dict(site="Grenoble",source_sha256=hashlib.sha256((HERE/"acr_m3_transport.c").read_bytes()).hexdigest(),
  Makefile_sha256=hashlib.sha256((HERE/"Makefile").read_bytes()).hexdigest(),
  rounds=3,start_delay_seconds=25,network="forty sources plus one sink",
  system="Contiki-NG IoT-LAB M3, CSMA, NullNet, 500-byte/8-fragment payload",
  algorithm="STATIC 4-head transport: not original adaptive ACR-MCR",
  logical_to_physical={**{str(k):int(v["board"]) for k,v in SITE["nodes"].items()},"41":SITE["sink_physical_board"]},
  firmware={})
for node in range(1,42):
    label=f"node_{node:02d}.iotlab"
    cmd=["gmake","-B","TARGET=iotlab","BOARD=m3","WERROR=0",
         "ARCH_PATH=../../../arch",f"ACR_NODE_ID={node}",
         "CL_ROUNDS=3","ACR_START_DELAY_S=25","acr_m3_transport.iotlab"]
    env=os.environ.copy();env["PATH"]="/opt/homebrew/opt/make/libexec/gnubin:"+env["PATH"]
    proc=subprocess.run(cmd,cwd=PORT,env=env,text=True,capture_output=True)
    (logdir/f"build_node_{node:02d}.log").write_text(proc.stdout+"\n"+proc.stderr)
    if proc.returncode:raise RuntimeError(f"Failed to compile logical node {node}; inspect {logdir}")
    source=PORT/"acr_m3_transport.iotlab"
    if not source.exists():raise FileNotFoundError(source)
    target=OUT/label;target.write_bytes(source.read_bytes())
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    manifest["firmware"][str(node)]=dict(logical_id=node,
      physical_board=manifest["logical_to_physical"][str(node)],
      filename=label,sha256=digest,bytes=target.stat().st_size)
    (HERE/"41_firmware_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print("M3_41_BUILD",node,"/41",label,digest[:16],flush=True)
if len({v["sha256"] for v in manifest["firmware"].values()})!=41:
    raise ValueError("Not all node images differ at build level")
archive=HERE/"firmware_41.tar.gz"
with tarfile.open(archive,"w:gz") as tar:
    for p in sorted(OUT.glob("node_*.iotlab")):
        tar.add(p,arcname=p.name)
print("M3_41_ALL_SOURCE_HASHED_FIRMWARE_COMPILED",archive,archive.stat().st_size,flush=True)
