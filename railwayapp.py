import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk




# Load datasets (adjust paths as needed)
@st.cache_data
def load_data():
    

    small_areas_gdf = gpd.read_file('/workspaces/Datathon_2024/data/smasvaedi/smasvaedi_2021.json')

    # Filter rows where nuts3 is '001'
    smasvaedi_filtered = small_areas_gdf[small_areas_gdf['nuts3'] == '001']

    # Select the necessary columns
    smasvaedi_filtered = smasvaedi_filtered[['smsv', 'smsv_label_en', 'geometry']]
    

    
    # Change smsv to str
    smasvaedi_filtered['smsv'] = smasvaedi_filtered['smsv'].astype(str)
    # Get all the unique smsv values and save them in an array
    smsv_arr = smasvaedi_filtered['smsv'].unique()
    
    # Create a new list with the additional numbers
    new_numbers = ['0020', '0035', '0018', '0022', '0013', '0034', '0033', '0026', '0048', '0186', '0019', '0011', '0042', '0039', '0053', '0024', '0176', '0004', '0192', '0060', '0028', '0043', '0037']
    
    # Convert smsv_arr to a list
    smsv_arr = smsv_arr.tolist()
    
    # Extend the smsv_arr list with the new numbers
    smsv_arr.extend(new_numbers)
    small_areas_gdf = smasvaedi_filtered
    city_lane_gdf = gpd.read_file('/workspaces/Datathon_2024/data/geojson_files/cityline_2025.geojson')

    employed_df = pd.read_csv('/workspaces/Datathon_2024/data/num_of_people_working/fjoldi_starfandi.csv')
    # Rename 'smasvaedi' to 'smsv' if not already done
    employed_df.rename(columns={'smasvaedi': 'smsv'}, inplace=True)
    
    # Change smsv to str and pad with leading zeros to ensure 4 digits
    employed_df['smsv'] = employed_df['smsv'].astype(str).str.zfill(4)
    # Check if smsv values from employed_df are in smsv_arr and filter accordingly
    employed_df = employed_df[employed_df['smsv'].isin(smsv_arr)]
    
    population_df = pd.read_csv('/workspaces/Datathon_2024/data/num_of_residents/ibuafjoldi.csv')
    # Rename column name from smasvaedi to smsv
    population_df.rename(columns={'smasvaedi': 'smsv'}, inplace=True)
    population_df['smsv'] = population_df['smsv'].astype(str).str.zfill(4)
    # Filter based on smsv array
    population_df = population_df[population_df['smsv'].isin(smsv_arr)]

    return small_areas_gdf, city_lane_gdf, employed_df, population_df

small_areas_gdf, city_lane_gdf, employed_df, population_df = load_data()

# Calculate centroids for geometry and create latitude and longitude columns
small_areas_gdf['centroid'] = small_areas_gdf.geometry.centroid
small_areas_gdf['latitude'] = small_areas_gdf.centroid.y
small_areas_gdf['longitude'] = small_areas_gdf.centroid.x

# Sidebar Widgets
st.sidebar.title("Visualization Filters")
selected_year = st.sidebar.slider("Select Year", min_value=2020, max_value=2025, value=2024)
dataset_choice = st.sidebar.selectbox("Select Dataset", ["Population", "Employment", "City Lane"])
map_type = st.sidebar.selectbox("Select Map Type", ["Scatter", "Heatmap"])

# Data Filtering
population_filtered = population_df[population_df['ar'] == selected_year]
employed_filtered = employed_df[employed_df['ar'] == selected_year]

# Merge population and employment data with spatial data to get lat/lon
population_filtered = population_filtered.merge(small_areas_gdf[['smsv', 'latitude', 'longitude']], on='smsv', how='left')
employed_filtered = employed_filtered.merge(small_areas_gdf[['smsv', 'latitude', 'longitude']], on='smsv', how='left')

# Map Visualization
st.title("City Planning Visualization")
if dataset_choice == "Population":
    st.subheader("Population Distribution")
    map_data = population_filtered.rename(columns={"fjoldi": "count"})
elif dataset_choice == "Employment":
    st.subheader("Employment Distribution")
    map_data = employed_filtered.rename(columns={"fjoldi": "count"})
else:
    st.subheader("City Lane Visualization")
    map_data = city_lane_gdf

# Pydeck Map
if dataset_choice in ["Population", "Employment"]:
    # Ensure data is in the right format for Pydeck
    map_data = map_data.dropna(subset=['latitude', 'longitude'])
    layer = pdk.Layer(
        "ScatterplotLayer" if map_type == "Scatter" else "HeatmapLayer",
        data=map_data,
        get_position=["longitude", "latitude"],
        get_radius=200 if map_type == "Scatter" else 1000,
        get_color="[200, 30, 0, 160]" if map_type == "Scatter" else None,
        aggregation="mean" if map_type == "Heatmap" else None,
    )
    view_state = pdk.ViewState(latitude=64.1355, longitude=-21.8954, zoom=10)
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))

# Optimal Train Stop Points
if st.checkbox("Show Suggested Train Stops"):
    st.subheader("Optimal Train Stop Points")

    # Ensure population_filtered has valid lat/lon
    optimal_points = population_filtered.dropna(subset=['latitude', 'longitude'])
    if not optimal_points.empty:
        # Display the map with optimal points
        st.map(optimal_points[['latitude', 'longitude']])
    else:
        st.error("No optimal points to display.")

# Summary Section
st.sidebar.markdown("### Summary Statistics")
if dataset_choice == "Population":
    st.sidebar.write(population_filtered.describe())
elif dataset_choice == "Employment":
    st.sidebar.write(employed_filtered.describe())
else:
    st.sidebar.write(city_lane_gdf.describe())
