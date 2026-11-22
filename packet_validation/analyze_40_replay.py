#!/usr/bin/env python3
"""Strict audit for open-loop full-40-node Cooja route/telemetry replay.

All 40 source slots count in demand, regardless of route feasibility,
node failure or replay script decision. No significance claims are made.
"""
import argparse
import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

SUMMARY=re.compile(
 r"REPLAY_SUMMARY mode=(\d+) seed=(\d+) scenario=(S[15]) rounds=(\d+) "
 r"requested=(\d+) unique_sink=(\d+) timely500=(\d+) "
 r"mac_callbacks=(\d+) failures=(\d+) probe_callbacks=(\d+)"
)
KV=re.compile(r"(\w+)=([a-zA-Z0-9.:-]+)")
def parse_one(root):
    log=root/"COOJA.testlog"
    prov=root/"provenance.json"
    if not log.is_file() or not prov.is_file():
        raise ValueError(f"Missing trace or provenance: {root}")
    text=log.read_text(errors="replace")
    source=json.loads(prov.read_text())
    matches=SUMMARY.findall(text)
    if len(matches)!=1 or "TEST OK" not in text:
        raise ValueError(f"{root}: one complete summary and TEST OK required")
    vals=matches[0]
    mode,seed,scenario,rounds,requested,unique,timely,mc,failures,probe=vals
    mode=int(mode);seed=int(seed);rounds=int(rounds)
    requested,unique,timely,mc,failures,probe=map(int,(requested,unique,timely,mc,failures,probe))
    if mode!=(1 if source["method"]=="ACR-MCR" else 0) or seed!=source["seed"] or scenario!=source["scenario"] or rounds!=source["rounds"]:
        raise ValueError(f"{root}: source/method/seed mismatch")
    if not source.get("transport_validation_only") or source.get("controller_packet_feedback"):
        raise ValueError("Open-loop provenance requirement violated")
    demands=[x for x in text.splitlines() if x.startswith("DEMAND_TRACE")]
    latencies=[float(x.split("ms=")[-1]) for x in text.splitlines() if x.startswith("LATENCY_TRACE")]
    mac=[x for x in text.splitlines() if x.startswith("MAC_TRACE")]
    sink=[x for x in text.splitlines() if x.startswith("SINK_TRACE")]
    if len(demands)!=requested or len(latencies)!=unique or len(mac)!=mc:
        raise ValueError("Count mismatch: per-packet logs do not match summary")
    if len(sink)<unique or sum(0<=x<=500 for x in latencies)!=timely:
        raise ValueError("Latency or uniqueness mismatch")
    attempts=[]
    statuses=[]
    data_attempts=probe_attempts=0
    source_data_attempts=0
    probe_callbacks=0
    for line in mac:
        x=dict(KV.findall(line))
        n=int(x["attempts"])
        status=int(x["status"])
        attempts.append(n);statuses.append(status)
        if int(x["type"])==2:
            probe_attempts+=n; probe_callbacks+=1
        else:
            data_attempts+=n
        if int(x["type"])==1 and x["sender"]==x["src"]:
            source_data_attempts+=n
    if probe_callbacks!=probe:
        raise ValueError("Probe callback mismatch")
    qdrops=sum("DROP_QUEUE" in x for x in text.splitlines())
    result=dict(
        mode=mode,method=source["method"],scenario=scenario,seed=seed,
        nodes=40,sink=41,rounds=rounds,
        nominal_demand=40*rounds,
        source_queued=requested,unique_sink_delivery=unique,
        timely_500ms=timely,
        PDR_nominal=unique/(40*rounds),
        timely_ratio_nominal=timely/(40*rounds),
        PDR_conditional_to_queued=unique/requested if requested else None,
        mean_delivery_latency_ms=sum(latencies)/len(latencies) if latencies else None,
        radio_mac_attempts=sum(attempts),
        total_mac_failures=sum(x!=0 for x in statuses),
        probe_attempts=probe_attempts,
        data_attempts=data_attempts,
        source_data_attempts=source_data_attempts,
        queue_drops_logged=qdrops,
        original_controller_feedback_from_cooja=False,
        transport_validation_only=True,
        original_source_sha256=source["source_sha256"],
        replay_schedule_sha256=source["schedule_sha256"],
        source_provenance=source,
    )
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input-root",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--require-pairs",action="store_true")
    args=ap.parse_args()
    dirs=[p.parent for p in Path(args.input_root).rglob("COOJA.testlog")]
    if not dirs: raise ValueError("No packet traces")
    results=[parse_one(d) for d in dirs]
    keys=defaultdict(dict)
    for r in results:
        k=(r["scenario"],r["seed"])
        if r["mode"] in keys[k]: raise ValueError(f"Duplicate replay {k} mode={r['mode']}")
        keys[k][r["mode"]]=r
    pairs=[]
    for k,mods in sorted(keys.items()):
        if args.require_pairs and set(mods)!={0,1}:
            raise ValueError(f"Incomplete controller pair: {k}")
        if set(mods)!={0,1}:continue
        a,b=mods[0],mods[1]
        if a["nominal_demand"]!=b["nominal_demand"]:
            raise ValueError("Different nominal demand")
        pairs.append(dict(scenario=k[0],seed=k[1],
            timely_delta_ACR_minus_POINT=b["timely_ratio_nominal"]-a["timely_ratio_nominal"],
            PDR_delta_ACR_minus_POINT=b["PDR_nominal"]-a["PDR_nominal"],
            mac_attempts_delta=b["radio_mac_attempts"]-a["radio_mac_attempts"],
            probe_attempts_delta=b["probe_attempts"]-a["probe_attempts"]))
    out=Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    summary=dict(
        status="PASS",
        label="40-node OPEN-LOOP route replay, not a full packet-driven ACR-MCR port",
        n_runs=len(results),n_pairs=len(pairs),
        original_frozen_protocol_unchanged=True,
        closed_loop_packet_observation_used_by_controller=False,
        no_independent_hardware_validation=True,
        original_packet_size_bits=4000,
        replay_packet_size_bits=78*8,
        limitations="Short CSMA frames and open-loop synthetic controller decisions; no original 4000-bit fragmentation, distributed telemetry, CPU/idle energy, or physical channel calibration.",
        packet_runs=sorted(results,key=lambda r:(r["scenario"],r["seed"],r["mode"])),
        paired_differences=pairs,
    )
    out.write_text(json.dumps(summary,indent=2)+"\n")
    with out.with_suffix(".csv").open("w",newline="") as f:
        keys=["mode","method","scenario","seed","nodes","rounds","nominal_demand","source_queued","unique_sink_delivery","timely_500ms","PDR_nominal","timely_ratio_nominal","mean_delivery_latency_ms","radio_mac_attempts","total_mac_failures","probe_attempts","data_attempts","queue_drops_logged"]
        w=csv.DictWriter(f,fieldnames=keys)
        w.writeheader()
        for r in summary["packet_runs"]:w.writerow({k:r[k] for k in keys})
    print(f"AUDIT_PASS: {len(results)} Cooja experiments, {len(pairs)} paired blocks. No closed-loop inference.")
    for p in pairs:print(p)

if __name__=="__main__":main()
