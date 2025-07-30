# app.py (Streamlit UI)
import streamlit as st
import pandas as pd
from simulation import Simulation, Config
import plotly.express as px

st.set_page_config(page_title="Family Ownership Simulation", layout="wide")

st.title("Family Partnership Evolution Simulator")

with st.sidebar:
    st.header("Parameters")
    start_year = st.number_input("Start year", 1900, 3000, 2025)
    horizon = st.slider("Horizon (years)", 20, 200, 100)
    seed = st.number_input("Random seed", 0, 100000, 42)
    fert_mean = st.slider("Mean children per partner", 0.0, 4.0, 1.6, 0.1)
    invite_prob = st.slider("Invite probability @26", 0.0, 1.0, 0.6, 0.05)
    promo_prob = st.slider("Promotion probability", 0.0, 1.0, 0.7, 0.05)
    age_emeritus = st.slider("Age to emeritus", 45, 70, 55)
    age_econ_end = st.slider("Economic rights end age", 55, 90, 65)

cfg = Config(
    start_year=start_year,
    horizon_years=horizon,
    seed=seed,
    fertility_mean=fert_mean,
    invite_prob=invite_prob,
    promotion_prob=promo_prob,
    age_partner_to_emeritus=age_emeritus,
    age_econ_rights_end=age_econ_end
)

sim = Simulation(cfg)
history = sim.run()

st.subheader("Key Metrics Over Time")
metrics = ["partners_active","partners_emeritus","partners_economic","partners_voting","trainees","children","washouts"]
fig = px.area(history, x="year", y=metrics, title="Headcount by Status")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Partners (Economic vs Voting)")
fig2 = px.line(history, x="year", y=["partners_economic","partners_voting"], title="Rights Pools")
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Data Table")
st.dataframe(history.set_index('year'))

st.caption("Adjust parameters in the sidebar and rerun to see different scenarios.")