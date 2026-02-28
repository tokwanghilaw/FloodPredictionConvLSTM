import numpy as np

def clean_lake_mask(lake_mask_raw: np.ndarray) -> np.ndarray:
    """Convert lake mask to clean binary 0/1."""
    return (lake_mask_raw > 0.5).astype(np.float32)


def get_warning_level(level_m: float, thresholds: dict) -> tuple[str, str]:
    """Return warning name and color based on lake level."""
    if level_m >= thresholds.get("critical", 0.85):
        return "CRITICAL", "#e74c3c"
    elif level_m >= thresholds.get("alarm", 0.80):
        return "ALARM", "#e67e22"
    elif level_m >= thresholds.get("alert", 0.75):
        return "ALERT", "#f1c40f"
    else:
        return "NORMAL", "#2ecc71"


def estimate_flood(pred_level_m: float, dem: np.ndarray, lake_mask: np.ndarray, 
                   lake_bank_elev: float, overflow_threshold: float):
    """
    Estimate flood extent and depth using planar water surface.
    """
    water_surface_elev = pred_level_m + lake_bank_elev
    
    # Depth everywhere
    flood_depth = np.maximum(water_surface_elev - dem, 0.0)
    
    overflowing = pred_level_m > overflow_threshold
    
    # If not overflowing, only flood inside lake
    if not overflowing:
        flood_depth = flood_depth * lake_mask
    
    flooded = flood_depth > 0.01
    
    stats = {
        "overflowing": bool(overflowing),
        "overflow_depth": max(0.0, pred_level_m - overflow_threshold),
        "water_surface": float(water_surface_elev),
        "max_depth": float(np.max(flood_depth)),
        "mean_depth": float(np.mean(flood_depth[flooded])) if np.any(flooded) else 0.0,
        "flooded_pixels": int(np.sum(flooded)),
        "flooded_land_pct": 0.0
    }
    
    # Calculate % of land flooded (outside lake)
    land_mask = lake_mask < 0.5
    if np.any(land_mask):
        land_flooded = np.sum(flooded & land_mask)
        stats["flooded_land_pct"] = float(land_flooded / np.sum(land_mask) * 100)
    
    return flooded.astype(np.float32), flood_depth, stats