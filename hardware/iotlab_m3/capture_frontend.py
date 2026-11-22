#!/usr/bin/env python3
"""Capture actual M3 serial logs on IoT-LAB Saclay frontend for one owned run."""
import asyncio,json,re,sys,time
from pathlib import Path
exp=sys.argv[1]
out=Path.home()/"acr_phy_m3"/exp
out.mkdir(parents=True,exist_ok=False)
nodeids=(14,15)
log={n:[] for n in nodeids}
complete=0
finished=False
start=time.monotonic()
async def pump(node):
    global complete,finished
    reader,writer=await asyncio.open_connection(f"m3-{node}.saclay.iot-lab.info",20000)
    with (out/f"m3-{node}.serial.log").open("wb") as f:
        while time.monotonic()-start<190:
            try:line=await asyncio.wait_for(reader.readline(),timeout=3)
            except asyncio.TimeoutError:continue
            if not line:break
            f.write(line);f.flush()
            s=line.decode("utf-8","replace").strip()
            if "ACR_" in s:log[node].append(s)
            if node==2 and "ACR_REASSEMBLED" in s and "integrity=1" in s:
                complete+=1
            if node==1 and "ACR_TX_COMPLETE" in s:finished=True
    writer.close()
    await writer.wait_closed()
async def main():
    global complete
    error=None
    tasks=[asyncio.create_task(pump(n)) for n in nodeids]
    try:
        while time.monotonic()-start<190:
            await asyncio.sleep(2)
            if finished:
                await asyncio.sleep(10)
                break
            if all(t.done() for t in tasks):break
    except Exception as e:
        error=repr(e)
    finally:
        for t in tasks:
            if not t.done():t.cancel()
        results=await asyncio.gather(*tasks,return_exceptions=True)
        for x in results:
            if isinstance(x,Exception) and not isinstance(x,asyncio.CancelledError):
                error=repr(x)
    for n in nodeids:
        (out/f"m3-{n}.parsed.log").write_text("\n".join(log[n])+"\n")
    def lines(n,tag):
        return [s for s in log[n] if tag in s]
    tx=lines(1,"ACR_TX seq=")
    callbacks=lines(1,"ACR_MAC seq=")
    rx=lines(2,"ACR_RX seq=")
    verified=lines(2,"ACR_REASSEMBLED")
    source_completed=lines(1,"ACR_TX_COMPLETE")
    summary=dict(
      experiment=exp,physically_measured=True,
      platform="FIT IoT-LAB Grenoble M3 / AT86RF231",
      nodes=["m3-14","m3-15"],serial_port=20000,
      planned_application_samples=100,bytes_per_application_sample=500,parts_per_sample=8,
      observed_sender_frames=len(tx),observed_sender_callbacks=len(callbacks),
      observed_receiver_fragments=len(rx),
      observed_full_500byte_samples=len(verified),
      verified_integrity_pass_count=sum("integrity=1" in s for s in verified),
      sender_completed=bool(source_completed),
      raw_radio_registers_calibrated_as_dBm=False,
      SNR_established=False,
      packet_loss_inference_allowed=bool(source_completed),
      source_role_energest_records=len(lines(1,"ACR_ENERGEST")),
      receiver_role_energest_records=len(lines(2,"ACR_ENERGEST")),
      error=error,
      elapsed_seconds=time.monotonic()-start)
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2),flush=True)
    if error or not source_completed:
        raise SystemExit("Physical run incomplete; preserve logs but not interpret as confirmation")
asyncio.run(main())
