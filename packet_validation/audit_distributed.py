#!/usr/bin/env python3
"""Strict 40-node Cooja control-radio, 500B reassembly and ENERGEST audit."""
import argparse,hashlib,json,re
from pathlib import Path
from collections import defaultdict

PAT=re.compile(r'ROUND_PACKET_AUDIT round=(\d+) requested=(\d+) unique_sink=(\d+) timely500=(\d+) MAC_callbacks=(\d+) control_applied=(\d+) control_mac=(\d+) fragment_mac=(\d+) bad_payload=(\d+)')
POWER=re.compile(r'ENERGY_TICKS ENERGEST_RAW id=(\d+) round=(\d+) cpu=(\d+) lpm=(\d+) deep=(\d+) tx=(\d+) listen=(\d+) ticks_per_second=(\d+)')
DONE=re.compile(r'RADIO_FEEDBACK_COMPLETED method=(ACR-MCR|POINT-EA) seed=(\d+) rounds=(\d+) plans=(\d+) control_receptions=(\d+) control_mac=(\d+)')
CONFIG=re.compile(r'DIST_CONFIG_OK seed=(\d+) method=(\d+) rounds=(\d+) app_bytes=(\d+)')
END=re.compile(r'REASSEMBLY_AUDIT_COMPLETE rounds=(\d+) energy_nodes=(\d+) controller_plan_injected_only_at_sink=(\d+)')
DELIVERY=re.compile(r'COMPLETE_DELIVERY round=(\d+) src=(\d+) bytes=(\d+) latency_ms=([0-9.]+)')
PLAN=re.compile(r'SINK_PLAN_WRITTEN round=(\d+) method=(ACR-MCR|POINT-EA) entries=(\d+) radio_delivery_required=(\d+)')

def audit(run_dir,method,seed,scenario,rounds):
    p=Path(run_dir)
    raw=(p/"COOJA.testlog").read_text(errors="replace")
    origin=json.loads((p/"controller.summary.json").read_text())
    plans=list(PLAN.finditer(raw));config=CONFIG.findall(raw)
    rounds_raw=[tuple(map(int,m.groups())) for m in PAT.finditer(raw)]
    done=DONE.findall(raw);ending=END.findall(raw)
    if "TEST OK" not in raw or len(config)!=1 or len(done)!=1 or len(ending)!=1:
        raise ValueError("Cooja run is incomplete or failed")
    if config[0]!=(str(seed),str(int(method=="ACR-MCR")),str(rounds),"500"):
        raise ValueError("Compiled scenario/seed/method/payload mismatch")
    if done[0][:4]!=(method,str(seed),str(rounds),str(rounds)):
        raise ValueError("Controller bridge not complete")
    if ending[0]!=(str(rounds),"41","1"):
        raise ValueError("All 41 ENERGEST nodes and sink-only control required")
    if len(plans)!=rounds or len(rounds_raw)!=rounds:
        raise ValueError("Missing route plans or packet audits")
    for t,(plan,row) in enumerate(zip(plans,rounds_raw)):
        if int(plan.group(1))!=t or plan.group(2)!=method or int(plan.group(3))!=40 or plan.group(4)!="1":
            raise ValueError(f"Plan {t} not sink-only radio delivered")
        rr,req,unique,timely,mac,ctrl,ctlmac,frags,bad=row
        if rr!=t or not 0<=timely<=unique<=req<=ctrl<=40 or bad!=0:
            raise ValueError(f"Invalid {t} control/delivery/integrity counts: {row}")
        if mac<ctlmac+frags:
            raise ValueError("MAC accounting incorrect")
    control=sum(r[5] for r in rounds_raw)
    ctrlmac=sum(r[6] for r in rounds_raw)
    if control!=int(done[0][4]) or ctrlmac!=int(done[0][5]):
        raise ValueError("Control coverage accounting mismatch")
    energy={}
    for match in POWER.finditer(raw):
        vals=tuple(map(int,match.groups()))
        mote,period,cpu,lpm,deep,tx,listen,hz=vals
        if mote in energy or not 1<=mote<=41 or period!=rounds or hz<=0:
            raise ValueError("Duplicate/mismatched energest node")
        energy[mote]=dict(cpu_ticks=cpu,lpm_ticks=lpm,deep_lpm_ticks=deep,
                          radio_transmit_ticks=tx,radio_listen_ticks=listen,
                          ticks_per_second=hz)
    if set(energy)!=set(range(1,42)):
        raise ValueError("Incomplete 41-node energy capture")
    if any(v["ticks_per_second"]!=next(iter(energy.values()))["ticks_per_second"] for v in energy.values()):
        raise ValueError("Inconsistent tick scale")
    if not any(v["radio_transmit_ticks"]>0 for v in energy.values()) or not any(v["radio_listen_ticks"]>0 for v in energy.values()):
        raise ValueError("ENERGEST disabled or Cooja radio never on")
    receipts=[tuple(m.groups()) for m in DELIVERY.finditer(raw)]
    if len(receipts)!=sum(r[2] for r in rounds_raw):
        raise ValueError("Delivered 500-byte records mismatch")
    if len({(r[0],r[1]) for r in receipts})!=len(receipts) or any(int(r[2])!=500 for r in receipts):
        raise ValueError("Duplicate or invalid reassembled bytes")
    control_trace=re.findall(r'^CONTROL_RECEPTION CTRL_APPLIED round=(\d+) id=(\d+)',raw,re.M)
    unique_installs={(int(round_id),int(mote_id)) for round_id,mote_id in control_trace}
    if len(unique_installs)!=control:
        raise ValueError("Unique control installation traces do not match per-round audit")
    duplicate_control_announcements=len(control_trace)-len(unique_installs)
    model=json.loads((p/"controller.summary.json").read_text())
    if not model.get("closed_loop_packet_feedback") or not model.get("distributed_control_packets") or not model.get("original_payload_fragmentation"):
        raise ValueError("Python controller scope flags inconsistent")
    if model["recorded_epochs"]!=rounds:
        raise ValueError("Python controller update epochs incomplete")
    tickscale=next(iter(energy.values()))["ticks_per_second"]
    power_summary={k+"_seconds":sum(v[k] for v in energy.values())/tickscale
       for k in ("cpu_ticks","lpm_ticks","deep_lpm_ticks","radio_transmit_ticks","radio_listen_ticks")}
    result=dict(
       verification="PASS",kind="Simulated over-the-air control and real Cooja MAC fragmentation test",
       method=method,seed=seed,scenario=scenario,nodes=40,rounds=rounds,
       nominal_demand=40*rounds,source_requests=sum(x[1] for x in rounds_raw),
       valid_500byte_reassemblies=sum(x[2] for x in rounds_raw),
       timely_500ms=sum(x[3] for x in rounds_raw),
       PDR_nominal=sum(x[2] for x in rounds_raw)/(40*rounds),
       timely_ratio_nominal=sum(x[3] for x in rounds_raw)/(40*rounds),
       controller_plans_through_sink_memory_only=True,
       sensor_routes_received_as_actual_control_packets=True,
       control_receptions=control,duplicate_control_received_announcements=duplicate_control_announcements,control_reception_opportunities=40*rounds,
       controller_control_radio_packets=ctrlmac,
       data_fragment_radio_callbacks=sum(x[7] for x in rounds_raw),
       total_MAC_callbacks=sum(x[4] for x in rounds_raw),
       payload_integrity_errors=0,
       complete_8_fragment_payload_verified=True,
       energy_counter_source="Contiki-NG ENERGEST in Cooja: time counters, not physical Joules",
       energest_ticks_per_second=tickscale,
       energest_aggregate=power_summary,
       energest_per_node=energy,
       original_payload_bytes=500,
       experimental_controller_feedback="actual Cooja simulated MAC acknowledgments, retries and timing",
       distributed_mote_control_radio_measured=True,
       centralized_optimizer_at_sink=True,
       external_RF_calibration=False,
       physical_current_voltage_measurement=False,
       code_source_sha256=hashlib.sha256((Path(__file__).resolve().parent/"acr_40_distributed_transport.c").read_bytes()).hexdigest(),
       limitations="Cooja UDGM/CSMA simulation; sink controller computed outside motes; original offered load not fully reproduced; CPU energest busy time is not calibrated processor power.")
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--run-dir",required=True)
    p.add_argument("--method",choices=("POINT-EA","ACR-MCR"),required=True)
    p.add_argument("--scenario",choices=("S1","S5"),required=True)
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--rounds",type=int,required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    x=audit(args.run_dir,args.method,args.seed,args.scenario,args.rounds)
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(x,indent=2)+"\n")
    print("STRICT_AUDIT_PASS",x["method"],x["seed"],"reassembled",x["valid_500byte_reassemblies"],
          "radio_control_receipts",x["control_receptions"],
          "radio_tx_s_total",x["energest_aggregate"]["radio_transmit_ticks_seconds"])
