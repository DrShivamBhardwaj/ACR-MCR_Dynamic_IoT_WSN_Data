#!/usr/bin/env python3
"""Idempotent V7-only ACR physical resume; checkpoint flash and raw evidence.

Run explicitly. Never reruns the already successful source/parity/memory/POINT
steps. Refuses all new reservations while any IoT-LAB experiment is active.
No inference or "PASS" from a nonzero UART collector.
"""
import argparse, datetime, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path

ME=Path(__file__).resolve().parent
REPO=ME.parents[1]
ROOT=REPO.parent
D=REPO/'hardware/iotlab_m3/embedded_40'
CP=ME/'checkpoint.py'
ENV=ROOT/'.venv/bin/python'
OUT=ROOT/'logs/m3_frozen_decision_real_radio_seed9402_V7_ACR_recovery_20261122'
RAW=OUT/'acr_mcr'
ARCH=D/'evidence/FROZEN_41_BOARD_SEED9402_V7_ACR_ONLY_20261122'
AUDIT_ROOT=ROOT/'logs/m3_frozen_decision_real_radio_seed9402_V7_combined_20261122'
REUSE_POINT=ROOT/'logs/m3_frozen_decision_real_radio_seed9402_V6_20261122/point_ea'
EXPERIMENT=Path.home()/'Research/.iotlabcli-venv/bin/iotlab-experiment'

def execute(args,check=True):
    r=subprocess.run([str(x) for x in args],capture_output=True,text=True,cwd=REPO)
    if check and r.returncode:
        raise RuntimeError('Command failure: '+repr(args)+'\n'+r.stderr[-1600:]+'\n'+r.stdout[-1600:])
    return r
def git_push(label):
    execute(['git','add',str(ARCH.relative_to(REPO))])
    staged=execute(['git','diff','--cached','--name-only']).stdout.strip()
    if staged:
        assert all(x.startswith(str(ARCH.relative_to(REPO))+'/') for x in staged.splitlines())
        execute(['git','commit','-m','Checkpoint physical ACR risk '+label])
    for attempt in range(5):
        try:
            execute(['git','-c','rebase.autoStash=true','pull','--rebase','origin','main'])
            execute(['git','push','origin','main'])
            sha=execute(['git','rev-parse','HEAD']).stdout.strip()
            upstream=execute(['git','ls-remote','origin','refs/heads/main']).stdout.split()[0]
            assert sha==upstream
            print('GITHUB_SYNC_VERIFIED',label,sha,flush=True)
            return
        except Exception:
            if attempt==4:raise
    raise AssertionError('Git failed')
def checkpoint(status,stage,reason=''):
    arg=[ENV,CP,'record-complete' if status=='COMPLETE' else 'record-pending','--stage',stage]
    if status!='COMPLETE':
        arg += ['--status',status,'--reason',reason]
    r=execute(arg)
    print(r.stdout.strip(),flush=True)
def stage_done(stage):
    r=execute([ENV,CP,'should-skip','--stage',stage])
    return 'SAFE_TO_SKIP_VERIFIED' in r.stdout
def archive(allow_failed):
    dst=ARCH/'acr_mcr';dst.mkdir(parents=True,exist_ok=True)
    for p in RAW.rglob('*'):
        if not p.is_file():continue
        if p.name.endswith('.serial.log') or p.name in (
            'physical_summary.json','capture_summary.json','frozen_original_fixture.json',
            'reservation.json','deployment.json','preflight.json',
            'status.json','source_clock_calibration.json'):
            target=dst/p.relative_to(RAW)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,target)
    for f in ('session.log','orchestrator.log'):
        p=OUT/f
        if p.exists():shutil.copy2(p,ARCH/f)
    if (AUDIT_ROOT/'independent_audit.json').exists():
        shutil.copy2(AUDIT_ROOT/'independent_audit.json',ARCH/'independent_audit.json')
    summary=dst/'physical_summary.json'
    data=json.loads(summary.read_text()) if summary.exists() else {}
    readme=ARCH/'README.md'
    readme.write_text(
       '# V7 frozen-risk physical ARM checkpoint\n\n'
       'Registered independent synthetic seed9402 S5 round20, frozen '
       'original candidate and CVaR state on physical M3 sink, exact V5 '
       'sensor image hashes and V6 immutable physical layout. '
       'This is **NOT** fully closed-loop adaptive ACR-MCR. '
       'Matched POINT-EA (experiment 459607) is in immutable V6 archive.\n\n'
       f'ACR event capture condition: {data.get("scientific_validation_pass",None)}. '
       f'Experiment {data.get("experiment","NO_VALID_RESERVATION")}, '
       f'fully byte-verified 500-byte receipts {data.get("full_500B_sink_reassemblies","UNAVAILABLE")}/120, '
       f'original full 41-UART capture {data.get("captured_serial_nodes","UNAVAILABLE")}/41. '
       f'Audit failures: {data.get("failures","UNAVAILABLE")}.\n\n'
       'No service superiority, physical 500ms timely fraction, '
       'native NumPy PCG64 or host M1 Joules can be claimed. '
       'All partial data are retained even on failure.\n')
    manifest={}
    for f in ARCH.rglob('*'):
        if f.is_file() and f.name!='manifest_sha256.json':
            manifest[str(f.relative_to(ARCH))]=hashlib.sha256(f.read_bytes()).hexdigest()
    (ARCH/'manifest_sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('LOCAL_CAPTURE_BACKED_UP_TO_GIT_TREE',len(manifest),'files',flush=True)
    git_push('raw-original-41-UART-'+('failed' if allow_failed else 'completed'))
def ensure_only_pending():
    for stage in ('original_source','head_risk_parity_80',
                  'm3_frozen_kernel_memory','m3_v6_point_physical_pass'):
        if not stage_done(stage):
            raise RuntimeError(f'Previously successful stage {stage} no longer verifies; do not continue.')
        print('SKIP_ALREADY_SUCCESSFUL',stage,flush=True)
    if stage_done('m3_v7_risk_physical_pass'):
        print('NO_RESTART_NEEDED: V7 risk physical is already verified complete',flush=True)
        return False
    return True
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--dry-run',action='store_true')
    opt=parser.parse_args()
    if not ensure_only_pending():return 0
    reservation=execute([EXPERIMENT,'get','-e','--active'])
    active=json.loads(reservation.stdout)
    if active!={}:
        print('RESOURCE_BUSY_NO_DUPLICATE_RESERVATION',active,flush=True)
        return 75
    print('SAFE_RESOURCE_FREE: risk-only attempt, POINT never repeated',flush=True)
    if opt.dry_run:
        print('DRY_RUN_COMPLETE_NO_EXPERIMENT_REQUESTED',flush=True)
        return 0
    OUT.mkdir(parents=True,exist_ok=True)
    session=OUT/'session.log'
    cmd=[str(ENV),'-u',str(D/'run_41_frozen_seed9402_V7.py'),'--method','ACR-MCR']
    print('RUN_PENDING_ONLY',cmd,flush=True)
    flash_recorded=stage_done('m3_v7_risk_flash_pass')
    with session.open('a') as log:
        p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,
            cwd=REPO,start_new_session=True)
        while p.poll() is None:
            if not flash_recorded:
                f=RAW/'deployment.json'
                g=RAW/'reservation.json'
                if f.exists() and g.exists():
                    try:
                        q=json.loads(f.read_text())
                        if set(q)=={'0'} and len(q['0'])==41:
                            target=ARCH/'acr_mcr'
                            target.mkdir(parents=True,exist_ok=True)
                            for f0 in (f,g):
                                shutil.copy2(f0,target/f0.name)
                            git_push('41-of-41-flash-success')
                            checkpoint('COMPLETE','m3_v7_risk_flash_pass')
                            flash_recorded=True
                    except Exception as err:
                        print('FLASH_CHECKPOINT_RETRY',repr(err),flush=True)
            time.sleep(3)
        ret=p.returncode
    print('RISK_PHYSICAL_RUNNER_EXIT',ret,flush=True)
    # Independent strict original 41-board paired audit with source-locked
    # POINT-EA original evidence reused, never repeated or cherry-picked.
    AUDIT_ROOT.mkdir(parents=True,exist_ok=True)
    for lbl,src in (('point_ea',REUSE_POINT),('acr_mcr',RAW)):
        link=AUDIT_ROOT/lbl
        if link.is_symlink():
            assert link.resolve()==src.resolve()
        elif not link.exists():link.symlink_to(src,target_is_directory=True)
        else:raise RuntimeError(f'Refuse unknown existing {link}')
    audit=execute([ENV,D/'audit_41_frozen_seed9402_V6.py',
                   '--root',AUDIT_ROOT,'--out',AUDIT_ROOT/'independent_audit.json'],
                  check=False)
    (AUDIT_ROOT/'audit_stdout.log').write_text(audit.stdout+audit.stderr)
    print('INDEPENDENT_PAIR_AUDIT_EXIT',audit.returncode,flush=True)
    archive(allow_failed=(ret!=0 or audit.returncode!=0))
    if ret!=0 or audit.returncode!=0:
        checkpoint('FAILED','m3_v7_risk_physical_pass',
            f'Original logs archived; transport exit {ret}, independent strict audit exit {audit.returncode}.')
        return 2
    checkpoint('COMPLETE','m3_v7_risk_physical_pass')
    print('COMPLETE_PAIRED_SINGLE_SEED_NOT_FULL_CLOSED_LOOP',flush=True)
    return 0
if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        print('RESUME_FAIL_CLOSED',repr(exc),file=sys.stderr,flush=True)
        sys.exit(2)
