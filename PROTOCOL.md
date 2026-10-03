# ACR-MCR revised computational experiment protocol

Recorded before executing the revised benchmark. This is a dated, local analysis
plan, not an externally registered study. Source and protocol SHA-256 hashes are
recorded by the runner. Any corrective changes after a pilot must be recorded.

## Scientific questions

1. Does using calibrated upper predictions change timely delivery relative to
   matched point control, when objective weights and search budgets are held fixed?
2. What changes when calibration is frozen, rolling, or adaptively updated?
3. Do coverage-triggered head refresh and a residual-bootstrap tail penalty add
   value independently, after accounting for probe and control radio expenditure?

## Model and controls

Use the standalone revised Python transaction-level simulator. The environment
is synthetic; neither ns-3 validation nor physical deployment is claimed. Directed
radio edges are limited to 78 m for members, probes, and the backbone. All methods
use the same radio, telemetry budget, forecast learner, objective weights,
reconfiguration acceptance rule, initial topology, and indexed disturbance fields.
Only the named switches differ. The randomized control is named RANDOM-CH and is
not called LEACH. Previously reported results are superseded, not relabelled.

Methods: RANDOM-CH, POINT-EA, FROZEN-CP, ROLL-CP, ACI-PER, ACI-EVENT, ACR-MCR.
The last two differ only in the tail penalty; ACI-PER and ACI-EVENT differ only
in refresh scheduling. All evolutionary methods share 8 candidates, 4 generations,
fixed positive objective weights, and a 0.5% improvement requirement for accepting
a changed head set, except for recovery from failed heads.

Predictions target an observable capped transaction cost A + I(failed), with
A <= 4, and elapsed transaction service time. They do not target the simulator's
latent success probability or pretend this cost is uncapped ETX. Uniform probes
are independent of routing choices. Bounds are logged before observations; updates
occur after the round. Data-link coverage is evaluated separately from probe
coverage. Radio energy is debited for data, probes, acknowledgements, aggregation,
and explicitly modelled local control broadcasts. Injected failures disable nodes
without counting their stored batteries as consumed energy. Controller CPU energy
and a complete distributed telemetry-collection protocol remain outside scope.

## Runs and seeds

Main: 40 nodes, 160 rounds, first 20 rounds warm-up, seeds 1000--1029, S1--S5,
all seven methods: 1050 runs. S1 gradual interference; S2 interference burst;
S3 doubled offered load; S4 spatial node failure; S5 combined changes.
Separate stationary control: S0, seeds 1000--1009, all seven methods.
Pilot/debug seeds 9000--9009 never enter inferential estimates.
Scalability: 80 and 120 nodes, S5, seeds 2000--2009, POINT-EA and ACR-MCR.
Probe sensitivity: 0, 1 and 2 probes per source-round (default 1), S5, seeds
3000--3009, POINT-EA and ACR-MCR. No-probe control retains its prior predictor.
Head-count diagnostic: 60 nodes, k = 4, 5, 6, S5, seeds 4000--4009,
POINT-EA and ACR-MCR. These analyses are secondary, without outcome-driven tuning.
Timing profile: sequential, isolated runs at 40, 80 and 120 nodes, S5,
seeds 9500--9504, POINT-EA and ACR-MCR; excluded from outcome inference.

## Outcomes and analysis

Scheduled demand includes externally failed, energy-depleted and unassigned
sources. A source requests one sample per round, or two in a load-shift phase.
PDR is delivered/scheduled demand. Timely delivery is delivered by 500 ms/scheduled
demand. Service violation is a round with timely delivery < 0.80. Missing samples
are therefore failures, never silently removed from denominators. Conditional
delay is computed from actual delivery timestamps and clearly labelled.

Co-primary outcomes: timely delivery and service violation rate; contrast
ACR-MCR minus POINT-EA. Average the five scenarios within each seed, then use
30 paired seed differences. Report means, paired mean differences, 95% Student-t
intervals, a paired sign-flip Monte Carlo test (100000 random sign assignments,
fixed analysis seed), and Holm correction over the two co-primary tests. These
tests assume independent seed blocks; the sign-flip test additionally assumes
sign symmetry under the null. Report all outcomes even when null or adverse.

Secondary staged contrasts are POINT-EA→FROZEN-CP→ROLL-CP→ACI-PER→ACI-EVENT→ACR-MCR.
Report paired intervals and Holm-adjusted tests across these five contrasts and
the two outcomes (ten tests). RANDOM-CH is a descriptive randomized anchor.
Also report total radio energy, probe/control fractions, delivered-sample energy,
all-round and phase-specific probe/data coverage, refresh reasons, head changes,
and measured controller wall time. No network-lifetime superiority is inferred
from a fixed 160-round horizon. Figures must be generated from saved raw outputs.

## Verification gates

Verify keyed randomness; schedule-independent probe choices; all-edge range;
energy ledger conservation; injected-failure accounting; pre-update coverage;
reachable early coverage trigger; minimum refresh gap; stable incumbent acceptance;
fractional empirical CVaR; nonzero member and aggregation waiting time in delivered
timestamps; unreached and failed demands retained; and reproducibility on rerun.
No benchmark result is accepted until these checks pass. Preserve per-run,
per-round and diagnostic data plus all plotting/analysis sources in the supplement.
