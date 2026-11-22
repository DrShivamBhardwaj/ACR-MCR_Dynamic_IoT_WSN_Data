#!/usr/bin/env python3
"""Generate 41-mote Cooja experiment with OVER-THE-AIR route plans and 500B data.

The Python optimizer's plan is placed in SINK memory ONLY. Two 20-node
control frames per round are transmitted over 802.15.4 CSMA and rebroadcast
once per forwarder with a hop limit. All other mote routes are received
via radio, not injected into Cooja memory.
"""
import argparse,json
from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree as ET
from generate_40node_csc import build as build_base

JS=r'''
TIMEOUT(__TIMEOUT__);
var ProcessBuilder = Java.type("java.lang.ProcessBuilder");
var BufferedWriter = Java.type("java.io.BufferedWriter");
var BufferedReader = Java.type("java.io.BufferedReader");
var OutputStreamWriter = Java.type("java.io.OutputStreamWriter");
var InputStreamReader = Java.type("java.io.InputStreamReader");
var VM = Java.type("org.contikios.cooja.mote.memory.VarMemory");
var JFile = Java.type("java.io.File");

var command=Java.to(__CMD_ARRAY__, "java.lang.String[]");
var python = new ProcessBuilder(command).directory(new JFile(__DIR__))
    .redirectError(new JFile(__ERROR_LOG__)).start();
var toPython = new BufferedWriter(new OutputStreamWriter(python.getOutputStream(),"UTF-8"));
var fromPython = new BufferedReader(new InputStreamReader(python.getInputStream(),"UTF-8"));
var allMotes=sim.getMotes();
var sinkMote=null;
for(var m=0;m<allMotes.length;m++)if(allMotes[m].getID()==41)sinkMote=allMotes[m];
if(!sinkMote)throw new Error("No sink mote ID41");
var sinkMem=new VM(sinkMote.getMemory());

var current=-1,started=false,completed=0,plans=0,finished=false;
var starts={},demand={},unique={},mac=[],usedCtrl={},energySeen={};
var req=0,delivered=0,timely=0,ctrlApplied=0,ctrlTx=0,frags=0;
var badPayload=0,allControlApplied=0,allControlPackets=0;

function rpc(payload) {
  toPython.write(JSON.stringify(payload)+"\n");
  toPython.flush();
  var line=fromPython.readLine();
  if(line==null)throw new Error("Python controller terminated before response");
  var res=JSON.parse(String(line));
  if(res.error)throw new Error("Python controller "+res.error);
  return res;
}
function memoryVector(name,arr) {
  if(!arr || arr.length!=40)throw new Error("Wrong controller vector length "+name);
  var bytes=Java.to(arr.map(function(x){return x&255;}),"byte[]");
  sinkMote.getMemory().setMemorySegment(sinkMem.getVariableAddress(name),bytes);
}
function injectSinkOnly(plan) {
  if(plan.round!==current+1)throw new Error("Python plan out of order");
  memoryVector("cl_routes",plan.next);
  memoryVector("cl_probes",plan.probes);
  memoryVector("cl_enabled_map",plan.enabled);
  memoryVector("cl_heads",plan.heads);
  sinkMem.setInt8ValueOf("cl_plan_valid",Java.to([1],"byte[]")[0]);
  current=plan.round;
  plans++;
  log.log("SINK_PLAN_WRITTEN round="+current+" method=__METHOD__"+
          " entries=40 radio_delivery_required=1\n");
}
function fields(line) {
  var obj={},rx=/([a-z_]+)=([0-9]+)/g,found;
  while((found=rx.exec(String(line)))!==null)obj[found[1]]=parseInt(found[2],10);
  return obj;
}
while(true) {
  YIELD();
  if(id===41 && msg.contains("DIST_BOOT")) {
    var compiled=fields(msg);
    if(compiled.rounds!==__ROUNDS__ || compiled.seed!==__SEED__ ||
       compiled.method!==__METHOD_NUM__ || compiled.app_bytes!==500 ||
       compiled.ctrl_over_radio!==1)throw new Error("Distributed firmware configuration mismatch");
    log.log("DIST_CONFIG_OK seed="+compiled.seed+" method="+compiled.method+
            " rounds="+compiled.rounds+" app_bytes=500\n");
  }
  if(id===41 && msg.contains("ROUND_OPEN")) {
    if(started)throw new Error("Duplicate controller initialization");
    injectSinkOnly(rpc({cmd:"init"}));
    started=true;
  }
  if(msg.contains("CTRL_APPLIED")) {
    var x=fields(msg);
    if(x.round===current) {
      var key=current+":"+x.id;
      if(usedCtrl[key]===undefined){usedCtrl[key]=true;ctrlApplied++;}
      log.log("CONTROL_RECEPTION "+msg+"\n");
    }
  }
  if(msg.contains("DATA_DEMAND")) {
    var x=fields(msg),key=x.round+":"+x.src;
    if(x.round===current && demand[key]===undefined) {
      demand[key]=sim.getSimulationTime();
      req++;
    } else {
      log.log("DUPLICATE_OR_LATE_DEMAND "+msg+"\n");
    }
    log.log("DEMAND "+msg+"\n");
  }
  if(msg.contains("SINK_BAD_PAYLOAD")) {
    badPayload++;
    log.log("INTEGRITY_ERROR "+msg+"\n");
  }
  if(msg.contains("SINK_REASSEMBLED")) {
    var x=fields(msg),key=x.round+":"+x.src;
    if(x.app_bytes!==500 || x.parts!==8)throw new Error("Invalid completed payload framing");
    if(x.round!==current || demand[key]===undefined) {
      log.log("LATE_OR_UNMATCHED_COMPLETE "+msg+"\n");
    } else if(unique[key]===undefined) {
      unique[key]=true;delivered++;
      var delay=(sim.getSimulationTime()-demand[key])/1000.0;
      if(delay>=0 && delay<=500)timely++;
      log.log("COMPLETE_DELIVERY round="+x.round+" src="+x.src+
              " bytes=500 latency_ms="+delay+"\n");
    }
  }
  if(msg.contains("MAC_START")) {
    var x=fields(msg);
    if(x.round===current)starts[String(x.sender)]=sim.getSimulationTime();
  }
  if(msg.contains("MAC_TX")) {
    var x=fields(msg);
    if(x.round!==current) {
      log.log("LATE_MAC "+msg+"\n");
    } else {
      var first=starts[String(x.sender)];
      x.duration_ms=first===undefined?0:(sim.getSimulationTime()-first)/1000.0;
      mac.push(x);
      if(x.type===3)ctrlTx++;
      if(x.type===1)frags++;
      log.log("PACKET_CALLBACK "+msg+" duration_ms="+x.duration_ms+"\n");
    }
  }
  if(msg.contains("ENERGEST_RAW")) {
    var x=fields(msg);
    if(energySeen[String(x.id)]===undefined && x.round===__ROUNDS__) {
      energySeen[String(x.id)]=true;
      log.log("ENERGY_TICKS "+msg+"\n");
    }
  }
  if(id===41 && msg.contains("ROUND_BARRIER")) {
    if(!started)throw new Error("Missing controller boot");
    var info=fields(msg),round=info.round;
    if(round!==current)throw new Error("Cooja epoch "+round+" vs Python "+current);
    if(delivered>req)throw new Error("More reassembled deliveries than demands");
    var receivedCtrl=ctrlApplied;
    log.log("ROUND_PACKET_AUDIT round="+round+" requested="+req+
      " unique_sink="+delivered+" timely500="+timely+" MAC_callbacks="+mac.length+
      " control_applied="+receivedCtrl+" control_mac="+ctrlTx+
      " fragment_mac="+frags+" bad_payload="+badPayload+"\n");
    var response=rpc({cmd:"observe",round:round,mac:mac,
       sinks:{unique:delivered,timely:timely,requested:req,
              control_applied:receivedCtrl,control_mac:ctrlTx,fragments:frags}});
    completed++;allControlApplied+=receivedCtrl;allControlPackets+=ctrlTx;
    req=0;delivered=0;timely=0;ctrlApplied=0;ctrlTx=0;frags=0;
    demand={};unique={};mac=[];starts={};usedCtrl={};
    if(response.done) {
      if(plans!==__ROUNDS__ || completed!==__ROUNDS__)
        throw new Error("Missing plan/feedback rounds");
      finished=true;
      log.log("RADIO_FEEDBACK_COMPLETED method=__METHOD__ seed=__SEED__"+
          " rounds="+completed+" plans="+plans+
          " control_receptions="+allControlApplied+
          " control_mac="+allControlPackets+"\n");
    } else injectSinkOnly(response);
  }
  if(id===41 && msg.contains("DIST_DONE")) {
    if(!finished)throw new Error("Sink done before Python feedback complete");
    var count=Object.keys(energySeen).length;
    log.log("REASSEMBLY_AUDIT_COMPLETE rounds="+completed+
            " energy_nodes="+count+" controller_plan_injected_only_at_sink=1\n");
    if(count<30 || allControlApplied<__ROUNDS__*20 || badPayload>0) {
      log.log("VALIDATION_LIMIT energy_nodes="+count+" control_applied="+allControlApplied+
              " bad_payload="+badPayload+"\n");
      log.testFailed();
    }
    toPython.close();fromPython.close();
    log.testOK();
  }
}
'''

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--template",required=True)
    p.add_argument("--positions",required=True)
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--scenario",choices=["S1","S5"],required=True)
    p.add_argument("--method",choices=["POINT-EA","ACR-MCR"],required=True)
    p.add_argument("--rounds",type=int,choices=[4,16,40,160],required=True)
    p.add_argument("--python",required=True)
    p.add_argument("--controller-script",required=True)
    p.add_argument("--workdir",required=True)
    p.add_argument("--output-log",required=True)
    p.add_argument("--stderr-log",required=True)
    p.add_argument("--rx-success",type=float,default=.94)
    p.add_argument("--radio-range",type=float,default=78.0)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    b=SimpleNamespace(template=a.template,positions=a.positions,seed=a.seed,
        scenario=a.scenario,method=a.method,rounds=a.rounds,
        rx_success=a.rx_success,radio_range=a.radio_range,out=a.out)
    build_base(b)
    tree=ET.parse(a.out);root=tree.getroot()
    mt=root.find("./simulation/motetype")
    mt.find("description").text="500B/8fragment Cooja: controller only at sink, route control flooded by radio"
    mt.find("source").text="[CONTIKI_DIR]/examples/acr_mcr_transport/acr_40_distributed_transport.c"
    method_code=1 if a.method=="ACR-MCR" else 0
    scen=5 if a.scenario=="S5" else 1
    mt.find("commands").text=(
        "$(MAKE) TARGET=cooja clean\n"
        f"$(MAKE) acr_40_distributed_transport.cooja TARGET=cooja CL_ROUNDS={a.rounds} "
        f"CL_SEED={a.seed} CL_SCENARIO={scen} CL_METHOD={method_code}")
    cmd=[a.python,a.controller_script,"--seed",str(a.seed),"--scenario",a.scenario,
         "--method",a.method,"--rounds",str(a.rounds),"--out",a.output_log]
    script=JS
    for token,value in {
      "__TIMEOUT__":str((a.rounds*20+100)*1000),
      "__CMD_ARRAY__":json.dumps(cmd),
      "__DIR__":json.dumps(a.workdir),
      "__ERROR_LOG__":json.dumps(a.stderr_log),
      "__METHOD__":a.method,"__METHOD_NUM__":str(method_code),
      "__SEED__":str(a.seed),"__ROUNDS__":str(a.rounds)
    }.items():script=script.replace(token,value)
    runners=[q.find("plugin_config/script") for q in root.findall("plugin")
             if "ScriptRunner" in (q.text or "")]
    runners=[x for x in runners if x is not None]
    if len(runners)!=1:raise ValueError("One ScriptRunner required")
    runners[0].text=script
    ET.indent(tree,space="  ")
    tree.write(a.out,encoding="unicode",xml_declaration=True)
    print("Cooja radio-control + 500B fragmentation scenario generated: "+a.out)
if __name__=="__main__":main()
