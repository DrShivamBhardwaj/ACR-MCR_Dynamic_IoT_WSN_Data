# Independent 500-byte Cooja radio-control confirmation

Generated from a COMPLETE, independently audited 40-case registration.
Original 1,280-run synthetic model remains immutable.

40 sensors, one sink, 160 rounds per run, ten paired seed blocks
9201–9210, two Cooja scenarios S1/S5, POINT-EA and ACR-MCR.
Each original 500-byte application sample is eight MAC fragments.
Each controller plan is written to the sink ONLY and delivered to
sensor motes over actual simulated CSMA radio control messages.

## Registered primary outcomes

| ACR-MCR minus POINT-EA | Difference (percentage points) | 95% paired CI (pp) | Holm p |
|---|---:|---:|---:|
| PDR_nominal | +0.658 | [-1.981, +3.296] | 0.783716 |
| timely_ratio_nominal | -0.051 | [-0.179, +0.077] | 0.783716 |

The independent statistical unit is the seed block,
not the count of successful MAC frames or the 40 individual runs.
The confidence intervals describe the registered mean paired
difference over S1/S5, with Holm correction for the two co-primary outcomes.
A result with p >= 0.05 is not proof of equivalence.

## Descriptive network and telemetry accounting

| Metric | POINT-EA | ACR-MCR |
|---|---:|---:|
| Mean full 500B PDR | 0.63811 | 0.64469 |
| Mean completed within 500 ms | 0.00725 | 0.00674 |
| Mean installed control node-rounds | 4369.3 | 4430.7 |
| Mean control frame callbacks | 10475.2 | 10540.7 |
| Mean data-fragment frame callbacks | 68122.7 | 73381.0 |
| Mean total MAC callbacks | 82836.4 | 88214.4 |
| Aggregate Cooja radio TX node-seconds per run | 810.247 | 851.388 |
| Aggregate Cooja radio listen node-seconds per run | 130471.786 | 130430.639 |
| Aggregate Cooja CPU node-seconds per run | 131282.033 | 131282.027 |

The 40 runs cover a registered total of 256,000 original
sensor-round demand opportunities (40 sensors x 160 rounds x 40 runs).
Every missed control reception remains part of the nominal source-demand denominator.
Cooja ENERGEST reports dwell-time counters, not physical energy in Joules.
The sink computes each controller plan externally in Python.

## Independent physical boundary checks
Grenoble IoT-LAB M3 experiment 459543 tested a two-board
100-sample, 500-byte/8-fragment physical transfer. All 800 fragment
callbacks and receptions were recorded and 100 reconstructed samples
passed a byte-level integrity audit. Testbed supply-power integration
measured 11.7283 J total device energy over 107.661 s on the TX board
and 11.1273 J over 109.162 s on RX, including idle/CPU/radio operation.

Separate experiment 459550 used FOUR M3 boards and 50-byte
official radio-characterization packets. For nominal -17, -9, 0, +3 dBm
settings, receiver opportunities succeeded 0/1200, 0/1200,
167/1200 and 198/1200 respectively. Receiver RSSI is conditional
on reception. No calibrated input SNR or full deployed-controller
energy data were obtained.

## Inference limits

These Cooja runs use two limited radio regimes, not all five
disturbance laws or exact offered-load timing of the original model.
Control messages are radio-delivered but the Python decision program
still runs off-mote. Neither Cooja dwell time nor a two-board physical
power measurement accounts for full network CPU/computation energy.
Do not call this a calibrated SNR–PER experiment or a full physical
40-node adaptive controller deployment.

The cited comparative literature remains the 18 references supplied
in the earlier manuscript; verified additional source synthesis is [NEED SOURCE].
Any algorithmic novelty or claims of superiority must follow the
observed effects and the complete peer-reviewed literature, not a
desired result.

Firmware Cooja source SHA256: 8dae8321fcd71119b614a566989b0ded353885282e412a48235aee2846c189cb
