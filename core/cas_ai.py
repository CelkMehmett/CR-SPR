"""Cas-AI Core: Genetic + RL editing engine (simplified).

Features:
- Gene and Genome models
- Simple GA mutation operator (Gaussian perturbation)
- Lightweight bandit controller (epsilon-greedy) to pick genes to mutate
- Mutation lifecycle: Edit -> Validate -> Reinforce -> Commit (or Rollback)
- Gene bank for failed mutations
- Epigenetic memory extraction (deterministic embedding)
- Simple Merkle ledger for auditability
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Callable, Any, List, Optional, Tuple
import random
import time
import json
import hashlib
from core.epigenetics import EpigeneticMemory
from core.ethics import EthicsChecker
try:
    from core.guidrna import suggest_genes
except Exception:
    suggest_genes = None


@dataclass
class Gene:
    name: str
    value: float
    min_val: float = -float('inf')
    max_val: float = float('inf')
    meta: Dict[str, Any] = field(default_factory=dict)

    def clamp(self):
        self.value = max(self.min_val, min(self.max_val, self.value))


class Genome:
    def __init__(self, genes: Dict[str, Gene]):
        self.genes: Dict[str, Gene] = genes

    def copy(self) -> Genome:
        return Genome({n: Gene(n, g.value, g.min_val, g.max_val, dict(g.meta)) for n, g in self.genes.items()})

    def to_dict(self) -> Dict[str, float]:
        return {n: g.value for n, g in self.genes.items()}


class BanditController:
    """Simple epsilon-greedy multi-armed bandit where arms = gene names."""

    def __init__(self, arms: List[str], epsilon: float = 0.2):
        self.arms = list(arms)
        self.epsilon = epsilon
        self.counts: Dict[str, int] = dict.fromkeys(arms, 0)
        self.values: Dict[str, float] = dict.fromkeys(arms, 0.0)  # incremental mean

    def select(self) -> str:
        if random.random() < self.epsilon:
            return random.choice(self.arms)
        # pick highest estimated value
        return max(self.arms, key=lambda a: (self.values.get(a, 0.0), -self.counts.get(a, 0)))

    def update(self, arm: str, reward: float):
        self.counts[arm] = self.counts.get(arm, 0) + 1
        n = self.counts[arm]
        prev = self.values.get(arm, 0.0)
        # incremental mean
        self.values[arm] = prev + (reward - prev) / n


class GeneBank:
    """Store failed mutations for quarantine and later analysis."""

    def __init__(self):
        self.failed: List[Dict[str, Any]] = []

    def add(self, record: Dict[str, Any]):
        record['_ts'] = time.time()
        self.failed.append(record)


class MerkleLedger:
    """Append-only ledger storing JSON-records and a Merkle root."""

    def __init__(self):
        self.leaves: List[bytes] = []

    def append(self, record: Dict[str, Any]) -> str:
        raw = json.dumps(record, sort_keys=True, default=str).encode('utf-8')
        h = hashlib.sha256(raw).digest()
        self.leaves.append(h)
        return h.hex()

    def root(self) -> Optional[str]:
        if not self.leaves:
            return None
        nodes = list(self.leaves)
        while len(nodes) > 1:
            nxt = []
            for i in range(0, len(nodes), 2):
                a = nodes[i]
                b = nodes[i+1] if i+1 < len(nodes) else a
                nxt.append(hashlib.sha256(a + b).digest())
            nodes = nxt
        return nodes[0].hex()


def _make_embedding(changes: Dict[str, Tuple[float, float]]) -> List[float]:
    """Deterministic lightweight embedding from changes dict: use hash and map to floats."""
    s = json.dumps(changes, sort_keys=True)
    h = hashlib.sha256(s.encode('utf-8')).digest()
    # map digest into 8 small floats in [-1,1]
    out = []
    for i in range(8):
        chunk = h[i*4:(i+1)*4]
        val = int.from_bytes(chunk, 'big', signed=False) / 0xFFFFFFFF
        out.append((val * 2.0) - 1.0)
    return out


class CasAICore:
    def __init__(self, genome: Genome, evaluator: Callable[[Genome], float], epsilon: float = 0.2):
        """
        evaluator: function that accepts a Genome and returns a reward (higher is better).
        """
        self.genome = genome
        self.evaluator = evaluator
        self.bandit = BanditController(list(genome.genes.keys()), epsilon=epsilon)
        self.gene_bank = GeneBank()
        self.ledger = MerkleLedger()
        # integrate EpigeneticMemory object
        self.epigenetic_memory = EpigeneticMemory()
        # keep a plain list as well for compatibility with guideRNA
        self.epigenetic_memory_list: List[List[float]] = []
        # ethics checker
        self.ethics = EthicsChecker()

    def mutate_gene(self, gene_name: str, scale: float = 0.1) -> Dict[str, Any]:
        g = self.genome.genes[gene_name]
        old = g.value
        # gaussian perturbation proportional to magnitude
        noise = random.gauss(0, 1) * (abs(old) + 1.0) * scale
        new = old + noise
        new = max(g.min_val, min(g.max_val, new))

        # apply edit
        g.value = new
        g.clamp()

        return {'gene': gene_name, 'old': old, 'new': g.value, 'noise': noise}

    def validate_and_reinforce(self, edit_record: Dict[str, Any], baseline_reward: Optional[float] = None) -> Dict[str, Any]:
        # evaluate genome
        reward = float(self.evaluator(self.genome))
        gene = edit_record['gene']
        # treat baseline as previous reward if provided otherwise 0.0
        if baseline_reward is None:
            baseline_reward = 0.0

        success = reward >= baseline_reward

        # reinforce bandit
        self.bandit.update(gene, reward - baseline_reward)

        return {'reward': reward, 'success': success}

    def commit(self, edit_record: Dict[str, Any], validation: Dict[str, Any]):
        # create ledger entry and epigenetic memory
        changes = {edit_record['gene']: (edit_record['old'], edit_record['new'])}
        emb = _make_embedding(changes)
        # store embedding in EpigeneticMemory and list
        self.epigenetic_memory.add(emb, {'gene': edit_record['gene']})
        self.epigenetic_memory_list.append(emb)
        entry = {
            'ts': time.time(),
            'gene': edit_record['gene'],
            'old': edit_record['old'],
            'new': edit_record['new'],
            'reward': validation['reward'],
            'success': validation['success'],
            'embedding': emb,
        }
        self.ledger.append(entry)
        return entry

    def rollback(self, edit_record: Dict[str, Any], validation: Dict[str, Any]):
        gene = edit_record['gene']
        # restore old value
        if gene in self.genome.genes:
            self.genome.genes[gene].value = edit_record['old']
        # add to gene bank
        rec = dict(edit_record)
        rec.update(validation)
        self.gene_bank.add(rec)
        return rec

    def run_one_cycle(self, baseline_reward: Optional[float] = None, scale: float = 0.1) -> Dict[str, Any]:
        # selection: optionally bias bandit selection using epigenetic memory and guideRNA
        arms = list(self.genome.genes.keys())
        # default selection from bandit
        arm = self.bandit.select()
        try:
            # compute simple influence scores from epigenetics
            epi_influence = self.epigenetic_memory.influence_for_genes(arms)
            # if guideRNA available, get its top suggestions
            if suggest_genes:
                guide = suggest_genes(arms, self.bandit.counts, self.bandit.values, self.epigenetic_memory_list, top_k=3)
                # if guide suggests a gene, pick it with some probability
                if guide and random.random() < 0.6:
                    arm = guide[0]
                else:
                    # otherwise pick best from combined score
                    scored = {a: 0.7 * self.bandit.values.get(a, 0.0) + 0.3 * epi_influence.get(a, 0.0) for a in arms}
                    arm = max(arms, key=lambda a: scored.get(a, 0.0))
            else:
                # no guideRNA: bias bandit with epi influence
                scored = {a: 0.7 * self.bandit.values.get(a, 0.0) + 0.3 * epi_influence.get(a, 0.0) for a in arms}
                arm = max(arms, key=lambda a: scored.get(a, 0.0))
        except Exception:
            arm = self.bandit.select()

        edit = self.mutate_gene(arm, scale=scale)
        validation = self.validate_and_reinforce(edit, baseline_reward=baseline_reward)
        if validation['success']:
            # ethics approval before commit
            ok, reason = self.ethics.approve(edit, validation, self.genome)
            if ok:
                entry = self.commit(edit, validation)
                outcome = {'committed': True, 'entry': entry}
            else:
                # rollback and note reason
                rec = self.rollback(edit, validation)
                rec['_ethics_reject'] = reason
                outcome = {'committed': False, 'recorded': rec, 'reason': reason}
        else:
            rec = self.rollback(edit, validation)
            outcome = {'committed': False, 'recorded': rec}
        return outcome

    def run_experiment(self, iterations: int = 10, scale: float = 0.1) -> List[Dict[str, Any]]:
        results = []
        # initial baseline reward
        baseline = float(self.evaluator(self.genome))
        for _ in range(iterations):
            r = self.run_one_cycle(baseline_reward=baseline, scale=scale)
            # if committed, update baseline to new reward
            if r.get('committed'):
                baseline = r['entry']['reward']
            results.append(r)
        return results
