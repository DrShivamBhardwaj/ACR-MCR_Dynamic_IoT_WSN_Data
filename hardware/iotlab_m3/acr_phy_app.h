/* ACR-MCR physical M3 transport pilot. Actual 500B application samples,
 * eight IEEE 802.15.4 fragments, physical packet and radio counters.
 * Raw radio registers are not calibrated RSSI, SNR, or PER.
 */
#include "contiki.h"
#include "net/netstack.h"
#include "net/nullnet/nullnet.h"
#include "net/packetbuf.h"
#include "sys/energest.h"
#include "periph/rf2xx.h"
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#ifndef ACR_PHY_ROLE
#error "ACR_PHY_ROLE must be 1 for sender or 2 for receiver"
#endif
#define SENDER 1
#define RECEIVER 2
#define FRAG_COUNT 8
#define APP_SIZE 500
#define FRAG_LEN 64
#define N_SAMPLES 100
#ifndef ACR_PHY_START_DELAY_S
#define ACR_PHY_START_DELAY_S 3
#endif
typedef struct {
  uint16_t seq;
  uint8_t source;
  uint8_t part;
  uint8_t length;
  uint8_t payload[64];
} Frame;
static struct etimer timer;
static uint8_t reassembled[APP_SIZE], mask=0;
static uint16_t rx_seq=65535, good_samples=0,rx_fragments=0,errors=0;
static uint16_t tx_seq=0;
static uint8_t tx_part=0,tx_busy=0;
static uint16_t tx_last_seq=0;
static uint8_t tx_last_part=0;
static uint32_t callbacks=0,ack_success=0,ack_fail=0;
PROCESS(acr_phy_test,"ACR 500-byte physical IoT-LAB packet test");
AUTOSTART_PROCESSES(&acr_phy_test);

static uint8_t pattern(uint16_t seq,uint16_t at) {
  return (uint8_t)((17u+seq*7u+at*3u)%251u);
}
static void snapshot(void) {
  energest_flush();
  printf("ACR_ENERGEST role=%d cpu=%llu lpm=%llu tx=%llu listen=%llu hz=%lu\n",
   ACR_PHY_ROLE,(unsigned long long)energest_type_time(ENERGEST_TYPE_CPU),
   (unsigned long long)energest_type_time(ENERGEST_TYPE_LPM),
   (unsigned long long)energest_type_time(ENERGEST_TYPE_TRANSMIT),
   (unsigned long long)energest_type_time(ENERGEST_TYPE_LISTEN),
   (unsigned long)ENERGEST_SECOND);
}
static void receive(const void *bytes,uint16_t len,
                    const linkaddr_t *sender,const linkaddr_t *dest) {
#if ACR_PHY_ROLE==2
  Frame f;
  uint16_t at,j;
  uint8_t good=1,expected;
  extern rf2xx_t RF2XX_DEVICE;
  (void)sender;(void)dest;
  if(len<offsetof(Frame,payload) || len>sizeof(Frame))return;
  memset(&f,0,sizeof(f));memcpy(&f,bytes,len);
  if(f.source!=SENDER || f.seq>=N_SAMPLES || f.part>=FRAG_COUNT)return;
  expected=(f.part==7)?52:64;
  if(f.length!=expected || len!=offsetof(Frame,payload)+expected){errors++;return;}
  if(rx_seq!=f.seq){rx_seq=f.seq;mask=0;}
  if(!(mask&(1u<<f.part))) {
    at=(uint16_t)f.part*FRAG_LEN;
    memcpy(reassembled+at,f.payload,expected);
    mask|=(uint8_t)(1u<<f.part);
    rx_fragments++;
  }
  /* Original M3 rf231 driver lacks RADIO_PARAM_LAST_RSSI support.
     Registers sampled here are raw values, not calibrated SNR. */
  printf("ACR_RX seq=%u part=%u len=%u phy_rssi_reg=%u phy_ed_reg=%u\n",
    f.seq,f.part,(unsigned)len,
    rf2xx_reg_read(RF2XX_DEVICE,RF2XX_REG__PHY_RSSI),
    rf2xx_reg_read(RF2XX_DEVICE,RF2XX_REG__PHY_ED_LEVEL));
  if(mask==255) {
    for(j=0;j<APP_SIZE;j++)if(reassembled[j]!=pattern(f.seq,j)){good=0;break;}
    printf("ACR_REASSEMBLED seq=%u bytes=500 integrity=%u\n",f.seq,good);
    if(good)good_samples++;else errors++;
    rx_seq=65535;mask=0;
  }
#else
  (void)bytes;(void)len;(void)sender;(void)dest;
#endif
}
#if ACR_PHY_ROLE==1
static void mac_callback(void *ptr,int status,int attempts){
  (void)ptr;
  callbacks++;
  if(status==MAC_TX_OK)ack_success++;else ack_fail++;
  printf("ACR_MAC seq=%u part=%u status=%d attempts=%d\n",
    tx_last_seq,tx_last_part,status,attempts);
  tx_busy=0;
  process_poll(&acr_phy_test);
}
static void send_fragment(void){
  Frame f;
  linkaddr_t to=linkaddr_null;
  uint16_t at,j;
  uint8_t length;
  if(tx_seq>=N_SAMPLES || tx_busy)return;
  memset(&f,0,sizeof(f));
  f.seq=tx_seq;f.source=SENDER;f.part=tx_part;
  length=tx_part==7?52:64;
  f.length=length;
  at=(uint16_t)tx_part*FRAG_LEN;
  for(j=0;j<length;j++)f.payload[j]=pattern(tx_seq,at+j);
  to.u8[0]=RECEIVER;
  packetbuf_clear();
  packetbuf_copyfrom(&f,offsetof(Frame,payload)+length);
  packetbuf_set_addr(PACKETBUF_ADDR_RECEIVER,&to);
  packetbuf_set_addr(PACKETBUF_ADDR_SENDER,&linkaddr_node_addr);
  tx_last_seq=tx_seq;tx_last_part=tx_part;
  tx_busy=1;
  printf("ACR_TX seq=%u part=%u bytes=%u\n",tx_seq,tx_part,length);
  NETSTACK_MAC.send(mac_callback,NULL);
  if(++tx_part==8){tx_part=0;tx_seq++;}
}
#endif
PROCESS_THREAD(acr_phy_test,ev,data){
  static uint8_t finished=0;
  linkaddr_t a=linkaddr_null;
  PROCESS_BEGIN();
  (void)ev;(void)data;
  a.u8[0]=ACR_PHY_ROLE;
  linkaddr_set_node_addr(&a);
  nullnet_set_input_callback(receive);
  NETSTACK_RADIO.on();
  printf("ACR_HW_READY role=%d n_samples=100 application_bytes=500 parts=8\n",ACR_PHY_ROLE);
  etimer_set(&timer,CLOCK_SECOND*ACR_PHY_START_DELAY_S);
  while(1){
    PROCESS_WAIT_EVENT();
    if(etimer_expired(&timer)){
#if ACR_PHY_ROLE==1
      if(tx_seq<N_SAMPLES)send_fragment();
      else if(!finished){
        printf("ACR_TX_COMPLETE samples=%u callbacks=%lu ack_ok=%lu ack_fail=%lu\n",
             tx_seq,(unsigned long)callbacks,(unsigned long)ack_success,
             (unsigned long)ack_fail);
        snapshot();finished=1;
      }
      etimer_set(&timer,CLOCK_SECOND/12);
#else
      printf("ACR_RX_PROGRESS complete=%u fragments=%u bad=%u\n",
             good_samples,rx_fragments,errors);
      snapshot();
      etimer_set(&timer,CLOCK_SECOND*20);
#endif
    }
  }
  PROCESS_END();
}
