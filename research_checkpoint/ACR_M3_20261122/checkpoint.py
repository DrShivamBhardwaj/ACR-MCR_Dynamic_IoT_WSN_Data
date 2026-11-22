#!/usr/bin/env python3
"""ACR-MCR source-hashed, proof-gated, append/reverify Git resume ledger.

No scientific experiment is treated as complete from job exit code alone.
Only stage-specific source and evidence validators can mark it COMPLETE.
Each durable transition is committed and pushed before another stage begins.
"""
import argparse, datetime, fcntl, hashlib, json, os, subprocess, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
LEDGER=HERE/'ledger.json'
LOCK=HERE/'.checkpoint.lock'
BASE=REPO/'hardware/iotlab_m3/embedded_40'
SHA_ORIGINAL='3f134a8826525215f7cf2ff307bab3893c0d64b050f742bdc3c250b1c0302ea4'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):
    return str(p.relative_to(REPO))
def read(p):
    return json.loads(p.read_text())
def cmd(*args,check=True):
    p=subprocess.run(args,cwd=REPO,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if check and p.returncode:
        raise RuntimeError('COMMAND FAILED '+repr(args)+'\n'+p.stdout[-1800:]+'\n'+p.stderr[-1800:])
    return p.stdout.strip()
def original_check():
    f=REPO/'acr_mcr_v2.py'
    assert digest(f)==SHA_ORIGINAL, 'Original Python source changed; stop'
    return f
def proof(stage):
    e=[original_check()]
    result={}
    if stage=='original_source':
        result={'original_sha256':SHA_ORIGINAL,'interpretation':'Immutable original reference'}
    elif stage=='head_risk_parity_80':
        f=BASE/'extended_parity/80_fixture_parity.json'
        x=read(f)
        assert x['status']=='PASS_DETERMINISTIC_INNER_KERNEL'
        assert x['original_source_sha256']==SHA_ORIGINAL
        assert x['fixtures']==80 and x['independent_seed_blocks']==10
        assert x['risk_enabled_fixtures']==20 and x['full_search_trace_checks']==80
        assert x['evaluated_candidate_plan_and_objective_checks']==480
        assert x['max_objective_abs_error']<=1e-12
        e += [f,BASE/'acr_optimizer_core.c',BASE/'test_optimizer_parity.py']
        result={'fixtures':80,'seed_blocks':10,'risk_active_cases':20,'max_abs_error':x['max_objective_abs_error'],'scope':'fixed original state and frozen NumPy genotype/risk trace only'}
    elif stage=='m3_frozen_kernel_memory':
        f=BASE/'m3_frozen_kernel_memory_audit_seed9402.json'
        x=read(f)
        assert x['verdict']=='PASS_BINARIES_LINK_AND_FIT_FROZEN_M3_KERNEL'
        assert len(x['rows'])==2 and set(row['method'] for row in x['rows'])=={'point_ea','acr_mcr'}
        for row in x['rows']:
            assert row['flash_bytes']<x['platform_limits']['flash_bytes']
            assert row['ram_bytes']<x['platform_limits']['ram_bytes']
        e += [f]
        result={'fit':x['rows'],'scope':'compiled frozen-input M3 sink kernel; not full adaptive runtime'}
    elif stage=='m3_v6_point_physical_pass':
        p=BASE/'evidence/FROZEN_41_BOARD_SEED9402_V6_PARTIAL_20261122/point_ea'
        f=p/'physical_summary.json';g=p/'deployment.json'
        s=read(f);q=read(g)
        assert s['experiment']==459607 and s['method']=='POINT-EA'
        assert s['scientific_validation_pass'] is True and not s['failures']
        assert s['captured_serial_nodes']==41
        assert s['control_receptions']==120
        assert s['full_500B_sink_reassemblies']==47
        assert len(q.get('0',[]))==41 and set(q)=={'0'}
        assert sum(v['energy_snapshots']==1 for v in s['physical_serial_records'].values())==41
        ref=read(p/'frozen_original_fixture.json')
        assert ref['original_simulator_sha256']==SHA_ORIGINAL and ref['seed']==9402 and ref['scenario']=='S5' and ref['original_method']=='POINT-EA'
        sink=list(p.rglob('*logical-41.serial.log'))
        assert len(sink)==1
        x=sink[0].read_text()
        assert 'ONBOARD_OPT_READY fixture=POINT-EA_9402_S5_r20 risk=0' in x
        assert 'DIST_DONE' in x and x.count('SINK_REASSEMBLED round=')==47
        e += [f,g,p/'frozen_original_fixture.json',sink[0],
              BASE/'41_firmware_manifest_v6.json',BASE/'41node_physical_layout_v6.json']
        result={'experiment':459607,'flash_ok':41,'UART':41,'energest':41,'full_500B':47,
                'denominator':120,'scope':'single frozen original seed, packet-only hardware feasibility, not real adaptive closed loop'}
    elif stage=='host_m1_apple_cpu_power_estimate':
        p=REPO/'host_energy/authorized_m1_power_runs/20261122T161647Z'
        f=p/'independent_interval_power_verification.json'
        x=read(f)
        assert x['status']=='PASS_6_ROOT_POWER_TRACES_WITH_EXPLICIT_SCIENTIFIC_LIMITS'
        assert x['original_sha256']==SHA_ORIGINAL and x['independent_trace_count']==6
        assert x['workload_cases_each_method']==200
        assert x['sampled_while_euid_root'] is True
        assert x['original_cpu_subsystem_power_is_estimated'] is True
        assert x['calibrated_wallplug_J'] is None and x['actual_electricity_meter_used'] is False
        q=read(p/'independent_file_sha256.json')
        for name,hashvalue in q.items():
            assert digest(p/name)==hashvalue,('POWER_RAW_CHANGED',name)
        assert len(q)==16
        e += [f,p/'registration.json',p/'independent_file_sha256.json',
              REPO/'host_energy/verify_power_independent.py']
        result={'root_sampling':'CONFIRMED','raw_power_traces':6,'full_cases_per_method':200,
            'point_estimated_cpu_J_per_full_sim_case':x['by_method']['POINT-EA']['mean_estimated_cpu_J_per_simulator_case'],
            'acr_estimated_cpu_J_per_full_sim_case':x['by_method']['ACR-MCR']['mean_estimated_cpu_J_per_simulator_case'],
            'scope':'Apple aggregate CPU subsystem estimate, NOT host optimizer-only calibrated electrical energy'}
    elif stage=='m3_v7_risk_flash_pass':
        p=BASE/'evidence/FROZEN_41_BOARD_SEED9402_V7_ACR_ONLY_20261122/acr_mcr'
        f=p/'deployment.json';g=p/'reservation.json'
        q=read(f);r=read(g)
        assert len(q.get('0',[]))==41 and set(q)=={'0'}
        expected=read(BASE/'41_firmware_manifest_v6.json')
        assert expected['source_sha256']=='e4d15f7bb5ec35ee7177e7b154851619b7b19b3e9fb8fe4c0d5e4e285947f312'
        actual={f"m3-{int(v['physical_board'])}.grenoble.iot-lab.info" for v in expected['firmware'].values()}
        assert set(q['0'])==actual and len(actual)==41
        e += [f,g,BASE/'41_firmware_manifest_v6.json']
        result={'experiment':r.get('id'),'flash_ok':41,'scope':'firmware installation only; not packet delivery or adaptive physical validity'}
    elif stage=='m3_v7_risk_physical_pass':
        p=BASE/'evidence/FROZEN_41_BOARD_SEED9402_V7_ACR_ONLY_20261122/acr_mcr'
        f=p/'physical_summary.json';g=p/'deployment.json'
        s=read(f);q=read(g)
        assert s['method']=='ACR-MCR' and s['scientific_validation_pass'] is True
        assert not s['failures'] and s['captured_serial_nodes']==41
        assert len(q.get('0',[]))==41 and set(q)=={'0'}
        assert sum(v['energy_snapshots']==1 for v in s['physical_serial_records'].values())==41
        sink=list(p.rglob('*logical-41.serial.log'));assert len(sink)==1
        x=sink[0].read_text()
        assert 'ONBOARD_OPT_READY fixture=ACR-MCR_9402_S5_r20 risk=1' in x
        assert 'DIST_DONE' in x
        assert x.count('SINK_REASSEMBLED round=')==s['full_500B_sink_reassemblies']
        ref=read(p/'frozen_original_fixture.json')
        assert ref['original_simulator_sha256']==SHA_ORIGINAL and ref['seed']==9402 and ref['original_method']=='ACR-MCR'
        e += [f,g,p/'frozen_original_fixture.json',sink[0]]
        result={'experiment':s['experiment'],'flash_ok':41,'UART':41,'energest':41,
            'full_500B':s['full_500B_sink_reassemblies'],'denominator':120,
            'scope':'risk frozen input single seed only, not closed loop'}
    else:
        raise KeyError('No scientifically validated completion contract for '+stage)
    entries={rel(p):digest(p) for p in e}
    return result,entries

def new_state():
    return {'schema':1,'project':'ACR-MCR Original M3 40-source 41-board physical port',
       'original_reference_sha256':SHA_ORIGINAL,'stages':{},
       'policy':'Only COMPLETE stages with reverified hashes may be skipped. Failed and blocked tasks are never called successful.'}
def load():
    return read(LEDGER) if LEDGER.exists() else new_state()
def save(x):
    x['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    temp=LEDGER.with_suffix('.tmp')
    temp.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
    temp.replace(LEDGER)
def sync(stage):
    cmd('git','add',rel(LEDGER),rel(Path(__file__)))
    staged=cmd('git','diff','--cached','--name-only')
    if staged:
        assert set(staged.splitlines()).issubset({rel(LEDGER),rel(Path(__file__))}),staged
        cmd('git','commit','-m',f'Checkpoint ACR-M3 validated stage {stage}')
    # Shared Git branch: retain unrelated remote work and retry bounded failures.
    for attempt in range(5):
        try:
            cmd('git','-c','rebase.autoStash=true','pull','--rebase','origin','main')
            cmd('git','push','origin','main')
            local=cmd('git','rev-parse','HEAD')
            remote=cmd('git','ls-remote','origin','refs/heads/main').split()[0]
            assert local==remote,('git push not durable',local,remote)
            return local
        except Exception:
            if attempt==4:raise
    raise AssertionError('unreachable')
def action(args):
    original_check()
    x=load()
    if args.command=='status':
        for key,val in x['stages'].items():
            verified=''
            if val['status']=='COMPLETE':
                try:
                    got,art=proof(key)
                    assert art==val['evidence_sha256'], 'EVIDENCE_CHANGES'
                    verified='reverified'
                except Exception as exc: verified='DO_NOT_SKIP: '+str(exc)
            print(key,val['status'],verified, val.get('reason',''),val.get('details',{}))
        print('GIT_HEAD',cmd('git','rev-parse','HEAD'))
        return
    if args.command=='should-skip':
        val=x['stages'].get(args.stage,{})
        if val.get('status')!='COMPLETE':print('RUN_REQUIRED',args.stage);return
        got,art=proof(args.stage)
        if art!=val.get('evidence_sha256'):
            raise RuntimeError('Previously COMPLETE evidence changed; do not skip')
        print('SAFE_TO_SKIP_VERIFIED',args.stage)
        return
    if args.command=='record-complete':
        got,art=proof(args.stage)
        current=x['stages'].get(args.stage,{})
        if current.get('status')=='COMPLETE':
            assert current['evidence_sha256']==art,'Existing completed stage changed!'
        x['stages'][args.stage]={
          'status':'COMPLETE','details':got,'evidence_sha256':art,
          'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    elif args.command=='record-pending':
        assert args.reason
        if x['stages'].get(args.stage,{}).get('status')=='COMPLETE':
            raise RuntimeError('Refuse to downgrade a completed stage')
        x['stages'][args.stage]={
          'status':args.status,'reason':args.reason,
          'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    else:raise ValueError(args.command)
    save(x)
    print('DURABLY_PUSHED_GIT_COMMIT',sync(args.stage),args.stage,x['stages'][args.stage]['status'])

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=('status','should-skip','record-complete','record-pending'))
    p.add_argument('--stage')
    p.add_argument('--reason')
    p.add_argument('--status',default='PENDING',choices=('PENDING','FAILED','BLOCKED'))
    a=p.parse_args()
    with LOCK.open('w') as fh:
        fcntl.flock(fh,fcntl.LOCK_EX)
        action(a)
