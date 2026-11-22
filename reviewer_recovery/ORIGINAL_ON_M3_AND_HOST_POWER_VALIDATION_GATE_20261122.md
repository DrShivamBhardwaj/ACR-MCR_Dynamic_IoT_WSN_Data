# ACR-MCR original optimizer hardware evidence and pending power gate

Verified November 22, 2026, 20:36 IST, against original `acr_mcr_v2.py` SHA256 `3f134a8826525215f7cf2ff307bab3893c0d64b050f742bdc3c250b1c0302ea4`.

## Original deterministic C head-search / CVaR

`hardware/iotlab_m3/embedded_40/extended_parity/80_fixture_parity.json` contains a completed 80-state parity test over 10 independent simulator seeds, S1/S5, POINT-EA/ACR-MCR and rounds 0/20. Frozen original genotype streams and stress tensors were used on both sides. All 80 full-search traces matched the original Python head selection, including 20 risk-active cases; 480 candidate-plan/objective comparisons; maximum absolute fitness error 4.440892098500626e-16. The Cortex-M3 C objective implementation was compiled. **Native NumPy PCG64 weighted candidate RNG, physical ACK-conditioned predictor/calibrator updates, end-to-end closed-loop optimizer and independent adaptive physical service validation are NOT verified.**

## Actual 41-board matched kernel experiments already performed

Sequential historical frozen-source S5 seed9401 physical 41-M3 experiments 459594 (POINT-EA) and 459595 (ACR-MCR) were audited from original board UART traces. Both passed frozen C selected-head/objective checks, 41 original UART streams and per-500-byte byte integrity. The actual completed 500-byte source-round samples were 39/120 versus 10/120; over-air control installations were 80/120 versus 120/120. This is a **single frozen simulator-seed, nonrandomized chronological engineering contrast**. The risk controller did **not** demonstrate superiority, and no physical 500ms deadline inference or paired independent-seed interval is justified. Each of the two physical sessions missed one source's final ENERGEST, thus only 40/41 final energy records. Raw logs and strict audit are archived under `hardware/iotlab_m3/embedded_40/evidence/FROZEN_41_BOARD_V5_20261122/`.

## New registered physical replication

A second frozen original simulator-seed block (seed9402, S5, original round20) with two separately compiled original M3 kernel sink binaries was preregistered in `REGISTERED_SECOND_INDEPENDENT_PHYSICAL_BLOCK_20261122.md` before execution. This block was launched separately and may be analyzed only once both original physical traces and the strict audit are archived. **Do not invent a result from an active reservation.** Even two seeds are insufficient for general statistical confirmation.

## Host electrical power: fail-closed

The M1 MacBook Air original-controller 40-case matched runtime benchmark is real (ACR-MCR mean controller 0.177393s vs POINT-EA 0.118231s; 10 seed-block paired difference +0.059161 seconds, CI [0.052041, 0.066282]). This measures computational time, **not actual electric Joules**. `/usr/bin/powermetrics` requires administrator privileges and the connected remote Desktop Commander expressly blocks privileged execution, so no admin-authorized Apple power trace was collected. No wall-plug measurement is present. Physical power in separate Grenoble M3 tests belongs to remote sensor boards and cannot be relabeled host optimizer power. The 10-seed simulation and M3 power data must remain separate experimental populations.

## Publication claim gates

- **PASS**: original deterministic search and CVaR evaluation C/Python parity for fixed candidate, state and risk inputs.
- **PASS, bounded**: 40 physical sensor-board plus one sink radio-control/500B implementation with one frozen-head kernel execution per run.
- **PENDING**: original closed-loop adaptive controller, physical independent seed-level confirmatory service outcome, physical synchronized 500-ms deadline comparisons.
- **PENDING**: real administrator-authorized host CPU-package measurement, independently calibrated wall-plug Joules and physical full-network energy accounting.

Preserve negative comparisons, incomplete ENERGEST and failed deployments; do not state that all journal reviewer concerns are resolved.