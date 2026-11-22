# Registered independent 40-node Cooja packet-feedback evaluation

Frozen on 22 November 2026 before GitHub confirmation execution.
This protocol concerns a newly implemented simulator-memory-controlled
closed-loop co-simulation, and does NOT replace the 1,280-run original record.

## Mechanism
The original acr_mcr_v2.py optimization code is imported unchanged.
The 40-node Cooja application emits actual MAC acknowledgements, retry
attempts and packet timing. After each 5-second round, the ScriptRunner
passes those observations to the Python controller, updates its beta
link predictors and conformal calibration, and requests its next
head/path/probe plan. Python's original synthetic packet-transaction
sampling is NEVER used for those updates. Cooja injects the resulting
plans directly into each mote's memory before the next round's traffic.

This is real packet-feedback closed-loop **with privileged central control**.
Distributed controller command radio packets are not implemented or
priced. It is not hardware / full-distributed-validation evidence.

## Frozen comparison
- 40 sensor nodes + one sink, original model topology geometry.
- 160 rounds per experimental cell with first 20 rounds constituting
  the original model's predictor warmup, but **all 160 packet demands**
  remain in the packet-level denominator.
- Two procedures: original POINT-EA and original ACR-MCR optimization.
- Scenarios: S1 with Cooja success probability 0.94, and S5 with
  success probability 0.82 + original node-disable schedule. This
  does NOT reproduce the original time-varying interference field.
- Independent seeds: 8901–8910, ten paired seeds across both scenarios.
- Total: 10 seeds x 2 scenarios x 2 methods = 40 Cooja runs.
- Fixed Cooja short application packet: 78 bytes, one offered data
  sample per node per round, one route-independent probe per node
  per round. These differ from the original 4,000-bit packet and
  scenario-dependent offered load.
- Source bridge/optimizer binaries, radio config and SHA-256 source
  hashes recorded in every GitHub job.

## Registered outcomes and inference
For each seed and scenario calculate ACR-MCR minus POINT-EA on:
1. Unique source/round deliveries / (40 x 160).
2. Unique source/round sink receipts within 500ms of source enqueue /
   (40 x 160).

The **independent unit is the seed**. Aggregate the two scenario
paired effects within each seed and apply two-sided paired Student-t
confidence intervals and two-sided p-values (df=9). Holm-adjust the two
primary p-values. Source packet demand and sink delivery audit must
match the logged round; old-round receipts after a barrier are logged
but never moved into a different round. Failed/incomplete runs cannot
enter inference; no replacement seeds after inspecting effects.
Scenario-specific effects, MAC retries, probe attempts and search counts
remain descriptive (no subgroup superiority claims). Full raw per-run
MAC/controller traces are retained as bounded GitHub artifacts.

## Novelty gate
A claimed new algorithmic advantage is **NOT** established by this
protocol. Instead it tests whether uncertainty-aware choices, when
allowed to respond to actual packet outcomes, improve end-to-end service
over matched point-based choices. Retain negative results with full
intervals and costs. Any new telemetry-gating algorithm requires a
separate development/confirmation split and source/literature audit
before describing it as novel.

## Boundaries
No 500-byte application fragmentation/reassembly, no measured CPU/idle
or harvested energy, no real distributed status broadcast, and no
hardware RF calibration. The source uses CSMA Cooja packet timing rather
than the original scheduled half-duplex transaction model. Cooja radio
metrics and model energy debits cannot be presented as physical joules.
A full testbed/generalisation claim remains unwarranted until those
missing mechanisms are separately implemented and checked.
