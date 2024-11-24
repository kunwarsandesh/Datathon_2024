import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk

# Load datasets (adjust paths as needed)
@st.cache_data
def load_data():
    small_areas_gdf = gpd.read_file('/workspaces/Datathon_2024/data/smasvaedi/smasvaedi_2021.json')
    city_lane_gdf = gpd.read_file('/workspaces/Datathon_2024/data/geojson_files/cityline_2025.geojson')
    employed_df = pd.read_csv('/workspaces/Datathon_2024/data/num_of_people_working/fjoldi_starfandi.csv')
    population_df = pd.read_csv('/workspaces/Datathon_2024/data/num_of_residents/ibuafjoldi.csv')
    return small_areas_gdf, city_lane_gdf, employed_df, population_df


small_areas_gdf, city_lane_gdf, employed_df, population_df = load_data()

# Sidebar Widgets
st.sidebar.title("Visualization Filters")
selected_year = st.sidebar.slider("Select Year", min_value=2020, max_value=2025, value=2024)
dataset_choice = st.sidebar.selectbox("Select Dataset", ["Population", "Employment", "City Lane"])
map_type = st.sidebar.selectbox("Select Map Type", ["Scatter", "Heatmap"])

# Data Filtering
population_filtered = population_df[population_df['ar'] == selected_year]
employed_filtered = employed_df[employed_df['ar'] == selected_year]

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
    map_data = city_lane_gdf.rename(columns={"geometry": "location"})

# Pydeck Map
if dataset_choice in ["Population", "Employment"]:
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
    # Print out the columns of population_filtered to see what's available
    st.write("Columns in population_filtered:", population_filtered.columns.tolist())

    st.subheader("Optimal Train Stop Points")

    if 'small_area_id' in population_filtered.columns:
        optimal_points = population_filtered.groupby("small_area_id").mean()[["latitude", "longitude"]]
    elif 'smsv' in population_filtered.columns:
        optimal_points = population_filtered.groupby("smsv").mean()[["latitude", "longitude"]]
    else:
        st.error("Column for small areas not found in the dataset.")


    st.map(optimal_points)

# Summary Section
st.sidebar.markdown("### Summary Statistics")
if dataset_choice == "Population":
    st.sidebar.write(population_filtered.describe())
elif dataset_choice == "Employment":
    st.sidebar.write(employed_filtered.describe())
else:
    st.sidebar.write(city_lane_gdf.describe())
