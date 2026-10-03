"""Publication figures generated exclusively from the archived study outputs."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon
from scipy.stats import t as student_t
from acr_mcr_v2 import METHODS
from figure_text import CAPTIONS, EXPLANATIONS

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Nimbus Sans','DejaVu Sans'],
    'font.size':10,'axes.labelsize':10,'xtick.labelsize':9,'ytick.labelsize':9,
    'legend.fontsize':9,'axes.spines.top':False,'axes.spines.right':False,
    'axes.edgecolor':'#697580','axes.linewidth':.7,'grid.color':'#DDE3E8',
    'grid.linewidth':.5,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none'})
BLUE='#174A70';TEAL='#007A72';ORANGE='#A94716';GRAY='#606B75';PURPLE='#6A4C93'
raw=pd.read_csv(ROOT/'results/raw_results.csv')
summary=pd.read_csv(ROOT/'analysis/method_summary.csv')
scenario=pd.read_csv(ROOT/'analysis/scenario_effects.csv')
staged=pd.read_csv(ROOT/'analysis/staged_effects.csv')
rounds=pd.read_csv(ROOT/'analysis/main_rounds.csv.gz')
manifest=[]

def save(fig,n,caption=None):
    stem=f'Fig{n}'
    for ext in ['png','svg','eps']:
        fig.savefig(OUT/f'{stem}.{ext}',dpi=600,facecolor='white',bbox_inches='tight',pad_inches=.06)
    manifest.append(dict(number=n,file=f'{stem}.png',caption=CAPTIONS[n],explanation=EXPLANATIONS[n],dpi=600,source='Python source and archived raw outputs'))
    plt.close(fig)

# Editable schematics share the standalone figure generator.
from diagram_figures import diagram1, diagram2, CAPTIONS
save(diagram1(), 1, CAPTIONS[1])
save(diagram2(), 2, CAPTIONS[2])

# 3. Paired scenario effects for the two prespecified outcomes.
fig,axs=plt.subplots(1,2,figsize=(6.8,3.6),sharey=True)
labels=['S1  Gradual','S2  Burst','S3  Load','S4  Failure','S5  Combined']
for ax,metric,color,label in zip(axs,['timely_ratio','service_violation_rate'],[TEAL,BLUE],
    ['(a) Timely delivery change (pp)','(b) Violation-rate change (pp)']):
    d=scenario[scenario.metric==metric].sort_values('scenario')
    y=np.arange(len(d))
    ax.errorbar(100*d.difference,y,xerr=np.vstack([100*(d.difference-d.ci_low),100*(d.ci_high-d.difference)]),
                fmt='o',color=color,capsize=3,markersize=5,linewidth=1.3)
    ax.axvline(0,color=GRAY,lw=.8,ls='--');ax.set_xlabel(label);ax.grid(axis='x');ax.set_yticks(y,labels)
    ax.set_xlim(-3.5,3.5)
axs[0].invert_yaxis();fig.tight_layout(w_pad=2)
save(fig,3)

# 4. Component attribution under a fixed objective and search budget.
fig,axs=plt.subplots(1,2,figsize=(6.8,3.8),sharey=True)
order=['FROZEN-CP minus POINT-EA','ROLL-CP minus FROZEN-CP','ACI-PER minus ROLL-CP','ACI-EVENT minus ACI-PER','ACR-MCR minus ACI-EVENT']
labels=['Frozen − point','Rolling − frozen','Adaptive − rolling','Event − periodic','Tail − no tail']
for ax,metric,color,label in zip(axs,['timely_ratio','service_violation_rate'],[TEAL,BLUE],
    ['(a) Timely delivery change (pp)','(b) Violation-rate change (pp)']):
    d=staged[staged.metric==metric].set_index('contrast').loc[order]
    y=np.arange(5)
    ax.errorbar(100*d.difference,y,xerr=np.vstack([100*(d.difference-d.ci_low),100*(d.ci_high-d.difference)]),fmt='s',color=color,capsize=3,markersize=4)
    ax.axvline(0,color=GRAY,lw=.8,ls='--');ax.set_xlabel(label);ax.grid(axis='x');ax.set_yticks(y,labels);ax.set_xlim(-2.8,2)
axs[0].invert_yaxis();fig.tight_layout(w_pad=2)
save(fig,4)

# 5. Issued-bound coverage: aggregate numerators within non-overlapping bins.
fig,axs=plt.subplots(2,2,figsize=(6.8,4.8),sharex=True,sharey=True)
subset=rounds[rounds.scenario=='S5'].copy();subset['bin']=(subset['round']-1)//10
styles=[('FROZEN-CP',ORANGE,'--'),('ROLL-CP',GRAY,':'),('ACR-MCR',TEAL,'-')]
for ax,(kind,metric,label) in zip(axs.flat,[('probe','cost','(a) Probe transaction cost'),('data','cost','(b) Routed transaction cost'),('probe','delay','(c) Probe service time'),('data','delay','(d) Routed service time')]):
    for method,color,ls in styles:
        g=subset[subset.method==method].groupby(['seed','bin'])[[f'{kind}_{metric}_covered',f'{kind}_n']].sum()
        cov=(g[f'{kind}_{metric}_covered']/g[f'{kind}_n']).unstack('seed')
        mean=cov.mean(axis=1);se=cov.std(axis=1)/np.sqrt(cov.count(axis=1));ci=student_t.ppf(.975,29)*se
        x=10*mean.index.to_numpy()+5.5
        ax.plot(x,mean,color=color,ls=ls,lw=1.5,label=method)
        if method=='ACR-MCR':ax.fill_between(x,mean-ci,mean+ci,color='#D4ECE7',zorder=0)
    ax.axhline(.90,color='black',lw=.7,ls='--');ax.axvline(20.5,color=GRAY,lw=.6)
    ax.set_ylim(.58,1.02);ax.set_xlim(1,160);ax.set_title(label,loc='left',fontsize=9,pad=7)
    ax.grid(axis='y');ax.set_ylabel('Empirical coverage')
for ax in axs[1]:ax.set_xlabel('Round')
handles,labels=axs[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=3,bbox_to_anchor=(.5,-.02),frameon=False)
fig.tight_layout(rect=[0,.055,1,1],h_pad=1)
save(fig,5)

# 6. Energy accounting with uncertainty on total radio expenditure.
fig,ax=plt.subplots(figsize=(6.8,3.6));methods=list(METHODS)
y=np.arange(len(methods));left=np.zeros(len(methods))
for metric,label,color,hatch in [('energy_data_J','Data and ACKs',BLUE,''),('energy_probe_J','Probes and ACKs',TEAL,'//'),('energy_control_J','Local control',ORANGE,''),('energy_aggregation_J','Aggregation',GRAY,'..')]:
    values=summary[summary.metric==metric].set_index('method').loc[methods,'mean'].to_numpy()
    ax.barh(y,values,left=left,color=color,label=label,height=.66,hatch=hatch,edgecolor='white',linewidth=.4);left+=values
d=summary[summary.metric=='radio_energy_J'].set_index('method').loc[methods]
ax.errorbar(d['mean'],y,xerr=np.vstack([d['mean']-d.low,d.high-d['mean']]),fmt='none',ecolor='black',capsize=3,linewidth=.8)
ax.set_yticks(y,methods);ax.invert_yaxis();ax.set_xlabel('Total modelled radio expenditure over 160 rounds (J)');ax.set_xlim(0,13)
ax.grid(axis='x');ax.set_axisbelow(True);ax.legend(loc='upper center',bbox_to_anchor=(.50,-.16),ncol=2,frameon=False)
fig.tight_layout(rect=[0,.08,1,1])
save(fig,6)

# 7. Density and isolated decision-stage timing.
fig,axs=plt.subplots(1,2,figsize=(6.8,3.45))
timing=pd.read_csv(ROOT/'analysis/timing_profile.csv')
for method,color,marker in [('POINT-EA',BLUE,'o'),('ACR-MCR',TEAL,'s')]:
    for ax,kind in zip(axs,['delivery','timing']):
        means=[];cis=[]
        for n in [40,80,120]:
            if kind=='timing':x=timing[(timing.method==method)&(timing.nodes==n)].decision_stage_ms_per_round
            else:x=raw[(raw.method==method)&(raw.scenario=='S5')&(raw.nodes==n)&(raw.group==('main' if n==40 else 'scale'))].timely_ratio
            means.append(x.mean());cis.append(student_t.ppf(.975,len(x)-1)*x.std()/np.sqrt(len(x)))
        ax.errorbar([40,80,120],means,yerr=cis,color=color,marker=marker,ls='--' if method=='POINT-EA' else '-',capsize=3,label=method)
        ax.set_xticks([40,80,120]);ax.set_xlabel('Sensor count');ax.grid(axis='y')
axs[0].set_ylabel('(a) Timely delivery ratio');axs[0].set_ylim(0,.36)
axs[1].set_ylabel('(b) Decision time per round (ms)');axs[1].set_ylim(0,8)
axs[0].legend(frameon=False,loc='lower left');fig.tight_layout(w_pad=1.5)
save(fig,7)

# 8. Probe-budget trade-off and head-count diagnostic.
fig,axs=plt.subplots(1,2,figsize=(6.8,3.45))
for method,color,marker in [('POINT-EA',BLUE,'o'),('ACR-MCR',TEAL,'s')]:
    for ax,group,var,values,label in [(axs[0],'probes','probes',[0,1,2],'(a) Probes per source per round'),(axs[1],'heads','fixed_heads',[4,5,6],'(b) Fixed head count at 60 nodes')]:
        means=[];cis=[]
        for value in values:
            x=raw[(raw.group==group)&(raw.method==method)&(raw[var]==value)].timely_ratio
            means.append(x.mean());cis.append(student_t.ppf(.975,len(x)-1)*x.std()/np.sqrt(len(x)))
        ax.errorbar(values,means,yerr=cis,color=color,marker=marker,capsize=3,ls='--' if method=='POINT-EA' else '-',label=method)
        ax.set_xticks(values);ax.set_xlabel(label);ax.set_ylabel('Timely delivery ratio');ax.set_ylim(0,.38);ax.grid(axis='y')
axs[0].legend(frameon=False,loc='lower left');fig.tight_layout(w_pad=1.5)
save(fig,8)

(OUT/'figure_manifest.json').write_text(json.dumps(manifest,indent=2))
print('Wrote eight figures as 600 dpi PNG, SVG and EPS.')
