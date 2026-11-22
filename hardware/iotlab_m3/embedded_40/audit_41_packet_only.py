#!/usr/bin/env python3
"""Separate, explicitly limited 41-board packet audit after missing one ENERGEST.

DOES NOT override or replace the original strict 41-node combined audit;
that audit remains INCOMPLETE. This is engineering feasibility evidence,
not independent scientific proof of original ACR-MCR algorithm performance.
"""
import argparse,hashlib,json,sys
from pathlib import Path
from audit_41_physical import audit
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--capture-dir",required=True)
    p.add_argument("--topology",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    res=audit(a.capture_dir,a.topology)
    energy_failures=[x for x in res["failures"] if "ENERGEST" in x]
    nonenergy=[x for x in res["failures"] if "ENERGEST" not in x]
    if nonenergy:raise ValueError("Packet audit must not accept non-energy integrity failure: "+str(nonenergy))
    if res["observed_board_count"]!=41 or res["expected_real_sensor_nodes"]!=40:
        raise ValueError("Require all 41 original hardware serial traces")
    if not 0<=res["sink_unique_500B_reassemblies"]<=res["observed_data_demand_records"]<=120:
        raise ValueError("Impossible physical 500B sample receipts/demand")
    if not 0<=res["physically_radio_delivered_control_installs"]<=120:
        raise ValueError("Impossible physical radio-control count")
    pdir=Path(a.capture_dir)
    sink=[p for p in pdir.glob("*logical-41.serial.log")]
    if len(sink)!=1:raise ValueError("Missing unique actual sink UART")
    raw=sink[0].read_text(errors="replace")
    if "DIST_DONE" not in raw:raise ValueError("Sink controller did not end")
    if "SINK_BAD_PAYLOAD" in raw:raise ValueError("At least one complete 500-byte content failure")
    monitored=sum(1 for v in res["per_node_energest_records"].values() if v==1)
    report=dict(
      experiment=res["experiment"],
      verdict="PASS_PHYSICAL_STATIC_ROUTE_PACKET_FORMAT_ONLY",
      reviewer_level_claim="40 real M3 source nodes and one sink ran over-air fixed-head transport in one 3-round block.",
      original_strict_all_measurement_audit="INCOMPLETE",
      original_strict_audit_failures=res["failures"],
      counted_source_nodes=40,counted_sink_nodes=1,
      nominal_500byte_sample_opportunities=120,
      control_installed_rounds=res["physically_radio_delivered_control_installs"],
      source_data_demands_seen=res["observed_data_demand_records"],
      verified_500byte_completed_samples=res["sink_unique_500B_reassemblies"],
      observed_nominal_delivery_ratio=res["physical_500B_success_over_nominal"],
      physical_control_radio=True,physically_reassembled_500bytes=True,
      physical_radio_energest_complete=False,
      energy_node_records=monitored,
      energy_records_expected=41,
      omitted_energy_nodes=[int(k) for k,v in res["per_node_energest_records"].items() if v!=1],
      adaptive_conformal_algorithm_executed=False,
      complete_embedded_acr_mcr_optimizer_executed=False,
      true_end_to_end_500ms_delay_measured=False,
      limitations="Exploratory one-block physical static fixed-head controller; no independent 10-seed adaptive ACR-MCR; no synchronized source/sink clocks or 41-board absolute energy; 40/41 ENERGEST."
    )
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
