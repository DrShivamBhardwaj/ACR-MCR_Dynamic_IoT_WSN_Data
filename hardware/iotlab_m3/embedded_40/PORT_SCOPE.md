# Physical 40-sensor transport-only embedded port

Derived from the tested 40-node Cooja over-the-air control and 500-byte
fragmentation source. Distinct M3 firmware is compiled with ACR_NODE_ID
1..40 for sources and 41 for the sink. This first port uses a
**static** four-head map (heads 1,11,21,31) generated on the sink
itself, delivered as two 80-byte over-the-air control segments per
20s round, with TTL-3 rebroadcast. Each source offers one 500-byte
sample in 8 MAC fragments per round; sink verifies 500-byte contents.
All motes report ENERGEST ticks and transmission callbacks.
The sink is board 41 logically; physical IoT-LAB board number is
recorded separately in the deployment manifest.

This DOES NOT implement the original Python ACR-MCR optimiser on M3:
no adaptive conformal calibration, no minimisation of risk objective,
no event-triggered optimiser and no fully faithful predictor state.
The radio-control and packet-transfer implementation alone is not
scientific proof of adaptive-controller performance. A 3-board smoke
test is required before attempting the 41-board group, and an
independently repeated adaptive algorithm test remains [NEED SOURCE].
The sink does not have synchronized time with member nodes, so
application 500ms latency is not measured as a physical metric.
