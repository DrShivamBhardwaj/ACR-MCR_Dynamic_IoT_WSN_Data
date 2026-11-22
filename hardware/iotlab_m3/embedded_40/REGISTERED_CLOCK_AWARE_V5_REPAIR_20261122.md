# Clock-corrected V5 physical source-locked repeat, registered before data

22 November 2026. Original new simulator seed9402 S5 round20 unchanged.
After initial development sessions 459600/459602, the site-clock
calibration exposed a measurable difference: Grenoble frontend UTC was
about 185.8s BEHIND the Apple M1 Mac UTC, with RTT uncertainty.
The previous UART collector v3 incorrectly compared raw timestamps
from different clocks and rejected ALL 41 streams as pre-reservation.
Its impossible pre-reservation flag is preserved in original logs.
Clock-corrected earliest arrivals for 459600 and 459602 were 22.83s
and 36.64s after the corresponding reservations, respectively.
Original v3 source-identity BOOT was often emitted before TCP capture
attached, so missing boot marker alone must be reported as an
instrumentation limitation, not a packet integrity failure. Physical
sink actual ONBOARD_OPT_READY must separately contain correct fixture,
risk mode, predicted objective and candidate heads, and the site
deployment must match submitted 41 hashed firmware images.

A second issue was identified BEFORE this repeat: runner seed9402
accidentally selected V4 member firmware even though protocol had
frozen V5. This repeat pins source SHA256 e4d15f7bb5ec35ee7177e7b154851619b7b19b3e9fb8fe4c0d5e4e285947f312,
all 40 existing V5 member firmware hashes from the archived
41_firmware_manifest_v5.json, original fixed physical layout
41node_physical_layout_v4.json and the independent seed9402
method-specific original C kernel sink binaries. No route algorithm,
RF setting, Python source, risk objective, head-search candidate
genotypes or offered load is revised. Use three 20-second
rounds and denominator 120. Both methods must pass real sink
ONBOARD_OPT_READY and 41 original UART streams, real 500B
byte-reassembly and physical control tracking; losses remain measured
outcomes. Quantify total device ENERGEST coverage independently.

The source-dependent policy is frozen from original synthetic
observations, not live physical PHY observations; the study remains
a hardware engineering replication, NOT a complete physical
feedback-driven ACR-MCR controller validation. No physical
500-ms deadline inference or physical M1 host Joule inference.
Original rejected, incomplete, V4 and V5 developer test traces
are retained without deletions or favorable-outcome selection.
