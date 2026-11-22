# Registered before new M3 kernel physical execution, 22 November 2026

Purpose: verify that the portable deterministic C ACR-MCR/CVaR and
POINT-EA reference-input decision kernels actually execute on an
authorized Grenoble FIT IoT-LAB M3 Cortex-M3 board, not merely compile
for it.

Frozen source is original acr_mcr_v2.py SHA256
3f134a8826525215f7cf2ff307bab3893c0d64b050f742bdc3c250b1c0302ea4.
The portable C is generated from the exact make_plan(), fitness(),
empirical_cvar(), and 8-population, four-generation survivor search
rules. The original calibrator's C update and alert already passed
135 fixed-state parity comparisons. Full C fitness+search fixed-state
parity passed 12 synthetic original-state fixtures, 4 including CVaR,
with <2.3e-16 max absolute objective difference.

Hardware method-vs-method comparison uses the SAME real physical
M3-14 board and power profile acr_m3_active_power_20261122. For
initial tests, both method-specific immutable states are produced
from original seed 9401, scenario S1, round 20, 40 nodes. The
original NumPy PCG64 candidate sequence is FROZEN in read-only
firmware FLASH for each method, not reproduced by an embedded RNG.
The original 64x40x41 stress index array is preserved in 9-bit
packed FLASH form (512 rolling calibration records) and expanded
on demand by the C risk callback, not changed or downsampled.

For each method, record: actual firmware SHA256, original fixture SHA,
physical IoT-LAB experiment/reservation, all original UART records,
controller final selected heads, score and absolute error against the
original Python reference, 32 candidate sets, 64 CVaR scenarios
(ACR-MCR), clock ticks, ENERGEST CPU/LPM/TX/LISTEN ticks and any
physical control-node power/current/voltage OML data available.
Hardware PASS requires original objective discrepancy <=1e-7,
matching selected heads and recorded completion; no outcome may
be removed when unfavorable.

This fixture runs **standalone decision computation** on the M3.
It does not ingest live physical MAC feedback, does not replicate
NumPy PCG64 directly on the embedded CPU, and does not distribute
new routing choices to 40 M3 sensors. It is NOT an independent
physical ACR-MCR versus POINT-EA application-service comparison.
Power meter data from M3 cannot establish Apple M1 host optimizer
Joules. Comparing numeric objective values between methods is also
not a service improvement test, because the ACR-MCR objective
contains a separate risk penalty.

Further full controller scientific validation requires source-level
PCG64 random stream parity, actual M3 feedback update and head
search integrated into a radio control task, matched independent
physical trials with complete 41-board ENERGEST and calibrated
sensor-to-sink deadline accounting.
