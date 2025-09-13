import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import fastf1
from fastf1 import plotting
import requests
import io
import base64
from datetime import datetime

# --- Helpers & caching ---
st.set_page_config(page_title='F1 InsightX', layout='wide', initial_sidebar_state='expanded')
plotting.setup_mpl()

@st.cache_resource
def get_ergast_race_list(season=None):
    base = 'https://ergast.com/api/f1'
    url = f"{base}/{season}.json" if season else f"{base}.json"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    races = data.get('MRData', {}).get('RaceTable', {}).get('Races', [])
    return races

@st.cache_data(show_spinner=False)
def load_fastf1_session(season, gp, session):
    # FastF1 caches data in ~/.fastf1 or tmp
    fastf1.Cache.enable_cache('./ff1cache')
    try:
        session_obj = fastf1.get_session(season, gp, session)
        session_obj.load()  # loads laps, telemetry, weather
        return session_obj
    except Exception as e:
        st.error(f"Error loading FastF1 session: {e}")
        return None

@st.cache_data
def fetch_race_metadata(season, round_):
    # Ergast: /{season}/{round}.json
    url = f"https://ergast.com/api/f1/{season}/{round_}.json"
    r = requests.get(url, timeout=8)
    r.raise_for_status()
    return r.json()

# Small utility to allow CSV download
def get_table_download_link(df: pd.DataFrame, filename='data.csv'):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f"data:file/csv;base64,{b64}"
    return href

# Sidebar controls
st.sidebar.title('F1 InsightX — Controls')
with st.sidebar.expander('Session Selection', expanded=True):
    year = st.selectbox('Season (Year)', options=list(range(2005, datetime.now().year + 1)), index= datetime.now().year - 2005)
    races = get_ergast_race_list(year)
    race_options = [f"{r['round']}: {r['raceName']} ({r.get('Circuit', {}).get('circuitName','')})" for r in races]
    if races:
        sel_idx = st.selectbox('Grand Prix', options=list(range(len(races))), format_func=lambda i: race_options[i])
        selected_race = races[sel_idx]
        gp_round = selected_race['round']
        gp_name = selected_race['raceName']
    else:
        st.warning('No races found for this season via Ergast API')
        selected_race = None
        gp_round = None
        gp_name = None
    session_type = st.selectbox('Session', options=['FP1','FP2','FP3','Qualifying','Sprint','Race'], index=3)

with st.sidebar.expander('Driver / Lap Selection'):
    driver = st.text_input('Driver code (e.g. HAM, VER, LEC) — leave blank for all', value='')
    lap_filter = st.selectbox('Lap filter', options=['All laps','Fastest lap only','Stint filter (by tyre)'])
    tyre_choice = st.selectbox('Tyre compound (when filtering by stint)', options=['Soft','Medium','Hard','C3','C4','C5','Intermediate','Wet','All'], index=9)

with st.sidebar.expander('Advanced options'):
    show_telemetry = st.checkbox('Load detailed telemetry (slower)', value=True)
    telemetry_rate = st.selectbox('Telemetry downsample (points)', options=[None,1000,500,250,100], index=2)
    enable_live = st.checkbox('Attempt to fetch latest session if today?', value=True)

# Main layout
st.title('F1 InsightX')
st.markdown('Advanced interactive dashboard to visualise lap timing, telemetry, tyres, and weather data using FastF1 and Ergast APIs.')

if not selected_race:
    st.stop()

# Load session
with st.spinner('Loading session data (FastF1)...'):
    session_obj = load_fastf1_session(year, int(gp_round), session_type)

if session_obj is None:
    st.error('Session could not be loaded.')
    st.stop()

# Header info
col1, col2, col3 = st.columns([3,2,2])
with col1:
    st.subheader(f"{gp_name} — {year} — {session_type}")
    st.write(f"Circuit: {selected_race.get('Circuit', {}).get('circuitName','Unknown')}")
with col2:
    try:
        date = selected_race.get('date')
        st.write(f"Date: {date}")
    except:
        pass
with col3:
    # show basic weather info from FastF1 session if available
    weather = getattr(session_obj, 'weather', None)
    if weather is not None:
        st.write('Weather summary available')
    else:
        st.write('Weather not available')

# Laps table & summary
st.markdown('## Lap Times & Summary')

laps = session_obj.laps.copy()
if driver.strip():
    laps = laps[laps['Driver'].str.contains(driver.strip(), case=False, na=False)]

if laps.empty:
    st.warning('No laps found for your selection.')
else:
    # Provide a summary table
    summary_cols = ['Time','Driver','LapNumber','LapTime','Compound','Stint','IsPersonalBest']
    display_cols = [c for c in summary_cols if c in laps.columns]
    st.dataframe(laps[display_cols].sort_values('LapTime').reset_index(drop=True), use_container_width=True)

    # download
    dl_href = get_table_download_link(laps[display_cols], filename='laps.csv')
    st.markdown(f"[Download laps CSV]({dl_href})")

    # Basic lap time histogram
    st.markdown('### Lap time distribution')
    fig = px.histogram(laps, x='LapTime', nbins=40, title='Lap time distribution')
    st.plotly_chart(fig, use_container_width=True)

# Tyre / Strategy view
st.markdown('## Tyre & Strategy')
if 'Compound' in laps.columns:
    tyre_counts = laps['Compound'].value_counts().rename_axis('Compound').reset_index(name='Count')
    fig = px.pie(tyre_counts, names='Compound', values='Count', title='Tyre compound distribution')
    st.plotly_chart(fig, use_container_width=True)

    # stint timelines by driver
    st.markdown('### Stint timeline (per driver)')
    if 'Stint' in laps.columns:
        timeline = laps.groupby(['Driver','Stint']).agg({'LapNumber':['min','max']}).reset_index()
        timeline.columns = ['Driver','Stint','LapStart','LapEnd']
        st.dataframe(timeline)

# Telemetry viewer
st.markdown('## Telemetry Explorer')
if show_telemetry:
    # let user choose a driver and lap
    drivers = sorted(laps['Driver'].unique())
    lap_driver = st.selectbox('Driver for telemetry', options=drivers)
    driver_laps = session_obj.laps.pick_driver(lap_driver)
    fastest = driver_laps.pick_fastest()
    st.write(f"Selected: {lap_driver} — {len(driver_laps)} laps — fastest lap: {fastest['LapNumber']}")

    if st.button('Show telemetry plot'):
        with st.spinner('Loading telemetry...'):
            tel = fastest.get_telemetry() if hasattr(fastest, 'get_telemetry') else None
            if tel is None or tel.empty:
                st.warning('Telemetry not available for that lap')
            else:
                # downsample
                if telemetry_rate:
                    tel = tel.iloc[::max(1, int(len(tel)/telemetry_rate))]
                # Matplotlib plot for speed and throttle
                fig, ax = plt.subplots(2,1, figsize=(10,4), sharex=True)
                ax[0].plot(tel['Distance'], tel['Speed'])
                ax[0].set_ylabel('Speed (kph)')
                ax[0].grid(True)
                ax[1].plot(tel['Distance'], tel['Throttle'])
                ax[1].plot(tel['Distance'], tel['Brake'])
                ax[1].set_ylabel('Throttle / Brake')
                ax[1].set_xlabel('Distance (m)')
                ax[1].grid(True)
                st.pyplot(fig)

                # Interactive Map-ish with track position using Plotly
                if 'X' in tel.columns and 'Y' in tel.columns:
                    try:
                        fig2 = px.scatter(tel, x='X', y='Y', color='Speed', title='Track position colored by Speed', labels={'X':'Track X','Y':'Track Y'})
                        st.plotly_chart(fig2, use_container_width=True)
                    except Exception:
                        pass

# Weather & session telemetry summary
st.markdown('## Weather & Session Overview')
if hasattr(session_obj, 'weather') and session_obj.weather is not None:
    w = session_obj.weather
    st.write('Weather snapshot from FastF1 (when recorded):')
    try:
        st.metric('Air temp (°C)', w['ambientTemperature'])
        st.metric('Track temp (°C)', w['trackTemperature'])
        st.write('Conditions note:', w.get('condition', '—'))
    except Exception:
        st.write(w)
else:
    st.write('No weather data in FastF1 for this session.')

# Head-to-head lap comparison
st.markdown('## Head-to-head Lap Comparison')
with st.expander('Compare two drivers laps'):
    d1 = st.selectbox('Driver 1', options=drivers, index=0, key='d1')
    d2 = st.selectbox('Driver 2', options=drivers, index=min(1,len(drivers)-1), key='d2')
    if st.button('Compare'):
        l1 = session_obj.laps.pick_driver(d1).pick_fastest()
        l2 = session_obj.laps.pick_driver(d2).pick_fastest()
        t1 = l1.get_telemetry().add_suffix('_1')
        t2 = l2.get_telemetry().add_suffix('_2')
        # merge by distance approximate
        df1 = l1.get_telemetry()
        df2 = l2.get_telemetry()
        # simple overlay speed vs distance
        fig, ax = plt.subplots(figsize=(10,3))
        ax.plot(df1['Distance'], df1['Speed'], label=f"{d1} (lap {l1['LapNumber']})")
        ax.plot(df2['Distance'], df2['Speed'], label=f"{d2} (lap {l2['LapNumber']})")
        ax.set_xlabel('Distance (m)')
        ax.set_ylabel('Speed (kph)')
        ax.legend()
        st.pyplot(fig)

# Quick analytics panel
st.sidebar.markdown('---')
st.sidebar.subheader('Quick analytics')
if not laps.empty:
    best_lap = laps.loc[laps['LapTime'].idxmin()]
    st.sidebar.metric('Fastest lap (selected filters)', best_lap['LapTime'])
    st.sidebar.write('Top 5 drivers by best lap:')
    best_by_driver = laps.groupby('Driver')['LapTime'].min().sort_values().head(5).reset_index()
    st.sidebar.table(best_by_driver)

# Small info & troubleshooting
st.markdown('---')
st.markdown('### Tips & Troubleshooting')
st.markdown('''
- FastF1 downloads session data the first time; enable caching to speed subsequent loads.
- If telemetry plots fail, try disabling `show telemetry` or reduce `telemetry downsample`.
- Ergast API is rate-limited; if races don't appear, try again later.
''')

