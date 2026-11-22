# Reviewer scientific evidence addendum: original decision mathematics on M3

Date: 22 November 2026. This is a record of performed, independently
audited work, NOT a new acceptance decision and NOT a completed embedded
adaptive-routing experiment.

## Frozen original and independent fixed-state numerical parity

Original Python source SHA256:
3f134a8826525215f7cf2ff307bab3893c0d64b050f742bdc3c250b1c0302ea4.

The portable C99 port implements original Floyd-Warshall backbone
selection; per-node cluster assignment; complete energy, delay, route,
post-depletion CV and peak-depletion weights; exact fractional-tail
empirical CVaR at beta=.90; generation selection for 8 candidates
and four search generations. Exactly the original user-supplied
C-control update of calibration scores, quantile, clipped alpha
and alarm passed 135 mode-round parity tests earlier.

New source-locked tests:
- 10 independent topology seeds 9401–9410 x S1/S5 x
  POINT-EA/ACR-MCR x before/after conformal warmup: 80 independent
  fixed-state Python/C fixtures, including 20 full 64-scenario CVaR
  cases. All passed; worst absolute fitness discrepancy
  4.440892098500626e-16, identical selected heads and assignments.
- A separate five-seed S5 physically motivated failure study
  checked 40 additional fixed-state original Python/C scores under
  explicitly disabled nodes and blocked sink-backbone edges.
  Every case passed with worst discrepancy
  4.440892098500626e-16.
- Total: 120 fixed-state full-score parity comparisons, plus
  the earlier 135 adaptive-calibrator mode-round comparisons.

The original *candidate genotypes* and stochastic tail sample
indices are supplied from the original NumPy PCG64/SeedSequence
implementation. The embedded code has NOT independently ported
NumPy's random-number generator or stochastic source state.
These are therefore conditional mathematical parity tests.

## Real physical Cortex-M3 execution of original deterministic kernel

Two fresh, separate, authorized FIT IoT-LAB Grenoble M3-14
experiments used the same frozen original seed 9401, S1, round 20
and identical M3 hardware, while keeping method-specific original
prediction/risk inputs:
- 459572 ACR-MCR with 64 CVaR scenarios: selected original heads
  [4,7,9,23], 2.95 seconds measured on the real M3 100Hz clock.
  Firmware UART reports PASS, zero status error, objective absolute
  discrepancy 10 nanounits (1e-8) versus original Python.
- 459573 POINT-EA: same selected heads, 0.15 seconds on the
  real M3 clock, UART reports PASS, objective discrepancy 18
  nanounits (1.8e-8).
- Fully frozen risk tensor indices were compressed to a 9-bit
  read-only FLASH representation for the 512-record calibration
  score window. The score function was executed on the real M3,
  not simulated on a desktop.
- Original UART, firmware SHA256, board deployment and original
  IoT-LAB power-monitor OML were archived for both runs.

The two first physical OML records did not meet the preexisting
>=25 data point and >=40 second power monitoring threshold. They
cannot independently establish calibrated physical M3 electrical
Joules; no physical Apple M1 host Joules were measured. The
20-repetition fixed-window protocol was registered *before*
its new observations. It is not marked PASS until its original
power files independently pass the unchanged audit.

These results physically validate that a faithful deterministic
decision scoring/selection kernel runs on one M3 and matches
original Python for those frozen inputs. They do NOT validate
the full original 40-node physical closed-loop ACR-MCR controller:
the latter still requires onboard live calibration and prediction
updates, genuine feedback-informed head search, embedded RNG
equivalence or separately established policy equivalence,
radio-distributed route plans, 160-round service outcomes,
independent paired physical POINT-EA and ACR-MCR campaigns,
synchronized 500-ms deadline inference and complete energy.

Prior physical 41-board trials 459567/459568 still establish
static-four-cluster radio control and 500B reassembly, not live
ACR-MCR. The 40-sensor physical packet-only experiment 459568
observed 86/120 full 500-byte nominal source-round receipts
with 40/41 final ENERGEST reports; original strict all-measurement
audit remains incomplete and all unfavorable losses are retained.

**Status of full physical adaptive algorithm comparison: [NEED SOURCE].**
**Status of Apple M1 calibrated electrical energy in J: [NEED SOURCE].**
**Status of externally calibrated SNR-PER: [NEED SOURCE].**

## Scientific conclusion permitted now

The original point-versus-conformal service superiority was not
established in the frozen synthetic study. Deterministic C parity
and M3 execution address implementation feasibility only.
Do not infer physical service benefit from the fact that the C
and Python objective scores agree, nor treat one source-state
hardware runtime pair as a population-level statistical comparison.
