#include "acr_optimizer_core.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <float.h>
#define POSINF HUGE_VAL
#define LINK(s,u,v,a) ((s)->a[(u)*((s)->n+1)+(v)])
static double real_max(double a,double b) { return a>b?a:b; }
static void sort_int(int *a,int n) {
  int i,j,x;
  for(i=1;i<n;i++) { x=a[i];j=i-1;
    while(j>=0 && a[j]>x){a[j+1]=a[j];j--;}
    a[j+1]=x;
  }
}
static int compare_double_desc(const void *a,const void *b) {
  double x=*(const double*)a,y=*(const double*)b;
  return (x<y)-(x>y);
}
static double radio_tx(double dist,double bits) {
  const double ee=50e-9,efs=10e-12,emp=.0013e-12;
  double d0=sqrt(efs/emp);
  return bits*(ee+(dist<d0 ? efs*dist*dist : emp*pow(dist,4.)));
}
int acr_make_plan(const ACR_OptContext *s,const int *h,int k,
                  ACR_OptPlan *out) {
  double dj[ACR_MAX_HEADS+1][ACR_MAX_HEADS+1];
  int nx[ACR_MAX_HEADS+1][ACR_MAX_HEADS+1];
  int nodes[ACR_MAX_HEADS+1];
  int i,j,z,a,n,ns;
  if(!s || !out || s->n<1 || s->n>ACR_N || k<0 || k>ACR_MAX_HEADS)
    return -1;
  memset(out,0,sizeof(*out));
  n=s->n;
  for(i=0;i<n;i++){out->assigned[i]=-1;out->costs[i]=POSINF;}
  if(k==0){out->objective=1e6;return 0;}
  for(i=0;i<k;i++) {
    if(h[i]<0 || h[i]>=n) return -2;
    out->heads[i]=h[i];
  }
  sort_int(out->heads,k);
  ns=0;
  for(i=0;i<k;i++)
    if(!ns || out->heads[i]!=out->heads[ns-1])
      out->heads[ns++]=out->heads[i];
  k=ns;out->nheads=k;
  for(i=0;i<k;i++)nodes[i]=out->heads[i];
  nodes[k]=n;
  for(i=0;i<=k;i++)
    for(j=0;j<=k;j++) {
      dj[i][j]=POSINF;
      nx[i][j]=j;
    }
  for(i=0;i<k;i++)
    for(j=0;j<=k;j++)
      dj[i][j]=LINK(s,nodes[i],nodes[j],edge_cost);
  for(i=0;i<=k;i++)dj[i][i]=0.;
  for(z=0;z<=k;z++) {
    /* Original numpy expression updates each z simultaneously.
       With positive edge costs, in-place Floyd-Warshall is equivalent. */
    for(i=0;i<=k;i++)
      for(j=0;j<=k;j++) {
        double trial=dj[i][z]+dj[z][j];
        if(trial<dj[i][j]) {dj[i][j]=trial;nx[i][j]=nx[i][z];}
      }
  }
  for(a=0;a<k;a++) {
    int cur=a,len=0;
    if(!isfinite(dj[a][k]))continue;
    out->paths[a][len++]=nodes[a];
    for(i=0;i<=k;i++){
      cur=nx[cur][k];
      if(cur<0 || cur>k || len>=ACR_MAX_PATH)break;
      out->paths[a][len++]=nodes[cur];
      if(cur==k){out->path_len[a]=len;break;}
    }
  }
  for(i=0;i<n;i++) {
    double best=POSINF;
    int selected=-1;
    for(a=0;a<k;a++) {
      double cost=LINK(s,i,out->heads[a],edge_cost)+.30*dj[a][k];
      if(i==out->heads[a])
        cost=.30*dj[a][k];
      /* Python np.argmin resolves exact ties by smallest head index. */
      if(cost<best) {best=cost;selected=a;}
    }
    out->costs[i]=best;
    if(isfinite(best) && s->active[i] && selected>=0)
      out->assigned[i]=out->heads[selected];
  }
  return 0;
}
double acr_fitness(const ACR_OptContext *s,ACR_OptPlan *p) {
  int n=s->n,a,i,j,si,active_n=0,unserved=0;
  double depletion[ACR_N]={0};
  double mean_delay=0.,mean_route=0.;
  int count_delay=0,count_route=0;
  uint8_t losses[ACR_TAIL_MAX][ACR_N];
  double tail_means[ACR_TAIL_MAX];
  double sum_e=0.,mean_post=0.,var_post=0.,peak=0.,cv;
  double score,delay,route;
  if(s->has_risk &&
     (!s->stress || s->stress_samples<1 || s->stress_samples>ACR_TAIL_MAX))
    return p->objective=NAN;
  for(i=0;i<n;i++)
    if(s->active[i]){active_n++;if(p->assigned[i]<0)unserved++;}
  if(s->has_risk)memset(losses,1,sizeof(losses));
  for(a=0;a<p->nheads;a++) {
    int head=p->heads[a],members=0;
    double sum_attempts=0.,sum_ack=0.,collect=2.,rd=0.,rc=0.;
    if(!p->path_len[a])continue;
    for(i=0;i<n;i++) {
      if(p->assigned[i]!=head)continue;
      members++;
      if(i==head)continue;
      {
        double at=LINK(s,i,head,attempt_mean);
        sum_attempts+=at;
        sum_ack+=radio_tx(LINK(s,i,head,distance),64);
        depletion[i]+=s->load*(LINK(s,i,head,tx_energy)*at+64*50e-9);
      }
      collect+=LINK(s,i,head,d_used)*s->load;
    }
    depletion[head]+=s->load*(4000*50e-9*sum_attempts+sum_ack);
    depletion[head]+=members*s->load*4000*5e-9;
    for(j=0;j<p->path_len[a]-1;j++) {
      int u=p->paths[a][j],v=p->paths[a][j+1];
      double at=LINK(s,u,v,attempt_mean);
      depletion[u]+=LINK(s,u,v,tx_energy)*at+64*50e-9;
      if(v<n)
        depletion[v]+=4000*50e-9*at+radio_tx(LINK(s,u,v,distance),64);
      rd+=LINK(s,u,v,d_used);
      rc+=LINK(s,u,v,edge_cost);
    }
    mean_delay+=(collect+rd)*members;count_delay+=members;
    mean_route+=rc*members;count_route+=members;
    if(s->has_risk) {
      for(si=0;si<s->stress_samples;si++) {
        double stress_collection=2.,path_duration=0.;
        int path_ok=1,timely;
        for(i=0;i<n;i++)if(p->assigned[i]==head && i!=head) {
          double cost_dummy,dd;
          s->stress(s->stress_user,si,(unsigned)i,(unsigned)head,
                    &cost_dummy,&dd);
          stress_collection+=dd*s->load;
        }
        for(j=0;j<p->path_len[a]-1;j++) {
          int u=p->paths[a][j],v=p->paths[a][j+1];
          double cc,dd;
          s->stress(s->stress_user,si,(unsigned)u,(unsigned)v,&cc,&dd);
          path_duration+=dd;
          if(!(cc<4.5))path_ok=0;
        }
        timely=path_ok && (stress_collection+path_duration<=s->deadline_ms);
        losses[si][head]=timely?0:1;
        for(i=0;i<n;i++)if(p->assigned[i]==head && i!=head) {
          double cc,dd_dummy;
          s->stress(s->stress_user,si,(unsigned)i,(unsigned)head,
                    &cc,&dd_dummy);
          losses[si][i]=(uint8_t)(!(timely && cc<4.5));
        }
      }
    }
  }
  for(i=0;i<n;i++)if(s->active[i]){
    double post=real_max(0.,s->energy[i]-depletion[i]);
    mean_post+=post;sum_e+=depletion[i];
    {
      double ratio=depletion[i]/real_max(s->energy[i],.03);
      if(ratio>peak)peak=ratio;
    }
  }
  /* Python: depletion.sum() includes inactive nodes, too. */
  sum_e=0;
  for(i=0;i<n;i++)sum_e+=depletion[i];
  if(active_n>0)mean_post/=active_n;
  for(i=0;i<n;i++)if(s->active[i]){
    double post=real_max(0.,s->energy[i]-depletion[i]);
    var_post+=(post-mean_post)*(post-mean_post);
  }
  if(active_n>0)var_post/=active_n;
  cv=sqrt(var_post)/real_max(1e-8,mean_post);
  delay=count_delay?mean_delay/count_delay/s->deadline_ms:2.;
  route=count_route?mean_route/count_route/10.:5.;
  score=.32*sum_e/(.001*(active_n?active_n:1)) +
      .24*delay+.20*route+.12*cv+.12*peak+
      10.*unserved/(double)(active_n?active_n:1);
  if(s->has_risk) {
    unsigned n_s=(unsigned)s->stress_samples;
    double mass=n_s*(1.-s->tail_beta),total=0.;
    unsigned whole;double fraction;
    if(mass<=0.)return p->objective=NAN;
    for(si=0;si<s->stress_samples;si++) {
      double loss=0;
      for(i=0;i<n;i++)if(s->active[i])loss+=losses[si][i];
      tail_means[si]=loss/(active_n?active_n:1);
    }
    qsort(tail_means,n_s,sizeof(double),compare_double_desc);
    whole=(unsigned)floor(mass+1e-12);
    fraction=mass-whole;
    for(si=0;si<(int)whole;si++)total+=tail_means[si];
    if(fraction>1e-12 && whole<n_s)total+=fraction*tail_means[whole];
    score+=s->tail_weight*total/mass;
  }
  return p->objective=score;
}
static int compare_plans(const void *a,const void *b) {
  const ACR_OptPlan *x=a,*y=b;
  int i;
  if(x->objective<y->objective)return -1;
  if(x->objective>y->objective)return 1;
  for(i=0;i<x->nheads && i<y->nheads;i++) {
    if(x->heads[i]<y->heads[i])return -1;
    if(x->heads[i]>y->heads[i])return 1;
  }
  return (x->nheads>y->nheads)-(x->nheads<y->nheads);
}
int acr_select_trace(const ACR_OptContext *s,const ACR_SearchTrace *trace,
                     ACR_OptPlan *result) {
  ACR_OptPlan plans[ACR_POP],next[ACR_POP];
  int a,g,at=0;
  if(!s || !trace || !result ||
     trace->nheads<1 || trace->nheads>ACR_MAX_HEADS)return -1;
  for(a=0;a<ACR_POP;a++){
    if(acr_make_plan(s,trace->heads[at++],trace->nheads,&plans[a]))return -2;
    if(!isfinite(acr_fitness(s,&plans[a])))return -3;
  }
  for(g=0;g<ACR_GENERATIONS;g++) {
    qsort(plans,ACR_POP,sizeof(ACR_OptPlan),compare_plans);
    next[0]=plans[0];next[1]=plans[1];
    for(a=2;a<ACR_POP;a++){
      if(acr_make_plan(s,trace->heads[at++],trace->nheads,&next[a]))
        return -4;
      if(!isfinite(acr_fitness(s,&next[a])))return -5;
    }
    memcpy(plans,next,sizeof(plans));
  }
  qsort(plans,ACR_POP,sizeof(ACR_OptPlan),compare_plans);
  *result=plans[0];
  return at==ACR_CANDIDATES?0:-6;
}
