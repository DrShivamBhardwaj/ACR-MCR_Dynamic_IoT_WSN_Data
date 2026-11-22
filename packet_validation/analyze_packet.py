#!/usr/bin/env python3
"""Audit actual Cooja packet traces; no cross-mote time subtraction.

Every simulated packet demand is in the denominator. Host-observed simulation
time, not unsynchronized mote ticks, determines end-to-end delay. Results are
mechanism-level exploratory outcomes, not validation of original 40-node ACR-MCR.
"""
import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

SUMMARY = re.compile(
    r"VALIDATION_SUMMARY mode=(\d+) seed=(\d+) delivered=(\d+) timely=(\d+) "
    r"probe_callbacks=(\d+) data_callbacks=(\d+) relay_callbacks=(\d+) head_searches=(\d+)"
)
ATTEMPTS = re.compile(r"attempts=(\d+)")
STATUS = re.compile(r"mac_status=(\d+)")
ELAPSED = re.compile(r"host_elapsed_ms=([0-9.]+)")
HEAD = re.compile(r"head_changes=(\d+)")

def parse(path):
    text=path.read_text(errors="replace")
    matched=SUMMARY.findall(text)
    if len(matched)!=1 or "TEST OK" not in text:
        raise ValueError(f"{path}: missing/duplicate valid summary or Cooja TEST OK")
    mode,seed,delivered,timely,probes,data,relayed,searches=map(int,matched[0])
    if "mode"+str(mode) not in path.name:
        raise ValueError(f"{path}: wrong result mode label")
    prefixes={
        "probe": "PROBE_TRACE",
        "data": "SOURCE_TRACE",
        "relay": "RELAY_TRACE",
        "sink": "DATA_TRACE",
    }
    lines={name:[s for s in text.splitlines() if s.startswith(prefix)]
           for name,prefix in prefixes.items()}
    if len(lines["sink"])!=delivered:
        raise ValueError("Sink delivery trace count does not match summary")
    if len(lines["probe"])!=probes or len(lines["data"])!=data:
        raise ValueError("Source callback trace count does not match summary")
    latencies=[float(m.group(1)) for line in lines["sink"]
               for m in [ELAPSED.search(line)] if m]
    if len(latencies)!=delivered or any(t<0 for t in latencies):
        raise ValueError("Missing or invalid globally timed packet delivery")
    if sum(0<=t<=500 for t in latencies)!=timely:
        raise ValueError("Timely delivery calculation mismatch")
    def count_attempts(name):
        attempts=[int(m.group(1)) for line in lines[name]
                  for m in [ATTEMPTS.search(line)] if m]
        if len(attempts)!=len(lines[name]):
            raise ValueError("MAC callback attempts missing")
        return sum(attempts)
    def failures(name):
        statuses=[int(m.group(1)) for line in lines[name]
                  for m in [STATUS.search(line)] if m]
        return sum(status != 0 for status in statuses)
    done=[line for line in text.splitlines() if line.startswith("SENDER_DONE ")]
    changes=HEAD.search(done[0]) if len(done)==1 else None
    if not changes:
        raise ValueError("No valid sender completion")
    return {
        "mode":mode, "seed":seed, "run_id":path.parent.name, "requested":40,
        "PDR":delivered/40.0, "timely_ratio_500ms":timely/40.0,
        "delivered":delivered, "timely":timely,
        "mean_delivered_latency_ms":sum(latencies)/len(latencies) if latencies else None,
        "probes":probes, "source_data_callbacks":data,
        "relay_callbacks":len(lines["relay"]),
        "probe_mac_attempts":count_attempts("probe"),
        "data_mac_attempts":count_attempts("data"),
        "relay_mac_attempts":count_attempts("relay"),
        "probe_mac_failures":failures("probe"),
        "data_mac_failures":failures("data"),
        "relay_mac_failures":failures("relay"),
        "head_searches":searches,"head_changes":int(changes.group(1)),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dir",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    logs=sorted(Path(args.dir).rglob("mode*_testlog.txt"))
    if not logs: raise ValueError("No Cooja test logs found")
    rows=[parse(p) for p in logs]
    groups=defaultdict(dict)
    for r in rows:
        grp=(r["run_id"],r["seed"])
        if r["mode"] in groups[grp]: raise ValueError("Duplicate mode result")
        groups[grp][r["mode"]]=r
    paired=[]
    for (run_id,seed),pair in sorted(groups.items()):
        if set(pair)!={0,1}: raise ValueError(f"Unmatched mode for {run_id} seed{seed}")
        a,b=pair[0],pair[1]
        if a["probes"]!=b["probes"]:
            raise ValueError("Unequal telemetry probe budget")
        paired.append(dict(
            run_id=run_id,seed=seed,
            PDR_conformal_minus_point=b["PDR"]-a["PDR"],
            timely_conformal_minus_point=b["timely_ratio_500ms"]-a["timely_ratio_500ms"],
            source_probe_attempt_difference=b["probe_mac_attempts"]-a["probe_mac_attempts"],
            source_data_attempt_difference=b["data_mac_attempts"]-a["data_mac_attempts"],
            relay_attempt_difference=b["relay_mac_attempts"]-a["relay_mac_attempts"],
        ))
    out=Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.with_suffix(".csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader();w.writerows(rows)
    result=dict(
        status="exploratory_packet_mechanism_only",
        original_40_node_ACR_MCR_port_complete=False,
        mac="Contiki-NG CSMA; IEEE 802.15.4 Cooja emulation",
        model="4 motes, two candidate heads, one source, one sink; no original 8x4 search or full CVaR",
        n_run_pairs=len(paired),
        runs=rows,
        paired_differences=paired,
        measures="ACK/retry callback, end-to-end sink delivery, globally timed packet latency, explicit probe counts",
        missing="No physical power measurement, no multi-source aggregation, no independent hardware validation",
        warning="Do not treat these paired packet-level traces as a full ACR-MCR or hardware experiment."
    )
    out.write_text(json.dumps(result,indent=2)+"\n")
    print(f"PASS {len(rows)} packet-level mode runs, {len(paired)} matched pairs")
    for pr in paired:print(pr)
if __name__=="__main__":main()
