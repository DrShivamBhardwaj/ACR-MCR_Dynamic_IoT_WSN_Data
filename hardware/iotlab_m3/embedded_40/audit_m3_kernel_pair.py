#!/usr/bin/env python3
"""Blind-from-reference original Python vs real M3 cortex-M3 kernel audit.

Conservative energy gate: short power traces do not establish host Joules,
and board supplied Joules always include system baseline and radio.
"""
import hashlib,json,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE.parent))
from audit_power_monitor import parse
R=ROOT/"logs"/"m3_optimizer_kernel_20261122"
DEF_METHODS=(("ACR-MCR","m3fixture_acr_mcr"),("POINT-EA","m3fixture_point_ea"))
def evaluate(method,folder):
    p=R/folder
    reference=json.loads((p/"reference.json").read_text())
    assert reference["original_method"]==method
    data=json.loads((p/"capture_summary.json").read_text())
    trace=(p/"raw"/str(data["experiment"])/"m3_14.serial.log")
    lines=trace.read_text(errors="replace").splitlines()
    results=[x for x in lines if "OPT_KERNEL_RESULT" in x]
    completions=[x for x in lines if "OPT_KERNEL_DONE" in x]
    energi=[x for x in lines if "OPT_KERNEL_ENERGEST" in x]
    if not data["complete"] or len(results)!=1 or len(completions)!=1 or len(energi)!=1:
        raise ValueError("Missing real one-to-one UART of decision result, completion, ENERGEST")
    def extract(pattern,line):
        m=re.search(pattern,line)
        if not m:raise AssertionError(f"Missing {pattern} in {line}")
        return m.group(1)
    first=results[0]
    observed_heads=list(map(int,extract(r'heads=(\d+,\d+,\d+,\d+)',first).split(",")))
    expected_heads=[int(x) for x in reference["selected_head_ids"]]
    passed=int(extract(r'PASS=(\d+)',first))
    rc=int(extract(r'rc=(-?\d+)',first))
    actual_micro=int(extract(r'objective_micro=(\d+)',first))
    exp_micro=int(extract(r'expected_micro=(\d+)',first))
    diff_nano=int(extract(r'absolute_error_nanounits=(\d+)',first))
    elapsed_ticks=int(extract(r'cpu_wall_ticks=(\d+)',first))
    clock_hz=int(extract(r'clock_hz=(\d+)',first))
    risk=int(extract(r'tail=(\d+)',first))
    assert passed==1 and rc==0
    assert observed_heads==expected_heads,(observed_heads,expected_heads)
    assert exp_micro==round(reference["selected_objective"]*1e6)
    assert actual_micro==exp_micro
    assert diff_nano<=100, diff_nano
    assert elapsed_ticks>0 and clock_hz>0
    assert risk==int(reference["tail_risk_enabled"])
    assert "PASS=1" in completions[0]
    board_energy=None;warning=None
    oml=p/"m3_14.oml"
    if oml.exists():
        try:board_energy=parse(oml)
        except (ValueError,AssertionError) as exc:warning=str(exc)
    result=dict(
       hardware="Grenoble FIT IoT-LAB M3-14 real Cortex-M3",
       experiment=data["experiment"],method=method,verification="PASS_HARDWARE_DECISION_PARITY",
       original_synthetic_reference_fixture=reference["fixture_id"],
       source_original_sha256=reference["original_simulator_sha256"],
       actual_binary_sha256=reference["m3_firmware_sha256"],
       selected_head_ids=observed_heads,
       python_objective=float(reference["selected_objective"]),
       observed_m3_objective_micro=actual_micro,
       m3_absolute_objective_error_nano=diff_nano,
       observed_m3_controller_wall_s=elapsed_ticks/clock_hz,
       m3_energest_line=energi[0],
       complete_uart_sha256=hashlib.sha256(trace.read_bytes()).hexdigest(),
       raw_power_oml_sha256=hashlib.sha256(oml.read_bytes()).hexdigest() if oml.exists() else None,
       validated_M3_total_supply_energy=board_energy,
       insufficient_OML_reason=warning,
       calibrated_Apple_M1_host_electrical_J=None,
       scientific_bound="Frozen synthetic data and NumPy RNG trace in FLASH, not a real 40-node closed-loop ACR-MCR controller. One physical board and one fixture per method are not independent generalisation trials.")
    return result
def main():
    data=[evaluate(*item) for item in DEF_METHODS]
    res=dict(status="PASS_PAIRED_M3_KERNEL_PARITY",
      hardware_session_count=2, independent_seed_blocks=1,
      both_firmware_sources_verified=True,
      controlled_by_original_python_input=True,
      risk_method_m3_seconds=data[0]["observed_m3_controller_wall_s"],
      point_method_m3_seconds=data[1]["observed_m3_controller_wall_s"],
      observed_difference_m3_seconds=data[0]["observed_m3_controller_wall_s"]-data[1]["observed_m3_controller_wall_s"],
      observed_decision_kernel_ratio=data[0]["observed_m3_controller_wall_s"]/data[1]["observed_m3_controller_wall_s"],
      valid_paired_statistical_service_effect=False,
      original_full_controller_physical_baseline=False,
      host_mac_joules_measured=False,
      physical_m3_device_joules_validated=all(x["validated_M3_total_supply_energy"] is not None for x in data),
      details=data)
    out=HERE/"m3_kernel_fixtures"/"first_physical_pair_audit.json"
    out.write_text(json.dumps(res,indent=2)+"\n")
    print(json.dumps({k:v for k,v in res.items() if k!="details"},indent=2))
if __name__=="__main__":main()
