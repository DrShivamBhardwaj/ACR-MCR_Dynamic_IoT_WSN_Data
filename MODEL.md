# Model specification and audit notes

## Time and topology

The simulator is a centralized, scheduled, half-duplex transaction model.
Sensors are static in a 100 m square; the powered sink is 12 m above its top
edge. Geometry, initial battery and disturbance domains are separately seeded.
A directed edge is feasible at distance <=78 m. This same rule applies to
member access, head relays and probes. No connectivity repair is imposed.

All requested samples originate at data-phase time zero. A transaction waits
for sender and receiver availability. Member collection and aggregation precede
backbone forwarding. Different non-conflicting links can overlap; the sink can
receive concurrent flows. Each head's aggregate is 4000 bits regardless of its
number of contributing samples. Aggregation takes 2 ms. No CSMA/CA or explicit
fragmentation is simulated. Round queues reset; control and maintenance phases
are outside the measured data-phase latency window. There is no model of
inter-round backlog or an externally fixed sampling period.

## Channel field and information boundary

For each directed link and round, distance, Gaussian shadowing and a spatial
hotspot determine a latent success probability. The probability and frame
duration are environment variables only. Forecasting reads neither variable.
The probability formula and five disturbance schedules appear in the paper;
`Simulator.state` and `Simulator.environment` are authoritative implementations.

Random outcomes are indexed by seed, round, logical transaction class, source,
packet index, directed link and attempt. Changing execution order cannot shift
a later environmental draw. Policies choose different links from this common
field, so equality of their realized transmission histories is not asserted.
Environmental fingerprints are saved per round and matched across methods.

## Radio ledger

Each attempted 4000-bit transaction charges transmit electronics/amplifier
energy and receiver electronics. Successful delivery also charges a 64-bit ACK.
The powered sink has no battery ledger. Aggregation is charged for samples
successfully collected at a head. Probes use the same full-payload transaction
mechanism. Local control charges two ideal 256-bit broadcasts per active node
at every head search, including all feasible sensor listeners. This is partial
control accounting, not the implementation of a reliable distributed protocol.

The radio law uses 50 nJ/bit electronics, 10 pJ/bit/m² free-space amplification,
0.0013 pJ/bit/m⁴ multipath amplification and 5 nJ/bit aggregation. At the default
78 m range all feasible links lie below the approximately 87.7 m crossover.
Battery debits never exceed stored energy. Transactions with insufficient
required transmit, receive or ACK energy stop and are marked energy-censored.

Externally disabled nodes keep their battery energy. They cannot send or
receive and still contribute requested application demand. Initial total energy
equals remaining stored energy plus the four cumulative expenditure categories
within 1e-9 J at every round. Idle listening, sensing, wake-up and controller
processor expenditure are omitted and are explicitly outside the energy claim.

## Probe observation and learner

The geometric probe schedule selects up to B distinct neighbours per source
without replacement, using its own random domain. It does not depend on heads,
routes or current forecast values. Unavailable scheduled nodes cause a skip,
not replacement sampling. Hence geometric scheduling is policy-independent,
but the observed sample population can still vary with battery availability.
Uniform neighbours per source do not give equal inclusion probabilities to
every directed edge when degrees differ.

Only probes update the learner and calibration. Data outcomes are a separate
diagnostic stream. A completed radio transaction observes attempts A<=4,
ACK success S, cost C=A+1{S=0}, and elapsed service time D. Energy-interrupted
transactions are censored from this link-level diagnostic. Terminal four-try
radio failure has C=5 and is retained, so failures are not dropped from fitting.

The success estimate is a/(a+b), initialized with strength four and mean
clip(exp(-0.5(d/52)^2),0.1,0.99). Probe updates are
a=0.9a+S and b=0.9b+A-S. The mean duration-per-attempt estimate starts at 19 ms
and updates with weight 0.2. The expected capped attempt count is
1+q+q²+q³, q=1-p; predicted cost adds q⁴. Prediction scales use their
truncated-geometric standard deviations with floors 0.35 and 4 ms.

## Issued upper predictions

Before a round, predictions and residual quantiles are frozen. Every transaction
is compared with the bound issued from past data. At the end of the probe phase,
normalized signed residuals (observed-predicted)/scale update a pooled window of
at most 512 cost/time pairs. The order statistic is
min(m,max(1,ceil((m+1)(1-alpha)))), and its non-negative part corrects the point
prediction. Cost bounds are capped at five. The initial correction is 1.28.

Frozen calibration stops updating its window after the first 20 rounds.
Rolling calibration keeps alpha=0.1. Adaptive calibration updates each target
after warm-up by clipping alpha+0.03(0.1-round_mean_miss) to [0.02,0.40]. Empty
probe rounds do not update the calibrator. This clipped, batched ACI-inspired
rule is evaluated empirically; no general conformal validity guarantee is
claimed. Every method makes point-based decisions in warm-up.

## Decision and search

Directed edge costs combine the selected point/upper cost and time predictions,
point-based radio expectation, receiver battery penalty and a fixed positive
cost-excess penalty. Weights and normalizers are identical across evolutionary
variants. A candidate head set induces all head-to-sink shortest paths and
member assignments. Unassigned active sensors receive an explicit penalty.

Fitness combines candidate-specific predicted expenditure, delay surrogate,
backbone route cost, post-transmission energy coefficient of variation, peak
depletion ratio and unserved fraction. Unlike executed latency, the candidate
delay surrogate does not account for inter-flow relay contention. This is a
documented approximation, not an exact deadline feasibility test.

ACR-MCR additionally uses 64 bootstrap residual scenarios and weight 0.15 on
upper expected shortfall at beta=0.90. Cost/time residual pairs are sampled
together for each link, but complete cross-link dependence is not preserved.
A draw >=4.5 indicates transaction failure. Tail loss is the surrogate fraction
of active sources unserved, failed or late. The empirical tail calculation uses
six full top losses and 0.4 of the seventh, divided by 6.4. Candidate plans in
one search share the same stress fields.

There are eight candidates and four generations, with two retained elites and
one-head replacement mutation. A valid incumbent enters the population.
Candidate cardinality is max(2,round(0.1*active)), capped at the active count,
unless the fixed-head experiment specifies K. The retained incumbent can keep
an earlier cardinality. A changed plan requires at least 0.5% objective
improvement, except after a failed head. RANDOM-CH skips evolutionary search
and directly selects energy-weighted random heads; it is not LEACH.

Initialization and head failure trigger search immediately. Otherwise the
maximum gap is ten rounds. Event variants can search after three rounds when
either target's mean coverage over the previous three non-empty probe rounds
falls below 0.78. Assignment and backbone paths are refreshed every round,
even when the head set is retained. No alternate baseline-specific gate exists.

## Outcomes and limitations

PDR and timely-delivery ratios use total scheduled demand over rounds 21–160,
including disabled, depleted and unassigned original sources. Timely delivery
requires a completion timestamp <=500 ms. A service violation is a round whose
timely ratio is below 0.80. Conditional delay only summarizes delivered samples
and is NaN if none arrive. It is not an unconditional reliability metric.

Energy totals cover all 160 rounds. Energy per delivered sample also uses all
rounds, so its time window differs from the service endpoints. Probe and data
coverage use uncensored observed transactions after warm-up. Per-run coverage
ratios are equally weighted when combining scenario-seed results; these means
are not a single global transaction-weighted coverage estimate.

The study addresses attribution inside one controller family. It cannot establish
superiority over contemporary WSN protocols, IEEE 802.15.4 performance, embedded
feasibility or physical network lifetime. Observation cost, incomplete coverage
transfer and scheduling approximations are measured or exposed rather than
hidden by the revised claims.
