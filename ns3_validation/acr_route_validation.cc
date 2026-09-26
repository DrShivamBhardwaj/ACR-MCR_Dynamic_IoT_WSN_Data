#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/mobility-module.h"
#include "ns3/lr-wpan-module.h"
#include "ns3/lr-wpan-spectrum-value-helper.h"
#include "ns3/spectrum-module.h"
#include <iostream>
#include <map>
#include <set>
#include <vector>
#include <iomanip>
using namespace ns3;

static NetDeviceContainer g_main;
static NetDeviceContainer g_jam;
static std::vector<uint32_t> g_path;
static std::map<uint32_t,uint32_t> g_next;
static std::map<uint32_t,double> g_sentAt;
static std::set<uint32_t> g_seen;
static uint32_t g_generated=0, g_received=0, g_burstGen=0, g_burstRx=0, g_hopTx=0;
static double g_delaySum=0.0;
static double g_stop=80.0;

static uint32_t ReadSeq(Ptr<const Packet> p){
  uint8_t b[4]={0,0,0,0}; p->CopyData(b,4);
  return (uint32_t(b[0])<<24)|(uint32_t(b[1])<<16)|(uint32_t(b[2])<<8)|uint32_t(b[3]);
}
static Ptr<Packet> MakeSeqPacket(uint32_t seq){
  uint8_t b[80]={0};
  b[0]=(seq>>24)&0xff; b[1]=(seq>>16)&0xff; b[2]=(seq>>8)&0xff; b[3]=seq&0xff;
  return Create<Packet>(b,80);
}
static void SendHop(uint32_t from, uint32_t to, Ptr<Packet> p){
  g_hopTx++;
  g_main.Get(from)->Send(p, g_main.Get(to)->GetAddress(), 0x0800);
}
static bool ReceiveMain(uint32_t idx, Ptr<NetDevice> dev, Ptr<const Packet> p, uint16_t proto, const Address& from){
  uint32_t seq=ReadSeq(p);
  uint32_t sink=g_path.back();
  if(idx==sink){
    if(g_seen.insert(seq).second){
      g_received++;
      auto it=g_sentAt.find(seq);
      if(it!=g_sentAt.end()){
        double st=it->second; g_delaySum += Simulator::Now().GetSeconds()-st;
        if(st>=25.0 && st<55.0) g_burstRx++;
      }
    }
    return true;
  }
  auto it=g_next.find(idx);
  if(it!=g_next.end()){
    Ptr<Packet> cp=p->Copy();
    Simulator::Schedule(MilliSeconds(1.0), &SendHop, idx, it->second, cp);
  }
  return true;
}
static void Generate(uint32_t seq, double interval){
  double t=Simulator::Now().GetSeconds();
  g_generated++; g_sentAt[seq]=t;
  if(t>=25.0 && t<55.0) g_burstGen++;
  SendHop(g_path.front(), g_path[1], MakeSeqPacket(seq));
  if(t+interval<75.0) Simulator::Schedule(Seconds(interval), &Generate, seq+1, interval);
}
static void JamSend(double interval){
  Ptr<Packet> p=Create<Packet>(80);
  g_jam.Get(0)->Send(p, g_jam.Get(1)->GetAddress(), 0x0800);
  double t=Simulator::Now().GetSeconds();
  if(t+interval<55.0) Simulator::Schedule(Seconds(interval), &JamSend, interval);
}
int main(int argc,char** argv){
  uint32_t seed=1; bool risk=false; double jamInterval=0.006; double sourceInterval=0.10;
  double jamPower=-15.0; double riskY=16.0; double exponent=3.0;
  CommandLine cmd; cmd.AddValue("seed","run seed",seed); cmd.AddValue("risk","use peripheral risk-aware path",risk);
  cmd.AddValue("jamInterval","jammer packet interval",jamInterval); cmd.AddValue("sourceInterval","source interval",sourceInterval);
  cmd.AddValue("jamPower","jammer tx power dBm",jamPower); cmd.AddValue("riskY","risk path vertical offset",riskY);
  cmd.AddValue("exponent","log-distance exponent",exponent); cmd.Parse(argc,argv);
  RngSeedManager::SetSeed(12345); RngSeedManager::SetRun(seed);

  NodeContainer mainNodes; mainNodes.Create(8);
  NodeContainer jamNodes; jamNodes.Create(2);
  NodeContainer all; all.Add(mainNodes); all.Add(jamNodes);
  MobilityHelper mob; mob.SetMobilityModel("ns3::ConstantPositionMobilityModel"); mob.Install(all);
  std::vector<Vector> pos={
    Vector(-30,0,0), Vector(-15,0,0), Vector(0,0,0), Vector(15,0,0),
    Vector(-15,riskY,0), Vector(0,riskY+4.0,0), Vector(15,riskY,0), Vector(30,0,0)
  };
  for(uint32_t i=0;i<8;i++) mainNodes.Get(i)->GetObject<MobilityModel>()->SetPosition(pos[i]);
  jamNodes.Get(0)->GetObject<MobilityModel>()->SetPosition(Vector(0,4,0));
  jamNodes.Get(1)->GetObject<MobilityModel>()->SetPosition(Vector(0,6,0));

  LrWpanHelper h;
  h.AddPropagationLossModel("ns3::LogDistancePropagationLossModel","Exponent",DoubleValue(exponent));
  g_main=h.Install(mainNodes); g_jam=h.Install(jamNodes);
  h.CreateAssociatedPan(g_main,0x01); h.CreateAssociatedPan(g_jam,0x02);
  h.AssignStreams(g_main,1000+seed*20); h.AssignStreams(g_jam,2000+seed*20);

  ns3::lrwpan::LrWpanSpectrumValueHelper psd;
  DynamicCast<ns3::lrwpan::LrWpanNetDevice>(g_jam.Get(0))->GetPhy()->SetTxPowerSpectralDensity(psd.CreateTxPowerSpectralDensity(jamPower,11));
  DynamicCast<ns3::lrwpan::LrWpanNetDevice>(g_jam.Get(1))->GetPhy()->SetTxPowerSpectralDensity(psd.CreateTxPowerSpectralDensity(jamPower,11));

  g_path = risk ? std::vector<uint32_t>{0,4,5,6,7} : std::vector<uint32_t>{0,1,2,3,7};
  for(size_t i=0;i+1<g_path.size();i++) g_next[g_path[i]]=g_path[i+1];
  for(uint32_t i=0;i<8;i++) g_main.Get(i)->SetReceiveCallback(MakeBoundCallback(&ReceiveMain,i));

  Simulator::Schedule(Seconds(5.0), &Generate, 1u, sourceInterval);
  Simulator::Schedule(Seconds(25.0), &JamSend, jamInterval);
  Simulator::Stop(Seconds(g_stop)); Simulator::Run(); Simulator::Destroy();

  double pdr=g_generated?double(g_received)/g_generated:0.0;
  double bpdr=g_burstGen?double(g_burstRx)/g_burstGen:0.0;
  double delay=g_received?g_delaySum/g_received:0.0;
  std::cout<<seed<<","<<(risk?"RISK":"POINT")<<","<<g_generated<<","<<g_received<<","
           <<std::fixed<<std::setprecision(6)<<pdr<<","<<g_burstGen<<","<<g_burstRx<<","<<bpdr<<","<<delay<<","<<g_hopTx<<std::endl;
  return 0;
}
