#!/usr/bin/env bash
set -euo pipefail
ROOT="$HOME/research/ACR_MCR_Recovery_20261122"
D="$ROOT/data/hardware/iotlab_m3/embedded_40"
OUT="$ROOT/logs/m3_frozen_decision_real_radio_seed9402_V6_20261122"
mkdir -p "$OUT"
date -u '+START_UTC %F %T' | tee "$OUT/orchestrator.log"
for METHOD in POINT-EA ACR-MCR;do
  if [[ "$METHOD" == POINT-EA ]];then LABEL=point_ea;else LABEL=acr_mcr;fi
  echo "PHYSICAL_METHOD_BEGIN=$METHOD" | tee -a "$OUT/orchestrator.log"
  if caffeinate -i "$ROOT/.venv/bin/python" -u "$D/run_41_frozen_seed9402_V6.py" --method "$METHOD" > "$OUT/$LABEL.session.log" 2>&1;then
    echo "PHYSICAL_METHOD_CAPTURE_COMPLETED=$METHOD" | tee -a "$OUT/orchestrator.log"
  else
    echo "PHYSICAL_METHOD_CAPTURE_FAILED=$METHOD" | tee -a "$OUT/orchestrator.log"
  fi
  # Scheduler termination is asynchronous; never overlap reservations.
  for CHECK in $(seq 1 25);do
    "$HOME/Research/.iotlabcli-venv/bin/iotlab-experiment" get -e --active > "$OUT/active_$LABEL.json"
    if "$ROOT/.venv/bin/python" - "$OUT/active_$LABEL.json" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))
assert x=={},x
PY
    then break;fi
    sleep 5
  done
  "$ROOT/.venv/bin/python" - "$OUT/active_$LABEL.json" <<'PY'
import json,sys
assert json.load(open(sys.argv[1]))=={},'Owned testbed reservation remains; no overlapping physical runs'
PY
done
set +e
"$ROOT/.venv/bin/python" "$D/audit_41_frozen_seed9402_V6.py" --root "$OUT" --out "$OUT/independent_audit.json" > "$OUT/audit_log.txt" 2>&1
RC=$?
set -e
echo "SECOND_SEED_AUDIT_EXIT=$RC" | tee -a "$OUT/orchestrator.log"
"$ROOT/.venv/bin/python" - "$D" "$OUT" <<'PY'
import json,hashlib,shutil,sys
from pathlib import Path
d=Path(sys.argv[1]);root=Path(sys.argv[2]);dest=d/'evidence'/'FROZEN_41_BOARD_SEED9402_V6_20261122';dest.mkdir(exist_ok=True,parents=True)
for label in ('point_ea','acr_mcr'):
  for p in (root/label).rglob('*'):
    if p.is_file() and (p.name.endswith('.serial.log') or p.name in ('capture_summary.json','physical_summary.json','frozen_original_fixture.json','reservation.json','preflight.json','deployment.json','status.json','source_clock_calibration.json')):
      q=dest/label/p.relative_to(root/label);q.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(p,q)
for f in ('independent_audit.json','audit_log.txt','orchestrator.log'):
  p=root/f
  if p.exists():shutil.copy2(p,dest/f)
if (dest/'independent_audit.json').exists():
  result=json.loads((dest/'independent_audit.json').read_text())
  rows=[(m['method'],m['experiment'],m['status'],m['full_byte_verified_500B_sink_deliveries'],m['energest_motes_captured']) for m in result['methods']]
else:rows=[]
(dest/'README.md').write_text('# Second prospective fixture block: physical seed9402\n\n'
 'This independently chosen SIMULATOR seed9402 S5 round20 was frozen and registered before physical tests. '
 'Two chronologically separated sessions use POINT-EA and ACR-MCR source-frozen M3 kernel and unchanged real 40-source/one-sink V5 radio transport. '
 'Original raw UART logs, imperfect records and all auditor outcomes are retained. '
 'Both use V5 source and exact V6 layout replacing unflashable M3-215 with M3-196. No physical feedback closes the original adaptive controller. No host M1 Joules. '
 'Physical comparisons are descriptive at n=2 independent simulator seeds, without causal/statistical physical claims.\n'
 +'\n'.join(map(str,rows))+'\n')
hashes={str(q.relative_to(dest)):hashlib.sha256(q.read_bytes()).hexdigest() for q in dest.rglob('*') if q.is_file() and q.name!='manifest_sha256.json'}
(dest/'manifest_sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
print('ARCHIVED_SECOND_SEED_ORIGINAL_UART_COUNT',sum(q.name.endswith('.serial.log') for q in dest.rglob('*')),'RESULTS',rows)
PY
cd "$ROOT/data"
git add hardware/iotlab_m3/embedded_40/evidence/FROZEN_41_BOARD_SEED9402_V6_20261122
git -c core.whitespace=-trailing-space diff --cached --check
git commit -m 'Archive physical independent frozen seed9402 M3 point-versus-risk results without exclusions'
git push origin main
date -u '+END_UTC %F %T' | tee -a "$OUT/orchestrator.log"
