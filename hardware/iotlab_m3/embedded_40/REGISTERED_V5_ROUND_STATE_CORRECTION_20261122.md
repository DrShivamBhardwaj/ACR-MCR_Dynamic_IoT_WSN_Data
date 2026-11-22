# Second physical source scheduling fix, frozen BEFORE V5 deployment

After inspecting V4 C source, before ANY V4 firmware was physically
deployed, the V4 orchestration was cancelled. Its complete 40-native
firmware build logs remain preserved as build-only, NOT a new
physical result. No V4 packet observations exist.

Original physical V3 data show real over-air control installations
without expected application DATA_DEMAND. V4 would schedule the
per-sensor data timer only after both real radio control parts are
installed, but a separate legacy local round timer could still
erase have_ctrl and ctrl_round shortly thereafter. V5 removes
ONLY this independent source-clock reset, so source control validity
is changed only by an actual new radio-control round. A unique
last_data_sent_round prevents repeated source samples for a
previously installed radio plan. Both methods use identical V5
source firmware and exactly the same V4 physical node mapping
(only the source14 board M3-291 to M3-245 swap from V3).
No change is made to original Python ACR-MCR or POINT-EA,
their pre-frozen seed9401/S5/round20 synthetic predictions, 8x4
candidate set, risk CVaR weight, respective M3 sink firmware,
three rounds, 120 nominal source-round demands or 500B bytes.
All comparison claims remain strictly descriptive; physical
feedback is NOT processed by the original optimizer in later rounds.
No synchronized 500-ms delay or Apple M1 measured energy claim.
