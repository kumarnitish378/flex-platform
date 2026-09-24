"""Seeded randomness (`simulator-spec.md` §13).

Every agent draws from its own generator, seeded from the scenario seed and the agent id.
Per-agent streams mean adding or removing one agent cannot shift the random numbers every
other agent sees, so runs stay comparable.
"""

from __future__ import annotations

import hashlib

import numpy as np


def derive_seed(scenario_seed: int, agent_id: str) -> int:
    """Stable 64-bit seed for an agent. Same inputs, same stream, on any machine."""
    digest = hashlib.sha256(f"{scenario_seed}:{agent_id}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def generator_for(scenario_seed: int, agent_id: str) -> np.random.Generator:
    return np.random.default_rng(derive_seed(scenario_seed, agent_id))


class RngFactory:
    """Hands out one generator per agent id, creating each at most once."""

    def __init__(self, scenario_seed: int) -> None:
        self._seed = scenario_seed
        self._generators: dict[str, np.random.Generator] = {}

    def for_agent(self, agent_id: str) -> np.random.Generator:
        if agent_id not in self._generators:
            self._generators[agent_id] = generator_for(self._seed, agent_id)
        return self._generators[agent_id]

    @property
    def seed(self) -> int:
        return self._seed
