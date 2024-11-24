import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk

# Load datasets (adjust paths as needed)
@st.cache_data
def load_data():
    small_areas_gdf = gpd.read_file('/workspaces/Datathon_2024/data/smasvaedi/smasvaedi_2021.json')
    # Inspect GeoJSON data
    # Select the necessary columns
    smasvaedi_filtered = small_areas_gdf[['smsv', 'smsv_label_en', 'geometry']]
    
    # Filter rows where nuts3 is '001'
    smasvaedi_filtered = smasvaedi_filtered[small_areas_gdf['nuts3'] == '001']
    
    #change smsv to int
    smasvaedi_filtered['smsv'] = smasvaedi_filtered['smsv'].astype(str)
    #change label to string
    smasvaedi_filtered['smsv_label_en'] = smasvaedi_filtered['smsv_label_en'].astype(str)
    #get all the unique smsv values and save them in an array
    smsv_arr = smasvaedi_filtered['smsv'].unique()
    
    # Create a new list with the additional numbers
    new_numbers =['0020' ,'0035', '0018', '0022', '0013' ,'0034', '0033' ,'0026' ,'0048' ,'0186','0019' , '0011' ,'0042', '0039', '0053' ,'0024', '0176', '0004', '0192','0060', '0028', '0043' ,'0037']
    
    # Convert smsv_arr to a list
    smsv_arr = smsv_arr.tolist()
    
    # Extend the smsv_arr list with the new numbers (more efficient than append for large lists)
    smsv_arr.extend(new_numbers)
    small_areas_gdf = smasvaedi_filtered
    city_lane_gdf = gpd.read_file('/workspaces/Datathon_2024/data/geojson_files/cityline_2025.geojson')

    employed_df = pd.read_csv('/workspaces/Datathon_2024/data/num_of_people_working/fjoldi_starfandi.csv')
    # Rename 'smasvaedi' to 'smsv' if not already done
    employed_df.rename(columns={'smasvaedi': 'smsv'}, inplace=True)
    
    #change smsv to int
    employed_df['smsv'] = employed_df['smsv'].astype(str).str.zfill(4)
    #check if smsv values from employed_df are in smsv_arr  if not then filter them out
    employed_df = employed_df[employed_df['smsv'].isin(smsv_arr)]
    

    population_df = pd.read_csv('/workspaces/Datathon_2024/data/num_of_residents/ibuafjoldi.csv')
    #rename column name from smasvaedi to smsv
    population_df.rename(columns={'smasvaedi': 'smsv'}, inplace=True)
    
    population_df['smsv'] = population_df['smsv'].astype(str).str.zfill(4)
    
    #check if smsv values from population_df are in smsv_arr  if not then filter them out
    population_df = population_df[population_df['smsv'].isin(smsv_arr)]

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
    st.subheader("Optimal Train Stop Points")
    
    # Ensure latitude and longitude are numeric
    if 'latitude' in population_filtered.columns and population_filtered['latitude'].dtype == 'object':
        population_filtered['latitude'] = pd.to_numeric(population_filtered['latitude'], errors='coerce')
    if 'longitude' in population_filtered.columns and population_filtered['longitude'].dtype == 'object':
        population_filtered['longitude'] = pd.to_numeric(population_filtered['longitude'], errors='coerce')
    
    # Drop any non-numeric columns for aggregation
    try:
        optimal_points = population_filtered.groupby("smsv")[["latitude", "longitude"]].mean()
        optimal_points = optimal_points.dropna()  # Remove rows with missing lat/lon values
    except KeyError as e:
        st.error(f"KeyError encountered: {str(e)}")
        optimal_points = pd.DataFrame(columns=["latitude", "longitude"])  # Empty DataFrame to avoid further errors
    
    # Display the map if we have valid points
    if not optimal_points.empty:
        st.map(optimal_points)
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
