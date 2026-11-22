#!/usr/bin/env python3
"""Strict physical M3 repeated-decision/parity + external board-power audit.

Never interpret board-supply joules as the Apple M1 optimizer's joules.
No independent network throughput/PDR validation is contained here.
"""
import hashlib,json,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE.parent))
from audit_power_monitor import parse
R=ROOT/"logs"/"m3_optimizer_kernel_energy_extended_20261122"
def extract(pattern,text):
    m=re.search(pattern,text)
    if not m:raise ValueError("Malformed UART missing "+pattern)
    return m.group(1)
def check(method,folder):
    p=R/folder
    ref=json.loads((p/"reference_extended.json").read_text())
    e=int(json.loads((p/"capture_summary.json").read_text())["experiment"])
    assert ref["original_method"]==method and ref["repeated_identical_kernel_calls"]==20
    rawfile=p/"raw"/str(e)/"m3_14.serial.log"
    raw=rawfile.read_text(errors="replace")
    result=[ln for ln in raw.splitlines() if "OPT_KERNEL_RESULT" in ln]
    repeat=[ln for ln in raw.splitlines() if "OPT_KERNEL_REPETITIONS" in ln]
    done=[ln for ln in raw.splitlines() if "OPT_KERNEL_DONE" in ln]
    eng=[ln for ln in raw.splitlines() if "OPT_KERNEL_ENERGEST" in ln]
    if [len(x) for x in (result,repeat,done,eng)] != [1,1,1,1]:
        raise ValueError("Incomplete or duplicate original raw UART/ENERGEST entries")
    assert "PASS=1" in result[0] and "PASS=1" in done[0]
    n=int(extract(r'count=(\d+)',repeat[0]))
    assert n==20 and extract(r'allpass=(\d+)',repeat[0])=='1'
    selected=list(map(int,extract(r'heads=(\d+,\d+,\d+,\d+)',result[0]).split(",")))
    assert selected==ref["selected_head_ids"],(selected,ref["selected_head_ids"])
    error=int(extract(r'absolute_error_nanounits=(\d+)',result[0]))
    assert error<=100,error
    ticks=int(extract(r'sum_ticks=(\d+)',repeat[0]))
    hz=int(extract(r'hz=(\d+)',repeat[0]))
    assert ticks>0 and hz>0
    omlfile=p/"m3_14.oml"
    instrument=parse(omlfile)  # unchanged >25 samples, >40s and channel checks
    assert int(instrument["number_of_physical_samples"])>=25
    assert float(instrument["duration_s"])>=40
    return dict(
      experiment=e,method=method,
      physical_site="FIT IoT-LAB Grenoble",
      real_board="M3-14",
      fixture_id=ref["fixture_id"],
      firmware_sha256=ref["extended_elf_sha256"],
      reference_method=ref["original_method"],
      physical_execution_status="PASS_20_ITERATIONS_REFERENCE_PARITY",
      independent_topology_seeds=1,
      repeated_same_fixture_invocations=n,
      total_decision_kernel_wall_seconds=ticks/hz,
      average_kernel_wall_seconds_per_repeat=ticks/(hz*n),
      observed_heads=selected,
      objective_error_nanounits=error,
      original_uart_sha256=hashlib.sha256(rawfile.read_bytes()).hexdigest(),
      M3_power_data=instrument,
      measured_Apple_M1_host_optimizer_electrical_J=None,
      on_mote_adaptive_real_radio_feedback=False)
def main():
    pairs=[check("ACR-MCR","m3fixture_acr_mcr"),
           check("POINT-EA","m3fixture_point_ea")]
    result=dict(
      verdict="PASS_TWO_PHYSICAL_M3_KERNEL_SUPPLY_POWER_RECORDS",
      real_physical_board="M3-14",
      source_locked_original_seed=9401,scenario="S1",round=20,
      independent_seed_blocks=1,
      repeated_compute_invocations_per_method=20,
      verified_M3_external_device_supplied_energy_J=True,
      verified_M1_host_electrical_energy_J=False,
      comparison_scope="Original C deterministic decision kernel only; the two different original method objectives are not comparable service metrics",
      limitations="Device power integrates all board activity and monitoring intervals, not isolated processor execution energy; no randomized multi-seed physical controller, not calibrated M1 host energy, no 40-node physical adaptive routing parity.",
      cases=pairs)
    o=HERE/"m3_kernel_fixtures"/"extended_power_pair_audit.json"
    o.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="cases"},indent=2))
    for p in pairs:
        v=p["M3_power_data"]
        print("REAL_M3_POWER",p["method"],"EXPERIMENT",p["experiment"],
              "J",v["total_supplied_electrical_energy_j"],
              "DURATION",v["duration_s"],"W",v["time_average_total_power_w"],
              "SAMPLES",v["number_of_physical_samples"],
              "KERNEL_S",p["total_decision_kernel_wall_seconds"])
if __name__=="__main__":main()
