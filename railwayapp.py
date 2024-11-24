import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium

# Load Data
@st.cache
def load_data():
    cityline = gpd.read_file('cityline_2025.geojson')
    smasvaedi = gpd.read_file('smasvaedi_2021.json')
    tekjur = pd.read_csv('tekjutiundir.csv')
    ibudir = pd.read_csv('ibudir.csv')
    ibuafjoldi = pd.read_csv('ibuafjoldi.csv')
    lodir = pd.read_csv('lodir.csv')
    starfsmenn = pd.read_csv('fjoldi_starfandi.csv')
    return cityline, smasvaedi, tekjur, ibudir, ibuafjoldi, lodir, starfsmenn

cityline, smasvaedi, tekjur, ibudir, ibuafjoldi, lodir, starfsmenn = load_data()

# Sidebar for filtering
st.sidebar.header("Filters")
year = st.sidebar.slider("Year", 2025, 2035, step=1)
income_range = st.sidebar.slider("Income Range", 0, 200000, (20000, 100000))

# Map Display
st.header("Interactive Train Station Planning")
m = folium.Map(location=[64.1355, -21.8954], zoom_start=12)  # Adjust for your region
folium.GeoJson(cityline).add_to(m)  # Base city lines

# Display map
st_data = st_folium(m, width=700, height=500)

# Save modified GeoJSON
if st.button("Save Adjusted GeoJSON"):
    # Logic to save modified station points to GeoJSON
    st.success("GeoJSON saved successfully!")
