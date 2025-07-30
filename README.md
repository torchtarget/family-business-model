# Family Business Model

A Streamlit-based simulator that models how partnership composition in a family-owned firm evolves over generations.

## Setup

1. Install the Python requirements:

```bash
pip install -r requirements.txt
```

2. Launch the application:

```bash
streamlit run app.py
```

This will open a local web interface where you can adjust simulation settings and visualize the results.

## Configurable Parameters

Parameters exposed in the sidebar correspond to fields in `simulation.Config`:

- `start_year` – first year of the simulation.
- `horizon_years` – number of years to simulate.
- `seed` – random seed for reproducibility.
- `fertility_mean` – average number of children per partner.
- `fertility_age_start` and `fertility_age_end` – age range in which partners may have children.
- `invite_prob` – probability that an eligible 26‑year‑old is invited to join as a trainee.
- `promotion_prob` – chance that a trainee is promoted to partner.
- `probation_min` and `probation_max` – duration of the trainee period.
- `age_partner_to_emeritus` – age at which partners become emeritus.
- `age_econ_rights_end` – age when economic rights expire.
- `eligible_parent_status` – partner statuses considered when evaluating invitation eligibility.
- `initial_active_partners`, `initial_emeritus_partners`, and `initial_trainees` – numbers of each group present at the start of the simulation.

Tweak these values in the sidebar (or by creating a `Config` manually) and rerun to explore different scenarios.
