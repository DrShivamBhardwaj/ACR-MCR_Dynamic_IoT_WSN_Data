#include "aci_calibrator.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>
static int compare_double(const void *a,const void *b) {
  double x=*(const double *)a,y=*(const double *)b;
  return (x>y)-(x<y);
}
static double clamp(double x,double lo,double hi) {
  return x<lo?lo:(x>hi?hi:x);
}
void acr_aci_init(ACR_ACI *s,unsigned mode) {
  memset(s,0,sizeof(*s));
  s->mode=mode;
  s->alpha[0]=s->alpha[1]=0.10;
  s->q[0]=s->q[1]=1.28;
}
void acr_aci_update(ACR_ACI *s,const double *scores,
                    const uint8_t *covered,unsigned rows,unsigned round) {
  double fractions[2]={0.,0.};
  unsigned i,j;
  if(!rows)return;
  for(i=0;i<rows;i++) {
    fractions[0]+=covered[2*i]?1.:0.;
    fractions[1]+=covered[2*i+1]?1.:0.;
  }
  fractions[0]/=rows;fractions[1]/=rows;
  if(s->n_recent==ACR_ACI_RECENT) {
    memmove(&s->recent[0],&s->recent[1],
            (ACR_ACI_RECENT-1)*sizeof(s->recent[0]));
    s->n_recent--;
  }
  for(j=0;j<2;j++)s->recent[s->n_recent][j]=fractions[j];
  s->n_recent++;
  if(s->mode==ACR_ACI_FROZEN && round>=20)return;
  for(i=0;i<rows;i++) {
    if(s->n_scores==ACR_ACI_WINDOW) {
      memmove(&s->scores[0],&s->scores[1],
              (ACR_ACI_WINDOW-1)*sizeof(s->scores[0]));
      s->n_scores--;
    }
    for(j=0;j<2;j++)s->scores[s->n_scores][j]=scores[2*i+j];
    s->n_scores++;
  }
  if(s->mode==ACR_ACI_ADAPTIVE && round>=20) {
    for(j=0;j<2;j++) {
      double miscoverage=1.-fractions[j];
      s->alpha[j]=clamp(s->alpha[j]+.03*(.10-miscoverage),.02,.40);
    }
  }
  for(j=0;j<2;j++) {
    /* Python np.partition selects exactly this zero-indexed order statistic. */
    double ordered[ACR_ACI_WINDOW],quantile;
    unsigned n=s->n_scores;
    unsigned rank;
    for(i=0;i<n;i++)ordered[i]=s->scores[i][j];
    qsort(ordered,n,sizeof(double),compare_double);
    rank=(unsigned)ceil((n+1)*(1.-s->alpha[j]));
    if(rank<1)rank=1;
    if(rank>n)rank=n;
    quantile=ordered[rank-1];
    s->q[j]=quantile<0?0:quantile;
  }
}
int acr_aci_alert(const ACR_ACI *s) {
  unsigned i,j;
  if(s->n_recent<3)return 0;
  for(j=0;j<2;j++) {
    double m=0.;
    for(i=s->n_recent-3;i<s->n_recent;i++)
      m+=s->recent[i][j];
    if(m/3<.78)return 1;
  }
  return 0;
}
