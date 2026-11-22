#!/bin/bash
set -euo pipefail
ROOT="$HOME/research/ACR_MCR_Recovery_20261122"
D="$ROOT/data/hardware/iotlab_m3/embedded_40"
OUT="$ROOT/logs/m3_frozen_decision_real_radio_20261122_v5"
mkdir -p "$OUT"
date -u '+START_UTC %F %T' | tee "$OUT/orchestrator.log"
# Source hash and split method choice were preregistered before results.
for attempt in $(seq 1 100);do
  if grep -q '^V5_COMPLETE 41 ' "$ROOT/logs/m3_member_v5_compilation/build_all.log";then break;fi
  sleep 5
done
grep -q '^V5_COMPLETE 41 ' "$ROOT/logs/m3_member_v5_compilation/build_all.log"
python3 - "$D" <<'PY'
import json,hashlib,sys
from pathlib import Path
d=Path(sys.argv[1]);manifest=json.loads((d/'41_firmware_manifest_v5.json').read_text())
assert len(manifest['firmware'])==41
for i in range(1,41):
 f=d/'firmware_41_v5'/manifest['firmware'][str(i)]['filename']
 assert hashlib.sha256(f.read_bytes()).hexdigest()==manifest['firmware'][str(i)]['sha256']
assert manifest['source_sha256']==hashlib.sha256((d/'acr_m3_transport_control_triggered_v5.c').read_bytes()).hexdigest()
print('ALL_V5_NATIVE_M3_IMAGES_SOURCE_HASHES_PASSED')
PY
cd "$ROOT/data"
git add hardware/iotlab_m3/embedded_40/41_firmware_manifest_v5.json \
        hardware/iotlab_m3/embedded_40/firmware_41_v5.tar.gz
git -c core.whitespace=-trailing-space diff --cached --check
if ! git diff --cached --quiet;then
  git commit -m "Preserve 40 physical source firmware images for preregistered V5 pair"
fi
git push origin main
# One testbed reservation at a time. The original sink kernel binaries
# are immutable and method-specific. Study is OPEN-LOOP, one seed.
for METHOD in POINT-EA ACR-MCR;do
  if [ "$METHOD" = POINT-EA ];then LABEL=point_ea;else LABEL=acr_mcr;fi
  echo "START_PHYSICAL_METHOD=$METHOD" | tee -a "$OUT/orchestrator.log"
  if caffeinate -i "$ROOT/.venv/bin/python" -u "$D/run_41_frozen_baseline_v5.py" --method "$METHOD" \
       > "$OUT/$LABEL.session.log" 2>&1;then
    echo "CAPTURE_PROCESS_SUCCEEDED=$METHOD" | tee -a "$OUT/orchestrator.log"
  else
    echo "CAPTURE_PROCESS_FAILED=$METHOD" | tee -a "$OUT/orchestrator.log"
  fi
  # Fail-closed: no overlapping testbed reservations.
  "$HOME/Research/.iotlabcli-venv/bin/iotlab-experiment" get -e --active > "$OUT/active_after_$LABEL.json"
  "$ROOT/.venv/bin/python" - "$OUT/active_after_$LABEL.json" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))
assert x=={}, "A prior experiment remains active; do not overlap ownership"
PY
done
cd "$D"
"$ROOT/.venv/bin/python" "$D/audit_41_frozen_baseline_v5.py" \
  --root "$OUT" --out "$OUT/independent_audit.json" > "$OUT/audit_stdout.log" 2>&1 || true
# Always archive negative evidence and each original raw trace.
"$ROOT/.venv/bin/python" - "$D" "$OUT" <<'PY'
from pathlib import Path
import json,hashlib,sys,shutil
d=Path(sys.argv[1]);root=Path(sys.argv[2])
dest=d/'evidence'/'FROZEN_41_BOARD_V5_20261122';dest.mkdir(exist_ok=True,parents=True)
for label in ['point_ea','acr_mcr']:
 p=root/label;q=dest/label;q.mkdir(exist_ok=True,parents=True)
 for f in p.rglob('*'):
  if f.is_file() and (
    f.name.endswith('.serial.log') or f.name in
    ('capture_summary.json','frozen_original_fixture.json','reservation.json',
     'preflight.json','deployment.json','physical_summary.json','status.json')):
    tgt=q/f.relative_to(p);tgt.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(f,tgt)
x=root/'independent_audit.json'
if x.exists():
 shutil.copy2(x,dest/x.name)
 data=json.loads(x.read_text())
 else_status=[(q['method'],q['status'],q['physical_41_board_uart_count'],
              q['real_control_installations'],q['real_data_demand_logs'],
              q['full_byte_verified_500B_sink_deliveries']) for q in data['methods']]
else:
 data=None;else_status=[]
(dest/'README.md').write_text(
 '# Source-locked original frozen kernel physical V5 paired sessions\n\n'
 'Both original on-M3 search/CVaR method binaries use unchanged original '
 'synthetic Python fixture seed9401, scenario S5, round20. '
 'The sensor transport scheduling was corrected twice before this fresh pair '
 'so a sensor offers data AFTER receiving both actual radio route-control '
 'parts; this preserves original 500B payload and nominal 40x3=120 '
 'source-round denominator. Physical layout is identical for both '
 'methods. Every physical run is an exploratory three-round '
 'developer test, not independent statistical seed confirmation.\n\n'
 'Results (method,status,physical UART boards,control receipts,actual demands,'
 'fully byte-verified complete 500B sink samples):\n'+
 '\n'.join(map(str,else_status))+
 '\n\nOriginal adaptive ACR-MCR predictor, PCG64 risk generator and '
 'multi-round feedback state are NOT deployed on 40 physical nodes. '
 'No synchronized physical 500ms deadline. No validated physical '
 'M1 host Joules. Previous failed V3 trials retained separately.\n')
hashes={str(f.relative_to(dest)):hashlib.sha256(f.read_bytes()).hexdigest()
        for f in dest.rglob('*') if f.is_file() and f.name!='sha256_manifest.json'}
(dest/'sha256_manifest.json').write_text(json.dumps(hashes,indent=2)+'\n')
print('RESULTS',else_status, 'ARCHIVED_FILES',len(hashes),flush=True)
PY
cd "$ROOT/data"
git add hardware/iotlab_m3/embedded_40/evidence/FROZEN_41_BOARD_V5_20261122
git -c core.whitespace=-trailing-space diff --cached --check
git commit -m "Archive full independent physical 41M3 V4 frozen risk-versus-point UART and fail-closed audit"
git push origin main
echo ALL_V4_EXPERIMENT_FILES_PERSISTED
date -u '+FINISH_UTC %F %T'
