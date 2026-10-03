"""ACR-MCR revision: observable telemetry and transaction-level accounting.

This is a synthetic, scheduled, half-duplex network model, not an ns-3/PHY
implementation. See PROTOCOL.md and MODEL.md for its deliberate abstractions.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib
import math
import time
import numpy as np

MASK = (1 << 64) - 1


def keyed_uniform(seed, round_id, purpose, source, packet, u, v, attempt):
    """A random field, indexed by logical event rather than execution order."""
    x = int(seed) & MASK
    for z in (round_id, purpose, source, packet, u, v, attempt):
        x = (x ^ (int(z) + 0x9E3779B97F4A7C15 + (x << 6) + (x >> 2))) & MASK
    x = (x + 0x9E3779B97F4A7C15) & MASK
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & MASK
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & MASK
    x ^= x >> 31
    return ((x >> 11) + 0.5) / (1 << 53)


def rng_for(seed, purpose, round_id=0):
    return np.random.default_rng(np.random.SeedSequence([int(seed), purpose, round_id]))


def empirical_cvar(losses, beta=0.9):
    """Exact upper expected shortfall of an equally weighted empirical law."""
    x = np.sort(np.asarray(losses, float))[::-1]
    mass = len(x) * (1.0 - beta)
    k = int(math.floor(mass + 1e-12))
    fraction = mass - k
    total = float(x[:k].sum())
    if fraction > 1e-12:
        total += fraction * x[k]
    return total / mass


@dataclass(frozen=True)
class Config:
    nodes: int = 40
    rounds: int = 160
    warmup: int = 20
    area: float = 100.0
    radio_range: float = 78.0
    probes: int = 1
    deadline_ms: float = 500.0
    target_alpha: float = 0.10
    window: int = 512
    gamma: float = 0.03
    periodic: int = 10
    min_gap: int = 3
    max_period: int = 10
    coverage_alert: float = 0.78
    population: int = 8
    generations: int = 4
    improvement: float = 0.005
    head_fraction: float = 0.10
    fixed_heads: int = 0
    tail_samples: int = 64
    tail_weight: float = 0.15
    tail_beta: float = 0.90


METHODS = {
    'RANDOM-CH': ('point', False, False, True),
    'POINT-EA': ('point', False, False, False),
    'FROZEN-CP': ('frozen', False, False, False),
    'ROLL-CP': ('rolling', False, False, False),
    'ACI-PER': ('adaptive', False, False, False),
    'ACI-EVENT': ('adaptive', True, False, False),
    'ACR-MCR': ('adaptive', True, True, False),
}


class Calibrator:
    def __init__(self, cfg, mode):
        self.cfg, self.mode = cfg, mode
        self.alpha = np.full(2, cfg.target_alpha)
        self.scores = np.empty((0, 2))
        self.q = np.full(2, 1.28)
        self.recent_coverage = []

    def update(self, scores, covered, t):
        if not len(scores):
            return
        self.recent_coverage.append(np.mean(covered, axis=0))
        self.recent_coverage = self.recent_coverage[-5:]
        if self.mode == 'frozen' and t >= self.cfg.warmup:
            return
        self.scores = np.concatenate((self.scores, scores), axis=0)[-self.cfg.window:]
        if self.mode == 'adaptive' and t >= self.cfg.warmup:
            error = 1.0 - np.mean(covered, axis=0)
            self.alpha = np.clip(self.alpha + self.cfg.gamma * (self.cfg.target_alpha - error), .02, .40)
        n = len(self.scores)
        for j in range(2):
            rank = min(n, max(1, math.ceil((n + 1) * (1 - self.alpha[j]))))
            self.q[j] = max(0.0, np.partition(self.scores[:, j], rank - 1)[rank - 1])

    def alert(self):
        return len(self.recent_coverage) >= 3 and np.min(np.mean(self.recent_coverage[-3:], axis=0)) < self.cfg.coverage_alert


@dataclass
class Plan:
    heads: np.ndarray
    assigned: np.ndarray
    paths: dict
    costs: np.ndarray
    fitness: float = math.inf


class Simulator:
    packet_bits = 4000
    ack_bits = 64
    control_bits = 256
    e_elec = 50e-9
    e_fs = 10e-12
    e_mp = .0013e-12
    e_da = 5e-9
    min_energy = .00021

    def __init__(self, seed=1000, scenario='S1', method='ACR-MCR', cfg=None, diagnostics=False):
        self.cfg = cfg or Config()
        self.seed, self.scenario, self.method = int(seed), scenario, method
        self.mode, self.event, self.tail, self.random_heads = METHODS[method]
        self.n = self.cfg.nodes
        r = rng_for(seed, 11)
        self.pos = r.uniform(0, self.cfg.area, (self.n, 2))
        self.sink = np.array([self.cfg.area / 2, self.cfg.area + 12])
        self.energy0 = r.uniform(.45, .55, self.n)
        self.energy = self.energy0.copy()
        self.disabled = np.zeros(self.n, bool)
        allpos = np.vstack((self.pos, self.sink))
        self.distance = np.linalg.norm(self.pos[:, None] - allpos[None, :], axis=2)
        self.feasible = (self.distance <= self.cfg.radio_range) & (self.distance > 0)
        self.tx_energy = self.radio_tx(self.distance, self.packet_bits)
        p0 = np.clip(np.exp(-.5 * (self.distance / 52) ** 2), .1, .99)
        self.beta_a, self.beta_b = 4 * p0, 4 * (1 - p0)
        self.frame_hat = np.full((self.n, self.n + 1), 19.0)
        self.cal = Calibrator(self.cfg, self.mode)
        self.ledger = dict(data=0.0, probe=0.0, control=0.0, aggregation=0.0)
        self.failure_stored = 0.0
        self.rows, self.link_logs = [], []
        self.diagnostics = diagnostics
        self.heads = None
        self.last_search = -10000
        self.searches = self.accepted_changes = self.fitness_calls = 0
        self.controller_seconds = 0.0
        self.trigger_counts = dict(initial=0, periodic=0, coverage=0, failure=0)
        self.failure_done = False
        self.failure_center = rng_for(seed, 22).uniform(20, self.cfg.area - 20, 2)
        d = np.linalg.norm(self.pos - self.failure_center, axis=1)
        self.failure_nodes = np.argsort(d)[:max(2, int(.08 * self.n))]
        midpoint = (self.pos[:, None] + allpos[None, :]) / 2
        self.hotspot = np.exp(-np.sum((midpoint - np.array([50, 60])) ** 2, axis=2) / (2 * 27**2))

    @classmethod
    def radio_tx(cls, distance, bits):
        d0 = math.sqrt(cls.e_fs / cls.e_mp)
        d = np.asarray(distance)
        return bits * (cls.e_elec + np.where(d < d0, cls.e_fs * d*d, cls.e_mp * d**4))

    def alive(self):
        return (~self.disabled) & (self.energy >= self.min_energy)

    def state(self, t):
        x = t / max(1, self.cfg.rounds - 1)
        interference, load = .05, 1
        if self.scenario == 'S1':
            interference += .55 * max(0, x - .30) / .70
        elif self.scenario == 'S2':
            interference = .65 if .35 <= x <= .62 else .05
        elif self.scenario == 'S3':
            interference, load = .08, 2 if x >= .48 else 1
        elif self.scenario == 'S4':
            interference = .10
        elif self.scenario == 'S5':
            interference += .32 * max(0, x - .25) / .75 + (.35 if .35 <= x <= .52 else 0)
            load = 2 if x >= .50 else 1
        return interference, load

    def fail_nodes(self, t):
        if self.scenario in ('S4', 'S5') and not self.failure_done and t >= int(.55 * self.cfg.rounds):
            self.failure_stored = float(self.energy[self.failure_nodes].sum())
            self.disabled[self.failure_nodes] = True
            self.failure_done = True

    def environment(self, t):
        interference, self.load = self.state(t)
        shadow = rng_for(self.seed, 31, t).normal(0, .18, self.distance.shape)
        self.env_p = np.clip(np.exp(-.5 * (self.distance / 52)**2 - interference * (.5 + 1.3*self.hotspot) + shadow), .08, .995)
        backoff = np.clip(rng_for(self.seed, 32, t).normal(2*self.load, .8, self.distance.shape), .1, 10)
        self.env_frame = self.packet_bits / 250.0 + 1.0 + backoff + 4*interference*self.hotspot
        self.env_fingerprint = hashlib.sha256(self.env_p.tobytes() + self.env_frame.tobytes()).hexdigest()[:16]

    def predictions(self, t):
        self.p_hat = self.beta_a / (self.beta_a + self.beta_b)
        q = 1 - self.p_hat
        self.attempt_mean = 1 + q + q*q + q**3
        self.cost_pred = self.attempt_mean + q**4
        c2 = sum(k*k*self.p_hat*q**(k-1) for k in range(1, 5)) + 25*q**4
        a2 = sum(k*k*self.p_hat*q**(k-1) for k in range(1, 4)) + 16*q**3
        self.cost_scale = np.maximum(.35, np.sqrt(np.maximum(0, c2 - self.cost_pred**2)))
        self.delay_pred = self.attempt_mean * self.frame_hat
        self.delay_scale = np.maximum(4, self.frame_hat * np.sqrt(np.maximum(0, a2 - self.attempt_mean**2)))
        self.upper_c = np.minimum(5.0, self.cost_pred + self.cal.q[0]*self.cost_scale)
        self.upper_d = self.delay_pred + self.cal.q[1]*self.delay_scale
        use_bounds = self.mode != 'point' and t >= self.cfg.warmup
        self.c_used = self.upper_c if use_bounds else self.cost_pred
        self.d_used = self.upper_d if use_bounds else self.delay_pred
        receiver_penalty = np.r_[.5 / np.maximum(self.energy, .03), 0.0][None, :]
        self.edge_cost = (.50*self.c_used + .20*self.d_used/50 +
                          .15*self.tx_energy*self.attempt_mean/.0004 + .15*receiver_penalty +
                          .40*np.maximum(0, self.c_used - 2.4))
        valid = self.feasible & self.alive()[:, None] & np.r_[self.alive(), True][None, :]
        self.edge_cost = np.where(valid, self.edge_cost, np.inf)
        self.active = np.where(self.alive())[0]
        self.stress_c = self.stress_d = None

    def stress_fields(self, t):
        if not self.tail or t < self.cfg.warmup or len(self.cal.scores) < 8:
            return
        r = rng_for(self.seed, 41, t)
        ids = r.integers(0, len(self.cal.scores), (self.cfg.tail_samples, self.n, self.n+1))
        errors = self.cal.scores[ids]
        self.stress_c = np.clip(self.cost_pred[None] + self.cost_scale[None]*errors[..., 0], 1, 5)
        self.stress_d = np.maximum(1, self.delay_pred[None] + self.delay_scale[None]*errors[..., 1])

    def make_plan(self, heads):
        heads = np.asarray(sorted(set(map(int, heads))), int)
        if not len(heads):
            return Plan(heads, np.full(self.n, -1), {}, np.full(self.n, np.inf), 1e6)
        nodes = np.r_[heads, self.n]
        k = len(heads)
        dist = np.full((k+1, k+1), np.inf)
        dist[:k] = self.edge_cost[np.ix_(heads, nodes)]
        np.fill_diagonal(dist, 0)
        nxt = np.tile(np.arange(k+1), (k+1, 1))
        for z in range(k+1):
            trial = dist[:, z, None] + dist[None, z, :]
            mask = trial < dist
            dist = np.minimum(dist, trial)
            nxt = np.where(mask, nxt[:, z, None], nxt)
        paths = {}
        for a, c in enumerate(heads):
            if not np.isfinite(dist[a, k]):
                continue
            path, cur = [int(c)], a
            for _ in range(k+1):
                cur = int(nxt[cur, k]); path.append(int(nodes[cur]))
                if cur == k:
                    paths[int(c)] = path; break
        assignment_cost = self.edge_cost[:, heads] + .30*dist[:k, k][None, :]
        for a, c in enumerate(heads):
            assignment_cost[c, :] = np.inf
            assignment_cost[c, a] = .30*dist[a, k]
        best = np.argmin(assignment_cost, axis=1)
        costs = assignment_cost[np.arange(self.n), best]
        assigned = np.where(np.isfinite(costs) & self.alive(), heads[best], -1)
        return Plan(heads, assigned, paths, costs)

    def fitness(self, plan):
        self.fitness_calls += 1
        nlive = max(1, len(self.active))
        unserved = np.sum(plan.assigned[self.active] < 0) / nlive
        depletion = np.zeros(self.n)
        prediction_delay, route_cost = [], []
        losses = np.ones((self.cfg.tail_samples, self.n)) if self.stress_c is not None else None
        for c in plan.heads:
            c = int(c)
            if c not in plan.paths:
                continue
            members = np.where(plan.assigned == c)[0]
            ordinary = members[members != c]
            a = self.attempt_mean[ordinary, c]
            depletion[ordinary] += self.load*(self.tx_energy[ordinary, c]*a + self.ack_bits*self.e_elec)
            depletion[c] += self.load*(self.packet_bits*self.e_elec*a.sum() + self.radio_tx(self.distance[ordinary, c], self.ack_bits).sum())
            depletion[c] += len(members)*self.load*self.packet_bits*self.e_da
            collection = float(self.d_used[ordinary, c].sum())*self.load + 2.0
            path = plan.paths[c]
            rd, rc = 0.0, 0.0
            for u, v in zip(path[:-1], path[1:]):
                at = self.attempt_mean[u, v]
                depletion[u] += self.tx_energy[u, v]*at + self.ack_bits*self.e_elec
                if v < self.n:
                    depletion[v] += self.packet_bits*self.e_elec*at + self.radio_tx(self.distance[u, v], self.ack_bits)
                rd += self.d_used[u, v]; rc += self.edge_cost[u, v]
            prediction_delay.extend([collection + rd]*len(members))
            route_cost.extend([rc]*len(members))
            if losses is not None:
                collection_s = self.stress_d[:, ordinary, c].sum(axis=1)*self.load + 2
                path_d = np.zeros(self.cfg.tail_samples)
                path_ok = np.ones(self.cfg.tail_samples, bool)
                for u, v in zip(path[:-1], path[1:]):
                    path_d += self.stress_d[:, u, v]
                    path_ok &= self.stress_c[:, u, v] < 4.5
                timely = path_ok & (collection_s + path_d <= self.cfg.deadline_ms)
                losses[:, c] = 1 - timely
                if len(ordinary):
                    losses[:, ordinary] = 1 - (timely[:, None] & (self.stress_c[:, ordinary, c] < 4.5))
        post = np.maximum(0, self.energy[self.active] - depletion[self.active])
        cv = float(np.std(post)/max(1e-8, np.mean(post))) if len(post) else 1
        peak = float(np.max(depletion[self.active]/np.maximum(self.energy[self.active], .03))) if len(post) else 1
        energy = depletion.sum()/(.001*nlive)
        delay = np.mean(prediction_delay)/self.cfg.deadline_ms if prediction_delay else 2
        route = np.mean(route_cost)/10 if route_cost else 5
        score = .32*energy + .24*delay + .20*route + .12*cv + .12*peak + 10*unserved
        if losses is not None:
            score += self.cfg.tail_weight*empirical_cvar(losses[:, self.active].mean(axis=1), self.cfg.tail_beta)
        plan.fitness = float(score)
        return plan.fitness

    def trigger(self, t):
        if self.heads is None:
            return 'initial'
        if any(not self.alive()[c] for c in self.heads):
            return 'failure'
        gap = t - self.last_search
        if gap >= self.cfg.max_period:
            return 'periodic'
        if self.event and gap >= self.cfg.min_gap and t >= self.cfg.warmup and self.cal.alert():
            return 'coverage'
        return None

    def select(self, t):
        start = time.perf_counter()
        reason = self.trigger(t)
        if reason and len(self.active):
            k = min(len(self.active), self.cfg.fixed_heads or max(2, int(round(self.cfg.head_fraction*len(self.active)))))
            r = rng_for(self.seed, 51, t)
            prob = self.energy[self.active]/self.energy[self.active].sum()
            candidate = np.sort(r.choice(self.active, k, replace=False, p=prob))
            self.stress_fields(t)
            if not self.random_heads:
                candidates = [candidate]
                for _ in range(self.cfg.population-1):
                    candidates.append(np.sort(r.choice(self.active, k, replace=False, p=prob)))
                if self.heads is not None and len(self.heads) == k and all(self.alive()[self.heads]):
                    candidates[0] = self.heads.copy()
                plans = [self.make_plan(h) for h in candidates]
                for p in plans: self.fitness(p)
                for _ in range(self.cfg.generations):
                    plans.sort(key=lambda p: (p.fitness, tuple(p.heads)))
                    new = plans[:2]
                    while len(new) < self.cfg.population:
                        parent = plans[int(r.integers(0, max(2, self.cfg.population//2)))].heads.copy()
                        replace = int(r.integers(0, k))
                        pool = self.active[~np.isin(self.active, parent)]
                        if len(pool): parent[replace] = r.choice(pool)
                        child = self.make_plan(parent)
                        self.fitness(child); new.append(child)
                    plans = new
                best = min(plans, key=lambda p: (p.fitness, tuple(p.heads)))
                candidate = best.heads
                if self.heads is not None and reason != 'failure':
                    incumbent = self.make_plan(self.heads)
                    self.fitness(incumbent)
                    if best.fitness > (1-self.cfg.improvement)*incumbent.fitness:
                        candidate = self.heads.copy()
            if self.heads is None or not np.array_equal(candidate, self.heads):
                self.accepted_changes += 1
            self.heads = candidate
            self.searches += 1
            self.last_search = t
            self.trigger_counts[reason] += 1
            self.control_broadcasts()
        if self.heads is None:
            self.heads = np.array([], int)
        surviving = self.heads[self.alive()[self.heads]]
        plan = self.make_plan(surviving)
        self.controller_seconds += time.perf_counter()-start
        return plan, reason or 'none'

    def debit(self, node, amount, category):
        if node >= self.n or self.disabled[node]:
            return 0.0
        taken = min(float(self.energy[node]), max(0.0, float(amount)))
        self.energy[node] -= taken
        self.ledger[category] += taken
        return taken

    def control_broadcasts(self):
        """Two ideal one-hop 256-bit broadcasts per active node per search.

        This explicitly prices local status/assignment exchange, not a complete
        reliable multi-hop telemetry-collection/control protocol.
        """
        active = self.alive()
        for i in np.where(active)[0]:
            self.debit(i, 2*self.radio_tx(self.cfg.radio_range, self.control_bits), 'control')
            listeners = np.where(self.feasible[i, :self.n] & active)[0]
            for j in listeners:
                self.debit(j, 2*self.control_bits*self.e_elec, 'control')

    def transaction(self, t, u, v, source, packet, purpose, start, busy):
        assert self.feasible[u, v], (u, v, self.distance[u, v])
        category = 'probe' if purpose == 71 else 'data'
        now = max(start, busy[u], busy[v] if v < self.n else 0)
        begin, attempted, success, censored = now, 0, False, False
        for a in range(1, 5):
            tx = float(self.tx_energy[u, v]); rx = self.packet_bits*self.e_elec
            if self.disabled[u] or self.energy[u] < tx or (v < self.n and (self.disabled[v] or self.energy[v] < rx)):
                censored = True; break
            self.debit(u, tx, category)
            if v < self.n: self.debit(v, rx, category)
            now += float(self.env_frame[u, v])
            attempted += 1
            if keyed_uniform(self.seed, t, purpose, source, packet, u, v, a) < self.env_p[u, v]:
                ack_tx = float(self.radio_tx(self.distance[u, v], self.ack_bits))
                ack_rx = self.ack_bits*self.e_elec
                if self.energy[u] < ack_rx or (v < self.n and self.energy[v] < ack_tx):
                    censored = True; break
                self.debit(u, ack_rx, category)
                if v < self.n: self.debit(v, ack_tx, category)
                now += self.ack_bits/250.0
                success = True; break
        busy[u] = now
        if v < self.n: busy[v] = now
        obs = None
        if not censored and attempted:
            cost = attempted + int(not success)
            duration = now-begin
            pred = np.array([self.cost_pred[u,v], self.delay_pred[u,v]])
            scale = np.array([self.cost_scale[u,v], self.delay_scale[u,v]])
            upper = np.array([self.upper_c[u,v], self.upper_d[u,v]])
            y = np.array([cost, duration])
            obs = (u,v,attempted,int(success),duration,(y-pred)/scale,y<=upper)
            if self.diagnostics:
                self.link_logs.append(dict(round=t+1,kind=category,u=int(u),v=int(v),source=int(source),packet=int(packet),
                    cost=float(cost),duration_ms=duration,pred_cost=pred[0],pred_delay_ms=pred[1],
                    upper_cost=upper[0],upper_delay_ms=upper[1],covered_cost=int(y[0]<=upper[0]),
                    covered_delay=int(y[1]<=upper[1]),distance_m=float(self.distance[u,v])))
        return success, now, obs

    def data_phase(self, t, plan):
        busy = np.zeros(self.n)
        packets, observations = {}, []
        order = rng_for(self.seed, 61, t).permutation(self.n)
        heads = [int(c) for c in order if c in set(plan.heads)]
        for c in heads:
            packets[c] = []
            if not self.alive()[c]: continue
            for i in order:
                if plan.assigned[i] != c or not self.alive()[i]: continue
                for q in range(self.load):
                    if i == c:
                        packets[c].append((int(i), q))
                    else:
                        ok, _, obs = self.transaction(t,int(i),c,int(i),q,72,0,busy)
                        if obs is not None: observations.append(obs)
                        if ok: packets[c].append((int(i),q))
            self.debit(c,len(packets[c])*self.packet_bits*self.e_da,'aggregation')
            busy[c] += 2.0
        timestamps = []
        for c in heads:
            if not packets[c] or c not in plan.paths or not self.alive()[c]: continue
            ready, ok = busy[c], True
            for u,v in zip(plan.paths[c][:-1],plan.paths[c][1:]):
                ok,ready,obs = self.transaction(t,u,v,c,0,73,ready,busy)
                if obs is not None: observations.append(obs)
                if not ok: break
            if ok: timestamps.extend([ready]*len(packets[c]))
        return np.asarray(timestamps), observations

    def probe_schedule(self, t):
        r = rng_for(self.seed, 81, t)
        schedule = []
        for i in range(self.n):
            neighbors = np.where(self.feasible[i])[0]
            chosen = r.choice(neighbors,min(self.cfg.probes,len(neighbors)),replace=False)
            schedule.extend((i,int(v),q) for q,v in enumerate(chosen))
        return schedule

    def probe_phase(self, t):
        busy = np.zeros(self.n)
        observations = []
        for i,v,q in self.probe_schedule(t):
            if not self.alive()[i] or (v < self.n and not self.alive()[v]): continue
            _,_,obs = self.transaction(t,i,v,i,q,71,0,busy)
            if obs is not None: observations.append(obs)
        if observations:
            scores = np.array([o[5] for o in observations])
            covered = np.array([o[6] for o in observations])
            self.cal.update(scores,covered,t)
            # Updates use only observable attempts, ACK outcomes, and durations.
            for u,v,a,s,d,_,_ in observations:
                self.beta_a[u,v] = .90*self.beta_a[u,v] + s
                self.beta_b[u,v] = .90*self.beta_b[u,v] + a-s
                self.frame_hat[u,v] = .80*self.frame_hat[u,v]+.20*d/a
        return observations

    @staticmethod
    def coverage_counts(obs):
        if not obs: return 0,0,0
        return len(obs),int(sum(o[6][0] for o in obs)),int(sum(o[6][1] for o in obs))

    def run(self):
        start = time.perf_counter()
        for t in range(self.cfg.rounds):
            self.fail_nodes(t)
            self.environment(t)
            self.predictions(t)
            q_before = self.cal.q.copy()
            plan,reason = self.select(t)
            delivered,data_obs = self.data_phase(t,plan)
            probe_obs = self.probe_phase(t)
            demand = self.n*self.load
            timely = int(np.sum(delivered <= self.cfg.deadline_ms))
            nd,cd,dd = self.coverage_counts(data_obs)
            npb,cp,dp = self.coverage_counts(probe_obs)
            residual = float(self.energy0.sum()-self.energy.sum()-sum(self.ledger.values()))
            if abs(residual)>1e-9: raise AssertionError(('energy conservation',residual))
            self.rows.append(dict(round=t+1,analysis=int(t>=self.cfg.warmup),demand=demand,
                delivered=len(delivered),timely=timely,pdr=len(delivered)/demand,timely_ratio=timely/demand,
                service_violation=int(timely/demand<.80),delay_sum_ms=float(delivered.sum()),
                conditional_delay_ms=float(delivered.mean()) if len(delivered) else np.nan,
                delay_p95_ms=float(np.quantile(delivered,.95)) if len(delivered) else np.nan,
                probe_n=npb,probe_cost_covered=cp,probe_delay_covered=dp,
                data_n=nd,data_cost_covered=cd,data_delay_covered=dd,q_cost=q_before[0],q_delay=q_before[1],
                alpha_cost=float(self.cal.alpha[0]),alpha_delay=float(self.cal.alpha[1]),
                alive=int(self.alive().sum()),disabled=int(self.disabled.sum()),head_count=len(plan.heads),
                unassigned=int(np.sum(plan.assigned<0)),trigger=reason,env_fingerprint=self.env_fingerprint,
                energy_data=self.ledger['data'],energy_probe=self.ledger['probe'],
                energy_control=self.ledger['control'],energy_aggregation=self.ledger['aggregation']))
        a = self.rows[self.cfg.warmup:]
        sums = lambda key: sum(r[key] for r in a)
        div = lambda num,den: num/den if den else np.nan
        result=dict(method=self.method,scenario=self.scenario,seed=self.seed,nodes=self.n,rounds=self.cfg.rounds,
            probes=self.cfg.probes,fixed_heads=self.cfg.fixed_heads,PDR=div(sums('delivered'),sums('demand')),
            timely_ratio=div(sums('timely'),sums('demand')),
            service_violation_rate=np.mean([r['service_violation'] for r in a]),
            conditional_delay_ms=div(sums('delay_sum_ms'),sums('delivered')),
            radio_energy_J=sum(self.ledger.values()),energy_data_J=self.ledger['data'],
            energy_probe_J=self.ledger['probe'],energy_control_J=self.ledger['control'],
            energy_aggregation_J=self.ledger['aggregation'],disabled_stored_J=self.failure_stored,
            energy_per_delivered_mJ=1000*sum(self.ledger.values())/max(1,sum(r['delivered'] for r in self.rows)),
            probe_cost_coverage=div(sums('probe_cost_covered'),sums('probe_n')),
            probe_delay_coverage=div(sums('probe_delay_covered'),sums('probe_n')),
            data_cost_coverage=div(sums('data_cost_covered'),sums('data_n')),
            data_delay_coverage=div(sums('data_delay_covered'),sums('data_n')),
            final_alive=int(self.alive().sum()),searches=self.searches,accepted_changes=self.accepted_changes,
            fitness_evaluations=self.fitness_calls,controller_seconds=self.controller_seconds,
            simulation_seconds=time.perf_counter()-start,**{f'trigger_{k}':v for k,v in self.trigger_counts.items()})
        return result


if __name__ == '__main__':
    import argparse,json
    p=argparse.ArgumentParser()
    p.add_argument('--method',choices=list(METHODS),default='ACR-MCR')
    p.add_argument('--seed',type=int,default=9000)
    p.add_argument('--scenario',default='S1')
    a=p.parse_args()
    print(json.dumps(Simulator(a.seed,a.scenario,a.method).run(),indent=2))
