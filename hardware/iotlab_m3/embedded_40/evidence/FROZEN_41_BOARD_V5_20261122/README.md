# Frozen source-locked POINT-EA versus ACR-MCR physical V5 audit

On M3 sink, exact original deterministic fixed-input C search + CVaR kernel, candidate RNG and stress tensor frozen from original Python synthetic seed9401 S5 round20. Sensors run real 500-byte fragmented over-air transmission, with real radio control. 41 serial streams available for each of two sequential testbed sessions.
POINT-EA experiment 459594: 39/120 full source samples at sink, 80/120 real route-control receipts. ACR-MCR experiment 459595: 10/120 full samples and 120/120 route-control receipts. These are UNADJUSTED sequential single-fixture contrasts, NOT independent physical statistical seed comparisons, and cannot establish causal superiority or infer a 500ms deadline metric. Both sessions lack one final ENERGEST source record (40/41). The full adaptive feedback loop is not on embedded devices.

The complete original UART, receiver totals, firmware/frozen reference IDs, paired audit results, and failure limits are archived. No physical M1 host optimizer Joules were measured.

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
