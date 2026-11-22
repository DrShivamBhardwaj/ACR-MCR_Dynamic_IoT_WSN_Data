#!/usr/bin/env python3
"""Fail-closed audit of *frozen-fixture* original C kernel on 41 physical M3.

This is not live, adaptive closed-loop ACR-MCR. Independent testbed sessions
with the same seed are not independent statistical seed replications.
"""
import argparse,hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
def audit(method,root):
    label="point_ea" if method=="POINT-EA" else "acr_mcr"
    ref=json.loads((HERE/"m3_kernel_fixtures"/("m3fixture_"+label+"_S5_openloop")/"reference.json").read_text())
    folder=Path(root)/label
    captured=list((folder/"capture").glob("*/capture_summary.json"))
    if len(captured)!=1:raise ValueError(f"{method}: not one archived original capture")
    eid=int(captured[0].parent.name)
    c=json.loads(captured[0].read_text())
    layout=json.loads((HERE/"41node_physical_layout_v4.json").read_text())
    phys={int(k):int(v["board"]) for k,v in layout["nodes"].items()}
    phys[41]=int(layout["sink_physical_board"])
    logs={}
    missing=[]
    for logical,board in phys.items():
        f=captured[0].parent/f"m3-{board}_logical-{logical}.serial.log"
        if not f.is_file() or not f.stat().st_size:missing.append((logical,board))
        else:logs[logical]=f.read_text(errors="replace")
    sink=logs.get(41,"")
    ready=re.findall(r"ONBOARD_OPT_READY fixture=(\S+) risk=(\d+) heads=([0-9,]+) objective_micro=(\d+) error_nano=(\d+) cpu_ticks=(\d+) hz=(\d+) enabled=(\d+)",sink)
    issues=[]
    if len(ready)!=1:issues.append("Missing or duplicate real sink ONBOARD_OPT_READY")
    else:
        fixture,risk,heads,obj,err,clock,hz,enabled=ready[0]
        if fixture!=ref["fixture_id"]:issues.append("Wrong sink original fixture ID")
        observed=list(map(int,heads.split(",")))
        expected=[int(x)+1 for x in ref["selected_head_ids"]]
        if observed!=expected:issues.append(f"Wrong heads {observed} != {expected}")
        if abs(int(obj)/1e6-ref["selected_objective"])>1e-5:issues.append("M3 original objective mismatch")
        if int(err)>100:issues.append("M3 C objective parity error exceeds tolerance")
        if int(risk)!=(1 if method=="ACR-MCR" else 0):issues.append("Wrong risk mode")
        if int(clock)<=0 or int(hz)<=0:issues.append("Unrecorded M3 execution time")
    received=re.findall(r"SINK_REASSEMBLED round=(\d+) src=(\d+) app_bytes=500 parts=8 checksum=PASS",sink)
    receipts=[(int(r),int(s)) for r,s in received]
    unique=set(receipts)
    if len(receipts)!=len(unique):issues.append("Duplicate complete 500B source-round sink reassembly")
    if any(not 0<=r<3 or not 1<=s<=40 for r,s in receipts):issues.append("Invalid sample ID in sink")
    if "SINK_BAD_PAYLOAD" in sink:issues.append("At least one 500-byte payload integrity failure")
    if "DIST_DONE" not in sink:issues.append("No end-of-experiment physical sink completion")
    control=set()
    demands=set()
    energy={}
    for logical,log in logs.items():
        energy[logical]=len(re.findall(r"ENERGEST_RAW id=\d+",log))
        if logical==41:continue
        for round_id,node in re.findall(r"CTRL_APPLIED round=(\d+) id=(\d+)",log):
            key=(int(round_id),int(node))
            if node!=str(logical) or key in control:issues.append("Duplicate or misaddressed real control installation")
            control.add(key)
        for round_id,node in re.findall(r"DATA_DEMAND round=(\d+) src=(\d+)",log):
            demands.add((int(round_id),int(node)))
    if missing:issues.append("Missing serial boards "+str(missing))
    if len(logs)!=41:issues.append("Not all physical 41 sources captured")
    if not unique.issubset(demands):issues.append("Complete sink packets without original data-demand evidence")
    if len(control)>120 or len(demands)>120 or len(unique)>120:issues.append("Impossible source-round event counts")
    summary={
       "method":method,"experiment":eid,"session_name":c.get("experiment"),
       "original_source_sha256":ref["original_simulator_sha256"],
       "fixture_id":ref["fixture_id"],"firmware_sha256":ref["physical_sink_firmware_sha256"],
       "kernel_checked":len(ready)==1,"onboard_kernel_pass":len(ready)==1 and not any("objective" in i or "heads" in i or "fixture" in i for i in issues),
       "status":"PASS_EXPLORATORY_FROZEN_REAL_RADIO_TRACES" if not issues else "INCOMPLETE_OR_INVALID",
       "audit_issues":issues,"physical_41_board_uart_count":len(logs),"registered_nominal_sources":40,
       "registered_rounds":3,"nominal_source_round_demand":120,
       "real_control_installations":len(control),"real_data_demand_logs":len(demands),
       "full_byte_verified_500B_sink_deliveries":len(unique),
       "observed_full_500B_pdr_over_nominal":len(unique)/120,
       "energest_motes_captured":sum(v==1 for v in energy.values()),
       "energest_total_motes":41,
       "missing_or_duplicate_energest":[i for i,v in energy.items() if v!=1],
       "actual_sink_uart_sha256":hashlib.sha256(sink.encode()).hexdigest(),
       "physical_endpoint_500ms_deadline_measured":False,
       "full_closed_loop_adaptive_algorithm":False,
       "frozen_synthetic_fixture":True,
       "onboard_kernel_result":ready[0] if ready else None,
       "limitations":"One three-round 41-M3 session using original synthetic frozen RNG/edge/stress input, original risk or point C kernel only; NO physical feedback-driven conformal state update. No independent seed-block statistics. No synchronized 500ms deadlines. Energy data not equivalent to host CPU energy."}
    return summary
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",required=True)
    parser.add_argument("--out",required=True)
    a=parser.parse_args()
    results=[audit(m,a.root) for m in ("POINT-EA","ACR-MCR")]
    diff=results[1]["observed_full_500B_pdr_over_nominal"]-results[0]["observed_full_500B_pdr_over_nominal"]
    z=dict(status="EXPLORATORY_PAIRED_PHYSICAL_RADIO_EVIDENCE_NOT_INDEPENDENT_SEED_CONFIRMATION",
           hardware="40 physical M3 sources and one physical M3 sink",
           scenario="S5",seed=9401,original_round=20,
           methods=results,observed_acr_minus_point_delivery_fraction=diff,
           p_value=None,confidence_interval=None,seed_block_n=1,
           same_fixture_for_three_rounds=True,
           note="These physical sessions are chronological not randomized. The physical paths come from original synthetic frozen-position state, not real receiver feedback. Any PDR difference is descriptive and confounded by testbed time variation.")
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(z,indent=2)+"\n")
    print(json.dumps({k:v for k,v in z.items() if k!="methods"},indent=2))
    for s in results:print("PHYSICAL_RESULT",json.dumps({k:v for k,v in s.items() if k not in ("onboard_kernel_result","actual_sink_uart_sha256")}))
    if any(r["status"]!="PASS_EXPLORATORY_FROZEN_REAL_RADIO_TRACES" for r in results):
        raise SystemExit(2)
if __name__=="__main__":main()
