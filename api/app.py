"""
app.py — FastAPI Flood Prediction API for Lake Buhi
=====================================================
Serves the trained ConvLSTM model as a REST API that returns:
  - 6-hour lake level forecasts
  - Warning levels per hour
  - Flood extent/depth images as base64 PNGs (for map overlay)
  - Geographic bounds for placing the overlay on Leaflet/Mapbox

Run:
    cd "ConvLSTM Model v3"
    uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

Then open  http://localhost:8000/docs  for the interactive Swagger UI.
"""

from __future__ import annotations

import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"

from dotenv import load_dotenv # <--- ADD THIS
load_dotenv()                 # <--- ADD THIS

import numpy as np
import tensorflow as tf
from tensorflow import keras
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from supabase import create_client, Client

from api.model_loader import load_model, load_config
from api.flood import clean_lake_mask, estimate_flood, get_warning_level
from api.utils import (
    flood_depth_to_base64_png,
    flood_extent_to_base64_png,
    dem_to_base64_png,
    lake_mask_to_base64_png,
    get_image_bounds,
)

import tensorflow as tf
# Limit TensorFlow to use less memory
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    try:
        tf.config.set_logical_device_configuration(
            gpus[0],
            [tf.config.LogicalDeviceConfiguration(memory_limit=1024)])  # limit to ~1GB
    except RuntimeError as e:
        print(e)
else:
    # For CPU-only (Render free is CPU)
    tf.config.threading.set_intra_op_parallelism_threads(1)
    tf.config.threading.set_inter_op_parallelism_threads(1)

# 2. Tell the code to grab the keys from the "Environment"
# These names (in quotes) must match exactly what you type into Render later.
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# 3. Use those variables to start the client
supabase: Client = create_client(url, key)

# ---------------------------------------------------------------------------
# Paths — all .npy / .json / .keras files live in the model folder
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # project root
MODEL_DIR = PROJECT_ROOT / "model"  # model data folder
MODEL_PATH = MODEL_DIR / "best_model.keras"

# ---------------------------------------------------------------------------
# Global singletons (loaded once at startup)
# ---------------------------------------------------------------------------
_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model + static arrays once when the server starts."""
    print("Loading model and static data...")

    cfg = load_config(metadata_dir=MODEL_DIR)
    model = load_model(model_path=MODEL_PATH, metadata_dir=MODEL_DIR)

    dem = np.load(MODEL_DIR / "dem_small.npy")
    dem_norm = np.load(MODEL_DIR / "dem_small_norm.npy")
    lake_mask_raw = np.load(MODEL_DIR / "lake_small.npy")
    lake_mask = clean_lake_mask(lake_mask_raw)

    _state["model"] = model
    _state["cfg"] = cfg
    _state["dem"] = dem
    _state["dem_norm"] = dem_norm
    _state["lake_mask"] = lake_mask

    # Pre‑render static images (never changes)
    _state["dem_png"] = dem_to_base64_png(dem)
    _state["lake_png"] = lake_mask_to_base64_png(lake_mask)
    _state["bounds"] = get_image_bounds(cfg["dem_metadata"])

    print(f"  Model loaded from {MODEL_PATH}")
    print(f"  DEM shape: {dem.shape}")
    print(f"  Lake mask pixels: {int(lake_mask.sum())}")
    print("Ready to serve requests!")

    yield  # ← app is running

    _state.clear()


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Lake Buhi Flood Prediction API",
    description=(
        "ConvLSTM-based 6-hour flood forecast for Lake Buhi, Camarines Sur. "
        "Returns predicted lake levels, warning statuses, and flood-map "
        "overlays (base64 PNG) that can be displayed on a Leaflet/Mapbox map."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the frontend (any origin during dev) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://flood-prediction-app.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ForecastRequest(BaseModel):
    """12-hour input window of observed data."""
    rainfall: list[float] = Field(
        ...,
        min_length=12,
        max_length=12,
        description="12 hourly rainfall values in mm",
        json_schema_extra={"example": [0, 0.5, 2, 5, 10, 15, 25, 35, 45, 40, 30, 20]},
    )
    lake_level: list[float] = Field(
        ...,
        min_length=12,
        max_length=12,
        description="12 hourly lake/river level values in metres",
        json_schema_extra={"example": [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.78, 0.80, 0.83, 0.86, 0.90, 0.95]},
    )


class HourlyResult(BaseModel):
    hour: int = Field(description="Forecast hour (1–6)")
    predicted_level_m: float
    warning_level: str
    warning_color: str
    overflowing: bool
    overflow_depth_m: float
    water_surface_m: float
    flooded_land_pct: float
    max_depth_m: float
    mean_depth_m: float
    flooded_pixels: int
    flood_depth_png: str = Field(
        description="Base64-encoded RGBA PNG of flood depth (map overlay)"
    )
    flood_extent_png: str = Field(
        description="Base64-encoded RGBA PNG of flood extent (map overlay)"
    )


class ForecastResponse(BaseModel):
    hours: list[HourlyResult]
    bounds: dict = Field(
        description="Geographic bounding box {south, west, north, east} for the overlay"
    )
    dem_png: str = Field(description="Base64 PNG of the DEM (terrain background)")
    lake_png: str = Field(description="Base64 PNG of the lake mask")
    thresholds: dict = Field(description="Warning thresholds in metres")


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    dem_shape: list[int]
    lake_pixels: int


class SaveForecastRequest(BaseModel):
    rainfall: list[float]
    lake_level: list[float]
    forecast: dict


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["Status"])
async def health():
    """Check if the API is ready."""
    return HealthResponse(
        status="ok",
        model_loaded="model" in _state,
        dem_shape=list(_state["dem"].shape) if "dem" in _state else [],
        lake_pixels=int(_state["lake_mask"].sum()) if "lake_mask" in _state else 0,
    )


@app.post("/predict", response_model=ForecastResponse, tags=["Prediction"])
async def predict(req: ForecastRequest):
    """
    Run a 6-hour flood forecast.

    Send 12 hours of rainfall (mm) and lake level (m).
    Receive per-hour predictions with flood overlay images.
    """
    if "model" not in _state:
        raise HTTPException(503, "Model not loaded yet")

    model = _state["model"]
    cfg = _state["cfg"]
    dem = _state["dem"]
    dem_norm = _state["dem_norm"]
    lake_mask = _state["lake_mask"]

    norm = cfg["norm_params"]
    dem_meta = cfg["dem_metadata"]
    seq_meta = cfg["seq_metadata"]
    thresholds = norm["thresholds"]

    rain_min = norm["rainfall"]["min"]
    rain_max = norm["rainfall"]["max"]
    river_min = norm["riverlevel"]["min"]
    river_max = norm["riverlevel"]["max"]
    lake_bank_elev = dem_meta["lake"]["bank_elev"]
    overflow_threshold = thresholds["alarm"]

    h = seq_meta["input_shape"][1]
    w = seq_meta["input_shape"][2]

    # ── Normalise inputs ────────────────────────────────────────────────
    rain_range = rain_max - rain_min if rain_max > rain_min else 1.0
    river_range = river_max - river_min if river_max > river_min else 1.0

    rainfall_n = np.clip(
        [(r - rain_min) / rain_range for r in req.rainfall], 0, 1
    ).astype(np.float32)

    river_n = np.clip(
        [(r - river_min) / river_range for r in req.lake_level], 0, 1
    ).astype(np.float32)

    # ── Build spatial input tensor (1, 12, H, W, 4) ────────────────────
    inp = np.zeros((1, 12, h, w, 4), dtype=np.float32)
    for t in range(12):
        inp[0, t, :, :, 0] = rainfall_n[t]
        inp[0, t, :, :, 1] = river_n[t]
        inp[0, t, :, :, 2] = dem_norm
        inp[0, t, :, :, 3] = lake_mask

    # ── Run model ───────────────────────────────────────────────────────
    pred = model.predict(inp, verbose=0)  # (1, 6, H, W, 1)

    denorm = lambda v: float(v) * (river_max - river_min) + river_min

    # ── Process each forecast hour ──────────────────────────────────────
    hourly: list[HourlyResult] = []
    global_max_depth = 0.0

    # First pass: compute all flood results to find global max depth
    flood_results = []
    for hr in range(6):
        pred_m = denorm(pred[0, hr, 0, 0, 0])
        level_name, level_color = get_warning_level(pred_m, thresholds)
        fext, fdep, stats = estimate_flood(
            pred_m, dem, lake_mask, lake_bank_elev, overflow_threshold
        )
        flood_results.append((pred_m, level_name, level_color, fext, fdep, stats))
        if stats["max_depth"] > global_max_depth:
            global_max_depth = stats["max_depth"]

    if global_max_depth == 0:
        global_max_depth = 1.0  # avoid division by zero

    # Second pass: generate images with consistent colour scale
    for hr, (pred_m, level_name, level_color, fext, fdep, stats) in enumerate(flood_results):
        depth_png = flood_depth_to_base64_png(fdep, global_max_depth)
        extent_png = flood_extent_to_base64_png(fext)

        hourly.append(HourlyResult(
            hour=hr + 1,
            predicted_level_m=round(pred_m, 4),
            warning_level=level_name,
            warning_color=level_color,
            overflowing=stats["overflowing"],
            overflow_depth_m=round(stats["overflow_depth"], 4),
            water_surface_m=round(stats["water_surface"], 4),
            flooded_land_pct=round(stats["flooded_land_pct"], 2),
            max_depth_m=round(stats["max_depth"], 4),
            mean_depth_m=round(stats["mean_depth"], 4),
            flooded_pixels=stats["flooded_pixels"],
            flood_depth_png=depth_png,
            flood_extent_png=extent_png,
        ))

    return ForecastResponse(
        hours=hourly,
        bounds=_state["bounds"],
        dem_png=_state["dem_png"],
        lake_png=_state["lake_png"],
        thresholds=thresholds,
    )


@app.get("/static/dem", tags=["Static Layers"])
async def get_dem():
    """Return the DEM terrain image and its geographic bounds."""
    return {
        "dem_png": _state["dem_png"],
        "bounds": _state["bounds"],
    }


@app.get("/static/lake", tags=["Static Layers"])
async def get_lake():
    """Return the lake mask overlay and its geographic bounds."""
    return {
        "lake_png": _state["lake_png"],
        "bounds": _state["bounds"],
    }


@app.get("/thresholds", tags=["Configuration"])
async def get_thresholds():
    """Return the warning-level thresholds."""
    return _state["cfg"]["norm_params"]["thresholds"]


@app.post("/save", tags=["Save"])
async def save_forecast(req: SaveForecastRequest):
    """Save a forecast to the database."""
    data = {
        "rainfall": req.rainfall,
        "lake_level": req.lake_level,
        "forecast": req.forecast
    }
    response = supabase.table("saved_forecasts").insert(data).execute()
    return {"message": "Forecast saved successfully", "id": response.data[0]["id"]}


@app.get("/saved", tags=["Save"])
async def list_saved_forecasts():
    """Return saved forecasts from the database."""
    response = supabase.table("saved_forecasts").select("*").order("created_at", desc=True).execute()
    return response.data
