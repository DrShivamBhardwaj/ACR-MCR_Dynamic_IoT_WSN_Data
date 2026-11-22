# ACR-MCR native M3 40-source plus one sink pilot: experiment 459568

Scientific status is DUAL:
(1) PASS physical static route-control/500-byte packet transport code
path for one 3-round block with 41 original board UART streams:
119 of 120 possible sensor-round over-air control installations,
117 logged source data demands, 86 unique full 500-byte samples
reassembled and byte verified at the sink (86/120=71.67% of
registered nominal opportunities). Device board M3-245 replaced
serial-unavailable M3-291 at logical source ID5 after initial
incomplete experiment 459567. All other on-mote firmware binaries
were unchanged. Source and deployment hashes are archived.
(2) Original strict combined trace plus energy audit remains
INCOMPLETE because logical source 35 (physical M3-215) had no final
ENERGEST record, yielding 40/41 energy snapshots. The zero-ENERGEST
gap is not concealed and physical energy cannot be claimed complete.

The on-M3 algorithm is STATIC 4-head physical radio transport,
not original adaptive conformal/CVaR ACR-MCR. This is hardware
integration evidence only, not a multi-seed validation of the paper's
adaptive claims. UART wall clocks across boards are not synchronized;
a physical 500ms timely-delivery ratio cannot be inferred. This
evidence must be kept separate from Cooja and original simulator runs.

Both the original incomplete experiment 459567 and this corrected
capture are retained as successive development test results.
