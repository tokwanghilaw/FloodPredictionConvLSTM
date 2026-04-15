import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import base64
import matplotlib.pyplot as plt
import matplotlib as mpl
from io import BytesIO

API_BASE_URL = "https://floodpredictionconvlstm.onrender.com"

st.set_page_config(page_title="Lake Buhi Flood Dashboard", layout="wide")

st.markdown("""
    <style>
    .metric-container { background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

##SIDEBAR
st.sidebar.header("Input Observations (12-hr)")
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
            st.session_state['rain_list'] = rain_list
            st.session_state['lake_list'] = lake_list
            with st.spinner("API is calculating flood dynamics..."):
                payload = {"rainfall": rain_list, "lake_level": lake_list}
                response = requests.post(f"{API_BASE_URL}/predict", json=payload)
                response.raise_for_status()
                st.session_state['api_data'] = response.json()
                st.success("Forecast Updated!")
    except Exception as e:
        st.error(f"Connection Error: {e}")

##MAIN INTERFACE
st.title("Lake Buhi Flood Forecast System")

st.warning("""
**⚠️ Decision Support Tool Disclaimer**

This flood prediction system is a **decision-support tool** designed to assist in flood risk assessment and planning. It is **not** a definitive forecast and should not be used as the sole basis for emergency response or evacuation decisions.

Use this tool in conjunction with other flood monitoring resources and professional judgment.
""")

view_mode = st.sidebar.radio("Choose View", ["Live Forecast", "Saved Forecasts"])

if view_mode == "Saved Forecasts":
    st.header("📄 Saved Forecasts")

    try:
        response = requests.get(f"{API_BASE_URL}/saved")
        response.raise_for_status()
        saved_items = response.json()
    except Exception as e:
        saved_items = []
        st.error(f"Could not load saved forecasts: {e}")

    if saved_items:
        saved_options = [
            f"{item.get('created_at', 'unknown')} · {item.get('id', '')[:8]}"
            for item in saved_items
        ]
        selected_index = st.selectbox("Select a saved forecast", range(len(saved_options)), format_func=lambda i: saved_options[i])
        selected = saved_items[selected_index]
        forecast = selected.get('forecast', {})
        bounds = forecast.get('bounds', {})

        st.markdown(f"**Saved at:** {selected.get('created_at', 'unknown')}  ")
        st.markdown(f"**Forecast ID:** `{selected.get('id', '')}`")
        st.markdown(f"**Rainfall inputs:** {selected.get('rainfall', [])}")
        st.markdown(f"**Lake level inputs:** {selected.get('lake_level', [])}")

        if forecast and bounds:
            hour_idx = st.select_slider(
                "Select Forecast Progression (Hours Ahead)",
                options=range(1, 7),
                format_func=lambda x: f"+{x} Hour{'s' if x > 1 else ''}"
            )

            current_hour = forecast['hours'][hour_idx - 1]

            # Compute global max depth for colorbar
            max_depth = max(h['max_depth_m'] for h in forecast['hours'])

            col1, col2 = st.columns([2, 1])
            with col1:
                center_lat = (bounds['south'] + bounds['north']) / 2
                center_lon = (bounds['west'] + bounds['east']) / 2
                m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="cartodbpositron")

                lake_img = f"data:image/png;base64,{forecast['lake_png']}"
                folium.raster_layers.ImageOverlay(
                    image=lake_img,
                    bounds=[[bounds['south'], bounds['west']], [bounds['north'], bounds['east']]],
                    opacity=0.4,
                    name="Static Lake"
                ).add_to(m)

                flood_img = f"data:image/png;base64,{current_hour['flood_depth_png']}"
                folium.raster_layers.ImageOverlay(
                    image=flood_img,
                    bounds=[[bounds['south'], bounds['west']], [bounds['north'], bounds['east']]],
                    opacity=0.7,
                    name="Flood Depth Overlay"
                ).add_to(m)

                # Add colorbar legend if max_depth > 0
                if max_depth > 0:
                    fig, ax = plt.subplots(figsize=(0.7, 5.5))
                    cmap = mpl.cm.plasma
                    norm = mpl.colors.Normalize(vmin=0, vmax=max_depth)
                    cb = mpl.colorbar.ColorbarBase(ax, cmap=cmap, norm=norm, orientation='vertical')
                    cb.set_label('Flood Depth (m)', fontsize=10)
                    buf = BytesIO()
                    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
                    buf.seek(0)
                    colorbar_b64 = base64.b64encode(buf.read()).decode('utf-8')
                    plt.close(fig)

                    html = f'''
                    <div style="position: fixed; bottom: 50px; left: 50px; width: 90px; height: 260px; background-color: white; border:2px solid grey; z-index:9999; padding: 5px;">
                    <img src="data:image/png;base64,{colorbar_b64}" style="width:100%; height:100%; object-fit: contain;">
                    </div>
                    '''
                    m.get_root().html.add_child(folium.Element(html))

                st_folium(m, width=820, height=560)

            with col2:
                st.markdown(f"### Status: <span style='color:{current_hour['warning_color']}'>{current_hour['warning_level']}</span>", unsafe_allow_html=True)
                st.metric("Predicted Lake Level", f"{current_hour['predicted_level_m']} m")
                st.metric("Max Flood Depth", f"{current_hour['max_depth_m']} m")
                st.metric("Avg Flood Depth", f"{current_hour['mean_depth_m']} m")

                area_km2 = current_hour['flooded_pixels'] * (0.03 * 0.03)
                st.metric("Estimated Area Covered", f"{area_km2:.2f} km²")
                st.metric("Map Resolution", "30m per pixel")
                st.progress(current_hour['flooded_land_pct'] / 100, text=f"Land Submerged: {current_hour['flooded_land_pct']}%")
        else:
            st.warning("Saved forecast data is missing required display fields.")
    else:
        st.info("No saved forecasts found. Run a live forecast and save it from the Live Forecast view.")

else:
    if 'api_data' in st.session_state:
        data = st.session_state['api_data']
        
        # 6-Hour Time Slider
        hour_idx = st.select_slider(
            "Select Forecast Progression (Hours Ahead)",
            options=range(1, 7),
            format_func=lambda x: f"+{x} Hour{'s' if x > 1 else ''}"
        )
        
        #specific hour result (index is hour_idx - 1)
        current_hour = data['hours'][hour_idx - 1]
        bounds = data['bounds']
        
        # Compute global max depth for colorbar
        max_depth = max(h['max_depth_m'] for h in data['hours'])
        
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
            
            # Add colorbar legend if max_depth > 0
            if max_depth > 0:
                fig, ax = plt.subplots(figsize=(1, 6))
                cmap = mpl.cm.plasma
                norm = mpl.colors.Normalize(vmin=0, vmax=max_depth)
                cb = mpl.colorbar.ColorbarBase(ax, cmap=cmap, norm=norm, orientation='vertical')
                cb.set_label('Flood Depth (m)', fontsize=10)
                buf = BytesIO()
                fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
                buf.seek(0)
                colorbar_b64 = base64.b64encode(buf.read()).decode('utf-8')
                plt.close(fig)

                html = f'''
                <div style="position: fixed; bottom: 50px; left: 50px; width: 90px; height: 260px; background-color: white; border:2px solid grey; z-index:9999; padding: 5px;">
                <img src="data:image/png;base64,{colorbar_b64}" style="width:100%; height:100%; object-fit: contain;">
                </div>
                '''
                m.get_root().html.add_child(folium.Element(html))
            
            st_folium(m, width=820, height=560)

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
            st.metric("Map Resolution", "30m per pixel")
            
            st.progress(current_hour['flooded_land_pct'] / 100, text=f"Land Submerged: {current_hour['flooded_land_pct']}%")

            # Save Forecast Button
            if st.button("💾 Save Forecast"):
                try:
                    payload = {
                        "rainfall": st.session_state['rain_list'],
                        "lake_level": st.session_state['lake_list'],
                        "forecast": data
                    }
                    response = requests.post(f"{API_BASE_URL}/save", json=payload)
                    response.raise_for_status()
                    st.success("Forecast saved to database!")
                except Exception as e:
                    st.error(f"Failed to save forecast: {e}")

    else:
        st.info("👈 Enter the 12-hour rainfall and lake level data in the sidebar and click 'Run Forecast' to begin.")