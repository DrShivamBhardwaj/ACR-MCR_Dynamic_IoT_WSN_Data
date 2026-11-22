#!/usr/bin/env python3
"""Audit the new Grenoble IoT-LAB 459542 hardware run without guessing lost packets.

Do not infer full-cohort PER from this trace: UART started at sample 8.
The sender firmware reports 100 offered samples, but the capture records
sample IDs 8..99 only; missing 0..7 are neither successes nor failures.
"""
import argparse,hashlib,json,re
from pathlib import Path

TX=re.compile(r"ACR_TX seq=(\d+) part=(\d+) bytes=(\d+)")
ACK=re.compile(r"ACR_MAC seq=(\d+) part=(\d+) status=(\d+) attempts=(\d+)")
RX=re.compile(r"ACR_RX seq=(\d+) part=(\d+) len=(\d+) phy_rssi_reg=(\d+) phy_ed_reg=(\d+)")
COMP=re.compile(r"ACR_REASSEMBLED seq=(\d+) bytes=(\d+) integrity=(\d+)")
DONE=re.compile(r"ACR_TX_COMPLETE samples=(\d+) callbacks=(\d+) ack_ok=(\d+) ack_fail=(\d+)")
ENERG=re.compile(r"ACR_ENERGEST role=(\d+) cpu=(\d+) lpm=(\d+) tx=(\d+) listen=(\d+) hz=(\d+)")
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def audit(root):
    root=Path(root)
    snd=root/"m3-14.serial.log"
    rcv=root/"m3-15.serial.log"
    a=snd.read_text(errors="replace")
    b=rcv.read_text(errors="replace")
    tx=[tuple(map(int,x)) for x in TX.findall(a)]
    ack=[tuple(map(int,x)) for x in ACK.findall(a)]
    rx=[tuple(map(int,x)) for x in RX.findall(b)]
    full=[tuple(map(int,x)) for x in COMP.findall(b)]
    final=[tuple(map(int,x)) for x in DONE.findall(a)]
    ene_sender=[tuple(map(int,x)) for x in ENERG.findall(a)]
    ene_receiver=[tuple(map(int,x)) for x in ENERG.findall(b)]
    if len(final)!=1 or final[0]!=(100,800,800,0):
        raise ValueError("Physical sender did not confirm exact 100-sample run")
    if len(tx)!=len(ack) or not tx or not rx or not full:
        raise ValueError("Missing paired physical MAC/receiver evidence")
    if len(set((s,p) for s,p,_ in tx))!=len(tx):
        raise ValueError("TX log duplicate fragment IDs")
    if len(set((s,p) for s,p,_,_ in ack))!=len(ack):
        raise ValueError("ACK log duplicate IDs")
    if len(set((s,p) for s,p,_,_,_ in rx))!=len(rx):
        raise ValueError("Physical receive log duplicate fragment IDs")
    if any(status!=0 or attempts<=0 for s,p,status,attempts in ack):
        raise ValueError("Not all captured MAC callbacks successful")
    if {(s,p) for s,p,_ in tx}!={(s,p) for s,p,_,_ in ack}:
        raise ValueError("Sender MAC callback IDs do not match captured offers")
    if {(s,p) for s,p,_ in tx}!={(s,p) for s,p,_,_,_ in rx}:
        raise ValueError("Missing receiver fragment within overlap")
    if any((frag==7 and size!=52) or (frag<7 and size!=64) for s,frag,size in tx):
        raise ValueError("Wrong application fragment size")
    if any((frag==7 and size!=57) or (frag<7 and size!=69) for s,frag,size,rawr,rawe in rx):
        raise ValueError("Wrong over-air packet payload length")
    if any(size!=500 or intact!=1 for seq,size,intact in full):
        raise ValueError("A fully reassembled payload failed integrity check")
    ids=sorted({s for s,p,_ in tx})
    if ids!=list(range(ids[0],ids[-1]+1)):
        raise ValueError("Captured source sample IDs not contiguous")
    if len(ids)*8!=len(tx):
        raise ValueError("Captured source samples lack one of 8 fragments")
    if [(x[0]) for x in full]!=ids:
        raise ValueError("Completed application samples are not exactly captured offers")
    if not ene_sender or not ene_receiver:
        raise ValueError("Missing original M3 ENERGEST counters")
    summary=dict(
      verification="PASS",experiment=root.name,site="Grenoble",boards=["M3-14","M3-15"],
      transmitter_uart_sha256=sha(snd),receiver_uart_sha256=sha(rcv),
      original_source_offers_reported=100,original_source_callback_count_reported=800,
      original_source_ACK_success_reported=800,
      capture_starts_at_sample=int(ids[0]),capture_ends_at_sample=int(ids[-1]),
      excluded_uncaptured_source_samples=list(range(ids[0])),
      capture_complete_for_original_100_samples=(ids==list(range(100))),
      captured_matched_source_samples=len(ids),
      captured_matched_fragment_pairs=len(tx),
      captured_valid_500byte_reassemblies=len(full),
      captured_phy_register_count=len(rx),
      recorded_payload_integrity_failures=0,
      captured_window_fragment_delivery_ratio=len(rx)/len(tx),
      captured_window_full_sample_delivery_ratio=len(full)/len(ids),
      full_100_sample_PER_estimate_allowed=(ids==list(range(100))),
      received_register_values_unverified_rssi_or_snr=True,
      sender_radio_energest_last=dict(zip(("role","cpu_ticks","lpm_ticks","tx_ticks","listen_ticks","tick_rate"),ene_sender[-1])),
      receiver_radio_energest_last=dict(zip(("role","cpu_ticks","lpm_ticks","tx_ticks","listen_ticks","tick_rate"),ene_receiver[-1])),
      physical_power_monitor_not_audited_in_this_trace_module=True,
      source_original_controller_executed_on_hardware=False,
      limitations="Physical 2-board transport, not 40-node controller; initial UART frames uncaptured; radio register values uncalibrated; ENERGEST cannot yield Joules without currents/voltage.")
    return summary
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--capture-dir",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    result=audit(args.capture_dir)
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if "sha" not in k},indent=2))
