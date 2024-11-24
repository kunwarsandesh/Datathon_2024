import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk
from shapely.geometry import LineString

# Load datasets
@st.cache_data
def load_data():
    # Load small areas GeoJSON
    small_areas_gdf = gpd.read_file('/workspaces/Datathon_2024/data/smasvaedi/smasvaedi_2021.json')
    small_areas_gdf = small_areas_gdf.to_crs("EPSG:4326")  # Transform to EPSG:4326 for display and mapping
    
    # Filter and prepare small areas
    small_areas_gdf = small_areas_gdf[small_areas_gdf['nuts3'] == '001']
    small_areas_gdf = small_areas_gdf[['smsv', 'smsv_label_en', 'geometry']]
    small_areas_gdf['smsv'] = small_areas_gdf['smsv'].astype(str)
    
    # Re-project to a suitable CRS for geometric calculations
    projected_gdf = small_areas_gdf.to_crs("EPSG:3857")
    projected_gdf['centroid'] = projected_gdf.geometry.centroid  # Calculate centroids
    
    # Re-project centroids back to EPSG:4326 for use in the map
    centroids_in_4326 = projected_gdf.set_geometry('centroid').to_crs("EPSG:4326")
    small_areas_gdf['latitude'] = centroids_in_4326.geometry.y
    small_areas_gdf['longitude'] = centroids_in_4326.geometry.x

    # Load employment CSV
    employed_df = pd.read_csv('/workspaces/Datathon_2024/data/num_of_people_working/fjoldi_starfandi.csv')
    employed_df.rename(columns={'smasvaedi': 'smsv'}, inplace=True)
    employed_df['smsv'] = employed_df['smsv'].astype(str).str.zfill(4)

    # Load population CSV
    population_df = pd.read_csv('/workspaces/Datathon_2024/data/num_of_residents/ibuafjoldi.csv')
    population_df.rename(columns={'smasvaedi': 'smsv'}, inplace=True)
    population_df['smsv'] = population_df['smsv'].astype(str).str.zfill(4)

    return small_areas_gdf, employed_df, population_df

small_areas_gdf, employed_df, population_df = load_data()

# Sidebar Widgets
st.sidebar.title("GeoJSON File Selection")
selected_file = st.sidebar.radio(
    "Select City Lane GeoJSON File:",
    options=[
        "City Line 2025",
        "City Line 2029",
        "City Line 2030"
    ],
    index=0  # Default selection
)

# Map file names to paths
geojson_file_mapping = {
    "City Line 2025": '/workspaces/Datathon_2024/data/geojson_files/cityline_2025.geojson',
    "City Line 2029": '/workspaces/Datathon_2024/data/geojson_files/cityline_2029.geojson',
    "City Line 2030": '/workspaces/Datathon_2024/data/geojson_files/cityline_2030.geojson',
}

# Load the selected GeoJSON file
selected_file_path = geojson_file_mapping[selected_file]
city_lane_gdf = gpd.read_file(selected_file_path).to_crs("EPSG:4326")

# Group points by line and create LineStrings
def create_linestring(group):
    group = group.drop(columns="line")  # Exclude the grouping column explicitly
    points = group.sort_values("id").geometry.tolist()
    if len(points) > 1:  # Only create LineString if there are at least 2 points
        return LineString(points)
    return None  # Return None for invalid groups

line_strings = city_lane_gdf.groupby("line", group_keys=False).apply(create_linestring)

# Filter out None values (invalid LineStrings)
line_strings = line_strings[line_strings.notnull()]

# Convert LineStrings to a GeoDataFrame
city_lane_paths = gpd.GeoDataFrame(
    {"line": line_strings.index, "geometry": line_strings}, crs="EPSG:4326"
)

# Extract coordinates for Pydeck
city_lane_paths["coordinates"] = city_lane_paths.geometry.apply(
    lambda geom: list(geom.coords) if geom else None
)

# Line selection and thickness control
st.sidebar.title("Visualization Filters")
selected_year = st.sidebar.slider("Select Year", min_value=2020, max_value=2025, value=2024)
show_city_lane = st.sidebar.checkbox("Show City Lane", value=True)
if show_city_lane:
    line_thickness = st.sidebar.slider("Line Thickness", min_value=20, max_value=50, value=30)

# Filter data for the selected year
population_filtered = population_df[population_df['ar'] == selected_year]
employed_filtered = employed_df[employed_df['ar'] == selected_year]

# Merge with small areas for spatial data
population_filtered = population_filtered.merge(small_areas_gdf[['smsv', 'latitude', 'longitude']], on='smsv', how='left')
employed_filtered = employed_filtered.merge(small_areas_gdf[['smsv', 'latitude', 'longitude']], on='smsv', how='left')

# Map Visualization
st.title("City Planning Visualization")
layers = []

# Population Layer
if not population_filtered.empty:
    population_layer = pdk.Layer(
        "ScatterplotLayer",
        data=population_filtered.dropna(subset=['latitude', 'longitude']),
        get_position=["longitude", "latitude"],
        get_radius=200,
        get_color="[0, 128, 255, 160]",
        pickable=True,
    )
    layers.append(population_layer)

# Employment Layer
if not employed_filtered.empty:
    employment_layer = pdk.Layer(
        "ScatterplotLayer",
        data=employed_filtered.dropna(subset=['latitude', 'longitude']),
        get_position=["longitude", "latitude"],
        get_radius=200,
        get_color="[255, 0, 128, 160]",
        pickable=True,
    )
    layers.append(employment_layer)

# City Lane Layer
if show_city_lane:
    city_lane_layer = pdk.Layer(
        "PathLayer",
        data=city_lane_paths.dropna(subset=["coordinates"]),
        get_path="coordinates",
        get_width=line_thickness,
        get_color="[255, 0, 0]",
        pickable=True
    )
    layers.append(city_lane_layer)

# Set the map view
view_state = pdk.ViewState(
    latitude=small_areas_gdf['latitude'].mean(),
    longitude=small_areas_gdf['longitude'].mean(),
    zoom=10,
    pitch=50,
)

# Render the map
if layers:
    st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=view_state))
else:
    st.error("No data available to display.")

# Summary Section
st.sidebar.markdown("### Summary Statistics")
st.sidebar.write("Population Data:", population_filtered.describe())
st.sidebar.write("Employment Data:", employed_filtered.describe())
