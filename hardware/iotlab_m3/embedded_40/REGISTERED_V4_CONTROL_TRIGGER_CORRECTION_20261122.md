# V4 transport scheduling bug correction, preregistered

Earlier frozen-fixture V3 experiments 459586 (POINT-EA) and 459587
(ACR-MCR) must be preserved unmodified. ACR produced zero
DATA_DEMAND despite 78 observed control installations; POINT produced
42 demands despite 117 control installations. Physical source M3-291
did not yield a serial trace in both. On-mote PHY sink selection PASSED.

New **transport-only** source change, same two original Python-derived
frozen heads/point/CVaR objectives: sensor DATA_DEMAND timer is armed
in the sensor process after successful reception of both real over-air
control-frame parts, rather than from a potentially asynchronous local
round clock. Payload frame round is the actually received control
round; each source can produce at most one 500-byte sample per
control round. Control nonreception still remains a missed nominal
source opportunity, never replaced with an outcome. No relaxation of
checksum, route or radio-count requirements.

One physical unrecorded source at M3-291 is substituted with Alive
M3-245 in a newly frozen V4 physical mapping. Exactly the same V4
physical nodes and member source images are used for both methods.
The sink's original search/CVaR compiled binary, original seed9401
S5 round20 synthetic candidate/stress fixture, 20s rounds, 40x3=120
original nominal source demands and 500-byte data integrity stay
UNCHANGED. Two physical blocks are developer/debugging evidence,
not independent statistical replicates. Physically measured
500ms deadlines, full online conformal/risk state updates and
Apple M1 measured Joules remain [NEED SOURCE].
