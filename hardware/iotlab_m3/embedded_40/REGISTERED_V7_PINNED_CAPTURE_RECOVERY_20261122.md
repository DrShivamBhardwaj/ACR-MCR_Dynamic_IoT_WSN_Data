# Preregistered repair of failed ACR-MCR-only V6 UART capture

22 Nov 2026, before any new reservation.

The original POINT-EA seed9402 S5 round20 M3 experiment **459607**
passed 41/41 real firmware flash, 41 captured UART streams,
41 final ENERGEST and source-locked original frozen kernel.
Its outcome 47/120 complete verified 500-byte deliveries is locked.

The corresponding original ACR-MCR experiment **459611** passed
41/41 physical flash but was correctly rejected: four UART
streams were not connected, though 50 complete sink receipts were
observed. Investigation identified a **cross-experiment shared
filename race**: remote frontend capture used
~/acr_m3_transport_41/physical_layout.json. An independent account
reservation overwrote it during execution, changing logical
source31 back from M3-196 to M3-215 and/or other endpoints. The
actual old observations remain archived but cannot enter comparison.

For this single defective arm only, rerun with the exact original
40 source firmware V5 SHA256 e4d15f7bb5ec35ee7177e7b154851619b7b19b3e9fb8fe4c0d5e4e285947f312,
original seed9402 S5 round20 risk firmware and selected
40+1 M3 physical layout V6, and require real IoT-LAB
deployment status zero for all 41. Capture now reads a
UNIQUE, read-only-intended hash-pinned file
registered_v6_seed9402_layout_b3.json, not the shared name.
This does NOT change source data, optimizer, methods,
channel, controller's 8x4 candidate search, risk
objective, application 500B, three 20s rounds or
nominal 120 source-round denominator.

The original POINT-EA arm is not rerun or substituted,
and **every ACR rerun failure remains archived**.
The pair is nonrandomized, one synthetic seed, frozen original
predictor/RNG state, not a full live closed-loop adaptive
controller or statistical claim of service improvement.
No Apple M1 real host Joules have been measured.
