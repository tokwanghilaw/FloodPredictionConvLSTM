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

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Windows/Linux/macOS
- Virtual environment manager (venv, conda, etc.)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/FloodPredictionConvLSTM.git
   cd FloodPredictionConvLSTM
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv thesis_env
   
   # On Windows:
   thesis_env\Scripts\activate
   
   # On Linux/macOS:
   source thesis_env/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 📊 Usage

### Running the REST API

The API serves the model predictions as a REST service with Swagger documentation.

```bash
# Navigate to project root
cd FloodPredictionConvLSTM

# Start the API server
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API Base URL:** `http://localhost:8000`
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

**Example API Request:**
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "rainfall": [0, 0.5, 2, 5, 10, 15, 25, 35, 45, 40, 30, 20],
    "lake_level": [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.78, 0.80, 0.83, 0.86, 0.90, 0.95]
  }'
```

See [API_README.md](api/API_README.md) for full API documentation.

### Running the Dashboard

The dashboard provides an interactive interface for flood forecasting.

```bash
# Navigate to dashboard folder
cd dashboard

# Start the Streamlit app
streamlit run dash.py
```

The dashboard will open in your browser at `http://localhost:8501`

**Features:**
- Input 12-hour rainfall and lake level observations
- View 6-hour flood forecasts
- Interactive maps with flood extent overlays
- Real-time warning levels and statistics
- Save and load historical forecasts

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
- Trained on historical rainfall and lake level data
- Evaluated on held-out test set
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

### Adding Features

To extend the system:

1. **New API Endpoints:** Edit `api/app.py`
2. **New Visualizations:** Update `api/utils.py` or `dashboard/dash.py`
3. **Model Improvements:** Retrain using `model/Buhi_ConvLSTM_V3.ipynb`

## 📋 Requirements

Key dependencies (see `requirements.txt` for complete list):
- TensorFlow/Keras - Deep learning framework
- FastAPI - REST API framework
- Streamlit - Dashboard framework
- NumPy, Pandas - Data processing
- Matplotlib, Folium - Visualization
- Requests - HTTP client

## 🌍 Deployment

### API Deployment
The API can be deployed to cloud platforms:
- Render (supports Python/Uvicorn)
- AWS Lambda, EC2
- Google Cloud Run
- Azure App Service

### Dashboard Deployment
The dashboard can be deployed to:
- Streamlit Cloud (recommended)
- Heroku
- AWS, Google Cloud, Azure

Current production endpoints:
- **API:** https://floodpredictionconvlstm.onrender.com
- **Dashboard:** Deployed on Streamlit Cloud

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

## 👥 Contributors

- Aslita Cabalo - Developer/Researcher

## 📧 Contact

For questions or issues, please open an issue on GitHub or contact the project maintainers.

## 🙏 Acknowledgments

- Lake Buhi data provided by [Local Water Authority]
- Inspired by ConvLSTM research and flood prediction studies
- Built with TensorFlow, FastAPI, and Streamlit

---

**Last Updated:** April 2026
