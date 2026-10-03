"""Short figure captions and explanatory figure notes."""

CAPTIONS = {
    1: 'Observable information and feedback in ACR-MCR',
    2: 'Round sequence and head-refresh decisions',
    3: 'Timely-delivery and violation effects across dynamic regimes',
    4: 'Timely-delivery and violation effects of successive controller additions',
    5: 'Probe and routed-data coverage: (a,b) transaction cost; (c,d) service time',
    6: 'Radio expenditure for data, probes, control and aggregation',
    7: 'Scaling in S5: (a) timely delivery; (b) decision time',
    8: 'Sensitivity in S5: (a) probe budget; (b) fixed head count'
}

EXPLANATIONS = {
    1: ('Figure 1 separates the controller inputs from the evaluation records. Geometry, energy '
        'and availability enter the planner with the issued link predictions. Only probe outcomes '
        'update learning for the next round; current bounds stay fixed. Evaluation combines those '
        'bounds with separate probe and data records. Latent channel probabilities remain inside '
        'the simulator.'),
    2: ('The branches in Fig. 2 rejoin before member assignment, route construction and forwarding. '
        'Initialization and failed-head recovery bypass the 0.5% gain threshold. After data '
        'forwarding, the controller executes its fixed probe schedule, scores both observation '
        'streams against the frozen bounds and updates learning from probes only.'),
    3: ('Figure 3 reports ACR-MCR minus POINT-EA in percentage points across 30 paired seeds. '
        'Bars are pointwise 95% Student-t intervals. Positive differences favour ACR-MCR for '
        'timely delivery; negative differences favour it for violations. These scenario-level '
        'comparisons are exploratory. The co-primary inference instead averages S1–S5 within '
        'each seed before testing.'),
    4: ('Each adjacent comparison in Fig. 4 changes the named component while retaining '
        'objective weights and search budget. Differences are in percentage points, using '
        '30 seed blocks averaged over S1–S5. The bars show pointwise 95% intervals; the '
        'ten-test Holm correction applies to the significance tests, not these intervals.'),
    5: ('For Fig. 5, coverage counts are pooled over ten rounds within each seed and then '
        'averaged across 30 seeds. Shading gives a pointwise 95% interval for ACR-MCR. '
        'The horizontal reference is 0.90 coverage; the vertical reference marks the end '
        'of warm-up. The panels distinguish probe and selected-data transactions and do '
        'not measure joint coverage of an entire route.'),
    6: ('Figure 6 includes warm-up and averages S1–S5 within each of 30 seeds. Whiskers '
        'give 95% intervals for total expenditure. Full-payload probes contain 4000 bits. '
        'Stored energy in disabled nodes is excluded from consumption, while the control '
        'segment covers the declared ideal local broadcasts. Processor energy and reliable '
        'multi-hop telemetry collection are outside this ledger.'),
    7: ('In Fig. 7a, S5 service estimates use 30 seeds at 40 nodes and ten separate seeds '
        'at 80 and 120 nodes. Figure 7b uses five sequential profiling seeds per setting '
        'on an AMD EPYC 9V74 host. Bars are 95% intervals. Timing covers head search '
        'and route construction averaged over rounds, excluding prediction updates and '
        'packet execution.'),
    8: ('Figure 8 uses ten matched seeds in S5; bars show 95% intervals. Panel (a) varies '
        'the probe budget at 40 nodes, with the prior forecaster retained when probing is '
        'disabled. Panel (b) varies head count at a fixed 60 nodes. These settings were '
        'specified before execution and were not used to tune the primary configuration.')
}
