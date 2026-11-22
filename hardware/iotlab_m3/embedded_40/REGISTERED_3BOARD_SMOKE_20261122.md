# M3 physical three-node 500-byte/over-air control smoke

Registered before execution on 22 Nov 2026. Grenoble boards M3-14,
M3-15, M3-18 map to logical source IDs 1, 2 and sink ID 41.
The sink executes a STATIC 4-head logical assignment rather than
the original adaptive Python optimizer. Source1 is an intended head,
source2 routes via source1, source1 forwards to sink41; the other
38 logical sources are NOT deployed in this initial pilot.
Sink sends two 80-byte broadcast control-plan segments per round.
Three 20-second rounds and initial 25-second UART capture delay.
Each active source offers one original 500-byte application sample
as eight 802.15.4 CSMA packets each round, contingent on receipt of
both over-the-air control-plan parts. Unique reconstructed 500-byte
samples and physical MAC callback counts must be read from actual
M3 serial traces. Lost control, incomplete payloads and missed
rounds are outcomes, not reasons to infer unobserved successes.
A missing source/log makes the pilot inconclusive.
Do not claim original ACR-MCR controller or physical 40-node
validation: this is transport-only code-path validation for two
actual sources and one physical sink.
