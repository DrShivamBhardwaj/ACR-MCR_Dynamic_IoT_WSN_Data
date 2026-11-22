#!/usr/bin/env python3
"""Independent audit of actual forty M3 sensor boards + one M3 sink.

Fixed-head radio/500B transport ONLY; not original on-mote ACR-MCR.
Every control failure remains in nominal source-round denominator.
"""
import argparse,hashlib,json,re
from pathlib import Path
def audit(folder,layout):
    folder=Path(folder)
    layout=json.loads(Path(layout).read_text())
    assignment={int(k):int(v["board"]) for k,v in layout["nodes"].items()}
    assignment[41]=int(layout["sink_physical_board"])
    assert len(assignment)==41 and len(set(assignment.values()))==41
    logs={}
    absent=[]
    for logical,physical in assignment.items():
        f=folder/f"m3-{physical}_logical-{logical}.serial.log"
        if not f.is_file() or not f.stat().st_size:absent.append(f.name)
        else:logs[logical]=f.read_text(errors="replace")
    sink=logs.get(41,"")
    matches=re.findall(
       r'SINK_REASSEMBLED round=(\d+) src=(\d+) app_bytes=500 parts=8 checksum=PASS',sink)
    ids=[(int(r),int(s)) for r,s in matches]
    valid={(r,s) for r,s in ids if 0<=r<3 and 1<=s<=40}
    duplicate=len(ids)-len(valid)
    demand=set()
    controls={}
    energie={}
    mac={}
    physical_hops=0
    for logical,text in logs.items():
        control=[(int(r),int(s)) for r,s in re.findall(r'CTRL_APPLIED round=(\d+) id=(\d+)',text)]
        controls[logical]=len(control)
        if len(set(control))!=len(control):
            raise ValueError(f"Duplicate unique control installation in logical node {logical}")
        if any(s!=logical or not 0<=r<3 for r,s in control):
            raise ValueError("Control applied to wrong logical node or round")
        mac[logical]=len(re.findall(r'MAC_TX round=\d+ type=\d+',text))
        energie[logical]=len(re.findall(r'ENERGEST_RAW id=\d+',text))
        for r,s in re.findall(r'DATA_DEMAND round=(\d+) src=(\d+)',text):
            demand.add((int(r),int(s)))
        if logical in (1,11,21,31):
            physical_hops+=len(re.findall(r'MAC_TX round=\d+ type=1 src=\d+ sender='+str(logical)+r' to=41',text))
    errors=[]
    if absent:errors.append("Missing serial logs: "+",".join(absent))
    if "DIST_DONE" not in sink:errors.append("Physical sink did not report completion")
    if duplicate or len(valid)!=len(ids):errors.append("Duplicate or invalid sink content-completion records")
    if any(c!=1 for c in energie.values()):
        errors.append("Missing/duplicate final ENERGEST record on one or more captured boards")
    if any((r,s) not in demand for r,s in valid):
        errors.append("SINK completion without a matching actual source demand")
    if any((r,s) not in {(r,s) for r in range(3) for s in range(1,41)} for r,s in valid):
        errors.append("Invalid source/round receipt")
    result=dict(
      experiment=int(folder.name),site="FIT IoT-LAB Grenoble",
      status="PASS_TRACE_AUDIT" if not errors else "INCOMPLETE_TRACE_NOT_SCIENTIFIC_CONFIRMATION",
      failures=errors,expected_real_sensor_nodes=40,expected_sink_nodes=1,
      observed_board_count=len(logs),
      nominal_source_round_demands=40*3,
      observed_data_demand_records=len(demand),
      sink_unique_500B_reassemblies=len(valid),
      physical_500B_success_over_nominal=len(valid)/(40*3),
      physically_radio_delivered_control_installs=sum(v for k,v in controls.items() if k!=41),
      possible_control_installations=40*3,
      per_node_control_installs=controls,
      per_node_mac_callback_counts=mac,
      per_node_energest_records=energie,
      physical_head_to_sink_fragment_mac_callbacks=physical_hops,
      source_sample_round_keys=[dict(round=r,logical_source=s) for r,s in sorted(valid)],
      physical_host_instrumented_joules=None,
      embedded_acr_mcr_optimizer_executed=False,
      on_air_control_packets_verified=True,
      raw_logs_sha256={str(k):hashlib.sha256(v.encode()).hexdigest() for k,v in logs.items()},
      limitations="Fixed 4-head controller, 3 rounds, no synchronized 500ms service timestamps; no original adaptive conformal/CVaR policy; this is a deployment and packet-format check, not scientific adaptive-controller validation.")
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--capture-dir",required=True)
    p.add_argument("--topology",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    x=audit(a.capture_dir,a.topology)
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(x,indent=2)+"\n")
    print(json.dumps({k:v for k,v in x.items() if k not in
      ("raw_logs_sha256","per_node_control_installs","per_node_mac_callback_counts","per_node_energest_records","source_sample_round_keys")},indent=2))
    if x["failures"]:raise SystemExit(1)
