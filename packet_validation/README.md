# Packet-level conformal relay decision validation (exploratory)

This directory contains a Cooja/Contiki-NG packet experiment implemented to
address part of Discover Networks Reviewer 1's independent-validation concern.
The experiment can run on GitHub-hosted standard Ubuntu runners.

## What is implemented
- Four nodes: sink (ID 1), candidate relays (IDs 2 and 3), source (ID 4).
  Every delivered data sample must cross a relay.
- Contiki-NG CSMA and IEEE 802.15.4 packet emulation. Unicast MAC callbacks
  report ACK status and attempt count, not a synthetic radio coin flip.
- One route-independent alternating probe per round, one data demand per round,
  and relay-to-sink forwarding.
- Mode 0 uses a point estimate of capped attempt cost. Mode 1 uses point
  estimates plus online conformal upper bounds, a clipped alpha update, and
  coverage/periodic triggers for relay selection.
- Both modes share the number of candidate relays, probe schedule and acceptance
  threshold (at least 0.5 percent cost improvement to change relay).
- Latency is computed from global **Cooja simulation time**, because independent
  mote clock counters are not synchronized. Failed deliveries remain in demand.
- Logs record ACK/retry callbacks, chosen relays, probe coverage, sink delivery
  and timely delivery against 500 milliseconds.

## Limits that must accompany publication
This is a **packet-level decision-mechanism experiment**, not a complete
port of the released 40-node ACR-MCR study. It does *not* implement the
original eight-candidate/four-generation joint clustering search, the
64-bootstrap residual CVaR regularizer, 40-node aggregation, all five shift
scenarios, or the exact centralized energy ledger. It uses CSMA, whereas the
separate network-stack smoke test exercises RPL/TSCH.

No physical testbed, IEEE 802.15.4 PHY calibration or real battery measurement
is claimed. The paired modes use nominally equal simulator seeds but can change
the radio RNG draw order through route selection, so strictly keyed environmental
randomness is not established. MAC attempt counts are not calibrated Joules.

This code must **not** be described as "full ACR-MCR packet-level validation".
Cooja success demonstrates packet trace feasibility for a reduced two-relay
mechanism. Reviewer-level generalization remains open until the original
decision policy is ported and independently validated.

## GitHub execution
The companion workflow file is acr-recovery-packet-matrix.yml. A manual
dispatch executes three seeds, two radio-reception probabilities, and two
controller modes. The experiment has 40 requested data packets per mode.
Six paired comparisons are exploratory, without confirmatory p-values.
Short-lived artifacts preserve scripts, packet traces, JSON and CSV analyses.
Scheduled regression runs repeat the same seeds, and therefore must not be
misrepresented as fresh independent experiments.

## Local preflight
Pin Contiki-NG to upstream commit 4ccd1a3b9e767f168d12ec3df187fe6b7dc736b5
with its Cooja submodule. Copy acr_packet.c and Makefile under
contiki-ng/examples/acr_mcr_packet/, then run:

    python3 generate_csc.py --template CONTIKI/tests/07-simulation-base/05-nullnet-unicast.csc --mode 0 --seed 77 --out /tmp/point77.csc

From contiki-ng/tools/cooja/ and with Java and GNU Make 4 or later:

    ./gradlew run --args='--no-gui /tmp/point77.csc'

Parse COOJA.testlog, not just Gradle success. Do not reuse stale logs.
Run mode 1 separately with the same seed.

## Evidence record
Local smoke seed 77 passed in both mode 0 and mode 1.
Both modes delivered 40/40 samples, selected the same relay, and showed
no evidence of a service advantage. This is software feasibility only.
