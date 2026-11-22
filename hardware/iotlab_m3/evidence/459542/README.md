# FIT IoT-LAB Grenoble physical 500-byte transport, experiment 459542

This is new ACR-MCR-specific physical evidence. M3-14 transmitted and
M3-15 received. Source firmware reports 100 offered 500-byte samples
and 800/800 MAC callbacks successful. The original host UART capture
started at sample 8 and continued through 99, covering exactly 736
matched TX/RX fragments and 92 fully byte-verified 500-byte samples.
The original capture summary says packet_loss_inference_allowed=true
on the basis of sender termination; that is too permissive for the
full 100-sample sample set. The separate strict_audit.json explicitly
sets full_100_sample_PER_estimate_allowed=false.

The two observed 92/92 and 736/736 ratios describe the captured,
time-censored sample interval only. The uncaptured sample IDs 0-7
cannot be counted as successes or losses. Hardware PHY register snapshots
are not calibrated noise power, RSSI in dBm or SNR. ENERGEST provides
hardware time counters but not power calibration.

The archived firmware_source_at_build.h is extracted from the git
commit 204d11f that produced the original ELF binaries. Raw UART
files are retained without rewriting their contents. This is
a two-board fragmentation test, not a 40-board physical ACR-MCR run.
