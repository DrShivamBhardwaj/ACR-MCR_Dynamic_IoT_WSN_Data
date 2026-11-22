#!/usr/bin/env python3
"""Generate a Cooja ScriptRunner bridge with real packet feedback to Python."""
import argparse,json
from pathlib import Path
from xml.etree import ElementTree as ET
from types import SimpleNamespace
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

var cmd = Java.to(__CMD_ARRAY__, "java.lang.String[]");
var process = new ProcessBuilder(cmd).directory(new JFile(__DIR__))
               .redirectError(new JFile(__ERROR_LOG__)).start();
var toPython = new BufferedWriter(new OutputStreamWriter(process.getOutputStream(),"UTF-8"));
var fromPython = new BufferedReader(new InputStreamReader(process.getInputStream(),"UTF-8"));
var mems = {};
var motes = sim.getMotes();
for(var i=0;i<motes.length;i++) {
  if(motes[i].getID()>=1 && motes[i].getID()<=40) {
    mems[String(motes[i].getID())] = new VM(motes[i].getMemory());
  }
}
var started = false, completed = 0, planned = 0, activeRound = -1;
var starts = {}, demands = {}, delivered = {};
var observedMac = [], received = 0, timely = 0, requested = 0;

function rpc(request) {
  toPython.write(JSON.stringify(request)+"\n");
  toPython.flush();
  var response = fromPython.readLine();
  if(response==null) throw new Error("Python controller exited or closed stdout");
  var output=JSON.parse(String(response));
  if(output.error) throw new Error("Controller: "+output.error);
  return output;
}
function putByte(mem,name,val) {
  mem.setInt8ValueOf(name, Java.to([val], "byte[]")[0]);
}
function applyPlan(p) {
  if(!p.next || p.next.length!=40) throw new Error("Malformed Python plan");
  for(var i=0;i<40;i++) {
    var m=mems[String(i+1)];
    if(!m) throw new Error("Missing Cooja mote memory for node "+(i+1));
    putByte(m,"cl_next_hop",p.next[i]);
    putByte(m,"cl_probe_target",p.probes[i]);
    putByte(m,"cl_enabled",p.enabled[i]);
    putByte(m,"cl_head",p.heads[i]);
    putByte(m,"cl_ready",1);
  }
  planned++;
  activeRound=p.round;
  log.log("CONTROLLER_APPLIED round="+p.round+" method=__METHOD__ next0="+p.next[0]+
          " reason="+p.reason+"\n");
}
function fields(s) {
  var out={},re=/([a-z_]+)=([0-9]+)/g,m;
  while((m=re.exec(String(s)))!==null)out[m[1]]=parseInt(m[2],10);
  return out;
}
while(true) {
  YIELD();
  if(id==41 && msg.contains("CLOSED_BOOT")) {
    var compiled=fields(msg);
    if(compiled.rounds!==__ROUNDS__ || compiled.seed!==__SEED__ ||
       compiled.m!==__METHOD_NUM__) {
       throw new Error("Mote build mismatch rounds="+compiled.rounds+
                       " seed="+compiled.seed+" method="+compiled.m);
    }
    log.log("COMPILED_CONFIG_OK rounds="+compiled.rounds+
            " seed="+compiled.seed+" method="+compiled.m+"\n");
  }
  if(id==41 && msg.contains("ROUND_OPEN")) {
    if(started)throw new Error("Double Cooja controller boot");
    applyPlan(rpc({cmd:"init"}));
    started=true;
  }
  if(msg.contains("DATA_DEMAND")) {
    var x=fields(msg),key=x.round+":"+x.src;
    if(x.round===activeRound) {
      requested++;
      demands[key]=sim.getSimulationTime();
    } else {
      log.log("LATE_DEMAND "+msg+" activeRound="+activeRound+"\n");
    }
    log.log("DEMAND_TRACE "+msg+"\n");
  }
  if(msg.contains("SINK_RECV")) {
    var x=fields(msg),key=x.round+":"+x.src;
    if(x.round!==activeRound) {
      log.log("LATE_RECEIPT "+msg+" activeRound="+activeRound+"\n");
    } else if(delivered[key]===undefined && demands[key]!==undefined) {
      delivered[key]=true;received++;
      var elapsed=demands[key]===undefined?-1:
        (sim.getSimulationTime()-demands[key])/1000.0;
      if(elapsed>=0 && elapsed<=500)timely++;
      log.log("RECEIPT_TRACE round="+x.round+" src="+x.src+
              " end_to_end_ms="+elapsed+"\n");
    }
  }
  if(msg.contains("MAC_START")) {
    var x=fields(msg);
    if(x.round===activeRound) starts[String(x.sender)]=sim.getSimulationTime();
  }
  if(msg.contains("MAC_TX")) {
    var x=fields(msg);
    if(x.round!==activeRound) {
      log.log("LATE_MAC "+msg+" activeRound="+activeRound+"\n");
    } else {
      var first=starts[String(x.sender)];
      x.duration_ms=first===undefined?0:
        (sim.getSimulationTime()-first)/1000.0;
      observedMac.push(x);
      log.log("MAC_TRACE "+msg+" duration_ms="+x.duration_ms+"\n");
    }
  }
  if(id==41 && msg.contains("ROUND_BARRIER")) {
    if(!started)throw new Error("Round barrier before controller init");
    var b=fields(msg),n=b.round;
    var got=observedMac.length;
    log.log("ROUND_PACKET_AUDIT round="+n+" requested="+requested+
      " unique_sink="+received+" timely500="+timely+
      " MAC_callbacks="+got+"\n");
    if(received>requested) throw new Error("More matched sink receptions than source demands");
    var response=rpc({cmd:"observe",round:n,mac:observedMac,
      sinks:{unique:received,timely:timely,requested:requested}});
    completed++;
    observedMac=[];
    received=0;timely=0;requested=0;
    starts={};demands={};delivered={};
    if(response.done) {
      if(received>requested) throw new Error("Impossible receipt count");
      if(completed!==__ROUNDS__ || planned!==__ROUNDS__) {
        throw new Error("Epoch mismatch complete="+completed+" planned="+planned);
      }
      log.log("CLOSED_LOOP_COMPLETE method=__METHOD__ seed=__SEED__"+
              " observed_rounds="+completed+" plans="+planned+"\n");
      toPython.close();fromPython.close();
      log.testOK();
    } else {
      applyPlan(response);
    }
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
    p.add_argument("--rounds",type=int,choices=[16,40,160],required=True)
    p.add_argument("--python",required=True)
    p.add_argument("--controller-script",required=True)
    p.add_argument("--workdir",required=True)
    p.add_argument("--output-log",required=True)
    p.add_argument("--stderr-log",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--rx-success",type=float,default=.94)
    a=p.parse_args()
    args=SimpleNamespace(template=a.template,positions=a.positions,seed=a.seed,
          scenario=a.scenario,method=a.method,rounds=a.rounds,
          rx_success=a.rx_success,radio_range=78.0,out=a.out)
    build_base(args)
    tree=ET.parse(a.out)
    root=tree.getroot()
    mt=root.find("./simulation/motetype")
    mt.find("source").text="[CONTIKI_DIR]/examples/acr_mcr_closed/acr_40_closed.c"
    mt.find("description").text="40-node original Python optimizer with Cooja packet-feedback bridge; privileged control"
    mode=1 if a.method=="ACR-MCR" else 0
    scenario_id=5 if a.scenario=="S5" else 1
    mt.find("commands").text=(
        "$(MAKE) TARGET=cooja clean\n"
        f"$(MAKE) acr_40_closed.cooja TARGET=cooja CL_ROUNDS={a.rounds} "
        f"CL_SEED={a.seed} CL_SCENARIO={scenario_id} CL_METHOD={mode}")
    cmd=[a.python,a.controller_script,"--seed",str(a.seed),"--scenario",a.scenario,
         "--method",a.method,"--rounds",str(a.rounds),"--out",a.output_log]
    script=JS
    for key,value in {
      "__TIMEOUT__":str((a.rounds*5+100)*1000),
      "__CMD_ARRAY__":json.dumps(cmd),
      "__DIR__":json.dumps(a.workdir),
      "__ERROR_LOG__":json.dumps(a.stderr_log),
      "__METHOD__":a.method,"__METHOD_NUM__":str(mode),"__SEED__":str(a.seed),"__ROUNDS__":str(a.rounds)
    }.items():script=script.replace(key,value)
    scripts=[p.find("plugin_config/script") for p in root.findall("plugin")
             if "ScriptRunner" in (p.text or "")]
    scripts=[s for s in scripts if s is not None]
    if len(scripts)!=1:raise ValueError("Missing Cooja script config")
    scripts[0].text=script
    ET.indent(tree,space="  ")
    tree.write(a.out,encoding="unicode",xml_declaration=True)
    print("Closed-loop Cooja file:",a.out)
if __name__=="__main__":main()
