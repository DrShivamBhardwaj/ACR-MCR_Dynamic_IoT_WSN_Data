#!/usr/bin/env python3
"""Integrate NEW ACR M3 real supplied power, current and voltage OML records.

These are physical device-level total DC energies over monitored intervals.
Do not infer radio-only or per-packet electrical energy; baseline and host
Python controller energy are not measured.
"""
import argparse,hashlib,json,statistics
from pathlib import Path

def parse(path):
    rows=[]
    schema_found=False
    for line in path.read_text(errors="replace").splitlines():
        if "schema: 1 control_node_measures_consumption" in line:schema_found=True
        fields=line.split()
        if len(fields)!=8 or fields[1]!="1":continue
        try:
            t=int(fields[3])+int(fields[4])/1e6
            power=float(fields[5])
            voltage=float(fields[6])
            current=float(fields[7])
        except ValueError:continue
        if not 0<power<3 or not 1.5<voltage<5 or not 0<current<1:
            raise ValueError(f"Implausible physical power or voltage sample in {path}")
        if abs(power-voltage*current)>max(.007,power*.07):
            raise ValueError("Power and voltage/current instrument channels inconsistent")
        rows.append((t,power,voltage,current))
    if not schema_found or len(rows)<25:
        raise ValueError(f"Missing original consumption schema or insufficient samples {path} ({len(rows)})")
    if any(b[0]<=a[0] for a,b in zip(rows,rows[1:])):
        raise ValueError("Non-monotonic physical monitor timestamps")
    joules=sum((a[1]+b[1])*.5*(b[0]-a[0]) for a,b in zip(rows,rows[1:]))
    duration=rows[-1][0]-rows[0][0]
    if duration<40 or duration>1800:raise ValueError("Insufficient or impossible monitoring duration")
    return dict(
        device=path.stem,
        number_of_physical_samples=len(rows),
        first_timestamp_seconds=rows[0][0],
        last_timestamp_seconds=rows[-1][0],
        duration_s=duration,
        total_supplied_electrical_energy_j=joules,
        time_average_total_power_w=joules/duration,
        mean_supply_voltage_v=statistics.mean(x[2] for x in rows),
        mean_supply_current_a=statistics.mean(x[3] for x in rows),
        max_monitor_gap_s=max(b[0]-a[0] for a,b in zip(rows,rows[1:])),
        raw_file_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--monitor-dir",required=True)
    ap.add_argument("--experiment",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    p=Path(args.monitor_dir)
    files=sorted(p.glob("m3_*.oml"))
    if len(files)!=2 or {f.stem for f in files}!={"m3_14","m3_15"}:
        raise ValueError(f"Expected power/current/voltage OML for precisely M3-14 and M3-15; got {[q.name for q in files]}")
    data=[parse(file) for file in files]
    report=dict(
        verification="PASS",
        iotlab_experiment_id=int(args.experiment),
        measurement_site="FIT IoT-LAB Grenoble",
        power_profile="acr_m3_active_power_20261122",
        measured_quantities=["device_supply_power_w","device_supply_voltage_v","device_supply_current_a"],
        independent_new_firmware=True,
        roles={"m3_14":"TX, 100 times 500B eight-fragment source","m3_15":"RX, real 500B reassembly"},
        per_board=data,
        physical_total_energy_measured=True,
        transmission_only_power_measured=False,
        host_optimizer_CPU_energy_measured=False,
        time_resolved_packet_energy_attribution=False,
        energy_harvesting_or_energy_neutrality_validated=False,
        externally_calibrated_SNR_PER=False,
        limits="Active external DC supplied M3 boards; baseline CPU/radio/serial included in device power, so no per-packet physical energy estimate, no 40-node distributed optimizer power. Firmware is a transport-only hardware pilot.")
    out=Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
