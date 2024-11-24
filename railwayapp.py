import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk

# Load datasets
@st.cache_data
def load_data():
    # Load small areas GeoJSON
    small_areas_gdf = gpd.read_file('/workspaces/Datathon_2024/data/smasvaedi/smasvaedi_2021.json')
    
    # Filter and prepare small areas
    small_areas_gdf = small_areas_gdf[small_areas_gdf['nuts3'] == '001']
    small_areas_gdf = small_areas_gdf[['smsv', 'smsv_label_en', 'geometry']]
    small_areas_gdf['smsv'] = small_areas_gdf['smsv'].astype(str)
    
    # Convert all geometries to WGS 84 (EPSG:4326) for uniform coordinate reference system
    small_areas_gdf = small_areas_gdf.to_crs("EPSG:4326")
    # Fix invalid geometries
    small_areas_gdf['geometry'] = small_areas_gdf.geometry.buffer(0)
    small_areas_gdf = small_areas_gdf[small_areas_gdf.is_valid]
    
    # Extract latitude and longitude from geometries
    small_areas_gdf['latitude'] = small_areas_gdf.geometry.centroid.y
    small_areas_gdf['longitude'] = small_areas_gdf.geometry.centroid.x

    # Load city lane GeoJSON
    city_lane_gdf = gpd.read_file('/workspaces/Datathon_2024/data/geojson_files/cityline_2025.geojson')
    city_lane_gdf = city_lane_gdf.to_crs("EPSG:4326")
    city_lane_gdf['geometry'] = city_lane_gdf.geometry.buffer(0)
    city_lane_gdf = city_lane_gdf[city_lane_gdf.is_valid]

    # Load employment CSV
    employed_df = pd.read_csv('/workspaces/Datathon_2024/data/num_of_people_working/fjoldi_starfandi.csv')
    employed_df.rename(columns={'smasvaedi': 'smsv'}, inplace=True)
    employed_df['smsv'] = employed_df['smsv'].astype(str).str.zfill(4)

    # Load population CSV
    population_df = pd.read_csv('/workspaces/Datathon_2024/data/num_of_residents/ibuafjoldi.csv')
    population_df.rename(columns={'smasvaedi': 'smsv'}, inplace=True)
    population_df['smsv'] = population_df['smsv'].astype(str).str.zfill(4)

    return small_areas_gdf, city_lane_gdf, employed_df, population_df

# Load the datasets
small_areas_gdf, city_lane_gdf, employed_df, population_df = load_data()

# Streamlit Sidebar Widgets
st.sidebar.title("Visualization Filters")
selected_year = st.sidebar.slider("Select Year", min_value=2020, max_value=2025, value=2024)
map_type = st.sidebar.selectbox("Select Map Type", ["Scatter", "Heatmap"])
show_city_lane = st.sidebar.checkbox("Show City Lane")

# Filter data for the selected year
population_filtered = population_df[population_df['ar'] == selected_year]
employed_filtered = employed_df[employed_df['ar'] == selected_year]

# Merge population and employment data with small areas for spatial data
population_filtered = population_filtered.merge(
    small_areas_gdf[['smsv', 'latitude', 'longitude']], 
    on='smsv', 
    how='left'
)

employed_filtered = employed_filtered.merge(
    small_areas_gdf[['smsv', 'latitude', 'longitude']], 
    on='smsv', 
    how='left'
)

# Verify merge outcome
st.write("Population Filtered Sample:", population_filtered.head())

# Ensure only rows with valid latitude and longitude are used for visualization
population_filtered = population_filtered.dropna(subset=['latitude', 'longitude'])
employed_filtered = employed_filtered.dropna(subset=['latitude', 'longitude'])

# Map Visualization
st.title("City Planning Visualization")
layers = []

# Add Population Layer
if not population_filtered.empty:
    population_layer = pdk.Layer(
        "ScatterplotLayer",
        data=population_filtered,
        get_position=["longitude", "latitude"],
        get_radius=200,
        get_color="[0, 128, 255, 160]",
        pickable=True,
    )
    layers.append(population_layer)

# Add City Lane Layer if checked
if show_city_lane and not city_lane_gdf.empty:
    city_lane_layer = pdk.Layer(
        "PathLayer",
        data=city_lane_gdf,
        get_path="geometry.coordinates",
        get_width=5,
        get_color="[255, 0, 0]",
        pickable=True,
    )
    layers.append(city_lane_layer)

# Define the View State
view_state = pdk.ViewState(
    latitude=64.1355,
    longitude=-21.8954,
    zoom=10,
    pitch=50,
)

# Render the map if layers exist
if layers:
    st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=view_state))
else:
    st.error("No data available to display.")

# Summary Section in Sidebar
st.sidebar.markdown("### Summary Statistics")
if not population_filtered.empty:
    st.sidebar.write("Population Data:", population_filtered.describe())
if not employed_filtered.empty:
    st.sidebar.write("Employment Data:", employed_filtered.describe())
