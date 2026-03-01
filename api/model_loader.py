import os
# Ensure this matches app.py so both files use the same Keras backend
os.environ["TF_USE_LEGACY_KERAS"] = "1"

import json
from pathlib import Path
import tensorflow as tf
from tensorflow.keras.utils import register_keras_serializable
from tensorflow.keras.models import load_model as keras_load_model

@register_keras_serializable()
def extract_forecast(x):
    """Extract the last 6 timesteps (6-hour forecast)."""
    return x[:, -6:, :, :, :]

def load_config(metadata_dir: Path):
    with open(metadata_dir / "normalization_params.json") as f:
        norm_params = json.load(f)
    with open(metadata_dir / "dem_metadata.json") as f:
        dem_metadata = json.load(f)
    with open(metadata_dir / "sequence_metadata.json") as f:
        seq_metadata = json.load(f)
    return {
        "norm_params": norm_params,
        "dem_metadata": dem_metadata,
        "seq_metadata": seq_metadata
    }

def load_model(model_path: Path, metadata_dir: Path):
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    print(f"Loading model from {model_path}...")
    model = keras_load_model(
        model_path,
        custom_objects={'extract_forecast': extract_forecast}
    )
    print("✅ Model loaded successfully!")
    return model