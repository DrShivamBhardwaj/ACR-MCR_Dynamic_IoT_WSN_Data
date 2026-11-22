# Physical baseline scheduler reallocation V3, before any V3 data

Previous POINT-EA reservation failed WITHOUT execution, because the
IoT-LAB scheduler rejected eight boards marked Suspected, even though
a preflight returned success. Full rejected request and error are kept
in the first attempt folder. The original shared V2 layout is not changed.

V3 replaces physical device mapping ONLY from the current 258 Alive
Grenoble M3 list using the already published compact 41-node selector.
Both POINT-EA and ACR-MCR will use precisely the SAME V3 physical
mapping (logical IDs 1..40/41), as separate physical reservations.
The original Python seed9401 S5 round20 frozen candidate/stress values,
selected-head algorithm, code, 500-byte sample generation and 3-round
denominator are UNCHANGED. The 40 member firmware binaries are unchanged,
and each sink uses the existing source-hashed POINT-EA or ACR-MCR
onboard original deterministic kernel firmware.
These are engineering radio comparisons with one physical block per method,
not randomized independent-seed evidence. Live link observations do not
feed back to the next decisions.
