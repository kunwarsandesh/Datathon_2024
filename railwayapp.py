import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk

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

    # Load city lane GeoJSON and create line segments
    city_lane_gdf = gpd.read_file('/workspaces/Datathon_2024/data/geojson_files/cityline_2025.geojson')
    city_lane_gdf = city_lane_gdf.to_crs("EPSG:4326")  # Transform to EPSG:4326
    
    # Create line segments from consecutive points
    line_segments = []
    coords = city_lane_gdf.geometry.tolist()
    for i in range(len(coords)-1):
        start_point = coords[i]
        end_point = coords[i+1]
        line_segments.append({
            'line': city_lane_gdf.iloc[i]['line'],
            'segment': [[start_point.x, start_point.y], [end_point.x, end_point.y]]
        })
    
    city_lane_df = pd.DataFrame(line_segments)

    # Load employment CSV
    employed_df = pd.read_csv('/workspaces/Datathon_2024/data/num_of_people_working/fjoldi_starfandi.csv')
    employed_df.rename(columns={'smasvaedi': 'smsv'}, inplace=True)
    employed_df['smsv'] = employed_df['smsv'].astype(str).str.zfill(4)

    # Load population CSV
    population_df = pd.read_csv('/workspaces/Datathon_2024/data/num_of_residents/ibuafjoldi.csv')
    population_df.rename(columns={'smasvaedi': 'smsv'}, inplace=True)
    population_df['smsv'] = population_df['smsv'].astype(str).str.zfill(4)

    return small_areas_gdf, city_lane_df, employed_df, population_df

small_areas_gdf, city_lane_df, employed_df, population_df = load_data()

# Sidebar Widgets
st.sidebar.title("Visualization Filters")
selected_year = st.sidebar.slider("Select Year", min_value=2020, max_value=2025, value=2024)
map_type = st.sidebar.selectbox("Select Map Type", ["Scatter", "Heatmap"])
show_city_lane = st.sidebar.checkbox("Show City Lane")

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
        "ScatterplotLayer" if map_type == "Scatter" else "HeatmapLayer",
        data=population_filtered.dropna(subset=['latitude', 'longitude']),
        get_position=["longitude", "latitude"],
        get_radius=200 if map_type == "Scatter" else 1000,
        get_color="[0, 128, 255, 160]" if map_type == "Scatter" else None,
        pickable=True,
    )
    layers.append(population_layer)

# Employment Layer
if not employed_filtered.empty:
    employment_layer = pdk.Layer(
        "ScatterplotLayer" if map_type == "Scatter" else "HeatmapLayer",
        data=employed_filtered.dropna(subset=['latitude', 'longitude']),
        get_position=["longitude", "latitude"],
        get_radius=200 if map_type == "Scatter" else 1000,
        get_color="[255, 0, 128, 160]" if map_type == "Scatter" else None,
        pickable=True,
    )
    layers.append(employment_layer)

# City Lane Layer
if show_city_lane:
    city_lane_layer = pdk.Layer(
        "LineLayer",
        data=city_lane_df,
        get_source_position="segment[0]",
        get_target_position="segment[1]",
        get_color=[255, 0, 0],
        get_width=3,
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
