import json
from pathlib import Path
from tensorflow.keras.models import load_model as keras_load_model   # <-- THIS LINE IS THE FIX

def load_config(metadata_dir: Path):
    """Load normalization, DEM, and sequence metadata."""
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
    """Load the trained ConvLSTM model."""
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    print(f"Loading model from {model_path}...")
    model = keras_load_model(model_path)   # <-- FIXED: uses TensorFlow version
    print("Model loaded successfully!")
    return model