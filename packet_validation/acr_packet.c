/*
 * ACR-MCR packet-level mechanism experiment, not a full ACR-MCR port.
 * Uses real Contiki-NG CSMA transmissions and callbacks, not a synthetic
 * coin-flip channel. Both policies use the same fixed geometric probe schedule.
 * Endpoint: a single source (4), two possible cluster relays (2 and 3), sink (1).
 * Mode 0: point-cost relay selection; Mode 1: conformal-bound relay selection.
 * Limitation: no original evolutionary 40-node search or full residual bootstrap.
 */
#include "contiki.h"
#include "net/netstack.h"
#include "net/nullnet/nullnet.h"
#include "net/packetbuf.h"
#include "net/mac/mac.h"
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdint.h>

#ifndef ACR_POLICY
#define ACR_POLICY 0
#endif
#ifndef TOTAL_ROUNDS
#define TOTAL_ROUNDS 40
#endif
#define MSG_PROBE 1
#define MSG_DATA  2
#define MSG_FORWARD 3
#define MAX_RESID 24
#define WARMUP_ROUNDS 6

typedef struct {
  uint16_t round;
  uint8_t type;
  uint8_t head;
  uint8_t source;
  uint32_t source_tick;
} Packet;

typedef struct {
  uint8_t type;
  uint8_t head;
  uint16_t round;
  double predicted;
  double bound;
} TxMeta;

typedef struct {
  double mean_cost;
  double residuals[MAX_RESID];
  uint8_t n;
  uint8_t idx;
  uint16_t observed;
  uint16_t misses;
} LinkEvidence;

static LinkEvidence evidence[4];
static double alpha_t = 0.10;
static uint16_t round_id = 0;
static uint8_t selected_head = 2;
static uint16_t last_search = 0;
static uint16_t periodic_searches = 0;
static uint16_t trigger_searches = 0;
static uint16_t head_changes = 0;
static uint8_t coverage_recent[3];
static uint8_t coverage_count = 0;
static uint8_t coverage_idx = 0;
static TxMeta probe_meta, data_meta, forward_meta;
static Packet forward_buf;
static uint8_t forward_pending = 0;
static uint16_t data_tx_count=0, probe_tx_count=0, forwarded=0;
static double qsort_buffer[MAX_RESID];

PROCESS(acr_packet_process,"ACR packet-level policy mechanism");
AUTOSTART_PROCESSES(&acr_packet_process);

static int node_id(void) {
  return (int)linkaddr_node_addr.u8[0];
}
static linkaddr_t address_for(uint8_t id) {
  linkaddr_t addr = linkaddr_null;
  addr.u8[0] = id;
  return addr;
}
static double clip(double x,double lo,double hi) {
  return x<lo?lo:(x>hi?hi:x);
}
static double upper_quantile(uint8_t relay) {
  LinkEvidence *e=&evidence[relay];
  uint8_t i,j;
  int k;
  double val;
  if(e->n<3) return 1.28;
  for(i=0;i<e->n;i++) qsort_buffer[i]=e->residuals[i];
  for(i=1;i<e->n;i++) {
    val=qsort_buffer[i]; j=i;
    while(j>0 && qsort_buffer[j-1]>val) {
      qsort_buffer[j]=qsort_buffer[j-1];
      --j;
    }
    qsort_buffer[j]=val;
  }
  {
    double rank=((double)e->n+1.0)*(1.0-alpha_t);
    k=(int)rank;
    if((double)k<rank) ++k;
  }
  if(k<1) k=1;
  if(k>e->n) k=e->n;
  return qsort_buffer[k-1]>0.0?qsort_buffer[k-1]:0.0;
}
static double score_for(uint8_t relay) {
  double v=evidence[relay].mean_cost;
  if(ACR_POLICY && round_id>WARMUP_ROUNDS) {
    v+=upper_quantile(relay);
  }
  return v;
}
static void choose_head(void) {
  int eligible_periodic = round_id-last_search>=10;
  int coverage_fail=0;
  uint8_t i, next;
  double a,b,current,best;
  if(round_id<=WARMUP_ROUNDS) return;
  if(coverage_count>=3) {
    int sum=0;
    for(i=0;i<3;i++) sum+=coverage_recent[i];
    coverage_fail=(sum<2);
  }
  if(!eligible_periodic && !(ACR_POLICY && coverage_fail &&
        round_id-last_search>=3)) return;
  if(eligible_periodic) ++periodic_searches;
  else ++trigger_searches;
  a=score_for(2);
  b=score_for(3);
  next=(b<a)?3:2;
  current=score_for(selected_head);
  best=score_for(next);
  if(next!=selected_head && best < current*0.995) {
    selected_head=next;
    ++head_changes;
  }
  printf("HEAD_CHOICE mode=%d round=%u selected=%u score2=%.5f score3=%.5f alpha=%.4f reason=%s\n",
         ACR_POLICY,round_id,selected_head,a,b,alpha_t,
         eligible_periodic?"periodic":"coverage");
  last_search=round_id;
}
static void on_tx_done(void *ptr,int status,int attempts) {
  TxMeta *meta=(TxMeta*)ptr;
  if(meta==NULL) return;
  if(meta->type==MSG_PROBE) {
    LinkEvidence *e=&evidence[meta->head];
    double cost=clip(attempts+(status==MAC_TX_OK?0:1),1.0,5.0);
    double residual=cost-meta->predicted;
    int covered=(cost<=meta->bound);
    e->residuals[e->idx]=residual;
    e->idx=(e->idx+1)%MAX_RESID;
    if(e->n<MAX_RESID) ++e->n;
    e->mean_cost=0.9*e->mean_cost+0.1*cost;
    ++e->observed;
    if(!covered) ++e->misses;
    coverage_recent[coverage_idx]=covered?1:0;
    coverage_idx=(coverage_idx+1)%3;
    if(coverage_count<3) ++coverage_count;
    if(ACR_POLICY && meta->round>WARMUP_ROUNDS) {
      alpha_t=clip(alpha_t + 0.03*(0.10-(covered?0.0:1.0)),0.02,0.40);
    }
    printf("PROBE_RESULT mode=%d round=%u head=%u mac_status=%d attempts=%d cost=%.3f predicted=%.3f upper=%.3f covered=%d alpha=%.4f\n",
           ACR_POLICY,meta->round,meta->head,status,attempts,
           cost,meta->predicted,meta->bound,covered,alpha_t);
  } else if(meta->type==MSG_DATA) {
    printf("DATA_TX mode=%d round=%u head=%u mac_status=%d attempts=%d\n",
           ACR_POLICY,meta->round,meta->head,status,attempts);
  } else if(meta->type==MSG_FORWARD) {
    printf("RELAY_TX mode=%d round=%u head=%u mac_status=%d attempts=%d\n",
           ACR_POLICY,meta->round,meta->head,status,attempts);
  }
}
static void tx_packet(const Packet *pkt,uint8_t destination,TxMeta *meta) {
  linkaddr_t addr=address_for(destination);
  packetbuf_clear();
  packetbuf_copyfrom(pkt,sizeof(*pkt));
  packetbuf_set_addr(PACKETBUF_ADDR_RECEIVER,&addr);
  packetbuf_set_addr(PACKETBUF_ADDR_SENDER,&linkaddr_node_addr);
  NETSTACK_MAC.send(on_tx_done,meta);
}
static void input_callback(const void *data,uint16_t len,
                           const linkaddr_t *src,const linkaddr_t *dest) {
  Packet p;
  int id=node_id();
  (void)src; (void)dest;
  if(len!=sizeof(p)) return;
  memcpy(&p,data,sizeof(p));
  if(id==1 && p.type==MSG_FORWARD) {
    /* Mote clocks are not synchronized: host script measures global time. */
    printf("SINK_DATA mode=%d round=%u origin=%u head=%u\n",
           ACR_POLICY,p.round,p.source,p.head);
  }
  if((id==2 || id==3) && p.type==MSG_DATA) {
    forward_buf=p;
    forward_buf.type=MSG_FORWARD;
    forward_pending=1;
    process_poll(&acr_packet_process);
  }
}
PROCESS_THREAD(acr_packet_process,ev,data) {
  static struct etimer tick,data_phase;
  static Packet packet;
  static uint8_t target, id;
  PROCESS_BEGIN();
  (void)data;
  id=(uint8_t)node_id();
  evidence[2].mean_cost=2.0;
  evidence[3].mean_cost=2.0;
  nullnet_set_input_callback(input_callback);
  printf("BOOT mode=%d node=%u\n",ACR_POLICY,id);
  if(id==4) etimer_set(&tick,CLOCK_SECOND);
  while(1) {
    PROCESS_WAIT_EVENT();
    if(ev==PROCESS_EVENT_POLL && forward_pending && (id==2 || id==3)) {
      forward_pending=0;
      forward_meta.type=MSG_FORWARD;
      forward_meta.round=forward_buf.round;
      forward_meta.head=id;
      tx_packet(&forward_buf,1,&forward_meta);
      ++forwarded;
      printf("RELAY_FORWARD mode=%d round=%u head=%u\n",
             ACR_POLICY,forward_buf.round,id);
    }
    if(id==4 && ev==PROCESS_EVENT_TIMER) {
      if(etimer_expired(&tick)) {
        if(round_id>=TOTAL_ROUNDS) {
          printf("DONE mode=%d rounds=%u probes=%u data_tx=%u searches_periodic=%u searches_coverage=%u head_changes=%u\n",
                 ACR_POLICY,round_id,probe_tx_count,data_tx_count,
                 periodic_searches,trigger_searches,head_changes);
          break;
        }
        ++round_id;
        target=(round_id&1)?2:3;
        memset(&packet,0,sizeof(packet));
        packet.round=round_id; packet.type=MSG_PROBE;
        packet.source=4;packet.head=target;
        probe_meta.type=MSG_PROBE;
        probe_meta.head=target;
        probe_meta.round=round_id;
        probe_meta.predicted=evidence[target].mean_cost;
        probe_meta.bound=probe_meta.predicted+upper_quantile(target);
        tx_packet(&packet,target,&probe_meta);
        ++probe_tx_count;
        etimer_set(&data_phase,CLOCK_SECOND/4);
        etimer_set(&tick,2*CLOCK_SECOND);
      } else if(etimer_expired(&data_phase)) {
        choose_head();
        memset(&packet,0,sizeof(packet));
        packet.round=round_id;packet.type=MSG_DATA;
        packet.head=selected_head;packet.source=4;
        packet.source_tick=clock_time();
        data_meta.type=MSG_DATA;
        data_meta.head=selected_head;data_meta.round=round_id;
        printf("DATA_START mode=%d round=%u head=%u\n",
               ACR_POLICY,round_id,selected_head);
        tx_packet(&packet,selected_head,&data_meta);
        ++data_tx_count;
      }
    }
  }
  PROCESS_END();
}
