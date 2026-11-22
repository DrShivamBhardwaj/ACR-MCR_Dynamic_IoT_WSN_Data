/* Real Grenoble sink-only deterministic ACR original policy computation.
 * Original synthetic predictions and NumPy RNG choices are FROZEN in FLASH:
 * this is open-loop physical plan→MAC test, not feedback-driven ACR-MCR.
 * Included after cl_routes[]/cl_heads[] declarations in transport.
 */
#if ACR_NODE_ID == 41
#include "acr_optimizer_core.h"
#include "generated_fixture.h"
#include <math.h>
static ACR_OptContext opt_ctx;
static ACR_SearchTrace opt_trace;
static ACR_OptPlan opt_result;
static uint8_t opt_verified=0;
static clock_time_t opt_init_ticks=0;
static void old_python_risk_sample(void *ignored,unsigned ss,
                                   unsigned u,unsigned v,
                                   double *cc,double *dd) {
  (void)ignored;
  if(!FX_METHOD_RISK){*cc=0.;*dd=0.;return;}
  {
    uint32_t at=(ss*40u*41u+u*41u+v)*9u;
    uint32_t by=at>>3u, shift=at&7u;
    uint32_t packed=fx_idx_packed[by] |
      ((uint32_t)fx_idx_packed[by+1]<<8u) |
      ((uint32_t)fx_idx_packed[by+2]<<16u);
    uint32_t ix=(packed>>shift)&511u;
    uint32_t edge=u*41u+v;
    if(ix>=FX_N_SCORES){*cc=NAN;*dd=NAN;return;}
    *cc=fx_cost_pred[edge]+fx_cost_scale[edge]*fx_scores[2u*ix];
    *dd=fx_delay_pred[edge]+fx_delay_scale[edge]*fx_scores[2u*ix+1u];
    if(*cc<1.)*cc=1.;
    if(*cc>5.)*cc=5.;
    if(*dd<1.)*dd=1.;
  }
}
static uint8_t original_onboard_frozen_policy(void) {
  int i,j,h,a,rc,route,enabled=0;double error;
  clock_time_t t0=clock_time();
  memset(&opt_ctx,0,sizeof(opt_ctx));
  memset(&opt_trace,0,sizeof(opt_trace));
  opt_ctx.n=40;
  opt_ctx.load=FX_LOAD;
  opt_ctx.deadline_ms=500.;
  opt_ctx.tail_weight=.15;
  opt_ctx.tail_beta=.90;
  opt_ctx.has_risk=FX_METHOD_RISK;
  opt_ctx.stress_samples=FX_METHOD_RISK?64:0;
  opt_ctx.edge_cost=fx_edge_cost;
  opt_ctx.attempt_mean=fx_attempt_mean;
  opt_ctx.tx_energy=fx_tx_energy;
  opt_ctx.distance=fx_distance;
  opt_ctx.d_used=fx_d_used;
  opt_ctx.energy=fx_energy;
  opt_ctx.stress=old_python_risk_sample;
  opt_trace.nheads=FX_K;
  for(i=0;i<40;i++) opt_ctx.active[i]=fx_active[i];
  for(i=0;i<32;i++)
    for(j=0;j<8;j++)opt_trace.heads[i][j]=fx_trace_heads[i][j];
  rc=acr_select_trace(&opt_ctx,&opt_trace,&opt_result);
  opt_init_ticks=clock_time()-t0;
  error=fabs(opt_result.objective-(double)FX_EXPECTED);
  if(rc!=0 || opt_result.nheads!=4 ||
     opt_result.heads[0]!=FX_EXPECTED_H0 || error>1e-7) {
    printf("ONBOARD_OPT_FAIL fixture=%s rc=%d error_nano=%lu\n",
       FX_ID,rc,(unsigned long)llround(error*1e9));
    return 0;
  }
  for(i=0;i<40;i++) {
    h=opt_result.assigned[i];
    route=0;
    if(h>=0 && fx_active[i]) {
      if(i!=h)route=h+1;
      else for(a=0;a<opt_result.nheads;a++)
        if(opt_result.heads[a]==i && opt_result.path_len[a]>=2)
          route=opt_result.paths[a][1]+1;
    }
    cl_routes[i]=(uint8_t)route;
    cl_probes[i]=SINK_ID;
    cl_enabled_map[i]=(uint8_t)(route>0);
    cl_heads[i]=(uint8_t)(i==h);
    if(route>0)enabled++;
  }
  printf("ONBOARD_OPT_READY fixture=%s risk=%d"
         " heads=%d,%d,%d,%d objective_micro=%lu"
         " error_nano=%lu cpu_ticks=%lu hz=%lu enabled=%d\n",
    FX_ID,FX_METHOD_RISK,
    opt_result.heads[0]+1,opt_result.heads[1]+1,
    opt_result.heads[2]+1,opt_result.heads[3]+1,
    (unsigned long)llround(opt_result.objective*1e6),
    (unsigned long)llround(error*1e9),
    (unsigned long)opt_init_ticks,(unsigned long)CLOCK_SECOND,enabled);
  return 1;
}
#endif
