# Second prospective fixture block: physical seed9402

This independently chosen SIMULATOR seed9402 S5 round20 was frozen and registered before physical tests. Two chronologically separated sessions use POINT-EA and ACR-MCR source-frozen M3 kernel and unchanged real 40-source/one-sink V5 radio transport. Original raw UART logs, imperfect records and all auditor outcomes are retained. No physical feedback closes the original adaptive controller. No host M1 Joules. Physical comparisons are descriptive at n=2 independent simulator seeds, without causal/statistical physical claims.
('POINT-EA', 459600, 'PASS_EXPLORATORY_FROZEN_REAL_RADIO_TRACES', 55, 41)
('ACR-MCR', 459602, 'PASS_EXPLORATORY_FROZEN_REAL_RADIO_TRACES', 48, 41)

## Mandatory independent firmware-deployment correction (22 Nov 2026)

Reviewing original IoT-LAB \`deployment.json\` reveals that source-head
**M3-215 was assigned a nonzero (failed) firmware installation status**
in BOTH method sessions. In each session 40 of 41 requested boards
returned success code 0, while M3-215 returned code 1. Even though
41 UART sockets yielded data, **it is not proven that all 41 boards
ran the newly requested method/firmware**. The earlier trace-only
'PASS' applies to packet parsing and deterministic on-sink kernel
checks, NOT to full 41-board firmware-deployment provenance.
These experiments must therefore be classified as developer
diagnostics with a failed deployment gate. The 39/120 versus 10/120
and 55/120 versus 48/120 sample counts are preserved as observed
descriptive UART events but cannot support an independent
head-search/CVaR physical performance claim. These failures are
not filtered from the original nominal denominator. New experiment
protocol V6 requires **all 41 IoT-LAB deployment status codes 0**
before any hardware-validation claim is permitted.
