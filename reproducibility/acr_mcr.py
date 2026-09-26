import math
import heapq
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import numpy as np


@dataclass
class RadioModel:
    e_elec: float = 50e-9
    e_fs: float = 10e-12
    e_mp: float = 0.0013e-12
    e_da: float = 5e-9
    packet_bits: int = 4000

    @property
    def d0(self):
        return math.sqrt(self.e_fs / self.e_mp)

    def tx(self, d: float, bits: Optional[int] = None) -> float:
        b = self.packet_bits if bits is None else bits
        if d < self.d0:
            amp = self.e_fs * d * d
        else:
            amp = self.e_mp * d ** 4
        return b * (self.e_elec + amp)

    def rx(self, bits: Optional[int] = None) -> float:
        b = self.packet_bits if bits is None else bits
        return b * self.e_elec

    def da(self, bits: Optional[int] = None) -> float:
        b = self.packet_bits if bits is None else bits
        return b * self.e_da


class AdaptiveConformal:
    """Rolling absolute-residual conformal calibrator with ACI-style alpha update."""
    def __init__(self, alpha=0.10, window=200, gamma=0.01, adaptive=True, freeze_after=None):
        self.target_alpha = alpha
        self.alpha_t = alpha
        self.window = int(window)
        self.gamma = float(gamma)
        self.adaptive = bool(adaptive)
        self.freeze_after = freeze_after
        self.residuals: List[float] = []
        self.t = 0
        self.coverage_hist: List[int] = []
        self._q_cache = 0.20
        self._since_refresh = 0

    def q(self, force=False) -> float:
        if len(self.residuals) < 8:
            return 0.20
        if (not force) and self._since_refresh < 20:
            return float(self._q_cache)
        a = float(np.clip(self.alpha_t, 0.01, 0.35))
        n = len(self.residuals)
        level = min(1.0, math.ceil((n + 1) * (1 - a)) / n)
        try:
            qv = float(np.quantile(self.residuals, level, method="higher"))
        except TypeError:
            qv = float(np.quantile(self.residuals, level, interpolation="higher"))
        self._q_cache = qv
        self._since_refresh = 0
        return qv

    def interval(self, pred: float, lower=0.0, scale=1.0) -> Tuple[float, float]:
        q = self.q() * max(float(scale), 1e-12)
        return max(lower, pred - q), pred + q

    def update(self, pred: float, y: float, scale=1.0):
        self.t += 1
        scale = max(float(scale), 1e-12)
        q_before = self.q() * scale
        covered = int(abs(y - pred) <= q_before)
        self.coverage_hist.append(covered)
        frozen = self.freeze_after is not None and self.t > self.freeze_after
        if not frozen:
            self.residuals.append(abs(y - pred) / scale)
            if len(self.residuals) > self.window:
                self.residuals = self.residuals[-self.window:]
            self._since_refresh += 1
            if self.adaptive:
                err = 1 - covered
                self.alpha_t = float(np.clip(
                    self.alpha_t + self.gamma * (self.target_alpha - err), 0.01, 0.35
                ))

    def coverage(self, tail=200) -> float:
        if not self.coverage_hist:
            return float("nan")
        h = self.coverage_hist[-tail:]
        return float(np.mean(h))


@dataclass
class MethodConfig:
    name: str
    conformal: str  # none, static, adaptive
    use_cvar: bool
    event_trigger: bool
    periodic: int = 10
    max_period: int = 15
    min_gap: int = 3


METHODS = {
    "LEACH": MethodConfig("LEACH", "none", False, False, periodic=10),
    "POINT-EA": MethodConfig("POINT-EA", "none", False, False, periodic=10),
    "SCP-EA": MethodConfig("SCP-EA", "static", True, False, periodic=10),
    "ACP-EA": MethodConfig("ACP-EA", "adaptive", True, False, periodic=10),
    "ACR-NOCVAR": MethodConfig("ACR-NOCVAR", "adaptive", False, True, periodic=10, max_period=10, min_gap=5),
    "ACR-MCR": MethodConfig("ACR-MCR", "adaptive", True, True, periodic=10, max_period=10, min_gap=5),
}


class WSNSimulator:
    def __init__(self, n_nodes=60, area=100.0, rounds=140, seed=0, scenario="S0", method="ACR-MCR",
                 conformal_alpha=0.10, conformal_window=220, cvar_weight=0.10,
                 risk_gate_etx=2.4, k_frac=0.09, state_shift_interf=0.08,
                 state_shift_traffic=0.25):
        self.n = n_nodes
        self.area = float(area)
        self.rounds = int(rounds)
        self.rng_top = np.random.default_rng(seed)
        self.rng_env = np.random.default_rng(seed + 100_003)
        self.rng_opt = np.random.default_rng(seed + 200_003)
        self.seed = int(seed)
        self.scenario = scenario
        self.cfg = METHODS[method]
        self.method = method
        self.radio = RadioModel()
        self.conformal_alpha = float(conformal_alpha)
        self.conformal_window = int(conformal_window)
        self.cvar_weight = float(cvar_weight)
        self.risk_gate_etx = float(risk_gate_etx)
        self.state_shift_interf = float(state_shift_interf)
        self.state_shift_traffic = float(state_shift_traffic)
        self.pos = self.rng_top.uniform(0, self.area, size=(self.n, 2))
        self.sink = np.array([self.area / 2, self.area + 12.0])
        self.energy0 = self.rng_top.uniform(0.45, 0.55, size=self.n)
        self.energy = self.energy0.copy()
        self.dep_ewma = np.full(self.n, 0.00025)
        self.interf_est = 0.0
        self.traffic_est = 1.0
        self.last_chs: Optional[np.ndarray] = None
        self.last_opt = -999
        self.optimizer_calls = 0
        self.control_energy = 0.0
        self.etx_cal = self._make_calibrator(metric="etx")
        self.delay_cal = self._make_calibrator(metric="delay")
        self.dep_cal = self._make_calibrator(metric="dep")
        self.coverage_target = 0.90
        self.max_link_range = 78.0
        self.k_frac = float(k_frac)
        self.metrics = []
        self.failure_applied = False
        self.opt_interf_est = 0.0
        self.opt_traffic_est = 1.0

    def _make_calibrator(self, metric):
        if self.cfg.conformal == "none":
            return AdaptiveConformal(alpha=self.conformal_alpha, adaptive=False, freeze_after=0)
        if self.cfg.conformal == "static":
            return AdaptiveConformal(alpha=self.conformal_alpha, window=max(100, self.conformal_window), gamma=0.0, adaptive=False, freeze_after=max(100, self.conformal_window))
        # adaptive
        gamma = 0.008 if metric != "dep" else 0.004
        return AdaptiveConformal(alpha=self.conformal_alpha, window=self.conformal_window, gamma=gamma, adaptive=True)

    def scenario_state(self, t):
        x = t / max(1, self.rounds - 1)
        interf, traffic = 0.05, 1.0
        if self.scenario == "S1":
            interf = 0.05 + 0.55 * max(0, x - 0.30) / 0.70
        elif self.scenario == "S2":
            interf = 0.62 if 0.35 <= x <= 0.62 else 0.05
        elif self.scenario == "S3":
            traffic = 2.2 if x >= 0.48 else 1.0
            interf = 0.08
        elif self.scenario == "S4":
            interf = 0.10
        elif self.scenario == "S5":
            interf = 0.05 + 0.32 * max(0, x - 0.25) / 0.75
            if 0.35 <= x <= 0.52:
                interf += 0.35
            traffic = 2.0 if x >= 0.50 else 1.0
        return float(interf), float(traffic)

    def apply_correlated_failure(self, t):
        if self.failure_applied or self.scenario not in ("S4", "S5"):
            return
        if t < int(0.55 * self.rounds):
            return
        alive = np.where(self.energy > 0)[0]
        if len(alive) < 8:
            return
        center = self.rng_env.uniform(20, self.area - 20, size=2)
        d = np.linalg.norm(self.pos[alive] - center, axis=1)
        victims = alive[np.argsort(d)[: max(2, int(0.08 * self.n))]]
        self.energy[victims] = 0.0
        self.failure_applied = True

    def link_pred(self, i, j, traffic=None):
        a = self.pos[i]
        b = self.sink if j == self.n else self.pos[j]
        d = float(np.linalg.norm(a - b))
        p = math.exp(-0.50 * (d / 52.0) ** 2 - 0.95 * self.interf_est)
        p = float(np.clip(p, 0.18, 0.995))
        etx = 1.0 / p
        tr = self.traffic_est if traffic is None else traffic
        delay = 1.4 + 1.8 * (etx - 1.0) + 1.7 * tr
        return etx, delay, d

    def link_true(self, i, j, interf, traffic):
        a = self.pos[i]
        b = self.sink if j == self.n else self.pos[j]
        d = float(np.linalg.norm(a - b))
        shadow = self.rng_env.normal(0, 0.18)
        p = math.exp(-0.50 * (d / 52.0) ** 2 - 1.15 * interf + shadow)
        p = float(np.clip(p, 0.12, 0.995))
        etx = 1.0 / p
        queue = max(0.0, self.rng_env.normal(0.6 * traffic, 0.35))
        delay = 1.4 + 1.9 * (etx - 1.0) + 1.8 * traffic + queue
        return p, etx, delay, d

    def bounds(self, pred_etx, pred_delay):
        if self.cfg.conformal == "none":
            return pred_etx, pred_etx, pred_delay, pred_delay
        etx_scale = 0.15 + 0.35 * pred_etx
        delay_scale = 0.60 + 0.20 * pred_delay
        le, ue = self.etx_cal.interval(pred_etx, lower=1.0, scale=etx_scale)
        ld, ud = self.delay_cal.interval(pred_delay, lower=0.0, scale=delay_scale)
        return le, ue, ld, ud

    def energy_lower(self, i, horizon=5):
        if self.cfg.conformal == "none":
            q_dep = 0.0
        else:
            dep_scale = 5e-5 + 0.50 * self.dep_ewma[i]
            q_dep = self.dep_cal.q() * dep_scale
        return max(0.0, self.energy[i] - horizon * (self.dep_ewma[i] + q_dep))

    def _dijkstra(self, chs: np.ndarray, source: int, risk_aware=True):
        nodes = list(map(int, chs)) + [self.n]
        dist = {u: math.inf for u in nodes}
        prev = {}
        dist[source] = 0.0
        pq = [(0.0, source)]
        chset = set(map(int, chs))
        while pq:
            du, u = heapq.heappop(pq)
            if du != dist[u]:
                continue
            if u == self.n:
                break
            for v in nodes:
                if v == u or (v != self.n and v not in chset):
                    continue
                pu = self.pos[u]
                pv = self.sink if v == self.n else self.pos[v]
                d = float(np.linalg.norm(pu - pv))
                if d > self.max_link_range:
                    continue
                pe, pd, _ = self.link_pred(u, v)
                _, ue, _, ud = self.bounds(pe, pd)
                etx_used = ue if risk_aware and self.cfg.conformal != "none" else pe
                delay_used = ud if risk_aware and self.cfg.conformal != "none" else pd
                e_pen = 0.0
                if v != self.n:
                    el = self.energy_lower(v)
                    e_pen = 0.20 / max(0.03, el)
                if risk_aware and self.cfg.conformal != "none":
                    # Conformal risk gate: links with large upper ETX bounds are
                    # explicitly discouraged rather than receiving a cosmetic offset.
                    reliability_penalty = 0.45 * max(0.0, etx_used - self.risk_gate_etx)
                    w = 0.68 * etx_used + 0.20 * (delay_used / 8.0) + 0.12 * e_pen + reliability_penalty
                else:
                    w = 0.48 * etx_used + 0.28 * (delay_used / 8.0) + 0.24 * e_pen
                nd = du + w
                if nd < dist[v]:
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))
        if not math.isfinite(dist[self.n]):
            return None, math.inf
        path = [self.n]
        cur = self.n
        while cur != source:
            cur = prev[cur]
            path.append(cur)
        path.reverse()
        return path, dist[self.n]

    def assign_clusters(self, chs, risk_aware=True):
        alive = np.where(self.energy > 0)[0]
        chs = np.array([c for c in chs if self.energy[c] > 0], dtype=int)
        if len(chs) == 0:
            return {}, math.inf
        assigns = {int(c): [] for c in chs}
        total_cost = 0.0
        for i in alive:
            if i in assigns:
                assigns[int(i)].append(int(i))
                continue
            best, bestc = None, math.inf
            for c in chs:
                pe, pd, d = self.link_pred(int(i), int(c))
                _, ue, _, ud = self.bounds(pe, pd)
                etx_used = ue if risk_aware and self.cfg.conformal != "none" else pe
                delay_used = ud if risk_aware and self.cfg.conformal != "none" else pd
                ec = self.radio.tx(d) * etx_used
                if risk_aware and self.cfg.conformal != "none":
                    cst = ec / 0.001 + 0.42 * etx_used + 0.10 * delay_used + 0.35 * max(0.0, etx_used - self.risk_gate_etx)
                else:
                    cst = ec / 0.001 + 0.22 * etx_used + 0.08 * delay_used
                if cst < bestc:
                    bestc, best = cst, int(c)
            assigns[best].append(int(i))
            total_cost += bestc
        return assigns, total_cost

    def fitness(self, chs, stress):
        chs = np.unique(np.asarray(chs, dtype=int))
        if len(chs) == 0:
            return 1e9
        risk_aware = self.cfg.conformal != "none"
        assigns, _ = self.assign_clusters(chs, risk_aware=risk_aware)
        if not assigns:
            return 1e9
        energy_cost = 0.0
        delays, etxs = [], []
        etx_widths, delay_widths = [], []
        route_sum = 0.0
        for c, members in assigns.items():
            for i in members:
                if i == c:
                    continue
                pe, pd, d = self.link_pred(i, c)
                le, ue, ld, ud = self.bounds(pe, pd)
                eu = ue if risk_aware else pe
                du = ud if risk_aware else pd
                energy_cost += self.radio.tx(d) * eu + self.radio.rx() * eu
                delays.append(du); etxs.append(eu)
                if risk_aware:
                    etx_widths.append(max(0.0, ue-le))
                    delay_widths.append(max(0.0, ud-ld))
            energy_cost += len(members) * self.radio.da()
            path, rc = self._dijkstra(chs, c, risk_aware=risk_aware)
            if path is None:
                return 1e7 + 1e4 * len(chs)
            route_sum += rc
            for u, v in zip(path[:-1], path[1:]):
                pe, pd, d = self.link_pred(u, v)
                le, ue, ld, ud = self.bounds(pe, pd)
                eu = ue if risk_aware else pe
                energy_cost += self.radio.tx(d) * eu
                if v != self.n:
                    energy_cost += self.radio.rx() * eu
                delays.append(ud if risk_aware else pd); etxs.append(eu)
                if risk_aware:
                    etx_widths.append(max(0.0, ue-le))
                    delay_widths.append(max(0.0, ud-ld))

        e_norm = energy_cost / max(1e-6, 0.0013 * len(assigns))
        d_mean = float(np.mean(delays)) if delays else 0.0
        x_mean = float(np.mean(etxs)) if etxs else 1.0
        d_norm = d_mean / 10.0
        x_norm = x_mean / 4.0
        alive_e = self.energy[self.energy > 0]
        b_norm = float(np.std(alive_e) / max(1e-6, np.mean(alive_e)))
        r_norm = route_sum / max(1.0, 3.0 * len(chs))
        base = 0.32*e_norm + 0.16*d_norm + 0.15*x_norm + 0.12*b_norm + 0.15*r_norm

        if self.cfg.use_cvar:
            # Candidate-specific tail exposure. Unlike a simple rescaling of the
            # deterministic objective, these stress losses depend on each plan's
            # conformal interval widths, backbone fragility, and low-energy CHs.
            uw_etx = (float(np.mean(etx_widths)) / max(0.25, x_mean)) if etx_widths else 0.0
            uw_delay = (float(np.mean(delay_widths)) / max(1.0, d_mean)) if delay_widths else 0.0
            uncertainty_exposure = 0.55*uw_etx + 0.45*uw_delay
            ch_lowers = np.array([self.energy_lower(int(c), horizon=5) for c in chs], dtype=float)
            low_energy_exposure = float(np.mean(np.maximum(0.0, 0.18 - ch_lowers) / 0.18))
            route_fragility = 0.65*r_norm + 0.35*x_norm
            excess = (
                stress[:, 0] * (0.18*uncertainty_exposure + 0.04*x_norm) +
                stress[:, 1] * (0.12*route_fragility + 0.04*d_norm) +
                stress[:, 2] * (0.14*low_energy_exposure + 0.03*e_norm)
            )
            q = np.quantile(excess, 0.90)
            tail = excess[excess >= q]
            cvar_excess = float(np.mean(tail)) if len(tail) else float(q)
            base += self.cvar_weight * cvar_excess
        return float(base)

    def optimize_chs(self):
        alive = np.where(self.energy > 0)[0]
        if len(alive) <= 2:
            return alive.copy()
        k = max(2, min(len(alive), int(round(self.k_frac * len(alive)))))
        pop_size, gens = 6, 4
        # Higher residual energy and spatial spread are preferred in seeding.
        probs = self.energy[alive].copy()
        probs = np.maximum(probs, 1e-6); probs /= probs.sum()
        pop = []
        for _ in range(pop_size):
            pop.append(np.sort(self.rng_opt.choice(alive, size=k, replace=False, p=probs)))
        if self.last_chs is not None:
            keep = np.array([c for c in self.last_chs if c in set(alive)], dtype=int)
            if len(keep) >= k:
                pop[0] = np.sort(keep[:k])
        stress = np.abs(self.rng_opt.normal(0, 1, size=(8,3)))
        fit = np.array([self.fitness(x, stress) for x in pop])
        for _ in range(gens):
            order = np.argsort(fit)
            elites = [pop[i].copy() for i in order[:3]]
            new_pop = elites[:]
            while len(new_pop) < pop_size:
                p = pop[int(self.rng_opt.choice(order[:6]))].copy()
                child = set(map(int, p))
                swaps = 1 if self.rng_opt.random() < 0.8 else 2
                for _s in range(swaps):
                    if child:
                        child.remove(int(self.rng_opt.choice(list(child))))
                    avail = np.array([a for a in alive if a not in child], dtype=int)
                    if len(avail):
                        weights = self.energy[avail].copy(); weights=np.maximum(weights,1e-6); weights/=weights.sum()
                        child.add(int(self.rng_opt.choice(avail, p=weights)))
                while len(child) < k:
                    avail = [a for a in alive if a not in child]
                    child.add(int(self.rng_opt.choice(avail)))
                new_pop.append(np.array(sorted(child), dtype=int))
            pop = new_pop
            fit = np.array([self.fitness(x, stress) for x in pop])
        return pop[int(np.argmin(fit))]

    def risk_trigger(self, t):
        if self.last_chs is None:
            return True
        gap = t - self.last_opt
        if gap < self.cfg.min_gap:
            return False
        if gap >= self.cfg.max_period:
            return True
        if t < 18:
            return gap >= self.cfg.periodic
        q_e = self.etx_cal.q(); q_d = self.delay_cal.q(); q_dep = self.dep_cal.q()
        cov_e = self.etx_cal.coverage(100); cov_d = self.delay_cal.coverage(100)
        state_shift = (abs(self.interf_est - self.opt_interf_est) > self.state_shift_interf or
                       abs(self.traffic_est - self.opt_traffic_est) > self.state_shift_traffic)
        uncertainty_spike = (q_e > 1.25) or (q_d > 4.5) or (q_dep > 1.8)
        coverage_bad = ((not math.isnan(cov_e) and cov_e < 0.76) or (not math.isnan(cov_d) and cov_d < 0.76))
        calibration_alert = uncertainty_spike and coverage_bad
        if state_shift:
            return True
        if gap >= self.cfg.periodic and calibration_alert:
            return True
        return False

    def choose_chs(self, t):
        alive = np.where(self.energy > 0)[0]
        if len(alive) <= 2:
            return alive.copy()
        k = max(2, min(len(alive), int(round(self.k_frac * len(alive)))))
        if self.method == "LEACH":
            if self.last_chs is None or t - self.last_opt >= self.cfg.periodic:
                p = self.energy[alive].copy(); p=np.maximum(p,1e-6); p/=p.sum()
                self.last_chs = np.sort(self.rng_opt.choice(alive, size=k, replace=False, p=p))
                self.last_opt = t; self.optimizer_calls += 1
            return self.last_chs
        do_opt = False
        if self.cfg.event_trigger:
            do_opt = self.risk_trigger(t)
        else:
            do_opt = self.last_chs is None or t - self.last_opt >= self.cfg.periodic
        if do_opt:
            candidate = self.optimize_chs()
            # Hysteretic plan acceptance for the full framework: an emergency
            # re-optimization is committed only if it is not worse than the
            # currently active plan under the same risk audit. This prevents
            # stochastic optimizer churn during short-lived shifts.
            if self.method == "ACR-MCR" and self.last_chs is not None:
                current = np.array([c for c in self.last_chs if self.energy[c] > 0], dtype=int)
                if len(current) > 0:
                    audit_stress = np.abs(self.rng_opt.normal(0, 1, size=(8,3)))
                    f_old = self.fitness(current, audit_stress)
                    f_new = self.fitness(candidate, audit_stress)
                    if f_new <= 1.005 * f_old:
                        self.last_chs = candidate
                else:
                    self.last_chs = candidate
            else:
                self.last_chs = candidate
            self.last_opt = t; self.optimizer_calls += 1
            self.opt_interf_est = self.interf_est
            self.opt_traffic_est = self.traffic_est
            # optimization/control signalling overhead
            ctrl = 18 * self.radio.packet_bits // 8
            self.control_energy += ctrl * 8 * self.radio.e_elec * max(1, len(alive)) / 20
        return np.array([c for c in self.last_chs if self.energy[c] > 0], dtype=int)

    def transmit_attempts(self, p):
        # capped ARQ (max 4 attempts)
        for a in range(1,5):
            if self.rng_env.random() < p:
                return a, True
        return 4, False

    def execute_round(self, t, chs, interf, traffic):
        before = self.energy.copy()
        assigns, _ = self.assign_clusters(chs, risk_aware=(self.cfg.conformal != "none"))
        generated = 0; delivered = 0; delays = []
        observed_links = []
        ch_payload = {}
        member_ok = {}
        for c, members in assigns.items():
            ch_payload[c] = 0
            member_ok[c] = []
            for i in members:
                if self.energy[i] <= 0:
                    continue
                generated += 1
                if i == c:
                    member_ok[c].append(i); ch_payload[c] += 1
                    continue
                p, etx, dly, d = self.link_true(i, c, interf, traffic)
                pe, pd, _ = self.link_pred(i, c)
                att, ok = self.transmit_attempts(p)
                self.energy[i] -= self.radio.tx(d) * att * traffic
                self.energy[c] -= self.radio.rx() * att * traffic
                observed_links.append((pe, etx, pd, dly))
                if ok:
                    member_ok[c].append(i); ch_payload[c] += 1
            self.energy[c] -= self.radio.da() * max(1, ch_payload[c]) * min(traffic, 2.2)
        # route one aggregate packet per CH; successful route delivers all successful member samples in that cluster.
        for c in list(assigns.keys()):
            if self.energy[c] <= 0 or ch_payload.get(c,0) == 0:
                continue
            path, _ = self._dijkstra(np.array(list(assigns.keys()), dtype=int), c, risk_aware=(self.cfg.conformal != "none"))
            if path is None:
                continue
            route_ok = True; route_delay = 0.0
            for u, v in zip(path[:-1], path[1:]):
                if u != self.n and self.energy[u] <= 0:
                    route_ok=False; break
                p, etx, dly, d = self.link_true(u, v, interf, traffic)
                pe, pd, _ = self.link_pred(u, v)
                att, ok = self.transmit_attempts(p)
                self.energy[u] -= self.radio.tx(d) * att * min(traffic,2.2)
                if v != self.n:
                    self.energy[v] -= self.radio.rx() * att * min(traffic,2.2)
                route_delay += dly * att
                observed_links.append((pe, etx, pd, dly))
                if not ok:
                    route_ok=False; break
            if route_ok:
                delivered += len(member_ok[c])
                delays.extend([route_delay] * len(member_ok[c]))
        self.energy = np.maximum(self.energy, 0.0)
        dep = np.maximum(0.0, before - self.energy)
        # Update calibrators from actual observations.
        for pe, etx, pd, dly in observed_links:
            if self.cfg.conformal != "none":
                self.etx_cal.update(pe, etx, scale=0.15 + 0.35 * pe)
                self.delay_cal.update(pd, dly, scale=0.60 + 0.20 * pd)
        for i in np.where(before > 0)[0]:
            pred = float(self.dep_ewma[i])
            if self.cfg.conformal != "none":
                self.dep_cal.update(pred, float(dep[i]), scale=5e-5 + 0.50 * pred)
            self.dep_ewma[i] = 0.82*self.dep_ewma[i] + 0.18*dep[i]
        pdr = delivered / generated if generated else 0.0
        delay = float(np.mean(delays)) if delays else 50.0
        return generated, delivered, pdr, delay, float(dep.sum())

    def run(self):
        initial_total = float(self.energy.sum())
        fnd = None; hnd = None; lnd = None
        for t in range(self.rounds):
            self.apply_correlated_failure(t)
            alive0 = int(np.sum(self.energy > 0))
            if alive0 == 0:
                if lnd is None: lnd = t
                break
            interf, traffic = self.scenario_state(t)
            # Predictor adapts with lag; this deliberately creates non-stationary residuals.
            self.interf_est = 0.88*self.interf_est + 0.12*interf
            self.traffic_est = 0.90*self.traffic_est + 0.10*traffic
            chs = self.choose_chs(t)
            gen, dele, pdr, delay, dep = self.execute_round(t, chs, interf, traffic)
            alive = int(np.sum(self.energy > 0))
            if fnd is None and alive < self.n: fnd = t+1
            if hnd is None and alive <= self.n/2: hnd = t+1
            if lnd is None and alive == 0: lnd = t+1
            risk_violation = int(pdr < 0.80 or delay > 25.0)
            self.metrics.append({
                "round": t+1, "alive": alive, "generated": gen, "delivered": dele,
                "pdr": pdr, "delay": delay, "energy_dep": dep,
                "risk_violation": risk_violation,
                "etx_coverage": self.etx_cal.coverage(200),
                "delay_coverage": self.delay_cal.coverage(200),
                "q_etx": self.etx_cal.q(), "q_delay": self.delay_cal.q(),
            })
        total_gen = sum(m["generated"] for m in self.metrics)
        total_del = sum(m["delivered"] for m in self.metrics)
        valid_delays = [m["delay"] for m in self.metrics if m["delay"] < 50]
        final_total = float(self.energy.sum())
        return {
            "method": self.method, "scenario": self.scenario, "seed": self.seed,
            "rounds_completed": len(self.metrics),
            "PDR": total_del / total_gen if total_gen else 0.0,
            "mean_delay": float(np.mean(valid_delays)) if valid_delays else 50.0,
            "energy_consumed": initial_total - final_total + self.control_energy,
            "final_alive": int(np.sum(self.energy > 0)),
            "FND": fnd if fnd is not None else self.rounds+1,
            "HND": hnd if hnd is not None else self.rounds+1,
            "LND": lnd if lnd is not None else self.rounds+1,
            "risk_violation_rate": float(np.mean([m["risk_violation"] for m in self.metrics])) if self.metrics else 1.0,
            "optimizer_calls": self.optimizer_calls,
            "etx_coverage": self.etx_cal.coverage(500),
            "delay_coverage": self.delay_cal.coverage(500),
            "control_energy": self.control_energy,
        }
