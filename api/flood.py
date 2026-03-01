import numpy as np
from scipy.ndimage import binary_dilation, label


def clean_lake_mask(lake_mask_raw: np.ndarray, min_component_px: int = 5) -> np.ndarray:
    """
    Clean lake mask: keep all real components (>= min_component_px pixels),
    remove only tiny noise fragments.  The lake may have multiple disconnected
    parts (e.g. the bottom-left lobe) that are all real.
    """
    binary = lake_mask_raw > 0.5
    labeled, n_features = label(binary)

    if n_features > 1:
        component_sizes = [(i, int(np.sum(labeled == i)))
                           for i in range(1, n_features + 1)]
        keep_ids = [cid for cid, sz in component_sizes if sz >= min_component_px]
        lake_clean = np.isin(labeled, keep_ids).astype(np.float32)
    else:
        lake_clean = binary.astype(np.float32)

    return lake_clean


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
    FWDET lake-overflow flood estimation.
    Water spills FROM the lake boundary into adjacent terrain below the
    computed water-surface elevation.  Uses iterative flood fill so water
    cannot jump over ridges.

    Parameters
    ----------
    pred_level_m : float
        Predicted lake level in metres.
    dem : np.ndarray
        Digital elevation model (2-D, metres).
    lake_mask : np.ndarray
        Binary lake mask (1 = lake, 0 = land).
    lake_bank_elev : float
        Elevation of the lake bank (P95 of DEM inside lake), metres.
    overflow_threshold : float
        Lake level (metres) above which overflow begins.

    Returns
    -------
    flood_extent, flood_depth, stats_dict
    """
    flood_ext = np.zeros_like(dem, dtype=np.float32)
    flood_dep = np.zeros_like(dem, dtype=np.float32)

    if pred_level_m <= overflow_threshold:
        return flood_ext, flood_dep, {
            "overflowing": False,
            "overflow_depth": 0.0,
            "water_surface": 0.0,
            "flooded_land_pct": 0.0,
            "max_depth": 0.0,
            "mean_depth": 0.0,
            "flooded_pixels": 0,
        }

    # Overflow depth is only the amount ABOVE the threshold
    overflow_depth = pred_level_m - overflow_threshold
    water_surface = lake_bank_elev + overflow_depth

    struct = np.ones((3, 3))  # 8-connectivity

    # Start from the lake boundary (pixels just outside the lake)
    boundary = binary_dilation(lake_mask > 0, struct) & (lake_mask == 0)
    flood_bool = boundary & (dem <= water_surface)

    # Iterative flood fill - expand outward from boundary
    for _ in range(500):
        expanded = binary_dilation(flood_bool, struct)
        new_pixels = expanded & (dem <= water_surface) & ~flood_bool & (lake_mask == 0)
        if not new_pixels.any():
            break
        flood_bool |= new_pixels

    flood_ext = flood_bool.astype(np.float32)
    flood_dep[flood_bool] = np.maximum(0, water_surface - dem[flood_bool])

    land_px = dem.size - int(lake_mask.sum())
    flooded_px = int(flood_bool.sum())
    pct = 100.0 * flooded_px / land_px if land_px > 0 else 0.0

    stats = {
        "overflowing": True,
        "overflow_depth": float(overflow_depth),
        "water_surface": float(water_surface),
        "flooded_land_pct": float(pct),
        "max_depth": float(flood_dep.max()) if flooded_px > 0 else 0.0,
        "mean_depth": float(flood_dep[flood_bool].mean()) if flooded_px > 0 else 0.0,
        "flooded_pixels": flooded_px,
    }

    return flood_ext, flood_dep, stats