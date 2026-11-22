# Frozen Apple M1 host runtime benchmark

Registered before the host benchmark outcome. Matched POINT-EA versus
ACR-MCR in the ORIGINAL unchanged acr_mcr_v2.py Python simulator:
40 nodes, 160 rounds, probes 1, scenarios S1 and S5, untouched seeds
10301–10310, 40 process-isolated outcomes. Alternate method order by
seed to reduce systematic warmup/thermal order effects. Preserve
per-run process user/system CPU seconds, total process wall seconds,
controller-select instrumented wall seconds, search/evaluation counts.
No experiment result is removed on grounds of unexpected slowdown.

Machine: MacBook Air Apple M1, 8GB RAM. Unprivileged powermetrics
returned 'must be invoked as the superuser'. Remote command facility
blocks sudo. AC-connected battery sensors display zero net charge
current; they are not a processor energy sensor.

Physical host Joules are NOT measured. Neither a duty-cycle model nor
process CPU seconds may be converted to Joules without real calibrated
power samples. Proper energy calibration needs an authorized root
powermetrics session or external AC meter with synchronized timestamps
and comparable idle baseline. Host CPU time from the original simulator
is not equivalent to physical energy of the Python optimizer.
