# simulation.py
from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Literal, Set

Status = Literal['child','trainee','partner_active','partner_emeritus','washout','deceased']

@dataclass
class Config:
    start_year: int = 2025
    horizon_years: int = 100
    seed: int = 42
    # Demography
    fertility_mean: float = 1.6
    fertility_age_start: int = 28
    fertility_age_end: int = 42
    mortality_mean: int = 85
    mortality_sd: int = 8
    sex_ratio: float = 0.5
    # Selection
    invite_prob: float = 0.6
    promotion_prob: float = 0.7
    probation_min: int = 6
    probation_max: int = 9
    # Career
    age_partner_to_emeritus: int = 55
    age_econ_rights_end: int = 65
    eligible_parent_status: List[str] = field(default_factory=lambda: ['partner_active','partner_emeritus'])

@dataclass
class Person:
    id: int
    birth_year: int
    generation: int
    status: Status
    parent_ids: List[int] = field(default_factory=list)
    death_year: Optional[int] = None
    partner_since: Optional[int] = None
    emeritus_since: Optional[int] = None
    econ_rights_end_year: Optional[int] = None
    sex: str = 'F'

    @property
    def age(self):
        # age is computed externally per year when needed
        raise AttributeError('age computed externally')

class Simulation:
    def __init__(self, cfg: Config, initial_people: pd.DataFrame | None = None):
        self.cfg = cfg
        self.rng = np.random.default_rng(cfg.seed)
        self.year = cfg.start_year
        self.people: Dict[int, Person] = {}
        self.next_id = 1
        if initial_people is not None:
            for _, row in initial_people.iterrows():
                self._add_person_from_row(row)
        else:
            self._bootstrap_initial_state()

        self.history: List[Dict] = []

    def _bootstrap_initial_state(self):
        # crude seeding: create partners/trainees per specs
        # Ages random within ranges.
        def create_many(n, status, age_low, age_high):
            for _ in range(n):
                age = self.rng.integers(age_low, age_high+1)
                birth = self.year - age
                p = Person(id=self.next_id, birth_year=birth, generation=6, status=status)
                if status == 'partner_active':
                    p.partner_since = birth + 32
                if status == 'partner_emeritus':
                    p.partner_since = birth + 32
                    p.emeritus_since = birth + self.cfg.age_partner_to_emeritus
                if status == 'trainee':
                    pass
                self.people[self.next_id] = p
                self.next_id += 1
        create_many(30,'partner_active',35,55)
        create_many(30,'partner_emeritus',56,85)
        create_many(10,'trainee',27,32)

    def _add_person_from_row(self,row):
        p = Person(
            id=self.next_id,
            birth_year=int(row.birth_year),
            generation=int(row.generation),
            status=row.status,
            parent_ids=row.parent_ids or [],
            death_year=row.death_year if not np.isnan(row.death_year) else None,
            partner_since=row.partner_since if not np.isnan(row.partner_since) else None,
            emeritus_since=row.emeritus_since if not np.isnan(row.emeritus_since) else None,
            econ_rights_end_year=row.econ_rights_end_year if not np.isnan(row.econ_rights_end_year) else None,
            sex=row.sex
        )
        self.people[self.next_id] = p
        self.next_id += 1

    def run(self):
        for _ in range(self.cfg.horizon_years):
            self._tick()
        return pd.DataFrame(self.history)

    def _tick(self):
        year = self.year
        cfg = self.cfg
        # Helper lambdas
        def get_age(p):
            return year - p.birth_year

        # 1. Death & rights end
        for p in list(self.people.values()):
            if p.status == 'deceased':
                continue
            age = get_age(p)
            if p.death_year is None:
                # draw death year once
                exp_death = int(self.rng.normal(cfg.mortality_mean, cfg.mortality_sd))
                p.death_year = p.birth_year + exp_death
            if year >= p.death_year:
                p.status = 'deceased'

            # econ rights end
            if p.status in ['partner_active','partner_emeritus'] and p.econ_rights_end_year is None and age >= cfg.age_econ_rights_end:
                p.econ_rights_end_year = year

            # active→emeritus
            if p.status == 'partner_active' and age >= cfg.age_partner_to_emeritus:
                p.status = 'partner_emeritus'
                p.emeritus_since = year

        # 2. Births
        parents = [p for p in self.people.values()
                   if p.status in ['partner_active','partner_emeritus'] and
                      (year - p.birth_year) >= cfg.fertility_age_start and
                      (year - p.birth_year) <= cfg.fertility_age_end]
        for parent in parents:
            # probability of 1 birth in a given year from mean fertility spread across window
            years_window = cfg.fertility_age_end - cfg.fertility_age_start + 1
            p_birth = cfg.fertility_mean / years_window
            if self.rng.random() < p_birth:
                self._create_child(parent)

        # 3. Invitations at 26
        for p in self.people.values():
            if p.status == 'child' and get_age(p) == 26:
                if self._is_parent_eligible(p):
                    if self.rng.random() < cfg.invite_prob:
                        p.status = 'trainee'
                    else:
                        p.status = 'washout'
                else:
                    p.status = 'washout'

        # 4. Promotion 32–35
        for p in self.people.values():
            if p.status == 'trainee':
                age = get_age(p)
                if cfg.probation_min <= age - 26 <= cfg.probation_max:
                    # decide once at first eligible year
                    if self.rng.random() < cfg.promotion_prob:
                        p.status = 'partner_active'
                        p.partner_since = year
                    elif age >= 26 + cfg.probation_max:
                        p.status = 'washout'

        # 5. Record metrics
        counts = self._counts(year)
        self.history.append(counts)
        self.year += 1

    def _is_parent_eligible(self, child: Person) -> bool:
        # any parent in eligible status
        for pid in child.parent_ids:
            p = self.people.get(pid)
            if p and p.status in self.cfg.eligible_parent_status:
                return True
        # if we didn't store parents (seeded), assume eligible
        return True

    def _create_child(self, parent: Person):
        sex = 'M' if self.rng.random() < self.cfg.sex_ratio else 'F'
        child = Person(
            id=self.next_id,
            birth_year=self.year,
            generation=parent.generation + 1,
            status='child',
            parent_ids=[parent.id],
            sex=sex
        )
        self.people[self.next_id] = child
        self.next_id += 1

    def _counts(self, year: int) -> Dict:
        def is_econ(p):
            return p.status in ['partner_active','partner_emeritus'] and (p.econ_rights_end_year is None or year < p.econ_rights_end_year)
        def is_vote(p):
            return p.status in ['partner_active','partner_emeritus'] and p.status != 'deceased'
        return {
            'year': year,
            'partners_active': sum(p.status=='partner_active' for p in self.people.values()),
            'partners_emeritus': sum(p.status=='partner_emeritus' for p in self.people.values()),
            'partners_economic': sum(is_econ(p) for p in self.people.values()),
            'partners_voting': sum(is_vote(p) for p in self.people.values()),
            'trainees': sum(p.status=='trainee' for p in self.people.values()),
            'children': sum(p.status=='child' for p in self.people.values()),
            'washouts': sum(p.status=='washout' for p in self.people.values()),
            'living': sum(p.status!='deceased' for p in self.people.values()),
        }