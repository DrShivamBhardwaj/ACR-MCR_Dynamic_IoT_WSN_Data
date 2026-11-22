#!/usr/bin/env python3
"""Immutable physical probe-ACK trace archive with independent audit and Git push."""
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
ROOT=REPO.parent
EXP=459639
SOURCE=ROOT/'logs/real_probe_feedback_v9/experiment_second'
DEST=HERE/'evidence'/str(EXP)
DEST.mkdir(parents=True,exist_ok=True)
def cp(src,dest):
    if src.exists():
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dest)
for n in ('reservation.json','reservation_preflight.json','status.json',
          'status_from_iotlab.json','deployment.json','firmware_sha256.json',
          'physical_smoke_summary.json','capture_stdout.log','capture_stderr.log'):
    cp(SOURCE/n,DEST/n)
cp(ROOT/'logs/real_probe_feedback_v9/physical_runner_second.log',
   DEST/'original_runner.log')
manifest=json.loads((HERE/'MANIFEST_FIRMWARE_SMOKE_second.json').read_text())
if (SOURCE/'deployment.json').exists():
    deploy=json.loads((SOURCE/'deployment.json').read_text())
else:deploy={}
expected={'m3-16.grenoble.iot-lab.info','m3-15.grenoble.iot-lab.info',
          'm3-18.grenoble.iot-lab.info'}
valid_deploy=(set(deploy)=={'0'} and set(deploy.get('0',[]))==expected)
capture=SOURCE/'capture'/str(EXP)
for p in capture.glob('m3-*.log'):
    cp(p,DEST/'original_uart'/p.name)
cp(capture/'capture_summary.json',DEST/'capture_summary.json')
audit=DEST/'strict_radio_telemetry_audit.json'
test_success=False;problem=''
if valid_deploy and len(list((DEST/'original_uart').glob('m3-*.log')))==3:
    command=[str(ROOT/'.venv/bin/python'),str(HERE/'audit_physical_telemetry.py'),
       '--original-uart',str(DEST/'original_uart'),
       '--firmware',str(HERE/'MANIFEST_FIRMWARE_SMOKE_second.json'),
       '--out',str(audit)]
    p=subprocess.run(command,capture_output=True,text=True)
    (DEST/'audit_execution.log').write_text(p.stdout+'\n'+p.stderr)
    if p.returncode==0:
        x=json.loads(audit.read_text())
        test_success=x['verdict']=='PASS_REAL_PHY_REPORT_PATH'
        if not test_success:problem='Physical radio path partial, cannot claim both sources delivered probe observations'
    else:problem='Independent raw-source/sink MAC telemetry audit nonzero; see audit_execution.log'
else:
    problem='Missing exact three successful physical flashes or one of three original UART streams'
status=dict(experiment=EXP,
  status='PASS_2_SOURCE_PHYSICAL_PROBE_TELEMETRY_ONLY' if test_success else 'INCOMPLETE_KEEP_RAW',
  flashes_verified=valid_deploy,
  physical_feedback_proved_for_both_sources=test_success,
  original_acr_mcr_adaptive_controller_validated=False,
  concern=problem or 'Sink received independently source-matching actual ACK, retry and elapsed service time via radio. Still STATIC route algorithm.',
  original_firmware_hashes=manifest['files'])
(DEST/'final_status.json').write_text(json.dumps(status,indent=2)+'\n')
(DEST/'README.md').write_text(
    '# Native three-board radio feedback experiment 459639\n\n'
    f'Exact result: {status["status"]}.\n\n'
    'Originally registered source M3-16/head, member M3-15, sink M3-18, '
    'three rounds, 500B application fragmentation. Source MAC callback '
    'attempt/success/duration can be reported over actual radio to sink. '
    'Only sink observations independently matching the original per-node '
    'serial MAC record count as validated physical probe feedback.\n\n'
    f'Issue: {problem or "No physical source-to-sink telemetry mismatch detected."}\n\n'
    'Strict limits: fixed head-routing STATIC pilot, two sources, one sink. '
    'There is no updated original predictor, no conformal bound refit, no '
    'fresh-risk head search, no next-round adaptive route plan and no '
    '41-node physical feedback or deadlines. Do NOT call this full ACR-MCR.\n'
)
hashes={str(p.relative_to(DEST)):hashlib.sha256(p.read_bytes()).hexdigest()
    for p in DEST.rglob('*') if p.is_file() and p.name!='manifest_sha256.json'}
(DEST/'manifest_sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
print('VALIDATED_ORIGINAL_FEEDBACK_ARCHIVE',status['status'],'trace_files',len(hashes))
def command(*parts):
    p=subprocess.run(parts,capture_output=True,text=True,cwd=REPO)
    if p.returncode:raise RuntimeError(parts+tuple([p.stderr[-500:]]))
    return p.stdout.strip()
command('git','add',str(DEST.relative_to(REPO)))
if command('git','diff','--cached','--name-only'):
    command('git','commit','-m',f'Archive independent original physical V9 MAC feedback trace experiment {EXP}: {status["status"]}')
for attempt in range(3):
    try:
        command('git','-c','rebase.autoStash=true','pull','--rebase','origin','main')
        command('git','push','origin','main')
        local=command('git','rev-parse','HEAD')
        remote=command('git','ls-remote','origin','refs/heads/main').split()[0]
        if local!=remote:raise ValueError('not synced')
        print('GITHUB_DURABLE_ARCHIVE_SHA',local)
        break
    except Exception:
        if attempt==2:raise
