# Lake Buhi Flood Prediction System

A ConvLSTM-based deep learning system for predicting flood risks and lake level dynamics at Lake Buhi, Camarines Sur, Philippines.

## 🌊 Project Overview

This project uses a trained Convolutional LSTM (ConvLSTM) neural network to forecast:
- **6-hour lake level predictions** based on 12-hour historical rainfall and lake level observations
- **Flood extent and depth** visualizations using flood modeling
- **Warning levels** (Normal, Alert, Alarm, Critical) based on predicted lake levels
- **Real-time risk assessments** through a REST API and interactive dashboard

The system is designed for early warning and disaster management of flood risks in Lake Buhi.

## 📁 Project Structure

```
FloodPredictionConvLSTM/
├── model/                          # All model artifacts and data
│   ├── best_model.keras           # Trained ConvLSTM model
│   ├── dem_small.npy              # Digital Elevation Model
│   ├── dem_small_norm.npy         # Normalized DEM
│   ├── lake_small.npy             # Lake mask
│   ├── normalization_params.json  # Data normalization parameters
│   ├── dem_metadata.json          # DEM metadata and bounds
│   ├── sequence_metadata.json     # Sequence information
│   ├── BUHI_LAKE.*                # Geographic data (shapefiles)
│   ├── BUHI_DTM.tif               # Digital Terrain Model
│   └── Buhi_ConvLSTM_V3.ipynb     # Training notebook
│
├── api/                            # REST API Server
│   ├── app.py                     # FastAPI application entry point
│   ├── model_loader.py            # Model loading utilities
│   ├── flood.py                   # Flood estimation algorithms
│   ├── utils.py                   # Image rendering utilities
│   ├── __init__.py
│   └── API_README.md              # API documentation
│
├── dashboard/                      # Streamlit Dashboard
│   ├── dash.py                    # Interactive dashboard application
│   ├── README.md                  # Dashboard documentation
│
├── requirements.txt               # Python dependencies
├── README.md                      # This file
└── thesis_env/                    # Python virtual environment
```

See [dashboard/README.md](dashboard/README.md) for full dashboard documentation.

## 🧠 Model Details

### Architecture
- **Model Type:** Convolutional LSTM (ConvLSTM)
- **Input:** 12-hour sequences of rainfall and lake level data
- **Output:** 6-hour forecast of lake levels and flood extents
- **Framework:** TensorFlow/Keras

### Data Files
- **DEM (Digital Elevation Model):** 30m resolution elevation data
- **Lake Mask:** Binary mask identifying lake boundaries
- **Normalization Parameters:** Mean and std for input normalization

### Model Performance
- See `Buhi_ConvLSTM_V3.ipynb` for training notebook and results

## 🛠 Development

### Project Components

1. **API (`api/`):** FastAPI REST service for model inference
   - Handles prediction requests
   - Generates flood visualizations
   - Manages model state and caching

2. **Dashboard (`dashboard/`):** Streamlit web interface
   - User-friendly input form
   - Interactive map visualizations
   - Forecast history management

3. **Model (`model/`):** All model artifacts and training data
   - Trained weights and architecture
   - Input data (DEM, lake mask, normalization parameters)
   - Training notebooks

## 👥 Contributors/Researchers

- Bianca Natalie M. Labrador (BS Computer Science)
- Selwyn L. Lao (BS Computer Science)

## 🙏 Acknowledgments

- Hydrological Data provided by PAGASA - BRBFFWC
- IFSAR DEM provided by NAMRIA

---

**Last Updated:** April 2026
