#!/usr/bin/env python3
"""Build a separate packet-driven Cooja mote program from the audited open-loop mote."""
from pathlib import Path
here=Path(__file__).resolve().parent
source=(here/"acr_40_replay.c").read_text()
changes=[
 ("#include \"acr_40_plan.h\"", """#ifndef CL_SEED
#define CL_SEED 8201
#endif
#ifndef CL_METHOD
#define CL_METHOD 0
#endif
#ifndef CL_SCENARIO
#define CL_SCENARIO 1
#endif
#ifndef CL_ROUNDS
#define CL_ROUNDS 16
#endif
#define REPLAY_SEED CL_SEED
#define REPLAY_METHOD CL_METHOD
#define REPLAY_SCENARIO CL_SCENARIO
#define REPLAY_ROUNDS CL_ROUNDS
#define MSG_CONTROL 3

/* Exported symbols set by Cooja's in-process controller bridge.
   This is a privileged central controller, not measured control radio airtime. */
volatile uint8_t cl_next_hop=0;
volatile uint8_t cl_probe_target=0;
volatile uint8_t cl_enabled=1;
volatile uint8_t cl_head=0;
volatile uint8_t cl_ready=0;"""),
 ("PROCESS(acr_40_replay_process,\"ACR-MCR 40-node open-loop replay\");",
  "PROCESS(acr_40_replay_process,\"ACR-MCR 40-node packet-observation controller\");"),
 ("  if(!active_node[round][id-1] && !disabled) {",
  "    if(!cl_enabled && !disabled) {"),
 ("  next=route_next[period][id-1];",
  "  if(!cl_ready) return;\n  next=cl_next_hop;"),
 ("  p.planned_head=route_heads[period][id-1];",
  "  p.planned_head=cl_head;"),
 ("  next=probe_to[period][id-1];",
  "  if(!cl_ready) return;\n  next=cl_probe_target;"),
 ("  forward_to=route_next[p.round][id-1];",
  "  forward_to=cl_next_hop;"),
 ("  if(forward_to==0 || forward_to==id || !active_node[p.round][id-1]) return;",
  "  if(forward_to==0 || forward_to==id || !cl_enabled) return;"),
 ("  NETSTACK_MAC.send(tx_done,NULL);",
  """  printf("MAC_START round=%u src=%u sender=%u to=%u type=%u\\n",
    sending.packet.round,sending.packet.src,nodeid(),sending.destination,sending.packet.type);
  NETSTACK_MAC.send(tx_done,NULL);"""),
 ("  if(id<1 || id>40 || disabled || period>=REPLAY_ROUNDS) return;",
  "  if(id<1 || id>40 || disabled || period>=REPLAY_ROUNDS || !cl_ready) return;"),
 ("    if(id<1 || id>40) {", "    if(id<1 || id>40) {"),
]
for old,new in changes:
    if old not in source:
        raise ValueError("Not found: "+old)
    source=source.replace(old,new)
source=source.replace(
'  printf("REPLAY_BOOT m=%u seed=%d scenario=%d id=%u nodes=40 rounds=%d\\n",',
'  printf("CLOSED_BOOT m=%u seed=%d scenario=%d id=%u nodes=40 rounds=%d\\n",')
source=source.replace(
'          apply_radio_state(period);',
'''          if(id==41 && period==0) {
            printf("ROUND_OPEN round=0 node=41\\n");
          }
          if(id==41 && period>0) {
            printf("ROUND_BARRIER round=%u node=41\\n",period-1);
          }
          apply_radio_state(period);''')
source=source.replace(
'          if(id==1 && !done_announced) {',
'          if(id==41 && !done_announced) {')
source=source.replace(
'              REPLAY_METHOD,REPLAY_SEED,REPLAY_ROUNDS,tx_data,',
'              REPLAY_METHOD,REPLAY_SEED,REPLAY_ROUNDS,tx_data,')
source=source.replace("REPLAY_DONE m=%u","CLOSED_DONE m=%u")
# last barrier must be observed before success; no new commands after last.
source=source.replace(
'''        } else {
          if(id==41 && !done_announced) {''',
'''        } else {
          if(id==41 && !done_announced) {
            printf("ROUND_BARRIER round=%u node=41\\n",REPLAY_ROUNDS-1);''')
out=here/"acr_40_closed.c"
out.write_text(source)
print("CREATED",out,len(source.splitlines()))
