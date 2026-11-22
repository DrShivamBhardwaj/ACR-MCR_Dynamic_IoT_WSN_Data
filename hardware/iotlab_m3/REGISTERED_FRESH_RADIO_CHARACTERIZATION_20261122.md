# Fresh physical radio-power/receipt characterization, registered before data

November 22, 2026. The newly offered samples belong ONLY to ACR-MCR.
No prior Array or other journal observations enter this new sample table.

Site: FIT IoT-LAB Grenoble, four physically deployed M3 AT86RF231 nodes:
2, 14, 150, 350. Device firmware: archived official RIOT M3 radio
characterization (preserve exact remote ELF SHA256). Channel 11,
configured radio powers -17, -9, 0, +3 dBm, nominal payload 50 bytes,
100 unique source frames per transmitter/power, 4 transmitters.
For each source there are 3 receivers, 1600 offers and 4800
receiver-opportunities in total. Monitor channels 11 and 14 with
official IoT-LAB radio-control-node RSSI profile. The execution script
enforces zero other active user experiments before reservation.

Predeclared outputs: physical frame receipt fraction by ordered
TX node, RX node and power; conditional packet RSSI and LQI for
received packets only; errors reported by official parser;
power-setting-specific Wilson 95% intervals used as descriptive
binomial intervals, **not** independent spatial generalisation;
separately monitored channels 11 and 14 reference RSSI.

Scientific constraints: this uses 50B RIOT test frames, not full 500B
ACR application samples or original ACR-MCR controller; separate
100 x 500B link test experiment 459543 establishes that distinction.
Radio-reported RSSI is not an externally calibrated receiver input
power, noise floor or true physical SNR. Monitor on channel 14
is not the traffic channel noise. No SNR-PER curve or absolute PHY
energy-per-packet will be inferred without independent instrument
calibration. Raw logs/OML will be stored only in this ACR-MCR project.
