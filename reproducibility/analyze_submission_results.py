from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats

ROOT=Path(__file__).parent
OUT=ROOT/'results_submission'; OUT.mkdir(exist_ok=True)
df=pd.read_csv(OUT/'raw_20seed.csv')
metrics=['PDR','risk_violation_rate','mean_delay','energy_consumed','optimizer_calls','etx_coverage','delay_coverage']

# Descriptive summary with 95% t CIs
rows=[]
for (sc,m),g in df.groupby(['scenario','method']):
    for metric in metrics:
        x=g[metric].dropna().to_numpy(float)
        if not len(x): continue
        mean=x.mean(); sd=x.std(ddof=1) if len(x)>1 else 0.0
        se=sd/np.sqrt(len(x)) if len(x)>1 else 0.0
        tcrit=stats.t.ppf(.975,len(x)-1) if len(x)>1 else np.nan
        rows.append(dict(scenario=sc,method=m,metric=metric,n=len(x),mean=mean,sd=sd,ci95_low=mean-tcrit*se if len(x)>1 else mean,ci95_high=mean+tcrit*se if len(x)>1 else mean))
summary=pd.DataFrame(rows); summary.to_csv(OUT/'summary_long_20seed.csv',index=False)

# dynamic aggregate per seed (scenario-average first)
agg=df.groupby(['seed','method'],as_index=False).agg({m:'mean' for m in metrics})
agg.to_csv(OUT/'dynamic_seed_aggregate_20seed.csv',index=False)

def paired_stats(a,b):
    d=b-a; n=len(d)
    md=d.mean(); sd=d.std(ddof=1) if n>1 else 0
    se=sd/np.sqrt(n) if n>1 else 0
    tcrit=stats.t.ppf(.975,n-1) if n>1 else np.nan
    try:
        w=stats.wilcoxon(d,alternative='two-sided',zero_method='wilcox',method='auto')
        p=float(w.pvalue)
    except Exception:
        p=1.0
    dz=md/sd if sd>0 else np.nan
    return md, md-tcrit*se, md+tcrit*se, p, dz

comparators=['POINT-EA','SCP-EA','ACP-EA','ACR-NOCVAR']
statrows=[]
for comp in comparators:
  for sc in ['S1','S2','S3','S4','S5','ALL_DYNAMIC']:
    source=agg if sc=='ALL_DYNAMIC' else df[df.scenario==sc]
    for metric in ['PDR','risk_violation_rate','mean_delay','energy_consumed','optimizer_calls']:
        piv=source.pivot(index='seed',columns='method',values=metric).dropna(subset=[comp,'ACR-MCR'])
        a=piv[comp].to_numpy(float); b=piv['ACR-MCR'].to_numpy(float)
        md,lo,hi,p,dz=paired_stats(a,b)
        statrows.append(dict(comparator=comp,scenario=sc,metric=metric,n=len(a),comparator_mean=a.mean(),acr_mean=b.mean(),paired_delta_acr_minus_comparator=md,ci95_low=lo,ci95_high=hi,wilcoxon_p=p,cohen_dz=dz))
statsdf=pd.DataFrame(statrows)
# Exploratory Holm correction within each comparator+metric across the six scenario scopes.
# This is retained only as a secondary/exploratory diagnostic and is NOT the manuscript's
# prespecified primary multiplicity family.
statsdf['exploratory_holm_across_scenarios']=np.nan
for (comp,metric),ix in statsdf.groupby(['comparator','metric']).groups.items():
    idx=list(ix); pvals=statsdf.loc[idx,'wilcoxon_p'].to_numpy()
    order=np.argsort(pvals); m=len(pvals); adj=np.empty(m)
    running=0.0
    for rank,pos in enumerate(order):
        val=(m-rank)*pvals[pos]
        running=max(running,val)
        adj[pos]=min(1.0,running)
    statsdf.loc[idx,'exploratory_holm_across_scenarios']=adj

# Prespecified primary multiplicity family used in the manuscript:
# ACR-MCR vs POINT-EA on ALL_DYNAMIC for the two co-primary endpoints only
# (PDR and operational risk-violation rate). Other hypothesis tests are exploratory.
statsdf['primary_holm_p']=np.nan
primary_mask=(statsdf['comparator'].eq('POINT-EA') & statsdf['scenario'].eq('ALL_DYNAMIC') &
              statsdf['metric'].isin(['PDR','risk_violation_rate']))
idx=list(statsdf.index[primary_mask])
pvals=statsdf.loc[idx,'wilcoxon_p'].to_numpy(float)
order=np.argsort(pvals); m=len(pvals); adj=np.empty(m)
running=0.0
for rank,pos in enumerate(order):
    val=(m-rank)*pvals[pos]
    running=max(running,val)
    adj[pos]=min(1.0,running)
statsdf.loc[idx,'primary_holm_p']=adj
statsdf.to_csv(OUT/'paired_stats_20seed.csv',index=False)

# Coverage calibration summary, target .90
cov=[]
for (sc,m),g in df[df.method.isin(['SCP-EA','ACP-EA','ACR-NOCVAR','ACR-MCR'])].groupby(['scenario','method']):
    for metric in ['etx_coverage','delay_coverage']:
        x=g[metric].dropna().to_numpy(float)
        cov.append(dict(scenario=sc,method=m,metric=metric,mean=x.mean(),mae_to_090=np.mean(np.abs(x-.90)),bias=x.mean()-.90))
pd.DataFrame(cov).to_csv(OUT/'coverage_calibration_20seed.csv',index=False)

# compact tables printed
print('\nDYNAMIC AGGREGATE MEANS (scenario-averaged within seed):')
print(agg.groupby('method')[['PDR','risk_violation_rate','mean_delay','energy_consumed','optimizer_calls','etx_coverage','delay_coverage']].mean().round(5).to_string())
print('\nACR-MCR vs comparators, ALL_DYNAMIC:')
print(statsdf[statsdf.scenario=='ALL_DYNAMIC'][['comparator','metric','comparator_mean','acr_mean','paired_delta_acr_minus_comparator','ci95_low','ci95_high','wilcoxon_p','primary_holm_p','exploratory_holm_across_scenarios','cohen_dz']].round(6).to_string(index=False))
print('\nACR-MCR vs ACR-NOCVAR by scenario:')
print(statsdf[(statsdf.comparator=='ACR-NOCVAR') & (statsdf.metric.isin(['PDR','risk_violation_rate']))][['scenario','metric','comparator_mean','acr_mean','paired_delta_acr_minus_comparator','ci95_low','ci95_high','wilcoxon_p','primary_holm_p','exploratory_holm_across_scenarios','cohen_dz']].round(6).to_string(index=False))
