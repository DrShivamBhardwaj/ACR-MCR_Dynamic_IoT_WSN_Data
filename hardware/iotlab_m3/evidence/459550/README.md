# ACR-MCR-specific independent physical received-packet and radio-power experiment 459550

FIT IoT-LAB Grenoble, 22 Nov 2026. Registered before data:
hardware/iotlab_m3/REGISTERED_FRESH_RADIO_CHARACTERIZATION_20261122.md

Four M3 transmitters: 2,14,150,350. 100 offered 50-byte frames at
each of four supported nominal TX powers -17,-9,0,+3 dBm on channel 11.
The official RIOT M3 radio characterization software, SHA256 in
firmware.sha256, generated original raw per-node JSON. The official
radio_parse module converted it into original per-frame send, receive,
and error CSV. Independent audit PASS: 1600 frames offered by four
senders, 4800 ordered directed receiver opportunities (12 links x 4
power settings x 100 frames). At -17 dBm there were 0/1200 receipts;
at -9 dBm 0/1200; at 0 dBm 167/1200; at +3 dBm 198/1200.
Total 365/4800. All 1600 source send calls were successful.
This experiment does not use the 500B application samples or ACR
routing algorithm. Those were separately tested in 459543.

Packet RSSI/LQI are available only for RECEIVED frames, not for lost
ones, so assigning a received-frame RSSI to a lost frame would be
selection-biased. Control-node OML monitors channels 11 and 14; channel
14 is a different frequency and does NOT give a calibrated channel-11
noise input. Hence the experiment is an empirical TX-setting versus
packet-reception study, NOT an externally calibrated SNR–PER curve.
Configured TX power is a supported board setting, not a verified
injected-power measurement. Repeated frames within link are dependent;
Wilson bounds are descriptive idealizations, not independent-seed
intervals. Four nodes in one site/time block cannot establish generality.

original raw JSON, parser CSV, monitor OML, source checksums, and
audited per-power/per-link results are included. No prior project raw
records have been mixed into this newly captured experimental dataset.
