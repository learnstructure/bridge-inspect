#This file is not used in the current implementation. 

from pathlib import Path
import logging
from models.helpers import load_model_from_checkpoint, predict, analyze_cracks, DEVICE
import cv2
import numpy as np

logger = logging.getLogger(__name__)


def run_crack_detection(file_path):
    """
    Run crack detection on an image file.

    Args:
        file_path (str): Path to the image file

    Returns:
        dict: Aggregated crack detection results with damage assessment

    Raises:
        FileNotFoundError: If image or model not found
        RuntimeError: If model loading or prediction fails
    """
    try:
        # Validate image file exists
        image_path = Path(file_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {file_path}")

        # Load model with proper path resolution
        model_dir = Path(__file__).parent.parent / "models"
        model_path = model_dir / "unet_best.pth"

        if not model_path.exists():
            raise FileNotFoundError(f"Model checkpoint not found: {model_path}")

        logger.info(f"Loading model from: {model_path}")
        model = load_model_from_checkpoint(str(model_path), DEVICE)

        # Run prediction
        logger.info(f"Processing image: {file_path}")
        pred_mask = predict(str(file_path), model, DEVICE)

        # Analyze cracks
        crack_list = analyze_cracks(pred_mask, threshold=0.5, min_pixels=10)
        logger.info(f"Detected {len(crack_list)} cracks")

        # Aggregate results
        results = aggregate_crack_results(crack_list)
        results["pred_mask"] = pred_mask 
        return results

    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error during crack detection: {e}")
        return {"error": f"Processing failed: {str(e)}"}


def aggregate_crack_results(crack_list):
    """
    Aggregate individual crack detections into damage statistics.

    Args:
        crack_list (list): List of crack dictionaries from analyze_cracks()

    Returns:
        dict: Aggregated results with crack counts and damage state
    """
    if not crack_list:
        return {
            "Horizontal cracks": 0,
            "Vertical cracks": 0,
            "Diagonal cracks": 0,
            "Total cracks": 0,
            "Damage state": "0 - No damage",
        }

    # Count cracks by orientation
    horizontal = sum(1 for c in crack_list if c["orientation"] == "horizontal")
    vertical = sum(1 for c in crack_list if c["orientation"] == "vertical")
    diagonal = sum(1 for c in crack_list if c["orientation"] == "inclined")
    total = len(crack_list)

    # Calculate total crack area (pixel count)
    total_pixels = sum(c["pixel_count"] for c in crack_list)

    # Determine damage state (0-5 scale)
    if total == 0:
        damage_state = "0 - No damage"
    elif total <= 2 and total_pixels < 500:
        damage_state = "1 - Minor cracks"
    elif total <= 5 and total_pixels < 2000:
        damage_state = "2 - Moderate cracks"
    elif total <= 10 and total_pixels < 5000:
        damage_state = "3 - Significant cracks"
    else:
        damage_state = "4 - Severe damage"

    return {
        "Horizontal cracks": horizontal,
        "Vertical cracks": vertical,
        "Diagonal cracks": diagonal,
        "Total cracks": total,
        "Total crack area (pixels)": total_pixels,
        # "Damage state": damage_state,
    }



def overlay_cracks_on_image(image_path, crack_mask, overlay_color=(0, 255, 0), alpha=0.6):
    """
    Overlay predicted crack pixels on the original image.
    
    Args:
        image_path (str): Path to original image
        crack_mask (np.ndarray): Binary or probability mask from prediction
        overlay_color (tuple): BGR color for overlay (default: green)
        alpha (float): Transparency of overlay (0-1)
    
    Returns:
        np.ndarray: Image with cracks overlaid
    """
    # Read original image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")
    
    # Normalize mask to 0-255 if it's in 0-1 range
    if crack_mask.max() <= 1:
        binary_mask = (crack_mask > 0.5).astype(np.uint8) * 255
    else:
        binary_mask = (crack_mask > 0).astype(np.uint8) * 255
    
    # Resize mask to match image dimensions if needed
    if binary_mask.shape != img.shape[:2]:
        binary_mask = cv2.resize(binary_mask, (img.shape[1], img.shape[0]))
    
    # Create colored overlay
    overlay = img.copy()
    overlay[binary_mask > 0] = overlay_color
    
    # Blend original image with overlay
    result = cv2.addWeighted(img, 1 - alpha, overlay, alpha, 0)
    
    return result