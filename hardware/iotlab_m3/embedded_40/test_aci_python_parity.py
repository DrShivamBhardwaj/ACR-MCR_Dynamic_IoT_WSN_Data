#!/usr/bin/env python3
"""Deterministic numerical parity test for original Python conformal update only."""
import ctypes,hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from acr_mcr_v2 import Calibrator,Config
class ACI(ctypes.Structure):
    _fields_=[
      ("alpha",ctypes.c_double*2),("q",ctypes.c_double*2),
      ("scores",(ctypes.c_double*2)*512),
      ("recent",(ctypes.c_double*2)*5),
      ("n_scores",ctypes.c_uint),("n_recent",ctypes.c_uint),
      ("mode",ctypes.c_uint)]
def main():
    dylib=HERE/"aci_calibrator.test.dylib"
    subprocess.run(["cc","-dynamiclib","-O2","-std=c11",
      str(HERE/"aci_calibrator.c"),"-o",str(dylib),"-lm"],check=True)
    lib=ctypes.CDLL(str(dylib))
    lib.acr_aci_init.argtypes=[ctypes.POINTER(ACI),ctypes.c_uint]
    lib.acr_aci_update.argtypes=[ctypes.POINTER(ACI),
      ctypes.POINTER(ctypes.c_double),ctypes.POINTER(ctypes.c_uint8),
      ctypes.c_uint,ctypes.c_uint]
    lib.acr_aci_alert.argtypes=[ctypes.POINTER(ACI)]
    lib.acr_aci_alert.restype=ctypes.c_int
    maxalpha=maxq=0.
    epochs=0
    modes=[("point",0),("adaptive",1),("frozen",2)]
    for mode,code in modes:
        py=Calibrator(Config(),mode)
        state=ACI();lib.acr_aci_init(ctypes.byref(state),code)
        rng=np.random.default_rng(773+code)
        for t in range(45):
            k=1+(t*7)%18
            scores=np.ascontiguousarray(np.abs(rng.normal(size=(k,2))),dtype=np.float64)
            covered=np.ascontiguousarray(rng.uniform(size=(k,2))<0.83,dtype=np.uint8)
            py.update(scores,covered.astype(bool),t)
            lib.acr_aci_update(ctypes.byref(state),
                scores.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                covered.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),k,t)
            da=float(np.max(np.abs(np.array(state.alpha[:])-py.alpha)))
            dq=float(np.max(np.abs(np.array(state.q[:])-py.q)))
            maxalpha=max(maxalpha,da);maxq=max(maxq,dq)
            if da>1e-10 or dq>1e-10 or int(py.alert())!=lib.acr_aci_alert(ctypes.byref(state)):
                raise AssertionError(f"Original Python/C calibrator mismatch: {mode}, round={t}, alpha={da}, q={dq}")
            epochs+=1
    report=dict(
        verdict="PASS",checked_modes=[m for m,_ in modes],
        total_matched_mode_rounds=epochs,max_alpha_error=maxalpha,max_quantile_error=maxq,
        original_source_sha256=hashlib.sha256((ROOT/"acr_mcr_v2.py").read_bytes()).hexdigest(),
        port_source_sha256=hashlib.sha256((HERE/"aci_calibrator.c").read_bytes()).hexdigest(),
        scientific_boundary="Only calibrator's score-window, quantile, alpha and alert; this is NOT the ACR-MCR head-selection optimizer on real M3 hardware.")
    (HERE/"aci_python_parity_result.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    dylib.unlink(missing_ok=True)
if __name__=="__main__":main()
