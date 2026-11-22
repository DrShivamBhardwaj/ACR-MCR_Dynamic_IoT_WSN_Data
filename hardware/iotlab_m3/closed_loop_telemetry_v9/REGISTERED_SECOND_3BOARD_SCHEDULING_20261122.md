# Physical-source availability correction registered before new reservation

First booking 459638 for 14/15/18 was scheduled for 23 Nov 2026 at 12:33:10 UTC, almost 20 hours later. M3-14 was not Alive at diagnosis. This was a reservation failure with no on-board run, not a negative packet result. Its raw metadata is archived.

For a second independent engineering attempt, replace ONLY logical source1 physical M3-14 with Alive M3-16, retaining member M3-15 and sink M3-18. Same existing source SHA256, identical three firmware binaries, static-head transport and three rounds, 500-byte payloads, real per-probe MAC ACK/attempt/duration observation returns. Require 3/3 successful flashes, original 3 UART streams, source-MAC/sink radio telemetry matching. The site may still queue this new experiment; do not infer outcomes from preflight or a Waiting reservation. Not an adaptive original ACR-MCR physical controller.
