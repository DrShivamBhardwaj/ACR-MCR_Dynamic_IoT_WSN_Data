/*
 * 40-node open-loop packet-transport replay of the original ACR-MCR optimizer.
 * The plan arrays come from the UNMODIFIED original Python simulator.
 * MAC outcomes come from Contiki-NG/Cooja and are NOT fed into the next plan.
 * This is NOT closed-loop original-controller validation.
 */
#include "contiki.h"
#include "net/netstack.h"
#include "net/nullnet/nullnet.h"
#include "net/packetbuf.h"
#include "net/mac/mac.h"
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "acr_40_plan.h"

#define SINK_NODE 41
#define MSG_DATA 1
#define MSG_PROBE 2
#define MAX_QUEUE 32
#define ROUND_SECONDS 5
#define DATA_STAGGER 25
#define PROBE_OFFSET_MS 2700

typedef struct {
  uint16_t round;
  uint8_t src;
  uint8_t type;
  uint8_t ttl;
  uint8_t planned_head;
  uint8_t payload[72];
} Packet;

typedef struct {
  Packet packet;
  uint8_t destination;
} Job;

static Job pending[MAX_QUEUE];
static uint8_t rd_idx=0,wr_idx=0,nqueued=0,tx_busy=0;
static Job sending;
static uint16_t tx_data=0,tx_probe=0,forwarded=0,queue_overflow=0;
static uint16_t period=0;
static uint8_t done_announced=0;
static uint8_t disabled=0;
static struct etimer round_timer, data_timer, probe_timer;
static struct etimer heartbeat_timer;

PROCESS(acr_40_replay_process,"ACR-MCR 40-node open-loop replay");
AUTOSTART_PROCESSES(&acr_40_replay_process);

static uint8_t nodeid(void) {return linkaddr_node_addr.u8[0];}
static linkaddr_t address(uint8_t n) {
  linkaddr_t a=linkaddr_null;
  a.u8[0]=n;
  return a;
}
static uint8_t queue_pkt(const Packet *p,uint8_t dest) {
  if(nqueued>=MAX_QUEUE || dest<1 || dest>41) {
    ++queue_overflow;
    printf("DROP_QUEUE m=%u seed=%d round=%u src=%u dest=%u depth=%u\n",
      REPLAY_METHOD,REPLAY_SEED,p->round,p->src,dest,nqueued);
    return 0;
  }
  pending[wr_idx].packet=*p;
  pending[wr_idx].destination=dest;
  wr_idx=(wr_idx+1)%MAX_QUEUE;
  nqueued++;
  process_poll(&acr_40_replay_process);
  return 1;
}
static void tx_done(void *ptr,int status,int attempts) {
  (void)ptr;
  printf("MAC_TX m=%u seed=%d round=%u src=%u sender=%u to=%u type=%u status=%d attempts=%d\n",
      REPLAY_METHOD,REPLAY_SEED,sending.packet.round,sending.packet.src,
      nodeid(),sending.destination,sending.packet.type,status,attempts);
  tx_busy=0;
  process_poll(&acr_40_replay_process);
}
static void flush_queue(void) {
  linkaddr_t dst;
  if(tx_busy || nqueued==0 || disabled) return;
  sending=pending[rd_idx];
  rd_idx=(rd_idx+1)%MAX_QUEUE;
  --nqueued;
  dst=address(sending.destination);
  packetbuf_clear();
  packetbuf_copyfrom(&sending.packet,sizeof(Packet));
  packetbuf_set_addr(PACKETBUF_ADDR_RECEIVER,&dst);
  packetbuf_set_addr(PACKETBUF_ADDR_SENDER,&linkaddr_node_addr);
  tx_busy=1;
  NETSTACK_MAC.send(tx_done,NULL);
}
static void receive_packet(const void *buf,uint16_t len,
                          const linkaddr_t *src,const linkaddr_t *dest) {
  Packet p;
  uint8_t id=nodeid();
  uint8_t forward_to;
  (void)src;
  (void)dest;
  if(disabled || len!=sizeof(Packet)) return;
  memcpy(&p,buf,sizeof(Packet));
  if(p.round>=REPLAY_ROUNDS || p.src<1 || p.src>40) return;
  if(id==SINK_NODE) {
    if(p.type==MSG_DATA) {
      printf("SINK_RECV m=%u seed=%d round=%u src=%u head=%u\n",
        REPLAY_METHOD,REPLAY_SEED,p.round,p.src,p.planned_head);
    }
    return;
  }
  if(p.type==MSG_PROBE) return;
  if(p.type!=MSG_DATA || p.ttl<2 || id<1 || id>40) return;
  forward_to=route_next[p.round][id-1];
  if(forward_to==0 || forward_to==id || !active_node[p.round][id-1]) return;
  p.ttl--;
  if(queue_pkt(&p,forward_to)) ++forwarded;
}
static void apply_radio_state(uint16_t round) {
  uint8_t id=nodeid();
  if(id<1 || id>40) return;
  if(!active_node[round][id-1] && !disabled) {
    disabled=1;
    NETSTACK_RADIO.off();
    printf("NODE_DISABLE m=%u seed=%d round=%u node=%u\n",
      REPLAY_METHOD,REPLAY_SEED,round,id);
  }
}
static void emit_data(void) {
  Packet p;
  uint8_t id=nodeid(),next;
  if(id<1 || id>40 || disabled || period>=REPLAY_ROUNDS) return;
  next=route_next[period][id-1];
  if(next==0) return;
  memset(&p,0,sizeof(p));
  p.round=period;
  p.type=MSG_DATA;
  p.src=id;
  p.ttl=12;
  p.planned_head=route_heads[period][id-1];
  p.payload[0]=id;
  if(queue_pkt(&p,next)) {
    ++tx_data;
    printf("DATA_DEMAND m=%u seed=%d round=%u src=%u head=%u hop=%u\n",
        REPLAY_METHOD,REPLAY_SEED,period,id,p.planned_head,next);
  }
}
static void emit_probe(void) {
  Packet p;
  uint8_t id=nodeid(),next;
  if(id<1 || id>40 || disabled || period>=REPLAY_ROUNDS) return;
  next=probe_to[period][id-1];
  if(next==0 || next==id) return;
  memset(&p,0,sizeof(p));
  p.round=period;
  p.type=MSG_PROBE;
  p.src=id;
  p.ttl=1;
  if(queue_pkt(&p,next)) ++tx_probe;
}
PROCESS_THREAD(acr_40_replay_process,ev,data) {
  static uint8_t id;
  PROCESS_BEGIN();
  (void)data;
  id=nodeid();
  nullnet_set_input_callback(receive_packet);
  printf("REPLAY_BOOT m=%u seed=%d scenario=%d id=%u nodes=40 rounds=%d\n",
        REPLAY_METHOD,REPLAY_SEED,REPLAY_SCENARIO,id,REPLAY_ROUNDS);
  etimer_set(&round_timer,CLOCK_SECOND*2);
  while(1) {
    PROCESS_WAIT_EVENT();
    if(ev==PROCESS_EVENT_POLL) flush_queue();
    if(ev==PROCESS_EVENT_TIMER) {
      if(data==&round_timer && etimer_expired(&round_timer)) {
        if(period<REPLAY_ROUNDS) {
          apply_radio_state(period);
          if(id<1 || id>40) {
            etimer_set(&heartbeat_timer,CLOCK_SECOND*ROUND_SECONDS);
          } else {
            etimer_set(&data_timer,((clock_time_t)id*DATA_STAGGER*CLOCK_SECOND)/1000);
            etimer_set(&probe_timer,
              (clock_time_t)PROBE_OFFSET_MS*CLOCK_SECOND/1000+
              ((clock_time_t)id*DATA_STAGGER*CLOCK_SECOND)/1000);
          }
          etimer_set(&round_timer,CLOCK_SECOND*ROUND_SECONDS);
        } else {
          if(id==1 && !done_announced) {
            printf("REPLAY_DONE m=%u seed=%d n=40 rounds=%d tx_data=%u tx_probe=%u forwarded=%u drop_queue=%u\n",
              REPLAY_METHOD,REPLAY_SEED,REPLAY_ROUNDS,tx_data,
              tx_probe,forwarded,queue_overflow);
            done_announced=1;
          }
          etimer_set(&round_timer,CLOCK_SECOND);
        }
        if(period<REPLAY_ROUNDS) period++;
      }
      if(data==&data_timer && etimer_expired(&data_timer)) {
        /* Data are sent for the current planned round, already incremented. */
        if(period>0) {period--;emit_data();period++;}
      }
      if(data==&probe_timer && etimer_expired(&probe_timer)) {
        if(period>0) {period--;emit_probe();period++;}
      }
    }
  }
  PROCESS_END();
}
