# Exact physical porting status for the rejected ACR-MCR manuscript

Date: 22 Nov 2026, after completed IoT-LAB experiments.

## Actual hardware code-path evidence
- Grenoble M3 experiment **459566**: 2 sensor sources + 1 sink, fixed
  clustering and real CSMA radio control. Strict audit PASS for 6/6
  fully byte-verified 500B application samples, including 24 source2
  fragments successfully forwarded over source1 to sink. Three final
  ENERGEST time records. Original UART evidence archived.
- Experiment **459567**: first 40-sensor + 1 sink test. Observed
  57/120 nominal fully reassembled 500B samples, but serial node M3-291
  not captured and another node lacked final ENERGEST. Strict audit
  INCOMPLETE. Original logs and failed audit archived.
- Corrected experiment **459568**: 40 physical M3 sensors + 1 sink,
  original packet format and real over-air fixed-head control. All
  41/41 serial streams captured, sink byte-verified 86/120 original
  nominal 500B source-round opportunities, 117 source-demand records,
  119/120 physical node-round control installations. This is
  ONE exploratory three-round deployment block. Packet-only audit
  PASS. The original strict combined packet/energy audit is still
  INCOMPLETE because logical source35 M3-215 has no final ENERGEST,
  only 40/41 energy time records. No physical deadline timestamps
  synchronized across independent boards.
- C port of the original Calibrator score-window, quantile,
  clipped alpha update and alert rule compiled for Cortex-M3; 135
  point/adaptive/frozen Python/C parity combinations PASS with zero
  numerical difference. Module is not integrated with the deployed
  full algorithm or firmware policy.
- Compiled and source-hashed 41 unique M3 firmware binaries archived,
  with physical placement and a 41-image gz bundle.

## What is still NOT completed

**Full original ACR-MCR on embedded M3 is NOT implemented**: the
deployed sink uses deterministic STATIC four-head mapping rather
than the original adaptive prediction, bound-based link selection,
metaheuristic cluster-head optimization, event trigger and CVaR
regularizer. The 41 physical devices establish transport feasibility,
not scientific validity of ACR-MCR's original service claims.
Only one three-round physical block has been recorded and there are
no 10-seed, matched physical controller comparisons.

**Total system / host optimizer electrical energy in Joules remains
UNMEASURED.** Apple M1 host process CPU and controller times are
independently measured in host_energy/results/20261122_M1, but no
physical watts and hence no host Joules exist. The IoT-LAB
device-energy readings from experiment 459543 cover two M3 boards,
not the external Python optimizer or all 41 deployed devices.

**Physical SNR-to-PER calibration is still NOT established.** The
independent M3 459550 configured-TX-power/packet-reception experiment
measures real receipts and conditional RSSI but not calibrated
receiver input noise/SNR.

## Editorial classification

(1) Physical 40-source static clustering transport/fragment format:
**implemented and exercised (single exploratory three-round block)**.

(2) Full 40-node physical ACR-MCR algorithm with fair baseline
comparison and synchronized deadline inference: **[NEED SOURCE]**.

(3) Full physically measured optimizer-plus-network energy:
**[NEED SOURCE]**.

Do not combine Cooja, physical 2-board power or host CPU timing into a
fabricated 40-node real energy-per-delivered-sample result.
