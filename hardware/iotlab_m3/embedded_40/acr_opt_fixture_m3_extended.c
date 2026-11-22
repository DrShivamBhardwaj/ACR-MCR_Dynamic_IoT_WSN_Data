/* Runs ORIGINAL ACR-MCR / POINT deterministic select + CVaR kernel on a
 * real Grenoble Cortex-M3, fed a previously frozen synthetic-model state
 * in firmware flash. NOT live original adaptive routing on M3.
 */
#include "contiki.h"
#include "sys/energest.h"
#include "dev/watchdog.h"
#include "acr_optimizer_core.h"
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "generated_fixture.h"
#ifndef FX_START_DELAY_S
#define FX_START_DELAY_S 15
#endif
static struct etimer startup,shutdown;
static ACR_OptContext context;
static ACR_SearchTrace trace;
static ACR_OptPlan chosen;
static volatile uint32_t already=0;
static void sample_stress(void *user,unsigned sample,unsigned u,unsigned v,
                          double *cost,double *delay) {
  (void)user;
  if(!FX_METHOD_RISK) { *cost=0.; *delay=0.;return; }
  {
    const uint32_t at=(sample*40u*41u+u*41u+v)*9u;
    const uint32_t byte=at/8u,shift=at%8u;
    const uint32_t word=(uint32_t)fx_idx_packed[byte] |
        ((uint32_t)fx_idx_packed[byte+1]<<8u) |
        ((uint32_t)fx_idx_packed[byte+2]<<16u);
    const uint16_t idx=(word>>shift)&511u;
    const uint32_t n=u*41u+v;
    double c,d;
    if(idx>=FX_N_SCORES){ *cost=NAN; *delay=NAN;return; }
    c=fx_cost_pred[n]+fx_cost_scale[n]*fx_scores[2u*idx];
    d=fx_delay_pred[n]+fx_delay_scale[n]*fx_scores[2u*idx+1];
    if(c<1.)c=1.;
    if(c>5.)c=5.;
    if(d<1.)d=1.;
    *cost=c;*delay=d;
  }
}
PROCESS(acr_opt_kernel_process,"Frozen original Python/C CVaR kernel M3 parity");
AUTOSTART_PROCESSES(&acr_opt_kernel_process);
PROCESS_THREAD(acr_opt_kernel_process,ev,data) {
  static clock_time_t before,after;
  static int rc,i,j,success,rep,allpass;
  static double difference;
  PROCESS_BEGIN();
  printf("OPT_KERNEL_BOOT fixture=%s risk=%d scores=%d candidate_sets=32\n",
        FX_ID,FX_METHOD_RISK,FX_N_SCORES);
  etimer_set(&startup,CLOCK_SECOND*FX_START_DELAY_S);
  PROCESS_WAIT_EVENT_UNTIL(ev==PROCESS_EVENT_TIMER && data==&startup);
  memset(&context,0,sizeof(context));
  context.n=40;
  context.load=FX_LOAD;
  context.deadline_ms=500.;
  context.tail_beta=.90;
  context.tail_weight=.15;
  context.has_risk=FX_METHOD_RISK;
  context.stress_samples=FX_METHOD_RISK?64:0;
  context.edge_cost=fx_edge_cost;
  context.attempt_mean=fx_attempt_mean;
  context.tx_energy=fx_tx_energy;
  context.distance=fx_distance;
  context.d_used=fx_d_used;
  context.energy=fx_energy;
  for(i=0;i<40;i++)context.active[i]=fx_active[i];
  context.stress=sample_stress;
  trace.nheads=FX_K;
  for(i=0;i<32;i++)
    for(j=0;j<8;j++)trace.heads[i][j]=fx_trace_heads[i][j];
  before=clock_time();
  allpass=1;
  for(rep=0;rep<20;rep++) {
    rc=acr_select_trace(&context,&trace,&chosen);
    difference=fabs(chosen.objective-(double)FX_EXPECTED);
    success=rc==0 && chosen.nheads==FX_K &&
            difference<1e-7 && chosen.heads[0]==FX_EXPECTED_H0;
    if(!success)allpass=0;
    watchdog_periodic();
  }
  after=clock_time();
  success=allpass;
  already=(uint32_t)(after-before);
  printf("OPT_KERNEL_REPETITIONS fixture=%s count=20 allpass=%d sum_ticks=%lu hz=%lu\n",
         FX_ID,allpass,(unsigned long)already,(unsigned long)CLOCK_SECOND);
  printf("OPT_KERNEL_RESULT fixture=%s rc=%d PASS=%d heads=%d,%d,%d,%d"
         " objective_micro=%lu expected_micro=%lu"
         " absolute_error_nanounits=%lu cpu_wall_ticks=%lu"
         " clock_hz=%lu tail=%d\n",
         FX_ID,rc,success,chosen.heads[0],chosen.heads[1],
         chosen.heads[2],chosen.heads[3],
         (unsigned long)llround(chosen.objective*1000000.),
         (unsigned long)llround((double)FX_EXPECTED*1000000.),
         (unsigned long)llround(difference*1000000000.),
         (unsigned long)already,(unsigned long)CLOCK_SECOND,FX_METHOD_RISK);
  energest_flush();
  printf("OPT_KERNEL_ENERGEST fixture=%s cpu=%llu lpm=%llu tx=%llu"
         " listen=%llu hz=%lu\n",FX_ID,
     (unsigned long long)energest_type_time(ENERGEST_TYPE_CPU),
     (unsigned long long)energest_type_time(ENERGEST_TYPE_LPM),
     (unsigned long long)energest_type_time(ENERGEST_TYPE_TRANSMIT),
     (unsigned long long)energest_type_time(ENERGEST_TYPE_LISTEN),
     (unsigned long)ENERGEST_SECOND);
  /* Keep the monitoring window fixed at 120 s after warmup. ACR executes
     more real calculations; POINT sleeps for the corresponding remaining
     time. Compare total supplied device J only over equal-duration
     reservations, not as a wall-plug Apple M1 host estimate. */
  etimer_set(&shutdown,(clock_time_t)(already < CLOCK_SECOND*115u
                       ? CLOCK_SECOND*120u-already : CLOCK_SECOND*5u));
  PROCESS_WAIT_EVENT_UNTIL(ev==PROCESS_EVENT_TIMER && data==&shutdown);
  printf("OPT_KERNEL_DONE fixture=%s PASS=%d\n",FX_ID,success);
  PROCESS_END();
}
