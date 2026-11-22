# Forty native M3 sensor boards + one sink: frozen physical transport check

Registered before physical reservation/deployment, 22 Nov 2026.

Topology: 41 Alive M3 Grenoble devices selected using a deterministic
spatial placement procedure. Exact physical IDs, logical 1–40/41 mapping,
source and sink coordinates are in 41node_physical_layout.json.
Alive site status is NOT proof of reservation availability.

All 41 native firmware executables are built independently from the
same fixed-head transport source, with build macro ACR_NODE_ID=1..41.
Four fixed head IDs 1,11,21,31; each head relays its members' data to
logical sink41. Sink sends two full 80-byte control frames with up-to
three-hop rebroadcast per round. Every source can offer one 500-byte
application sample in eight separate CSMA MAC frames only if it
receives both control parts for that round. Three 20-second rounds
after 25-second UART capture delay. Nominal 40x3=120 source-round
application demands regardless of control reception.

All 41 original physical serial files must be archived; exact firmware
binary SHA256, provisioning manifest and IoT-LAB reservation/deployment
metadata must be retained. The auditor checks presence of 41 serial
streams, final sink completion, unique checksum-PASS 500-byte
reassembly per logical source/round, nonnegative control installations
and exactly one final ENERGEST record per mote. Missing control parts,
queue drops, MAC losses and complete sample failures remain measured
outcomes. They must NOT fail a scientifically valid packet-level
experiment or be excluded to raise PDR.

This is a native 40-source physical radio transport and clustering
wiring smoke, NOT the original ACR-MCR controller on hardware. No
adaptive conformal calibration, empirical CVaR optimizer, event-triggered
search, full physical calibrated SNR, or on-device optimizer CPU-energy
measurement is implemented. UART clocks are not synchronized, so a
500ms source-to-sink latency claim is NOT permitted. A validated
full adaptive embedded algorithm is still [NEED SOURCE].
