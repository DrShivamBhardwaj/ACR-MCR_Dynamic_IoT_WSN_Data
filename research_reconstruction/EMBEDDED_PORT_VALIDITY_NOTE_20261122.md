# Full original ACR-MCR feedback on M3: quantified source-level memory gate

Original frozen 40-node M3 CVaR image compiles at 35,760 bytes initialized
and zero-initialized SRAM, versus 65,536-byte physical M3 SRAM limit.
The original Python simulator represents the per-link beta_a,
beta_b and frame_hat arrays as NumPy float64 (40×41 each).
Those three arrays alone require 39,360 bytes. Added to the existing
frozen C program's static allocation, the literal dense port would
require at least 75,120 bytes before extra runtime variables or stack.
Original 64-scenario stress_c and stress_d NumPy tensors would
occupy 839,680 bytes EACH if materialized as float64, exceeding
M3 RAM and, together, flash. The source-verified numerical
calculation is archived in EMBEDDED_M3_MEMORY_FEASIBILITY_20261122.json.

This rules out a naive literal in-RAM implementation. It does NOT
rule out a scientifically equivalent streamed original CVaR
calculation with sparse online link-state, compressed/flash resident
tail-index streams or carefully bounded predictor state, nor a
full physical-network closed loop with an EXTERNAL host optimizer.
Such changes must be recorded as implementation choices and
verified under original Python/C precision, trigger sequence,
head choice and actual physical feedback.

The real-radio V9 telemetry return prototype (separate file)
is the next source-locked step. Its physical execution is NOT
evidence of a complete original adaptive controller. The
next validated pipeline must record per-hop M3 attempt/ACK/time
observations, apply the ORIGINAL residual/predictor/ACI update,
stream the four-generation risk objective, and radio-distribute
the next-round plan. Each stage needs a raw-evidence hash and
a physically independent matched POINT-EA test. A frozen
M3 kernel alone is not a closed-loop controller.
