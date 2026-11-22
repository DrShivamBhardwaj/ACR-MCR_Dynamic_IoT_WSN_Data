#!/usr/bin/env python3
"""Fail-closed final report for independently completed ACR distributed 500B run.

Never infer results from incomplete individual jobs or partial logs.
"""
import argparse, json, statistics, math, pathlib, shutil
SEEDS=list(range(9201,9211))
METHODS=("POINT-EA","ACR-MCR")
METRICS=("PDR_nominal","timely_ratio_nominal")
def analyze(inp,out):
    x=json.loads(pathlib.Path(inp).read_text())
    if (x.get("status")!="PASS" or x.get("registered_runs")!=40 or
        x.get("independent_seed_blocks")!=10 or x.get("seeds")!=SEEDS or
        x.get("scenarios")!=["S1","S5"] or
        not x.get("route_installed_only_by_radio") or
        not x.get("original_optimizer_feedback_from_cooja_MAC") or
        x.get("external_SNR_PER_calibration") is not False):
        raise ValueError("Incomplete, unregistered, or overstated confirmation result")
    rows=x["all_run_audits"]
    if len(rows)!=40 or len({(z["seed"],z["scenario"],z["method"]) for z in rows})!=40:
        raise ValueError("Missing / duplicate confirmation run")
    if len({z["code_source_sha256"] for z in rows})!=1:
        raise ValueError("Mixed protocol source hashes")
    index={(z["seed"],z["scenario"],z["method"]):z for z in rows}
    for seed in SEEDS:
        for regime in ("S1","S5"):
            for method in METHODS:
                z=index[(seed,regime,method)]
                if (z["verification"]!="PASS" or z["rounds"]!=160 or z["nodes"]!=40
                    or z["payload_integrity_errors"]!=0
                    or z["control_receptions"]>6400
                    or not z["complete_8_fragment_payload_verified"]
                    or z["nominal_demand"]!=6400):
                    raise ValueError("A registered raw trace failed integrity")
    lines=["# Independent 500-byte Cooja radio-control confirmation",
       "",
       "Generated from a COMPLETE, independently audited 40-case registration.",
       "Original 1,280-run synthetic model remains immutable.",
       "",
       "40 sensors, one sink, 160 rounds per run, ten paired seed blocks",
       "9201–9210, two Cooja scenarios S1/S5, POINT-EA and ACR-MCR.",
       "Each original 500-byte application sample is eight MAC fragments.",
       "Each controller plan is written to the sink ONLY and delivered to",
       "sensor motes over actual simulated CSMA radio control messages.",
       "",
       "## Registered primary outcomes",
       "",
       "| ACR-MCR minus POINT-EA | Difference (percentage points) | 95% paired CI (pp) | Holm p |",
       "|---|---:|---:|---:|"]
    effects=x["estimates"]
    for name in METRICS:
        o=effects[name]
        e=float(o["estimated_acr_minus_point"])
        lo,hi=map(float,o["ci95"])
        p=float(o["holm_adjusted_p"])
        if not (all(math.isfinite(z) for z in (e,lo,hi,p)) and
                lo<=e<=hi and 0<=p<=1):raise ValueError("Invalid primary stats")
        lines.append(f"| {name} | {100*e:+.3f} | [{100*lo:+.3f}, {100*hi:+.3f}] | {p:.6g} |")
    lines.extend(["","The independent statistical unit is the seed block,",
       "not the count of successful MAC frames or the 40 individual runs.",
       "The confidence intervals describe the registered mean paired",
       "difference over S1/S5, with Holm correction for the two co-primary outcomes.",
       "A result with p >= 0.05 is not proof of equivalence.",
       "",
       "## Descriptive network and telemetry accounting","",
       "| Metric | POINT-EA | ACR-MCR |",
       "|---|---:|---:|"])
    for k,label,fmt in [
       ("PDR_nominal","Mean full 500B PDR","{:.5f}"),
       ("timely_ratio_nominal","Mean completed within 500 ms","{:.5f}"),
       ("control_receptions","Mean installed control node-rounds","{:.1f}"),
       ("controller_control_radio_packets","Mean control frame callbacks","{:.1f}"),
       ("data_fragment_radio_callbacks","Mean data-fragment frame callbacks","{:.1f}"),
       ("total_MAC_callbacks","Mean total MAC callbacks","{:.1f}")]:
        v=[fmt.format(statistics.mean(float(z[k]) for z in rows if z["method"]==m)) for m in METHODS]
        lines.append(f"| {label} | {v[0]} | {v[1]} |")
    for t,name in [("radio_transmit_ticks_seconds","Aggregate Cooja radio TX node-seconds per run"),
                   ("radio_listen_ticks_seconds","Aggregate Cooja radio listen node-seconds per run"),
                   ("cpu_ticks_seconds","Aggregate Cooja CPU node-seconds per run")]:
        v=[statistics.mean(z["energest_aggregate"][t] for z in rows if z["method"]==m) for m in METHODS]
        lines.append(f"| {name} | {v[0]:.3f} | {v[1]:.3f} |")
    sums={m:{k:sum(z[k] for z in rows if z["method"]==m)
             for k in ("source_requests","valid_500byte_reassemblies","timely_500ms",
                       "control_receptions","control_reception_opportunities","payload_integrity_errors")}
          for m in METHODS}
    for m in METHODS:
        if sums[m]["control_reception_opportunities"]!=20*6400:
            raise ValueError("Inconsistent source and per-round denominator")
        if sums[m]["payload_integrity_errors"]!=0:
            raise ValueError("Unverified complete payload")
    lines.extend(["","The 40 runs cover a registered total of 256,000 original",
       "sensor-round demand opportunities (40 sensors x 160 rounds x 40 runs).",
       "Every missed control reception remains part of the nominal source-demand denominator.",
       "Cooja ENERGEST reports dwell-time counters, not physical energy in Joules.",
       "The sink computes each controller plan externally in Python.",
       "",
       "## Independent physical boundary checks",
       "",
       ""])
    # The physical evidence is separate and site-verified, with no ACR power
    # or deployment extrapolation. Explicitly avoid any invented locality.
    lines[-2:]=[
       "Grenoble IoT-LAB M3 experiment 459543 tested a two-board",
       "100-sample, 500-byte/8-fragment physical transfer. All 800 fragment",
       "callbacks and receptions were recorded and 100 reconstructed samples",
       "passed a byte-level integrity audit. Testbed supply-power integration",
       "measured 11.7283 J total device energy over 107.661 s on the TX board",
       "and 11.1273 J over 109.162 s on RX, including idle/CPU/radio operation.",
       "",
       "Separate experiment 459550 used FOUR M3 boards and 50-byte",
       "official radio-characterization packets. For nominal -17, -9, 0, +3 dBm",
       "settings, receiver opportunities succeeded 0/1200, 0/1200,",
       "167/1200 and 198/1200 respectively. Receiver RSSI is conditional",
       "on reception. No calibrated input SNR or full deployed-controller",
       "energy data were obtained.",
       "",
       "## Inference limits",
       "",
       "These Cooja runs use two limited radio regimes, not all five",
       "disturbance laws or exact offered-load timing of the original model.",
       "Control messages are radio-delivered but the Python decision program",
       "still runs off-mote. Neither Cooja dwell time nor a two-board physical",
       "power measurement accounts for full network CPU/computation energy.",
       "Do not call this a calibrated SNR–PER experiment or a full physical",
       "40-node adaptive controller deployment.",
       "",
       "The cited comparative literature remains the 18 references supplied",
       "in the earlier manuscript; verified additional source synthesis is [NEED SOURCE].",
       "Any algorithmic novelty or claims of superiority must follow the",
       "observed effects and the complete peer-reviewed literature, not a",
       "desired result.",
       "",
       f"Firmware Cooja source SHA256: {next(iter({z['code_source_sha256'] for z in rows}))}",
       ""
    ]
    out=pathlib.Path(out)
    out.parent.mkdir(exist_ok=True,parents=True)
    out.write_text("\n".join(lines))
    print("COMPLETE_40_CASE_REPORT_WRITTEN",out)
    print("MEANS",json.dumps(sums))
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    analyze(args.input,args.out)
