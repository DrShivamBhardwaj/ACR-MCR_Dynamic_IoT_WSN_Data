"""Prespecified paired analyses; all main outcomes retained."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
from scipy.stats import t as student_t
from acr_mcr_v2 import METHODS

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis'

def interval(x):
    x=np.asarray(x,float);x=x[np.isfinite(x)]
    mean=float(np.mean(x));se=float(np.std(x,ddof=1)/np.sqrt(len(x))) if len(x)>1 else 0
    width=float(student_t.ppf(.975,len(x)-1)*se) if len(x)>1 else 0
    return dict(n=len(x),mean=mean,low=mean-width,high=mean+width)

def holm(values):
    order=np.argsort(values);out=np.empty(len(values));running=0
    for rank,k in enumerate(order):
        running=max(running,min(1.,(len(values)-rank)*values[k]));out[k]=running
    return out

def pair(a,b,metric,signs):
    joined=a[[metric]].join(b[[metric]],lsuffix='_a',rsuffix='_b',how='inner')
    d=(joined[f'{metric}_a']-joined[f'{metric}_b']).to_numpy()
    v=interval(d)
    null=np.abs(signs[:,:len(d)]@d/len(d))
    p=(1+int(np.sum(null>=abs(v['mean'])-1e-15)))/(len(null)+1)
    return dict(metric=metric,a_mean=float(joined[f'{metric}_a'].mean()),b_mean=float(joined[f'{metric}_b'].mean()),
                difference=v['mean'],ci_low=v['low'],ci_high=v['high'],n=v['n'],p=p)

def main():
    OUT.mkdir(exist_ok=True)
    raw=pd.read_csv(ROOT/'results/raw_results.csv')
    assert len(raw)==1280 and raw.run_id.nunique()==1280
    main=raw[raw.group=='main']
    assert len(main)==1050
    assert main.groupby(['method','scenario']).size().eq(30).all()
    metrics=['PDR','timely_ratio','service_violation_rate','conditional_delay_ms','radio_energy_J',
        'energy_data_J','energy_probe_J','energy_control_J','energy_aggregation_J','energy_per_delivered_mJ',
        'probe_cost_coverage','probe_delay_coverage','data_cost_coverage','data_delay_coverage',
        'final_alive','searches','accepted_changes','trigger_coverage','trigger_failure']
    blocks=main.groupby(['method','seed'])[metrics].mean()
    summary=[]
    for method in METHODS:
        for metric in metrics:
            summary.append(dict(method=method,metric=metric,**interval(blocks.loc[method,metric])))
    pd.DataFrame(summary).to_csv(OUT/'method_summary.csv',index=False)
    signs=np.random.default_rng(260921).choice(np.array([-1,1],dtype=np.int8),(100000,30))
    primary=[]
    for metric in ['timely_ratio','service_violation_rate']:
        primary.append(dict(contrast='ACR-MCR minus POINT-EA',**pair(blocks.loc['ACR-MCR'],blocks.loc['POINT-EA'],metric,signs)))
    adj=holm([x['p'] for x in primary])
    for row,p in zip(primary,adj):row['p_holm']=float(p)
    pd.DataFrame(primary).to_csv(OUT/'primary_effects.csv',index=False)
    chain=['POINT-EA','FROZEN-CP','ROLL-CP','ACI-PER','ACI-EVENT','ACR-MCR']
    staged=[]
    for b,a in zip(chain[:-1],chain[1:]):
        for metric in ['timely_ratio','service_violation_rate']:
            staged.append(dict(contrast=f'{a} minus {b}',**pair(blocks.loc[a],blocks.loc[b],metric,signs)))
    adj=holm([x['p'] for x in staged])
    for row,p in zip(staged,adj):row['p_holm']=float(p)
    pd.DataFrame(staged).to_csv(OUT/'staged_effects.csv',index=False)
    sc=[]
    for scenario,g in main.groupby('scenario'):
        for metric in ['PDR','timely_ratio','service_violation_rate','radio_energy_J']:
            a=g[g.method=='ACR-MCR'].set_index('seed');b=g[g.method=='POINT-EA'].set_index('seed')
            sc.append(dict(scenario=scenario,**pair(a,b,metric,signs)))
    pd.DataFrame(sc).to_csv(OUT/'scenario_effects.csv',index=False)
    sensitivity=[]
    for group,g in raw[raw.group!='main'].groupby('group'):
        for (n,probes,k,method),h in g.groupby(['nodes','probes','fixed_heads','method']):
            for metric in metrics:
                if h[metric].notna().any():
                    sensitivity.append(dict(group=group,nodes=n,probes=probes,fixed_heads=k,method=method,metric=metric,**interval(h[metric])))
    pd.DataFrame(sensitivity).to_csv(OUT/'sensitivity_summary.csv',index=False)
    all_rounds=[]
    env={}
    for _,run in main.iterrows():
        rounds=pd.read_csv(ROOT/'results/rounds'/f'{run.run_id}.csv.gz')
        assert len(rounds)==160
        key=(run.seed,run.scenario)
        fields=tuple(rounds.env_fingerprint)
        if key in env:assert fields==env[key],key
        else:env[key]=fields
        rounds['seed']=run.seed;rounds['method']=run.method;rounds['scenario']=run.scenario
        all_rounds.append(rounds)
    rd=pd.concat(all_rounds,ignore_index=True)
    rd.to_csv(OUT/'main_rounds.csv.gz',index=False,compression='gzip')
    # Pool within each seed, then summarize across independent seeds.
    phase=[]
    for (method,scenario,seed),g in rd.groupby(['method','scenario','seed']):
        for label,lo,hi in [('warmup',1,20),('early',21,55),('middle',56,100),('late',101,160)]:
            h=g[g['round'].between(lo,hi)]
            for kind in ['probe','data']:
                for metric in ['cost','delay']:
                    num=h[f'{kind}_{metric}_covered'].sum();den=h[f'{kind}_n'].sum()
                    phase.append(dict(method=method,scenario=scenario,seed=seed,phase=label,kind=kind,metric=metric,
                                      coverage=num/den if den else np.nan,count=int(den)))
    pd.DataFrame(phase).to_csv(OUT/'phase_coverage.csv',index=False)
    manifest=json.loads((ROOT/'results/manifest.json').read_text())
    for name in ['acr_mcr_v2.py','run_study.py','PROTOCOL.md']:
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==manifest['source_sha256'][name]
    checks=dict(total_runs=len(raw),primary_runs=len(main),primary_seed_blocks=30,
                main_round_records=len(rd),common_environment_fields_verified=True,locked_source_hashes_verified=True,
                groups=raw.groupby('group').size().to_dict())
    (OUT/'analysis_verification.json').write_text(json.dumps(checks,indent=2))
    print('VERIFICATION',json.dumps(checks))
    print('PRIMARY',json.dumps(primary))
    print('STAGED',json.dumps(staged))
    print(pd.DataFrame(summary).pivot(index='method',columns='metric',values='mean').round(5).to_string())

if __name__=='__main__':main()
