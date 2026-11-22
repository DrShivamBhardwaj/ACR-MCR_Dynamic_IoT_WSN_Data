# Post-debug physical integration repeat, exact change log

Run 459567 was INCOMPLETE and is retained without data removal.
The first 41-board transport trial produced 57 complete 500-byte
sink deliveries out of 120 nominal opportunities, but one source
M3-291 did not provide a UART stream, M3-215 missed final energy
trace, and some source-demand messages were uncaptured.
This is a TRANSPORT DEBUG / evidence-completeness correction,
not a new independent confirmation study. Full original ACR-MCR
adaptive optimizer remains unimplemented on M3.

Before the repeat: replace one non-reporting physical source M3-291
with Alive M3-245 at logical source ID5. Logical firmware is unchanged.
Preserve both original site manifests and original complete first-trial
logs. Start UART capture while the IoT-LAB run is Launching, retry
TCP connections for up to 90 seconds, and continue capturing for 20
seconds after sink completion to retain final member ENERGEST.
All 41 firmware image SHA256 hashes and physical route logic remain
unchanged. No outcome thresholds, statistical inferential tests,
newly favorable seeds or original algorithm changes have been made.
The repeat will be reported alongside failed/incomplete first run.
