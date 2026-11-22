# Incomplete physical on-M3 original frozen risk versus point trials V3

POINT-EA experiment459586 (source-locked original frozen kernel PASS):
40/41 physical source/sink serial logs, 117/120 radio-control
installations, 42 logged source-demand messages, 33/120 byte-verified
500B deliveries, 39/41 ENERGEST. ACR-MCR experiment459587
(frozen source-locked on-M3 original CVaR/head search PASS): 40/41
serial logs, 78/120 radio-control installations, 0 source-demand
records, 0/120 500B sink deliveries, 39/41 ENERGEST.

Both testbeds used identical V3 physical logical 40+1 board mapping
and original frozen synthetic seed9401 S5 round20. In both sessions
physical M3-291 logical14 failed serial acquisition. The sender's
original DATA clock was derived from a local board timer rather than
being armed after actual over-the-air control reception; the raw
control-installations without subsequent DATA demands suggest this
implementation timing problem. A newly registered V4 experiment
replaces the control-to-data scheduling, replacing only this transport
timer mechanism, with the original on-M3 method-specific optimizer
firmware and synthetic fixture UNCHANGED.

No valid statistical hypothesis test or comparative physical
controller service claim may be made from these incomplete traces.
Raw unsuccessful trial logs and negative evidence are preserved.
The ACR optimizer and physical radio are open-loop; the original
adaptive controller still does not consume physical feedback.
