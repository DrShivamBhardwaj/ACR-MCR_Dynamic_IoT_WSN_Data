/*
 * ACR-MCR Contiki-NG transport validation. Simulated controller injects
 * plan ONLY at the sink. The sink emits actual 802.15.4 CSMA control frames,
 * each source installs its route only after radio reception.
 *
 * Application data is exactly 500 bytes, fragmented into 8 separate MAC
 * packets and reassembled/checked at the sink before delivery counting.
 * No claim of true PHY SNR calibration or physical power measurement.
 */
#include "contiki.h"
#include "net/netstack.h"
#include "net/nullnet/nullnet.h"
#include "net/packetbuf.h"
#include "net/mac/mac.h"
#include "sys/energest.h"
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#ifndef CL_ROUNDS
#define CL_ROUNDS 4
#endif
#ifndef CL_SEED
#define CL_SEED 8701
#endif
#ifndef CL_SCENARIO
#define CL_SCENARIO 1
#endif
#ifndef CL_METHOD
#define CL_METHOD 0
#endif

#ifndef ACR_START_DELAY_S
#define ACR_START_DELAY_S 25
#endif
#ifndef ACR_NODE_ID
#error "ACR_NODE_ID (1..40 member, 41 sink) must be supplied per M3 firmware binary"
#endif
#if ACR_NODE_ID<1 || ACR_NODE_ID>41
#error "ACR_NODE_ID out of bound"
#endif
#define SINK_ID 41
#define NODE_COUNT 40
#define MSG_FRAG 1
#define MSG_PROBE 2
#define MSG_CONTROL 3
#define MSG_CONTROL_ACK 4
#define MSG_LINK_PROBE_TELEMETRY 5
/* This stage delivers actual physical member MAC observations to sink.
 * It does NOT yet implement full original adaptive head search. */
#define FRAGMENT_BYTES 64
#define APPLICATION_BYTES 500
#define FRAGMENT_COUNT 8
#define CONTROL_PART_COUNT 2
#define CONTROL_NODES_PER_PART 20
#define CONTROL_HOPS 3
#define ROUND_SECONDS 20
#define DATA_START_MS 3500
#define PROBE_START_MS 11000
#define QUEUE_CAP 48

/* The privileged bridge only writes these arrays on the sink mote.
   Other motes install their settings after a real radio control frame. */
volatile uint8_t cl_routes[NODE_COUNT];
volatile uint8_t cl_probes[NODE_COUNT];
volatile uint8_t cl_enabled_map[NODE_COUNT];
volatile uint8_t cl_heads[NODE_COUNT];
volatile uint8_t cl_plan_valid=0;

typedef struct {
  uint16_t round;
  uint8_t type;
  uint8_t src;
  uint8_t ttl;
  uint8_t part;
  uint8_t parts;
  uint8_t head;
  uint8_t bytes;
  uint8_t payload[80];
} Frame;

typedef struct {
  Frame frame;
  uint8_t destination;
} QueueItem;

static QueueItem q[QUEUE_CAP];
static QueueItem active;
static uint8_t rd=0,wr=0,tx_busy=0;
static clock_time_t active_tx_started_ticks;
static uint8_t sink_probe_seen[40]; /* bitmask: source/round for 3 rounds */
static uint32_t sink_probe_records=0;
static uint16_t nq=0,period=0;
static uint32_t mac_sent=0,control_sent=0,data_sent=0,probe_sent=0;
static uint32_t queue_dropped=0;
static uint8_t route_next=0,route_probe=0,route_enabled=1,route_head=0;
static uint8_t have_ctrl=0,radio_disabled=0;
static uint16_t ctrl_round=65535;
static uint8_t done_logged=0,energy_logged=0;
static uint8_t reassembly[40][APPLICATION_BYTES];
static uint8_t reassembly_parts[40];
static uint16_t reassembly_round[40];
static uint16_t finished_round[40];
static uint32_t source_delivered=0,control_applied_count=0;
static struct etimer round_clock, control_clock, data_clock, probe_clock;

PROCESS(acr_transport_process,"ACR 500-byte distributed control and reassembly test");
AUTOSTART_PROCESSES(&acr_transport_process);

static uint8_t node(void) { return linkaddr_node_addr.u8[0]; }
static linkaddr_t peer(uint8_t id) {
  linkaddr_t a=linkaddr_null;
  a.u8[0]=id;
  return a;
}
static uint8_t sample_byte(uint8_t src,uint16_t round,uint16_t offset) {
  return (uint8_t)((src*17u+(unsigned)round*7u+offset*3u)%251u);
}
static uint16_t frame_len(const Frame *f) {
  return (uint16_t)(offsetof(Frame,payload)+(size_t)f->bytes);
}
static uint8_t queue_frame(const Frame *f,uint8_t dst) {
  if(nq>=QUEUE_CAP || dst>SINK_ID) {
    ++queue_dropped;
    printf("QUEUE_DROP round=%u type=%u id=%u src=%u part=%u\n",
       f->round,f->type,node(),f->src,f->part);
    return 0;
  }
  q[wr].frame=*f;
  q[wr].destination=dst;
  wr=(wr+1)%QUEUE_CAP;
  nq++;
  process_poll(&acr_transport_process);
  return 1;
}
static void transmit_done(void *ptr,int status,int attempts) {
  (void)ptr;
  printf("MAC_TX round=%u type=%u src=%u sender=%u to=%u part=%u status=%d attempts=%d bytes=%u\n",
     active.frame.round,active.frame.type,active.frame.src,node(),
     active.destination,active.frame.part,status,attempts,frame_len(&active.frame));
  if(active.frame.type==MSG_PROBE && node()!=SINK_ID &&
     route_next>0 && active.frame.round<CL_ROUNDS) {
    /* Telemetry is generated from the actual physical MAC callback;
       service ticks are measured on the TRANSMITTING mote itself.
       No central access to off-mote radio state. */
    Frame telem;
    uint32_t elapsed=clock_time()-active_tx_started_ticks;
    uint32_t elapsed_ms=(elapsed*1000UL)/CLOCK_SECOND;
    memset(&telem,0,sizeof(telem));
    telem.type=MSG_LINK_PROBE_TELEMETRY;
    telem.round=active.frame.round;
    telem.src=node();
    telem.ttl=12;
    telem.bytes=8;
    telem.payload[0]=active.destination;
    telem.payload[1]=(attempts<0)?0:((attempts>255)?255:(uint8_t)attempts);
    telem.payload[2]=(status==0)?1:0;
    telem.payload[3]=(uint8_t)(elapsed_ms&255);
    telem.payload[4]=(uint8_t)((elapsed_ms>>8)&255);
    telem.payload[5]=(uint8_t)status;
    telem.payload[6]=active.frame.type;
    telem.payload[7]=1; /* actual source firmware MAC callback */
    printf("PROBE_TX_EVIDENCE round=%u src=%u to=%u attempts=%d ok=%d duration_ms=%lu native_ticks=%lu\n",
      active.frame.round,node(),active.destination,attempts,status==0,
      (unsigned long)elapsed_ms,(unsigned long)elapsed);
    /* Report via the source's radio-installed route to the sink.
       Loss of this report is a first-class observation outcome. */
    queue_frame(&telem,route_next);
  }
  tx_busy=0;
  process_poll(&acr_transport_process);
}
static void dispatch_next(void) {
  linkaddr_t destination;
  uint16_t bytes;
  if(tx_busy || !nq || radio_disabled)return;
  active=q[rd];
  rd=(rd+1)%QUEUE_CAP;--nq;
  destination=peer(active.destination);
  bytes=frame_len(&active.frame);
  packetbuf_clear();
  packetbuf_copyfrom(&active.frame,bytes);
  packetbuf_set_addr(PACKETBUF_ADDR_RECEIVER,&destination);
  packetbuf_set_addr(PACKETBUF_ADDR_SENDER,&linkaddr_node_addr);
  tx_busy=1;
  active_tx_started_ticks=clock_time();
  mac_sent++;
  if(active.frame.type==MSG_CONTROL)control_sent++;
  else if(active.frame.type==MSG_FRAG)data_sent++;
  else if(active.frame.type==MSG_PROBE)probe_sent++;
  printf("MAC_START round=%u type=%u src=%u sender=%u to=%u part=%u bytes=%u\n",active.frame.round,active.frame.type,active.frame.src,node(),active.destination,active.frame.part,bytes);
  NETSTACK_MAC.send(transmit_done,NULL);
}
static void energy_snapshot(void) {
  energest_flush();
  printf("ENERGEST_RAW id=%u round=%u cpu=%llu lpm=%llu deep=%llu tx=%llu listen=%llu ticks_per_second=%lu\n",
    node(),period,
    (unsigned long long)energest_type_time(ENERGEST_TYPE_CPU),
    (unsigned long long)energest_type_time(ENERGEST_TYPE_LPM),
    (unsigned long long)energest_type_time(ENERGEST_TYPE_DEEP_LPM),
    (unsigned long long)energest_type_time(ENERGEST_TYPE_TRANSMIT),
    (unsigned long long)energest_type_time(ENERGEST_TYPE_LISTEN),
    (unsigned long)ENERGEST_SECOND);
}
static void install_control(uint16_t round,uint8_t part,const Frame *f) {
  uint8_t i,id=node(),offset;
  if(id<1 || id>NODE_COUNT || part>=2 || f->bytes!=80)return;
  if(ctrl_round!=round) {
    ctrl_round=round;
    have_ctrl=0;
  }
  if(have_ctrl & (1u<<part))return;
  have_ctrl|=(1u<<part);
  i=(uint8_t)(id-1);
  if(i/CONTROL_NODES_PER_PART==part) {
    offset=(i%CONTROL_NODES_PER_PART)*4;
    route_next=f->payload[offset];
    route_probe=f->payload[offset+1];
    route_enabled=f->payload[offset+2];
    route_head=f->payload[offset+3];
  }
  if(have_ctrl==3) {
    control_applied_count++;
    printf("CTRL_APPLIED round=%u id=%u next=%u probe=%u enabled=%u head=%u\n",
      round,id,route_next,route_probe,route_enabled,route_head);
  }
}
static void receive(const void *input,uint16_t len,
                    const linkaddr_t *sender,const linkaddr_t *destination) {
  Frame f;
  uint8_t id=node();
  (void)sender;(void)destination;
  if(len<offsetof(Frame,payload) || len>sizeof(Frame))return;
  memset(&f,0,sizeof(f));
  memcpy(&f,input,len);
  if(f.bytes>80 || len!=frame_len(&f) || f.round>=CL_ROUNDS)return;

  if(f.type==MSG_CONTROL && id!=SINK_ID) {
    uint8_t seen_before=(ctrl_round==f.round && (have_ctrl&(1u<<f.part)));
    if(f.part>=CONTROL_PART_COUNT)return;
    install_control(f.round,f.part,&f);
    if(!seen_before && f.ttl>1 && !radio_disabled) {
      /* Each radio floods each control part only once. The payload was
         installed from over-the-air bytes, not through Cooja memory. */
      f.ttl--;
      queue_frame(&f,0);  /* broadcast */
    }
    return;
  }
  if(f.type==MSG_LINK_PROBE_TELEMETRY) {
    if(f.src<1 || f.src>40 || f.bytes!=8 || f.payload[6]!=MSG_PROBE
       || f.payload[7]!=1)return;
    if(id==SINK_ID) {
      uint8_t bit=(uint8_t)(1u<<f.round),src=(uint8_t)(f.src-1);
      uint16_t duration_ms=(uint16_t)f.payload[3] | ((uint16_t)f.payload[4]<<8);
      if(!(sink_probe_seen[src]&bit)) {
        sink_probe_seen[src]|=bit;
        sink_probe_records++;
        printf("SINK_REAL_PROBE_OBS round=%u src=%u to=%u attempts=%u ok=%u duration_ms=%u status=%u via_radio=1\n",
          f.round,f.src,f.payload[0],f.payload[1],f.payload[2],
          (unsigned)duration_ms,f.payload[5]);
      }
      return;
    }
    if(!route_enabled || !route_next || f.ttl<2 || route_next==id)return;
    f.ttl--;
    queue_frame(&f,route_next);
    return;
  }
  if(f.type==MSG_PROBE || f.type==MSG_CONTROL_ACK || f.type!=MSG_FRAG)return;
  if(f.part>=FRAGMENT_COUNT || f.src<1 || f.src>40)return;

  if(id==SINK_ID) {
    uint8_t idx=f.src-1;
    if(finished_round[idx]==f.round)return;
    uint16_t off=(uint16_t)f.part*FRAGMENT_BYTES;
    uint8_t expected=(f.part==7)?52:64;
    if(f.bytes!=expected)return;
    if(reassembly_round[idx]!=f.round) {
      reassembly_round[idx]=f.round;
      reassembly_parts[idx]=0;
    }
    if(!(reassembly_parts[idx] & (1u<<f.part))) {
      memcpy(&reassembly[idx][off],f.payload,f.bytes);
      reassembly_parts[idx]|=(uint8_t)(1u<<f.part);
    }
    if(reassembly_parts[idx]==255) {
      uint8_t valid=1;
      uint16_t j;
      for(j=0;j<APPLICATION_BYTES;j++) {
        if(reassembly[idx][j]!=sample_byte(f.src,f.round,j)) { valid=0;break; }
      }
      if(valid) {
        printf("SINK_REASSEMBLED round=%u src=%u app_bytes=500 parts=8 checksum=PASS\n",
           f.round,f.src);
        source_delivered++;
        finished_round[idx]=f.round;
      } else {
        printf("SINK_BAD_PAYLOAD round=%u src=%u part=%u offset=%u\n",
           f.round,f.src,f.part,j);
      }
      reassembly_parts[idx]=0; /* paired-key duplicate suppression done in ScriptRunner */
      reassembly_round[idx]=65535; /* ignore late duplicates in script */
    }
    return;
  }
  if(!route_enabled || !route_next || f.ttl<2 || route_next==id)return;
  f.ttl--;
  queue_frame(&f,route_next);
}
static void controller_frame(uint16_t round,uint8_t part) {
  Frame f;
  uint8_t i,base;
  if(node()!=SINK_ID || !cl_plan_valid) {
    if(node()==SINK_ID) printf("CTRL_SOURCE_NOT_READY round=%u\n",round);
    return;
  }
  memset(&f,0,sizeof(f));
  f.round=round;f.type=MSG_CONTROL;f.src=SINK_ID;f.ttl=CONTROL_HOPS;
  f.part=part;f.parts=2;f.bytes=80;
  base=(uint8_t)(part*CONTROL_NODES_PER_PART);
  for(i=0;i<CONTROL_NODES_PER_PART;i++) {
    uint8_t idx=base+i,at=i*4;
    f.payload[at]=cl_routes[idx];
    f.payload[at+1]=cl_probes[idx];
    f.payload[at+2]=cl_enabled_map[idx];
    f.payload[at+3]=cl_heads[idx];
  }
  queue_frame(&f,0);
  printf("CONTROL_ENQUEUED round=%u chunk=%u id=41 entries=20 payload_bytes=80\n",round,part);
}
static void send_fragments(void) {
  Frame f;
  uint8_t id=node(),part,next=route_next;
  uint16_t j,offset;
  uint8_t usable;
  if(id<1 || id>40 || radio_disabled || !route_enabled || !route_next
     || have_ctrl!=3 || period==0 || period>CL_ROUNDS)return;
  if(ctrl_round!=period-1)return;
  printf("DATA_DEMAND round=%u src=%u app_bytes=500 fragments=8 head=%u next=%u\n",
         period-1,id,route_head,next);
  for(part=0;part<FRAGMENT_COUNT;part++) {
    memset(&f,0,sizeof(f));
    f.round=period-1;f.type=MSG_FRAG;f.src=id;f.ttl=12;
    f.part=part;f.parts=8;f.head=route_head;
    offset=(uint16_t)part*FRAGMENT_BYTES;
    usable=(part==7)?52:64;
    f.bytes=usable;
    for(j=0;j<usable;j++)f.payload[j]=sample_byte(id,f.round,offset+j);
    queue_frame(&f,next);
  }
}
static void send_probe(void) {
  Frame f;
  uint8_t id=node();
  if(id<1 || id>40 || radio_disabled || !route_enabled
     || !route_probe || route_probe==id || have_ctrl!=3
     || period==0 || period>CL_ROUNDS || ctrl_round!=period-1)return;
  memset(&f,0,sizeof(f));
  f.round=period-1;f.type=MSG_PROBE;f.src=id;f.ttl=1;
  f.bytes=8;
  queue_frame(&f,route_probe);
}
PROCESS_THREAD(acr_transport_process,ev,data) {
  static uint8_t id;
  PROCESS_BEGIN();
  {
    linkaddr_t addr=linkaddr_null;
    addr.u8[0]=ACR_NODE_ID;
    linkaddr_set_node_addr(&addr);
    NETSTACK_RADIO.on();
  }
  id=node();
  if(id!=ACR_NODE_ID) {
    printf("ACR_FATAL_ADDR expected=%u observed=%u\n",(unsigned)ACR_NODE_ID,id);
    PROCESS_EXIT();
  }
  memset(reassembly_round,0xFF,sizeof(reassembly_round));
  memset(finished_round,0xFF,sizeof(finished_round));
  if(id==SINK_ID) {
    /* Transport-only deterministic fixed-cluster mapping:
       four heads 1, 11, 21, 31; no adaptive ACR algorithm here. */
    uint8_t n;
    for(n=0;n<40;n++) {
      uint8_t physical_head=(uint8_t)(1+10*(n/10));
      cl_routes[n]=(n+1==physical_head)?SINK_ID:physical_head;
      cl_probes[n]=SINK_ID;
      cl_enabled_map[n]=1;
      cl_heads[n]=(n+1==physical_head)?1:0;
    }
    cl_plan_valid=1;
  }
  nullnet_set_input_callback(receive);
  printf("M3_TRANSPORT_BOOT id=%u site=real_physical_telemetry algorithm=STATIC_HEADS_NOT_ACR seed=%d method=%d scenario=%d rounds=%d app_bytes=500 fragments=8 ctrl_over_radio=1\n",
         id,CL_SEED,CL_METHOD,CL_SCENARIO,CL_ROUNDS);
  etimer_set(&round_clock,CLOCK_SECOND*ACR_START_DELAY_S);
  while(1) {
    PROCESS_WAIT_EVENT();
    if(ev==PROCESS_EVENT_POLL)dispatch_next();
    if(ev==PROCESS_EVENT_TIMER) {
      if(data==&round_clock && etimer_expired(&round_clock)) {
        if(period<CL_ROUNDS) {
          if(id==SINK_ID) {
            cl_plan_valid=1;
            if(period==0) printf("ROUND_OPEN round=0 node=41\n");
            else printf("ROUND_BARRIER round=%u node=41\n",period-1);
            etimer_set(&control_clock,(CLOCK_SECOND*400)/1000);
          } else {
            have_ctrl=0;
            ctrl_round=65535;
            etimer_set(&data_clock,
              (CLOCK_SECOND*(DATA_START_MS+(unsigned)id*65))/1000);
            etimer_set(&probe_clock,
              (CLOCK_SECOND*(PROBE_START_MS+(unsigned)id*45))/1000);
          }
          etimer_set(&round_clock,CLOCK_SECOND*ROUND_SECONDS);
        } else {
          if(id==SINK_ID && !done_logged) {
            printf("ROUND_BARRIER round=%u node=41\n",CL_ROUNDS-1);
            done_logged=1;
          } else if(id==SINK_ID && done_logged==1) {
            printf("DIST_DONE seed=%d method=%d rounds=%d packets=%lu control_packets=%lu reassembled=%lu\n",
                   CL_SEED,CL_METHOD,CL_ROUNDS,(unsigned long)mac_sent,
                   (unsigned long)control_sent,(unsigned long)source_delivered);
            printf("SINK_PROBE_OBS_TOTAL rounds=%u unique_records=%lu source_round_possible=%lu\n",
               CL_ROUNDS,(unsigned long)sink_probe_records,(unsigned long)(40UL*CL_ROUNDS));
            done_logged=2;
          }
          if(!energy_logged && ((id!=SINK_ID && period==CL_ROUNDS) || (id==SINK_ID && done_logged>=1))) {
            energy_snapshot();
            energy_logged=1;
          }
          etimer_set(&round_clock,CLOCK_SECOND);
        }
        if(period<CL_ROUNDS)period++;
      }
      if(data==&control_clock && etimer_expired(&control_clock)
         && id==SINK_ID && period>0 && period<=CL_ROUNDS) {
        controller_frame(period-1,0);
        controller_frame(period-1,1);
      }
      if(data==&data_clock && etimer_expired(&data_clock))send_fragments();
      if(data==&probe_clock && etimer_expired(&probe_clock))send_probe();
    }
  }
  PROCESS_END();
}
