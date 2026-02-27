import base64
import io
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

def flood_depth_to_base64_png(depth_map: np.ndarray, max_depth: float = None) -> str:
    """Convert flood depth to colorful base64 PNG (transparent where no flood)."""
    if max_depth is None or max_depth == 0:
        max_depth = np.max(depth_map) + 1e-6 if np.max(depth_map) > 0 else 1.0
    
    norm = np.clip(depth_map / max_depth, 0, 1)
    rgba = (plt.cm.plasma(norm) * 255).astype(np.uint8)
    rgba[..., 3] = (norm > 0.005).astype(np.uint8) * 220   # semi-transparent
    
    img = Image.fromarray(rgba)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def flood_extent_to_base64_png(extent_map: np.ndarray) -> str:
    """Red outline for flood extent."""
    rgba = np.zeros((*extent_map.shape, 4), dtype=np.uint8)
    rgba[extent_map > 0.5] = [220, 20, 60, 160]   # Crimson
    img = Image.fromarray(rgba)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def dem_to_base64_png(dem: np.ndarray) -> str:
    """Terrain background."""
    norm = (dem - dem.min()) / (dem.ptp() + 1e-8)
    rgba = (plt.cm.terrain(norm) * 255).astype(np.uint8)
    img = Image.fromarray(rgba)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def lake_mask_to_base64_png(lake_mask: np.ndarray) -> str:
    """Blue lake mask."""
    rgba = np.zeros((*lake_mask.shape, 4), dtype=np.uint8)
    rgba[lake_mask > 0.5] = [30, 144, 255, 140]   # Dodger blue
    img = Image.fromarray(rgba)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def get_image_bounds(dem_meta: dict) -> dict:
    """Geographic bounds for Leaflet/Mapbox."""
    ext = dem_meta.get("display_extent", [123.45, 123.59, 13.38, 13.50])
    return {
        "south": ext[2],
        "west":  ext[0],
        "north": ext[3],
        "east":  ext[1]
    }