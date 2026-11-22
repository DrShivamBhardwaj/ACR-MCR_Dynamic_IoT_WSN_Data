#!/usr/bin/env python3
"""Independent-from-published-summary replay of co-primary paired comparisons.

Source of truth: frozen original CSV and 40 original Cooja cell-level audits.
Never pool 30 original seeds with ten Cooja packet seeds as one sample.
"""
from pathlib import Path
import csv,hashlib,json,math,statistics
import numpy as np
from scipy.stats import ttest_1samp,t
ROOT=Path(__file__).resolve().parents[1]
HERE=Path(__file__).resolve().parent
SHA='3f134a8826525215f7cf2ff307bab3893c0d64b050f742bdc3c250b1c0302ea4'
assert hashlib.sha256((ROOT/'acr_mcr_v2.py').read_bytes()).hexdigest()==SHA
report=ROOT/'packet_validation/results/45009267734/full_40case_result.json'
original_csv=ROOT/'analysis/primary_effects.csv'
original=[row for row in csv.DictReader(original_csv.open())]
assert len(original)==2
orig={}
for item in original:
    assert item['contrast']=='ACR-MCR minus POINT-EA'
    assert int(item['n'])==30
    orig[item['metric']]={k:float(item[k]) for k in
                          ('difference','ci_low','ci_high','p','p_holm')}
assert set(orig)=={'timely_ratio','service_violation_rate'}
x=json.loads(report.read_text())
assert x['status']=='PASS' and x['registered_runs']==40
assert x['original_frozen_model_unmodified'] and x['independent_seed_blocks']==10
assert x['route_installed_only_by_radio'] and x['original_optimizer_feedback_from_cooja_MAC']
SEEDS=tuple(range(9201,9211));SCENARIOS=('S1','S5');METHODS=('POINT-EA','ACR-MCR')
expect={(sc,seed,m) for sc in SCENARIOS for seed in SEEDS for m in METHODS}
index={}
for r in x['all_run_audits']:
    key=(r['scenario'],r['seed'],r['method'])
    assert key in expect and key not in index,key
    assert r['verification']=='PASS' and r['nodes']==40 and r['rounds']==160
    assert r['nominal_demand']==6400 and r['payload_integrity_errors']==0
    assert r['complete_8_fragment_payload_verified']
    assert r['source_requests']>=r['valid_500byte_reassemblies']>=r['timely_500ms']
    assert r['control_receptions']<=r['control_reception_opportunities']==6400
    assert r['sensor_routes_received_as_actual_control_packets']
    assert r['controller_plans_through_sink_memory_only']
    index[key]=r
assert set(index)==expect
source_hashes={r['code_source_sha256'] for r in index.values()}
assert len(source_hashes)==1

primary={}
metric_map=(('PDR_nominal','full_500byte_PDR'),('timely_ratio_nominal','within_500ms'))
for key,nice in metric_map:
    differences=np.array([statistics.mean(
        index[(sc,seed,'ACR-MCR')][key]-index[(sc,seed,'POINT-EA')][key]
        for sc in SCENARIOS) for seed in SEEDS],float)
    mean=float(differences.mean())
    se=float(differences.std(ddof=1)/math.sqrt(len(differences)))
    margin=float(t.ppf(.975,len(differences)-1)*se)
    p=float(ttest_1samp(differences,0).pvalue)
    claimed=x['estimates'][key]
    for actual,stored in ((mean,claimed['estimated_acr_minus_point']),
                          (mean-margin,claimed['ci95'][0]),
                          (mean+margin,claimed['ci95'][1]),
                          (p,claimed['p_unadjusted'])):
        assert abs(actual-stored)<1e-11,(key,actual,stored)
    primary[key]=dict(
      label=nice,method_acr_minus_point=mean,
      ci95=[mean-margin,mean+margin],p_unadjusted=p,
      independent_seed_effects=differences.tolist(),
      independent_units=10)
ordered=sorted(primary,key=lambda k:primary[k]['p_unadjusted'])
running=0
for i,k in enumerate(ordered):
    running=max(running,min(1,(len(primary)-i)*primary[k]['p_unadjusted']))
    primary[k]['p_holm']=running
    assert abs(running-x['estimates'][k]['holm_adjusted_p'])<1e-11

descriptive={}
for k in ('control_receptions','controller_control_radio_packets',
          'data_fragment_radio_callbacks','total_MAC_callbacks'):
    bymethod={m:statistics.mean(r[k] for r in index.values() if r['method']==m)
              for m in METHODS}
    differences=np.array([statistics.mean(
        index[(sc,seed,'ACR-MCR')][k]-index[(sc,seed,'POINT-EA')][k]
        for sc in SCENARIOS) for seed in SEEDS])
    descriptive[k]=dict(by_method_means=bymethod,
        difference=float(differences.mean()),
        ci95_exploratory_unadjusted=[
           float(differences.mean()-t.ppf(.975,9)*differences.std(ddof=1)/math.sqrt(10)),
           float(differences.mean()+t.ppf(.975,9)*differences.std(ddof=1)/math.sqrt(10))])
result=dict(
  status='PASS_RECOMPUTED_FROM_ORIGINAL_40_CELL_CASES',
  original_source_sha256=SHA,
  original_30_seed_primary_records=orig,
  cooja_run_id=45009267734,
  packet_40_cell_source_sha256=next(iter(source_hashes)),
  independent_10_seed_packet_effects=primary,
  exploratory_packet_accounting=descriptive,
  distinct_units='Original 30 synthetic paired blocks vs new Cooja 10 independent seed blocks. Never combine.',
  publisher_venue='new submission research reconstruction, not formal Discover Networks revision',
  cannot_support=[
      'ACR-MCR service superiority over POINT-EA',
      'full embedded physical adaptive controller performance',
      'equivalence of methods from nonsignificant p',
      'causal link between conformal uncertainty and physical 500ms deadline',
      'calibrated wall-plug or on-M3 total sensor network energy'])
HERE.mkdir(exist_ok=True,parents=True)
out=HERE/'RECOMPUTED_PRIMARY_COMPARISONS_20261122.json'
out.write_text(json.dumps(result,indent=2)+'\n')
print('REPLAY_PASS',json.dumps({k:{
    'effect_pp':round(v['method_acr_minus_point']*100,5),
    'ci_pp':[round(a*100,5) for a in v['ci95']],
    'holm_p':v['p_holm']} for k,v in primary.items()},indent=2))
for k,v in descriptive.items():print('DESCRIPTIVE',k,v['difference'],v['ci95_exploratory_unadjusted'])
