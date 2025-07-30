import pandas as pd
from simulation import Simulation, Config

# Helper to build dataframe for a single person

def person_df(**kwargs):
    defaults = {
        'parent_ids': [],
        'partner_since': None,
        'emeritus_since': None,
        'econ_rights_end_year': None,
        'death_year': None,
        'sex': 'F',
    }
    defaults.update(kwargs)
    return pd.DataFrame([defaults])

def base_config(**overrides):
    cfg = Config(
        start_year=2000,
        horizon_years=1,
        seed=0,
        initial_active_partners=0,
        initial_emeritus_partners=0,
        initial_trainees=0,
    )
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg


def test_trainee_promoted_to_partner():
    birth_year = 2000 - 32  # age 32 at start
    df = person_df(id=1, birth_year=birth_year, generation=1, status='trainee')
    cfg = base_config(promotion_prob=1.0)
    sim = Simulation(cfg, initial_people=df)
    sim.run()
    assert sim.people[1].status == 'partner_active'


def test_partner_becomes_emeritus():
    age_thresh = 50
    birth_year = 2000 - age_thresh
    df = person_df(
        id=1,
        birth_year=birth_year,
        generation=1,
        status='partner_active',
        death_year=2100,
    )
    cfg = base_config(age_partner_to_emeritus=age_thresh)
    sim = Simulation(cfg, initial_people=df)
    sim.run()
    assert sim.people[1].status == 'partner_emeritus'


def test_birth_generation():
    birth_year = 2000 - 30
    df = person_df(id=1, birth_year=birth_year, generation=1, status='partner_active')
    cfg = base_config(fertility_mean=100)
    sim = Simulation(cfg, initial_people=df)
    sim.run()
    # one child added
    assert len(sim.people) == 2
    child = sim.people[2]
    assert child.status == 'child'
    assert child.generation == 2
    assert child.parent_ids == [1]


def test_death_handling():
    df = person_df(id=1, birth_year=1970, generation=1, status='partner_active', death_year=2000)
    cfg = base_config()
    sim = Simulation(cfg, initial_people=df)
    sim.run()
    assert sim.people[1].status == 'deceased'
