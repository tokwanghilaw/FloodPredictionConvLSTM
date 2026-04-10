# Flood Prediction Dashboard

This dashboard provides a web interface for flood prediction using a ConvLSTM model.

## Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended: thesis_env)

## Installation

1. Activate the virtual environment:
   ```
   & thesis_env\Scripts\Activate.ps1
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Dashboard

The dashboard consists of two components: a FastAPI backend and a Streamlit frontend. Run them in separate terminals.

### Terminal 1: Start the API
```
python -m uvicorn api.app:app
```

This starts the FastAPI server on `http://127.0.0.1:8000` (default).

### Terminal 2: Start the Streamlit App
```
python -m streamlit run dashboard/dash.py
```

This starts the Streamlit app on `http://localhost:8501` (default).

## Usage

Open your browser and navigate to the Streamlit app URL to interact with the dashboard. The API provides endpoints for predictions.