#!/usr/bin/env python3
"""Independent raw-interval verification of root-authorized Apple M1 power.

Scientific scope: Apple *estimated* CPU-subsystem Joules for full original
simulator workloads; NOT calibrated wall-plug, NOT exclusively optimizer.
"""
from pathlib import Path
import csv,datetime,hashlib,json,math,re,statistics,sys
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'acr_mcr_v2.py'
SHA="3f134a8826525215f7cf2ff307bab3893c0d64b050f742bdc3c250b1c0302ea4"
HEADER=re.compile(r"(?m)^\*\*\* Sampled system activity \((.*?)\) \(([\d.]+)ms elapsed\) \*\*\*$")
POWER=re.compile(r"(?m)^CPU Power:\s*([\d.]+)\s*(mW|W)\s*$")
METHODS=('IDLE','POINT-EA','ACR-MCR','ACR-MCR','POINT-EA','IDLE')
def hash_file(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit(path):
    assert hash_file(SOURCE)==SHA
    path=Path(path)
    reg=json.loads((path/'registration.json').read_text())
    assert reg['status']=='RAW_POWER_SAMPLED_NOT_CALIBRATED_JOULES'
    assert reg.get('logged_in_as_root') is True and reg['original_sim_sha256']==SHA
    assert reg['methods']==list(METHODS)
    assert reg['repeats_per_method']==5 and len(reg['raw_phases'])==6
    phases=[];rows=[]
    for i,method in enumerate(METHODS,1):
        p=path/f"phase_{i:02}_{method.replace('-','_')}.powermetrics.txt"
        q=path/f"phase_{i:02}_{method.replace('-','_')}.workload.json"
        w=json.loads(q.read_text())
        assert w['method']==method
        if method!='IDLE':
            assert w['source_sha256']==SHA and w['cases']==100
            assert w['seeds']==list(range(10301,10311)) and w['scenarios']==['S1','S5']
            assert w['whole_program_wall_seconds']>0 and w['controller_wall_seconds_sum']>0
        raw=p.read_text(errors='replace')
        head=HEADER.findall(raw);power=POWER.findall(raw)
        assert len(head)==len(power) and 35<=len(head)<=70,(i,len(head),len(power))
        samples=[]
        for (date,dt_ms),(value,unit) in zip(head,power):
            ts=datetime.datetime.strptime(date,'%a %b %d %H:%M:%S %Y %z')
            sec=float(dt_ms)/1000.
            watt=float(value)*(0.001 if unit.lower()=='mw' else 1)
            assert .7<sec<1.5 and 0<=watt<=25,(i,sec,watt)
            samples.append((ts,sec,watt))
        for a,b in zip(samples,samples[1:]):
            wall=(b[0]-a[0]).total_seconds()
            assert 0<=wall<=2.3,(i,wall)
        total_energy=sum(t*W for _,t,W in samples)
        total_elapsed=sum(t for _,t,_ in samples)
        duration=float(w['phase_s'])
        assert abs(total_elapsed-duration)<3.0,(i,duration,total_elapsed)
        record=dict(index=i,method=method,samples=len(samples),
                    sample_elapsed_s=total_elapsed,phase_elapsed_s=duration,
                    cpu_watt_timeweighted=sum(t*W for _,t,W in samples)/total_elapsed,
                    interval_integrated_apple_cpu_J=total_energy,
                    original_full_simulator_cases=(w.get('cases',0)),
                    real_workload_wall_seconds=w.get('whole_program_wall_seconds',0),
                    original_controller_wall_seconds=w.get('controller_wall_seconds_sum',0),
                    raw_power_sha256=hash_file(p),workload_sha256=hash_file(q),
                    first_sample_time=samples[0][0].isoformat(),
                    last_sample_time=samples[-1][0].isoformat(),
                    trace_sample_intervals_s=[t for _,t,_ in samples])
        phases.append(record)
    # Interpolate time-index baseline between both observed IDLE phases.
    idle_a=phases[0]['cpu_watt_timeweighted']
    idle_b=phases[-1]['cpu_watt_timeweighted']
    for p in phases:
        if p['method']=='IDLE':continue
        f=(p['index']-1)/5
        b=(1-f)*idle_a+f*idle_b
        # Following original collector: sampler runs 3s before worker.
        # Remove 3s from nominal duration; isolate inexact alignment.
        run_s=p['phase_elapsed_s']-3
        assert run_s>0
        p['interpolated_idle_W']=b
        p['approx_baseline_corrected_cpu_J']=(p['cpu_watt_timeweighted']-b)*run_s
        p['estimated_joules_per_full_simulation_case']=p['approx_baseline_corrected_cpu_J']/100
        p['conservative_idle_sensitivity_CPU_J']=[
            (p['cpu_watt_timeweighted']-max(idle_a,idle_b))*run_s,
            (p['cpu_watt_timeweighted']-min(idle_a,idle_b))*run_s]
    group={}
    for name in ('POINT-EA','ACR-MCR'):
        arr=[p for p in phases if p['method']==name]
        group[name]=dict(phases=2,cases_total=200,
             mean_subsystem_cpu_W=statistics.mean(p['cpu_watt_timeweighted'] for p in arr),
             mean_baseline_adjusted_cpu_J_per_100_cases=statistics.mean(
                 p['approx_baseline_corrected_cpu_J'] for p in arr),
             mean_estimated_cpu_J_per_simulator_case=statistics.mean(
                 p['estimated_joules_per_full_simulation_case'] for p in arr),
             raw_per_100case_estimates_J=[
                 p['approx_baseline_corrected_cpu_J'] for p in arr])
    diff=group['ACR-MCR']['mean_estimated_cpu_J_per_simulator_case']-group['POINT-EA']['mean_estimated_cpu_J_per_simulator_case']
    report=dict(status="PASS_6_ROOT_POWER_TRACES_WITH_EXPLICIT_SCIENTIFIC_LIMITS",
        original_sha256=SHA,method_sequence=list(METHODS),
        independent_trace_count=6,workload_cases_each_method=200,
        original_model_unchanged=True,measured_by="Apple powermetrics CPU subsystem sampler",
        sampled_while_euid_root=True,
        actual_electricity_meter_used=False,calibrated_wallplug_J=None,
        original_cpu_subsystem_power_is_estimated=True,
        per_process_optimizer_attribution=False,
        phase_results=phases,by_method=group,
        exploratory_difference_estimated_cpu_J_per_simulation_case=diff,
        limitation="Only two sequential blocks per method, aggregate CPU power includes all Mac processes and simulation overhead, phase boundaries approximate; do not infer confidence intervals, calibrated electrical Joules, physical host optimizer exclusive Joules, or hardware energy.")
    final=path/'independent_interval_power_verification.json'
    final.write_text(json.dumps(report,indent=2)+"\n")
    lines=[
        '# Root-authorized Apple M1 CPU-subsystem power: independent raw-interval audit','',
        'The owner-approved six-phase sample was independently checked against original',
        'powermetrics CPU power, sample elapsed milliseconds, source SHA256 and complete',
        '100-case workload files. Every stage met the registered order and trace-density',
        'requirements. These are **Apple-estimated CPU subsystem energies**, not',
        'independent calibrated electrical-energy measurements.','',
        '| Method | 100-case phase 1 (estimated baseline-adjusted J) | Phase 2 (J) | Mean per full simulator case (J) |',
        '|---|---:|---:|---:|']
    for name in ('POINT-EA','ACR-MCR'):
        q=group[name]
        lines.append(f"| {name} | {q['raw_per_100case_estimates_J'][0]:.3f} | {q['raw_per_100case_estimates_J'][1]:.3f} | {q['mean_estimated_cpu_J_per_simulator_case']:.4f} |")
    lines.extend(['',
       f"Exploratory ACR-MCR minus POINT-EA difference: {diff:+.4f} estimated CPU-subsystem J per full simulator case.",
       'This is *not* optimizer-exclusive energy, because each workload executes the',
       'complete Python simulator and all other Mac processes affect aggregate power.',
       'Both methods were measured only twice, in a nonrandomized order. Neither',
       'a calibrated physical electrical-energy measurement nor an inferential',
       'energy advantage/disadvantage can be established from these two blocks.',
       '',
       f"Original immutable model SHA256: \`{SHA}\`.",
       'The full six original unedited powermetrics traces, workload records and',
       'interval-level time verification are preserved with SHA256 manifest.',
       'Sampling was conducted with local root authorization rather than a',
       'Remote Desktop Commander privilege escalation. No more administrator',
       'permission is needed to preserve, inspect or recompute existing evidence.',
       ''])
    (path/'INDEPENDENT_CPU_POWER_REPORT.md').write_text('\n'.join(lines))
    manifest={p.name:hash_file(p) for p in sorted(path.iterdir())
              if p.is_file() and p.name!='independent_file_sha256.json'}
    (path/'independent_file_sha256.json').write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(dict(status=report['status'],samples=[p['samples'] for p in phases],
        point=group['POINT-EA']['mean_estimated_cpu_J_per_simulator_case'],
        acr=group['ACR-MCR']['mean_estimated_cpu_J_per_simulator_case'],
        delta=diff,files=len(manifest)),indent=2))
if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: python verify_power_independent.py <run-dir>')
    audit(sys.argv[1])
