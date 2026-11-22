# Pre-registered radio-control, 500-byte fragmentation and ENERGEST study

Date: 22 November 2026. The initial debugging smoke test used seed 8701,
S1, POINT-EA, four rounds; those results are excluded from inference.

## Independent test matrix

Original point and conformal optimizer implementations are unchanged.
New experimental co-simulation uses:
- 40 sensors + 1 sink and the original geometry.
- Independent topology/radio seed blocks 9201–9210, with no overlap with
  any earlier discovery/confirmation cohorts.
- Two regimes: S1 Cooja RX-success=0.94; S5 Cooja RX-success=0.82 and
  original model's node-enable decisions. These are **chosen simulation
  parameters**, not measured SNR/PER values.
- POINT-EA versus ACR-MCR, each assigned the same scenario/seed.
- 160 controller/packet-feedback rounds, 20-sec Cooja round period.
- Only the sink receives privileged controller-plan memory writes. The
  sink generates two broadcast control frames (20 node entries each),
  with up to three rebroadcast hops. Each sensor applies a route only
  when both control parts arrive over the simulated IEEE 802.15.4 link.
- Each source sample is exactly 500 application bytes. Eight frames
  carry 64,64,64,64,64,64,64,52 payload bytes. Sink verifies every
  reassembled byte and only then emits a delivery.
- Cooja's MAC callbacks (ACK, attempts, delay, actual frame length) feed
  the **next** controller round's link estimator and conformal update.
- Contiki ENERGEST is enabled and its raw CPU, LPM, radio TX and radio
  listen ticks are collected on all 41 motes. No unverified current
  draw, voltage, or Joule conversion is permitted.
- Full 40 registered runs = 10 seeds x 2 regimes x 2 methods.
- Cooja/audit must report: 160 plans, 160 feedback rounds, 41 energest
  records, per-round control delivery, 500B content integrity, source
  demand, MAC attempts and reassembled receipts. Every failed cell
  blocks aggregate confirmation.

## Co-primary statistical endpoints

1. 500-byte fully reassembled samples / 6400 nominal source-round demands.
2. Application delivery completed within 500ms of the logged source
   demand / 6400 nominal source-round demands.

Within each seed, average S1/S5 ACR-minus-POINT signed differences.
The ten seeds, not the forty runs, are independent units. Two-sided
paired Student-t 95% CIs and p-values, Holm correction for both outcomes.
If a comparison is tied exactly over all seeds, return a descriptive
zero effect and p=1, NOT a superiority claim. Declared exploratory:
control-installation success rate, Cooja radio TX/listen dwell time,
MAC-retry cost, queue losses and controller CPU runtime. These are
not electrical current measurements. No subgroup testing to promote
favourable scenarios.

## Acceptance conditions and limits

- The earlier four-round debug run showed 121/160 possible control
  installations, 117 full 500-byte deliveries, 0 payload errors, and
  populated nonzero ENERGEST radio counters for all 41 motes. These
  figures are *engineering feasibility* only, not independent validation.
- Cooja UDGM radio loss, topology and timing are still simulated, not
  a calibrated physical SNR/PER channel.
- The controller algorithm executes on external Python in the Cooja
  host rather than distributed embedded motes; its CPU energy is NOT
  included in Contiki ENERGEST on sensor nodes. Only distribution of
  control frames is over the simulated radio.
- The original model's variable traffic load and dynamic interference
  are not replicated precisely. Thus the result is an independent
  packet-level **design-constraint** test, not a bit-identical replay
  of the original transaction simulator.
- Firmware must not be labelled real-hardware tested unless a fresh
  IoT-LAB experiment containing exact source/firmware hashes is
  archived. External RSSI/noise/SNR measurements remain a separate gate.

Do not update the frozen 1,280-run results with these new experiments.


## Explicit correction to validation gate (22 November, 15:15 IST)

The first 160-round cloud run incorrectly treated fewer than 20
route-plan receptions per round as a software failure. In the S1
seed9210 ACR-MCR raw controller log, 3,038/6,400 actual unique
node-round installations were measured. This is an intended transport
outcome under radio loss, not a reason to reject data. The test now
logs exact measured missed control opportunities and fails only if
full energy capture of 41 motes is missing, if any reassembled payload
fails byte-integrity, if fewer than two sink-origin control frames are
counted per round, or if the recorded control receptions exceed
physically possible opportunities. No change to the optimizer,
data generation, seed matrix, method parameters, or primary endpoints.
This replaces the initial incorrect validation gate BEFORE analyzing
the complete 40-case result. All 40 registered combinations will be
recomputed in a single corrected GitHub study; prior intermediate
outcomes are excluded from the confirmatory inferential analysis.
