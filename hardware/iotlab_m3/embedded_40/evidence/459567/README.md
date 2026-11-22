# Physical 40-source plus one sink static transport attempt 459567, INCOMPLETE

This new Grenoble physical reservation deployed 41 source-hashed M3
firmware images and physically transferred 500-byte application
fragments through radio-delivered fixed-cluster control plans.
The physical sink logged 57 unique fully byte-verified 500-byte
reassemblies across the 3 rounds and 120 nominal source-round
opportunities. This is a descriptive diagnostic, not accepted
complete 41-board scientific evidence.

Strict raw-trace auditor returned
INCOMPLETE_TRACE_NOT_SCIENTIFIC_CONFIRMATION because:
- M3-291 (logical source 5) TCP port 20000 refused the UART capture,
  leaving 40 of 41 source serial streams.
- M3-215 (logical source 35) emitted no final ENERGEST record before
  the collector closed following sink completion.
- Some completed payloads had no matching observable source demand
  because source serial coverage was incomplete.

Run source, exact physical mapping, all original raw UART, firmware
SHA256, reservation metadata and strict negative audit are preserved.
The algorithm is a static fixed-head physical transport, NOT original
on-M3 ACR-MCR.
