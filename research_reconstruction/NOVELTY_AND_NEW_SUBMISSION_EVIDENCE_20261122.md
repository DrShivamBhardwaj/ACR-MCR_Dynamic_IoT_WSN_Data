# ACR-MCR scientific novelty and independent evidence for a new submission

Date: 22 November 2026. This research reconstruction follows a rejection;
it is NOT a formal revision of the rejected Discover Networks submission.

Source boundary: author-supplied ACR_MCR_Three_Pass_Reviewer_Revised.docx
contains 18 references; author-supplied ACR_MCR_Updated_Reviewer_Response.docx
describes 9 additional publisher-checked references [19–27]. The complete
27-entry manuscript has not been inspected here. The 18 original entries and
the supplied claims regarding 19–27 are treated as author-provided material,
not independently verified findings or reproduced baselines. Scientific data
below come only from the unchanged original model and private GitHub
versioned experimental files.

## 1. Claim that is defensible, and claim that is not

The original clustering search, point forecasts, conformal prediction,
adaptive update and CVaR surrogate are established component techniques.
Combining them cannot by itself establish methodological novelty. The
falsifiable contribution is the *incremental decision value* of issued
link uncertainty bounds, relative to the POINT-EA policy with the same
telemetry, geometry, learner, weights, search budget and baseline conditions.
A second question concerns the radio cost of collecting those observations.

Original synthetic measurements find near-nominal 90.03% probe service-time
coverage but only 83.20% coverage of policy-selected link traffic. The
6.83 percentage point difference is an empirical selection-population gap,
not a new formal conformal coverage guarantee. Probing consumes 49.84% of
mean MODELLED radio expenditure. These observations can motivate an
independent negative decision-value study, but do not demonstrate algorithmic
superiority or an original conformal theorem.

## 2. Distinction from each supplied class of prior literature

| Author-provided references | Established approach | Claims to avoid | Unresolved decision-value question |
|---|---|---|---|
| [1–3] Heinzelman, De Couto, RPL RFC | Energy clustering, ETX, low-power lossy routing | First clustering or new deployed RPL | Effect of uncertainty bounds under identical telemetry/search budget |
| [4–5] Kundu, Dhaka | Uncertain node energy, KDE deployment, GWO–PSO head choice | First uncertainty-aware clustering or heuristic head search | Incremental use of transaction bounds beyond point estimates |
| [6–7] Counassegarane/Punniakodi, QPSODRL | Dynamic routing, learned clustering and combined optimisation | Novelty by merely linking clustering and route choice | A fair component-matched controller contrast |
| [8–12] conformal theory and adaptive online variants | Prediction sets, marginal and sequential coverage under their assumptions | Claimed mathematical coverage for the original clipped batch update | Selection-induced gap between probe and routed-data coverage |
| [13–14] wireless conformal work | Already uses conformal calibration in wireless inference | First wireless conformal algorithm | Does calibrated link uncertainty improve application deadlines? |
| [15] feedback covariate shift; [16] conformal risk control | Selection-dependent observation and loss-level risk control | Claims of implemented shift weighting or deadline-loss guarantee | Can a suitable operational loss be calibrated with radio-cost accounting? |
| [17] CVaR; [18] Holm | Risk surrogate and multiple-testing correction | Novelty of CVaR/Holm | Whether the tail surrogate improves actual registered service endpoints |
| [19–21] as supplied in updated response | Discover Networks packet QoS, energy/delivery routing review and changing IoT routing | No other packet-level or adaptive QoS work exists | Reproducing full algorithm decisions under MAC and control drops |
| [22–25] as supplied in updated response | Dynamic clustering, delay/energy trade-offs and congestion/queue routing | First use of queueing or energy-aware packet routes | Bound versus point under identical real radio operation |
| [26–27] as supplied in updated response | Temporal calibration and uncertainty-aware routing in other fields | Unreproduced external methods are quantitative baselines | Transfer and generalisation conditions, not invented superiority |

Additional direct prior art and complete verification of all 27 bibliographic
records remain [NEED SOURCE]. The supplied updated reviewer response states
publisher DOI metadata were checked, but its source descriptions do not
establish a matched external implementation.

## 3. Recomputed registered primary effects

Original source SHA256:
3f134a8826525215f7cf2ff307bab3893c0d64b050f742bdc3c250b1c0302ea4.
No original simulator changes.

Original 1,280-run synthetic study, co-primary contrasts 30 independent
paired topology/traffic seed blocks. ACR-MCR minus POINT-EA:

| Outcome | Difference, percentage points | 95% paired CI | Holm p |
|---|---:|---:|---:|
| Timely delivery | −0.213 | [−1.066, +0.640] | 0.616 |
| Service violations | −0.733 | [−1.841, +0.374] | 0.379 |

The latter outcome is lower-is-better, but neither confidence interval
excludes zero. Neither comparison supports service superiority.

Full-format Cooja feedback run 45009267734: 40 sensors + one sink,
160 rounds per run, ten independent seeds 9201–9210, scenarios S1/S5,
two methods, 40 independent raw audited cells, all integrity checks
PASS. Sensor routing control is delivered over 802.15.4 CSMA,
500-byte samples are fragmented into eight MAC frames, and plans are
written to SINK-ONLY Cooja memory by the external Python controller.
Recomputed independently from all original cell results:

| Registered outcome | ACR−POINT difference, pp | Paired 95% CI, pp | Holm p |
|---|---:|---:|---:|
| Full 500B reassembly / nominal demands | +0.658 | [−1.981, +3.296] | 0.783716 |
| Full 500B within simulated 500 ms / nominal demands | −0.051 | [−0.179, +0.077] | 0.783716 |

The paired seed is the independent unit, not individual frames.
Nonsignificance is NOT evidence that both controllers are equivalent.

ACR-MCR generated +5258.3 data-fragment MAC callbacks per 160-round
Cooja run, exploratory unadjusted paired 95% interval [2019.9, 8496.7],
and +5377.95 all-type MAC callbacks, interval [1910.2, 8845.7].
These exploratory observations are not physical device energy or
causally attributed effects. Cooja simulates only two PHY regimes,
not the full five original interference/load laws or measured SNR.

The original synthetic and later Cooja populations are separate.
Do not pool the 30 original seeds with the 10 Cooja seeds, mix
modelled Joules with ENERGEST ticks, or compare unlike deadlines.

## 4. Original M3 port and physical results, without overstating

Native Grenoble M3 fixed-head radio transport passed an independent
2-source multihop test (experiment 459566; six of six fully verified
500-byte samples). A static 40-source/sink physical test (459568)
recorded 86/120 complete samples but one missing ENERGEST record.
It is not the original adaptive controller.

Native M3 deterministic original head-search and CVaR fixed-state
computations pass 80 of 80 Python/C tests over 10 source-locked seeds;
all 480 candidate/fitness comparisons pass; maximum absolute
difference is 4.44e-16. A frozen original 40-node point/risk
sink image compiles and fits under the device's 512-KiB flash and
64-KiB static RAM limits. This does not demonstrate runtime PCG64
generation, live telemetry forwarding to the sink, real-M3 ACI
updates, or dynamically recomputed head search.

Some physical 41-node attempts had a failed firmware flash
on M3-215 or missing UART streams. Those raw results remain archived,
but cannot serve as valid full-node effects. POINT-EA frozen
seed9402 experiment 459607 passed 41/41 flash, 41 UART and
41 ENERGEST and recorded 47/120 full samples. Its original-risk
matched arm has NOT passed all relevant capture gates.
An independent paired physical adaptive-controller effect
is still [NEED EXPERIMENT].

Authorised Apple M1 powermetrics measured estimated CPU-subsystem
energy per full simulation case, POINT-EA 1.986 J and ACR-MCR 2.270 J;
these are aggregate Apple CPU estimates, NOT calibrated
per-process optimizer or wall-plug electrical Joules.

## 5. Full closed-loop physical validation acceptance gate

A physical adaptive-controller claim must have all of the following,
not a successful Contiki build or sink receipt alone:

1. 41/41 independently verified physical firmware flash success,
all original per-node UART logs, SHA256 for each executable, source
code and manifest, run-specific sink identification, recorded
failure nodes and no exclusion of missing source demands.
2. Member hardware reporting its actual per-hop ACK, retry count
and monotonic service-duration telemetry over a recorded radio
protocol to sink. The controller must NOT have privileged access
to off-mote outcomes; a sink 500B receipt is not a substitute for
per-hop probe service-time residuals.
3. Original ACI probe scores and covered indicators must update
predictor and calibration state at the end of the physical round.
An independently replayed Python implementation must match every
M3 alpha, quantile and next-round head-search input.
4. Original four-head 8-candidate/four-generation search, incumbent
improvement rule, empirical 64-scenario tail term and failure/
periodic/coverage triggers must be executed against fresh physical
state. If M3 uses a different PRNG, fixed point, feature set or risk
surrogate, label it a new *changed algorithm* and preregister its
own comparison.
5. The next route-control broadcast must derive from those
previous physical observations and be captured over radio.
Synchronised physical source/sink timing is required for
500-ms deadline claims. Physical TX/RX/CPU power and host energy
must not be invented.
6. Repeat balanced or randomized independent physical seed/site/
interference blocks. Predeclare paired endpoints, contrast
family, confidence intervals and multiplicity. The original
single-seed frozen sequential trials are not an efficacy
confirmation.

All six items have NOT passed, hence the complete original
embedded feedback controller remains [NEED EXPERIMENT].

## 6. Submission positioning

This is a new submission project, not a formal response to an
unaccepted journal revision. Evidence now supports a transparent
negative decision-value result with explicit telemetry cost and
the selection-population gap. A novel risk-aware controller with
operational deadline/missing-demand calibration is a *candidate
research direction*, not a completed contribution. It would
need its own method implementation and independent confirmation,
with POINT-EA, original ACR-MCR and budget-matched baselines.

Keep original, Cooja and physical studies separate in Methods
and Results. Avoid false universal superiority claims and
unsupported transfer of statistical guarantees. Manuscript
acceptance and full physical validation remain unresolved.
