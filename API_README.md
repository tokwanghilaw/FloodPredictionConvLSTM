# Lake Buhi Flood Prediction API

**ConvLSTM-based 6-hour flood forecast for Lake Buhi, Camarines Sur.**

This API serves a trained deep learning model that predicts lake overflow flooding. It accepts 12 hours of rainfall and lake level data, and returns 6 hourly forecasts with flood map overlays ready for display on a web map.

---

## Quick Start (for the website developer)

### 1. Install Python dependencies

```bash
cd "ConvLSTM Model v3"
pip install -r requirements.txt
```

### 2. Start the API server

```bash
cd "ConvLSTM Model v3"
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

### 3. Open the interactive docs

Go to **http://localhost:8000/docs** — this is a Swagger UI where you can test every endpoint.

---

## API Endpoints

### `POST /predict` — Run a flood forecast

**This is the main endpoint your website will call.**

#### Request body (JSON):

```json
{
  "rainfall": [0.0, 0.5, 2.0, 5.0, 10.0, 15.0, 25.0, 35.0, 45.0, 40.0, 30.0, 20.0],
  "lake_level": [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.78, 0.80, 0.83, 0.86, 0.90, 0.95]
}
```

- `rainfall` — exactly **12 floats**, hourly rainfall in **millimetres**
- `lake_level` — exactly **12 floats**, hourly lake/river level in **metres**

#### Response (JSON):

```json
{
  "hours": [
    {
      "hour": 1,
      "predicted_level_m": 0.8234,
      "warning_level": "ALARM",
      "warning_color": "#e67e22",
      "overflowing": true,
      "overflow_depth_m": 0.0234,
      "water_surface_m": 85.12,
      "flooded_land_pct": 2.31,
      "max_depth_m": 0.45,
      "mean_depth_m": 0.12,
      "flooded_pixels": 384,
      "flood_depth_png": "<base64 string>",
      "flood_extent_png": "<base64 string>"
    }
    // ... 6 total (hour 1–6)
  ],
  "bounds": {
    "south": 13.38,
    "west": 123.40,
    "north": 13.50,
    "east": 123.60
  },
  "dem_png": "<base64 string>",
  "lake_png": "<base64 string>",
  "thresholds": {
    "normal": 0.0,
    "alert": 0.75,
    "alarm": 0.80,
    "critical": 0.85
  }
}
```

#### Key fields explained:

| Field | What it is | How to use it |
|-------|-----------|---------------|
| `hours[].predicted_level_m` | Predicted lake level in metres | Display as text / chart |
| `hours[].warning_level` | `NORMAL`, `ALERT`, `ALARM`, or `CRITICAL` | Color-coded status badge |
| `hours[].warning_color` | CSS hex color for the warning level | Use directly in UI styling |
| `hours[].overflowing` | Whether the lake is overflowing | Show/hide flood overlays |
| `hours[].flooded_land_pct` | % of land area flooded | Display as statistic |
| `hours[].max_depth_m` | Maximum flood depth in metres | Display as statistic |
| `hours[].flood_depth_png` | Base64 RGBA PNG — flood depth heatmap | **Map overlay image** |
| `hours[].flood_extent_png` | Base64 RGBA PNG — flood extent (red) | **Map overlay image** |
| `bounds` | Geographic bounding box (WGS84) | Position overlays on map |
| `dem_png` | Base64 RGB PNG — terrain background | Static background layer |
| `lake_png` | Base64 RGBA PNG — lake shape (blue) | Static lake layer |
| `thresholds` | Warning level thresholds in metres | Draw threshold lines on charts |

### `GET /health` — Check if the API is ready

```json
{
  "status": "ok",
  "model_loaded": true,
  "dem_shape": [128, 128],
  "lake_pixels": 1042
}
```

### `GET /static/dem` — Get terrain image + bounds

Returns `{ "dem_png": "...", "bounds": {...} }`. Use this for the static background layer (doesn't change).

### `GET /static/lake` — Get lake mask image + bounds

Returns `{ "lake_png": "...", "bounds": {...} }`. Use this for the static lake overlay (doesn't change).

### `GET /thresholds` — Get warning thresholds

Returns `{ "normal": 0.0, "alert": 0.75, "alarm": 0.80, "critical": 0.85 }`.

---

## How to Display Flood Maps on the Website

### Using Leaflet.js (recommended)

```javascript
// 1. Create the map centered on Lake Buhi
const map = L.map('map').setView([13.44, 123.50], 12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

// 2. After calling /predict, display the overlays:
const response = await fetch('http://localhost:8000/predict', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    rainfall: [0, 0.5, 2, 5, 10, 15, 25, 35, 45, 40, 30, 20],
    lake_level: [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.78, 0.80, 0.83, 0.86, 0.90, 0.95]
  })
});
const data = await response.json();

// 3. Geographic bounds for all overlays
const imageBounds = [
  [data.bounds.south, data.bounds.west],  // southwest corner
  [data.bounds.north, data.bounds.east]   // northeast corner
];

// 4. Add terrain background (static — only need to add once)
const demOverlay = L.imageOverlay(
  'data:image/png;base64,' + data.dem_png,
  imageBounds, { opacity: 0.6 }
).addTo(map);

// 5. Add lake mask (static — only need to add once)
const lakeOverlay = L.imageOverlay(
  'data:image/png;base64,' + data.lake_png,
  imageBounds, { opacity: 0.7 }
).addTo(map);

// 6. Add flood depth for a specific forecast hour (e.g., hour 3)
const hourData = data.hours[2];  // 0-indexed, so index 2 = hour 3
const floodOverlay = L.imageOverlay(
  'data:image/png;base64,' + hourData.flood_depth_png,
  imageBounds, { opacity: 0.7 }
).addTo(map);

// 7. To switch hours, remove old overlay and add new one
// floodOverlay.remove();
// const newOverlay = L.imageOverlay('data:image/png;base64,' + data.hours[4].flood_depth_png, imageBounds).addTo(map);
```

### Suggested UI Layout

```
┌──────────────────────────────────────────────────────┐
│  LAKE BUHI FLOOD PREDICTION SYSTEM                   │
├──────────────┬───────────────────────────────────────┤
│              │                                       │
│  INPUT FORM  │          LEAFLET MAP                  │
│  ──────────  │   (terrain + lake + flood overlay)    │
│  Rainfall    │                                       │
│  [12 inputs] │                                       │
│              │                                       │
│  Lake Level  │      ┌─────────────────────┐         │
│  [12 inputs] │      │  Hour slider: 1-6   │         │
│              │      └─────────────────────┘         │
│  [PREDICT]   │                                       │
│              ├───────────────────────────────────────┤
│  WARNING:    │  FORECAST CHART                       │
│  ┌────────┐  │  (lake level line chart, hours 1-6,  │
│  │ ALARM  │  │   with threshold lines)               │
│  └────────┘  │                                       │
│              │  Stats: flooded 2.3% | max 0.45m     │
├──────────────┴───────────────────────────────────────┤
│  Footer / Credits                                    │
└──────────────────────────────────────────────────────┘
```

---

## Warning Levels

| Level | Threshold | Color | Meaning |
|-------|-----------|-------|---------|
| NORMAL | < 0.75 m | 🟢 `#2ecc71` | No risk |
| ALERT | 0.75 – 0.79 m | 🟡 `#f1c40f` | Monitor closely |
| ALARM | 0.80 – 0.84 m | 🟠 `#e67e22` | Overflow begins — evacuate low areas |
| CRITICAL | ≥ 0.85 m | 🔴 `#e74c3c` | Major flooding — full evacuation |

---

## File Structure

```
ConvLSTM Model v3/
├── api/                        ← API source code
│   ├── __init__.py
│   ├── app.py                  ← FastAPI application (main entry point)
│   ├── flood.py                ← Flood estimation logic (FWDET)
│   ├── model_loader.py         ← Model loading with custom_objects
│   └── utils.py                ← PNG generation for map overlays
├── requirements.txt            ← pip dependencies
├── Buhi_ConvLSTM_V3.ipynb      ← Training notebook
│
├── ── Source Data (do not modify) ──
├── BUHI_DTM.tif
├── BUHI_LAKE.shp (+ .cpg, .dbf, .prj, .qmd, .shx)
├── BUHI_Rainfall-Data.csv
├── BUHI_Riverlevel-Data.csv
├── BUHI_station_metadata.csv
│
└── ── Generated by notebook (needed by API) ──
    ├── best_model.keras         ← Trained model weights
    ├── dem_small.npy            ← 128×128 DEM array
    ├── dem_small_norm.npy       ← Normalized DEM
    ├── lake_small.npy           ← 128×128 lake mask
    ├── normalization_params.json
    ├── dem_metadata.json
    └── sequence_metadata.json
```

**The API needs these 7 generated files to run.** They are created when the notebook runs Cells 1–8.

---

## CORS

The API allows all origins (`*`) by default for development. For production, edit `api/app.py` and change:

```python
allow_origins=["*"]
```

to your actual domain:

```python
allow_origins=["https://your-website.com"]
```

---

## Notes

- The model input is always **12 hours** of data; the output is always **6 hours** of predictions.
- All images are **128×128 pixels** — they stretch to fill the geographic bounds on the map.
- The `flood_depth_png` and `flood_extent_png` are **RGBA** (transparent where no flooding).
- The `dem_png` and `lake_png` are static — fetch them once from `/static/dem` and `/static/lake`, or use the ones returned in the `/predict` response.
