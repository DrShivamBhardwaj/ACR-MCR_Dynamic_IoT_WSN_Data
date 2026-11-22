#!/usr/bin/env python3
"""Reject incomplete or inconsistent Cooja feedback-controller runs.

Observed simulator packet traffic is evaluated against ALL 40 source-round
demands. This is centralized-control closed-loop, not distributed validation.
"""
import argparse,hashlib,json,re
from pathlib import Path
from collections import defaultdict

ROUND=re.compile(r"ROUND_PACKET_AUDIT round=(\d+) requested=(\d+) unique_sink=(\d+) timely500=(\d+) MAC_callbacks=(\d+)")
CLOSED=re.compile(r"CLOSED_LOOP_COMPLETE method=(POINT-EA|ACR-MCR) seed=(\d+) observed_rounds=(\d+) plans=(\d+)")

def audit(path,method,seed,scenario,rounds):
    log=(path/"COOJA.testlog").read_text(errors="replace")
    origin=json.loads((path/"controller.summary.json").read_text())
    observations=[json.loads(line) for line in (path/"controller.jsonl").read_text().splitlines()]
    expected=int(rounds)
    plans=[x["plan"] for x in observations if "plan" in x]
    measured=[x["observation"] for x in observations if "observation" in x]
    rows=[tuple(map(int,m.groups())) for m in ROUND.finditer(log)]
    complete=CLOSED.findall(log)
    if "TEST OK" not in log or len(complete)!=1:
        raise ValueError("Cooja test failed or incomplete")
    if complete[0] != (method,str(seed),str(expected),str(expected)):
        raise ValueError("Cooja method/seed/round identity mismatch")
    if len(plans)!=expected or len(measured)!=expected or len(rows)!=expected:
        raise ValueError(f"Missing plans/observations: {len(plans)}/{len(measured)}/{len(rows)}")
    for t,(p,o,r) in enumerate(zip(plans,measured,rows)):
        if p["round"]!=t or o["round"]!=t or r[0]!=t:
            raise ValueError(f"Non-sequential feedback at round {t}")
        if len(p["next"])!=40 or len(p["enabled"])!=40 or len(p["probes"])!=40:
            raise ValueError("Invalid 40-node route/probe plan")
        if any(v not in range(42) for v in p["next"]):
            raise ValueError("Invalid next hop")
        if not (0<=r[3]<=r[2]<=r[1]<=40):
            raise ValueError("Impossible per-round packet count")
        if r[4]!=o["mac_callbacks"] or r[2]!=o["sink_unique"] or r[3]!=o["timely500"]:
            raise ValueError("Python bridge and Cooja trace disagree")
        if o["probes_used"]>r[4]:
            raise ValueError("Probe accounting inconsistent")
    if not origin.get("closed_loop_packet_feedback") or origin.get("distributed_control_packets"):
        raise ValueError("Scientific scope flags wrong")
    if origin["recorded_epochs"]!=expected or origin["seed"]!=seed or origin["method"]!=method:
        raise ValueError("Controller report metadata mismatch")
    collected=sum(x[1] for x in rows)
    delivered=sum(x[2] for x in rows)
    timely=sum(x[3] for x in rows)
    mac=sum(x[4] for x in rows)
    return dict(
        verification="PASS",method=method,scenario=scenario,seed=seed,
        nodes=40,rounds=rounds,nominal_demand=40*rounds,
        requests_queued=collected,unique_sink=delivered,timely500=timely,
        PDR_on_all_demand=delivered/(40*rounds),
        timely_ratio_on_all_demand=timely/(40*rounds),
        observed_MAC_callbacks=mac,
        feedback_rounds=len(measured),
        actual_probe_callbacks=sum(x["probes_used"] for x in measured),
        alpha_update_after_warmup=(
            len({round(x["alpha_cost"],6) for x in measured[20:]})>1
            if method=="ACR-MCR" and rounds>20 else None),
        controller_searches=origin["controller_searches"],
        source_sha256=hashlib.sha256((Path(__file__).resolve().parents[1]/"acr_mcr_v2.py").read_bytes()).hexdigest(),
        original_optimizer_update_feedback="Cooja MAC/ACK/duration observations",
        external_control="simulator-memory injection (no actual control packets)",
        original_payload_500B=False,
        physical_radio_energy=False
    )

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-dir",required=True)
    ap.add_argument("--method",choices=["POINT-EA","ACR-MCR"],required=True)
    ap.add_argument("--seed",type=int,required=True)
    ap.add_argument("--scenario",choices=["S0","S1","S2","S3","S4","S5"],required=True)
    ap.add_argument("--rounds",type=int,required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    result=audit(Path(a.run_dir),a.method,a.seed,a.scenario,a.rounds)
    out=Path(a.out);out.parent.mkdir(exist_ok=True,parents=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
