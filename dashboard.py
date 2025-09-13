import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import fastf1
from fastf1 import plotting
import os
from datetime import datetime

# Setup
st.set_page_config(page_title="F1 InsightX", layout="wide")
plotting.setup_mpl()

# Ensure cache folder exists
os.makedirs("ff1cache", exist_ok=True)
fastf1.Cache.enable_cache("ff1cache")

# Sidebar: Session Selection
st.sidebar.title("Session Selection")
year = st.sidebar.selectbox("Season", list(range(2018, datetime.now().year + 1)), index=datetime.now().year - 2018)

schedule = fastf1.get_event_schedule(year)
event_names = schedule.EventName.tolist()
event_choice = st.sidebar.selectbox("Grand Prix", event_names)
session_type = st.sidebar.selectbox("Session", ["FP1", "FP2", "FP3", "Qualifying", "Sprint", "Race"], index=3)

# Load Session
try:
    session = fastf1.get_session(year, event_choice, session_type)
    session.load()
except Exception as e:
    st.error(f"Could not load session: {e}")
    st.stop()

st.title(f"F1 InsightX — {year} {event_choice} {session_type}")

# Lap Data
laps = session.laps
if laps.empty:
    st.warning("No laps available.")
    st.stop()

st.subheader("Lap Times")
st.dataframe(laps[["Driver", "LapNumber", "LapTime", "Compound"]].reset_index(drop=True), use_container_width=True)

fig = px.histogram(laps, x="LapTime", nbins=40, title="Lap Time Distribution")
st.plotly_chart(fig, use_container_width=True)

# Tyre Usage
if "Compound" in laps.columns:
    st.subheader("Tyre Strategy")
    tyre_counts = laps["Compound"].value_counts().reset_index()
    tyre_counts.columns = ["Compound", "Count"]
    st.plotly_chart(px.pie(tyre_counts, names="Compound", values="Count", title="Tyre Usage"), use_container_width=True)

# Telemetry 
st.subheader("Telemetry (Fastest Lap)")
drivers = sorted(laps.Driver.unique())
driver_choice = st.selectbox("Choose Driver", drivers)

try:
    fastest = laps.pick_driver(driver_choice).pick_fastest()
    tel = fastest.get_telemetry()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(tel.Distance, tel.Speed, label="Speed")
    ax.set_xlabel("Distance (m)")
    ax.set_ylabel("Speed (kph)")
    ax.legend()
    st.pyplot(fig)

    st.plotly_chart(px.scatter(tel, x="X", y="Y", color="Speed", title="Track Map"), use_container_width=True)

except Exception as e:
    st.error(f"Could not load telemetry: {e}")

st.markdown("---")
st.caption("Built by Preet Harquissandas")