#!/usr/bin/env python3
"""Mechanical SRAM feasibility bounds for a literal 40-node Python state port.

Does not claim a streamed/quantized implementation is impossible.
"""
from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parents[1]
SRC=R/'acr_mcr_v2.py'
text=SRC.read_text()
SHA='3f134a8826525215f7cf2ff307bab3893c0d64b050f742bdc3c250b1c0302ea4'
assert hashlib.sha256(SRC.read_bytes()).hexdigest()==SHA
assert 'tail_samples: int = 64' in text
assert 'self.beta_a, self.beta_b = 4 * p0, 4 * (1 - p0)' in text
assert 'self.frame_hat = np.full((self.n, self.n + 1), 19.0)' in text
assert 'self.stress_c = np.clip(' in text and 'self.stress_d = np.maximum(' in text
n=40;edges=n*(n+1);samples=64;f64=8
bss=35760
ram=65536;flash=524288
fields=dict(
  beta_a=edges*f64,
  beta_b=edges*f64,
  frame_hat=edges*f64,
  cost_pred=edges*f64,
  delay_pred=edges*f64,
  edge_cost=edges*f64,
  stress_cost=samples*edges*f64,
  stress_delay=samples*edges*f64,
  calibrator_last_512_scores=512*2*f64)
minimal_original_double_live_predictor=fields['beta_a']+fields['beta_b']+fields['frame_hat']
paired_dense_stress=fields['stress_cost']+fields['stress_delay']
assert minimal_original_double_live_predictor+bss>ram
assert fields['stress_cost']>ram
assert paired_dense_stress>flash
obj=dict(
 source_sha256=SHA,sensors=n,sink_count=1,directed_edge_slots=edges,
 synthetic_tail_scenarios=samples,source_float_type='original NumPy float64 in Python',
 m3_sram_bytes=ram,m3_flash_bytes=flash,
 previously_compiled_frozen_kernel_BSS_plus_data_bytes=bss,
 byte_requirements=fields,
 naive_minimal_3_double_predictor_arrays_bytes=minimal_original_double_live_predictor,
 naive_predictor_plus_frozen_static_RAM_bytes=minimal_original_double_live_predictor+bss,
 naive_pair_dense_stress_bytes=paired_dense_stress,
 claim='Literal dense Python-style float64 state does not fit M3 64KB SRAM. A logically equivalent streamed/sparse, compressed or offloaded implementation may still be possible but requires its own parity and physical validation.',
 alternatives=[
   'Full feedback closed loop on connected host, with physical radio control and calibrated measurement; clearly label external optimizer, not embedded.',
   'Native M3 streamed exact-double risk terms and sparse link-state updates: requires carefully bounded stack/flash and independent Python/C parity; no result yet.',
   'Fixed-point/float32 quantization for predictor and compressed tail fields: changes numerical semantics and needs separate equivalence tolerances, failure cases and tests.'
 ],
 limit='This is a memory-footprint lower-bound check for naive layout, not a proof that any complete optimised native M3 port is impossible.'
)
out=R/'research_reconstruction/EMBEDDED_M3_MEMORY_FEASIBILITY_20261122.json'
out.write_text(json.dumps(obj,indent=2)+'\n')
print('PASS_MEMORY_BOUND',minimal_original_double_live_predictor+bss,'vs',ram,
      'one dense stress',fields['stress_cost'],'pair',paired_dense_stress)
