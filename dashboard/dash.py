import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import base64

# --- CONFIGURATION ---
# Replace with your actual Render URL (e.g., https://your-app.onrender.com)
API_BASE_URL = "http://localhost:8000" 

st.set_page_config(page_title="Lake Buhi Flood Dashboard", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .metric-container { background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

## --- 1. SIDEBAR: DATA ENTRY ---
st.sidebar.header("📥 Input Observations (12-hr)")
st.sidebar.info("Enter 12 hourly values separated by commas.")

rain_str = st.sidebar.text_area("Rainfall (mm)", "0, 0.5, 2, 5, 10, 15, 25, 35, 45, 40, 30, 20")
lake_str = st.sidebar.text_area("Lake Level (m)", "0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.78, 0.80, 0.83, 0.86, 0.90, 0.95")

if st.sidebar.button("🚀 Run 6-Hour Forecast"):
    try:
        # Convert comma strings to list of floats
        rain_list = [float(x.strip()) for x in rain_str.split(',')]
        lake_list = [float(x.strip()) for x in lake_str.split(',')]
        
        if len(rain_list) != 12 or len(lake_list) != 12:
            st.error("Please ensure exactly 12 values are entered for both fields.")
        else:
            with st.spinner("API is calculating flood dynamics..."):
                payload = {"rainfall": rain_list, "lake_level": lake_list}
                response = requests.post(f"{API_BASE_URL}/predict", json=payload)
                response.raise_for_status()
                st.session_state['api_data'] = response.json()
                st.success("Forecast Updated!")
    except Exception as e:
        st.error(f"Connection Error: {e}")

## --- 2. MAIN INTERFACE ---
st.title("🌊 Lake Buhi Flood Forecast System")

if 'api_data' in st.session_state:
    data = st.session_state['api_data']
    
    # 6-Hour Time Slider
    hour_idx = st.select_slider(
        "Select Forecast Progression (Hours Ahead)",
        options=range(1, 7),
        format_func=lambda x: f"+{x} Hour{'s' if x > 1 else ''}"
    )
    
    # Get specific hour result (index is hour_idx - 1)
    current_hour = data['hours'][hour_idx - 1]
    bounds = data['bounds']
    
    # --- UI COLUMNS ---
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create Folium Map
        center_lat = (bounds['south'] + bounds['north']) / 2
        center_lon = (bounds['west'] + bounds['east']) / 2
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="cartodbpositron")
        
        # Add the Static Lake Mask
        lake_img = f"data:image/png;base64,{data['lake_png']}"
        folium.raster_layers.ImageOverlay(
            image=lake_img,
            bounds=[[bounds['south'], bounds['west']], [bounds['north'], bounds['east']]],
            opacity=0.4,
            name="Static Lake"
        ).add_to(m)

        # Add the Dynamic Flood Depth Overlay
        flood_img = f"data:image/png;base64,{current_hour['flood_depth_png']}"
        folium.raster_layers.ImageOverlay(
            image=flood_img,
            bounds=[[bounds['south'], bounds['west']], [bounds['north'], bounds['east']]],
            opacity=0.7,
            name="Flood Depth Overlay"
        ).add_to(m)
        
        st_folium(m, width=800, height=500)

    with col2:
        # Warning Badge
        st.markdown(f"### Status: <span style='color:{current_hour['warning_color']}'>{current_hour['warning_level']}</span>", unsafe_allow_html=True)
        
        # Metrics
        st.metric("Predicted Lake Level", f"{current_hour['predicted_level_m']} m")
        st.metric("Max Flood Depth", f"{current_hour['max_depth_m']} m")
        st.metric("Avg Flood Depth", f"{current_hour['mean_depth_m']} m")
        
        # Land Cover Calculation (Area calculation)
        # Note: 1 pixel is approx 0.0009 km2 (30m x 30m). Adjust if your res is different.
        area_km2 = current_hour['flooded_pixels'] * (0.03 * 0.03) 
        st.metric("Estimated Area Covered", f"{area_km2:.2f} km²")
        
        st.progress(current_hour['flooded_land_pct'] / 100, text=f"Land Submerged: {current_hour['flooded_land_pct']}%")

else:
    st.info("👈 Enter the 12-hour rainfall and lake level data in the sidebar and click 'Run Forecast' to begin.")