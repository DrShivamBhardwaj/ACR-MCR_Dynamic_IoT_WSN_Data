#!/usr/bin/env python3
"""Choose 40 physically close Grenoble M3 source boards plus one sink.

Makes a deterministic static four-cluster *transport* topology, NOT the
original ACR-MCR algorithm. Alive availability != reservation entitlement;
a separate IoT-LAB scheduler preflight must succeed.
"""
import argparse,hashlib,json,math,re,subprocess
from pathlib import Path
KEY=re.compile(r"m3-(\d+)\.grenoble\.iot-lab\.info")
def dist(a,b):
    return math.sqrt(sum((float(a[k])-float(b[k]))**2 for k in ("x","y","z")))
def main():
    p=argparse.ArgumentParser();p.add_argument("--out",required=True)
    args=p.parse_args()
    cli=Path.home()/"Research/.iotlabcli-venv/bin/iotlab-status"
    raw=subprocess.check_output([str(cli),"--nodes","--site","grenoble",
        "--archi","m3","--state","Alive","--jmespath","items[*]"],text=True)
    docs=json.loads(raw)
    alive={int(m.group(1)):r for r in docs
        if (m:=KEY.fullmatch(r["network_address"])) and all(k in r for k in ("x","y","z"))}
    if len(alive)<41:raise RuntimeError(f"Only {len(alive)} M3 Alive entries")
    items=list(alive.items())
    def radius(pair):
        n,r=pair
        near=sorted((dist(r,other),o) for o,other in items if o!=n)
        return (near[39][0],sum(x[0] for x in near[:40]),n)
    sink_id,sink=min(items,key=radius)
    close=sorted(((dist(sink,r),n,r) for n,r in items if n!=sink_id))[:40]
    candidates=sorted(close,key=lambda item:(item[0],item[1]))
    head_list=candidates[:4]
    membership={i:[] for i in range(4)}
    for _,n,r in close:
        if n in {a[1] for a in head_list}:continue
        options=sorted(range(4),key=lambda i:(dist(r,head_list[i][2]),len(membership[i]),i))
        index=next(i for i in options if len(membership[i])<9)
        membership[index].append((n,r))
    logical={}
    for i,head in enumerate(head_list):
        base=1+i*10
        logical[str(base)]=dict(board=head[1],role="head",sink_board=sink_id,
                x=head[2]["x"],y=head[2]["y"],z=head[2]["z"])
        for j,(n,r) in enumerate(sorted(membership[i],key=lambda a:(dist(a[1],head[2]),a[0])),start=1):
            logical[str(base+j)]=dict(board=n,role="member",head_board=head[1],
                x=r["x"],y=r["y"],z=r["z"])
    assert len(logical)==40 and len({x["board"] for x in logical.values()})==40
    distances=[dist(alive[r["board"]],alive[r["head_board"]]) for r in logical.values() if r["role"]=="member"]
    manifest=dict(date="2026-11-22",testbed_site="Grenoble",platform="M3 AT86RF231",
      procedure="40 closest Alive boards to optimized sink; four nearest heads; 9 members each",
      independent_hardware_sources=40,sink_logical_id=41,sink_physical_board=sink_id,
      max_sink_to_source_distance_m=max(row[0] for row in close),
      max_member_to_head_distance_m=max(distances),
      nodes=logical,
      observational_limit="ALIVE does not prove a 41-board reservation is currently schedulable. This is STATIC fixed-head transport, not embedded ACR-MCR.")
    q=Path(args.out);q.parent.mkdir(exist_ok=True,parents=True)
    q.write_text(json.dumps(manifest,indent=2)+"\n")
    print(f"SELECTED Sink: M3-{sink_id}, 40 source nodes, radius={manifest['max_sink_to_source_distance_m']:.3f}m, max_member_head={max(distances):.3f}m")
    for i in (1,11,21,31):print("HEAD",i,"physical",logical[str(i)]["board"])
if __name__=="__main__":main()
