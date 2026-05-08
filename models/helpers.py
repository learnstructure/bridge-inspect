from torchvision.transforms import v2
import torch
from PIL import Image
import cv2
import numpy as np
import importlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

IMG_SIZE = (448, 448)
DEVICE = torch.device("cpu")

# --- Transform for Prediction (expect only image) ---
pred_transform = v2.Compose(
    [
        v2.Resize(IMG_SIZE),
        v2.ToImage(),
        v2.ToDtype(torch.float32, scale=True),
        v2.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)


def load_model(model_name: str, checkpoint_path: str | Path, device=DEVICE):
    """
    Load a model from checkpoint with proper error handling.

    Args:
        model_name (str): Name of the model module (e.g., 'unet')
        checkpoint_path (str | Path): Path to the checkpoint file
        device: torch device

    Returns:
        model: Loaded model in eval mode

    Raises:
        ModuleNotFoundError: If model module not found
        RuntimeError: If checkpoint loading fails
    """
    try:
        logger.debug(f"Loading model: {model_name}")
        model_module = importlib.import_module(f"models.{model_name}")
        model = model_module.get_model().to(device)

        state_dict = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(state_dict)
        model.eval()
        logger.info(f"Successfully loaded {model_name} model")
        return model
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            f"Model module 'models.{model_name}' not found"
        ) from e
    except Exception as e:
        raise RuntimeError(f"Failed to load model: {e}") from e


def load_model_from_checkpoint(checkpoint_path: str | Path, device=DEVICE):
    """
    Load model from checkpoint, inferring model name from filename.

    Args:
        checkpoint_path (str | Path): Path to checkpoint (e.g., 'models/unet_best.pth')
        device: torch device

    Returns:
        model: Loaded model

    Raises:
        ValueError: If checkpoint path format is invalid
    """
    checkpoint_path = Path(checkpoint_path)

    # Extract model name from filename (e.g., 'unet' from 'unet_best.pth')
    stem = checkpoint_path.stem
    if "_" not in stem:
        raise ValueError(
            f"Invalid checkpoint filename '{checkpoint_path.name}'. "
            "Expected format: '<model_name>_<variant>.pth' (e.g., 'unet_best.pth')"
        )

    model_name = stem.split("_")[0]
    return load_model(model_name, checkpoint_path, device)


def predict(image_path, model, device):
    """
    Run inference on an image.

    Args:
        image_path (str): Path to image file
        model: Loaded model
        device: torch device

    Returns:
        np.ndarray: Prediction mask (448x448) with values in [0, 1]

    Raises:
        FileNotFoundError: If image not found
        ValueError: If image cannot be opened
    """
    try:
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        image = Image.open(image_path).convert("RGB")
        # Use the prediction-specific transform
        input_tensor = pred_transform(image).unsqueeze(0).to(device)
        with torch.no_grad():
            output = model(input_tensor)
            pred = torch.sigmoid(output).cpu().numpy().squeeze()
        return pred
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Cannot open image: {image_path}") from e
    except Exception as e:
        raise ValueError(f"Error during prediction: {e}") from e


def analyze_cracks(prob_mask, threshold=0.5, min_pixels=10):
    """
    Extract crack instances and orientations from a probability mask.

    Args:
        prob_mask (np.ndarray): 2D array of float, values in [0,1].
        threshold (float): Pixels > threshold become crack.
        min_pixels (int): Minimum number of pixels to consider a valid crack.

    Returns:
        list of dict: Each dict contains 'id', 'pixel_count', 'orientation', 'angle_deg'.
    """
    # 1. Binarize using threshold
    binary_mask = (prob_mask > threshold).astype(np.uint8)

    # 2. Morphological cleaning (remove small holes, close small gaps)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary_mask = cv2.morphologyEx(
        binary_mask, cv2.MORPH_CLOSE, kernel
    )  # Close small gaps
    binary_mask = cv2.morphologyEx(
        binary_mask, cv2.MORPH_OPEN, kernel
    )  # Remove small noise

    # 3. Connected components
    num_labels, labels = cv2.connectedComponents(binary_mask, connectivity=8)
    # label 0 is background; cracks are labels 1..num_labels-1

    crack_info = []
    for label_id in range(1, num_labels):
        # Coordinates of pixels belonging to this crack
        pts = np.column_stack(np.where(labels == label_id))
        if len(pts) < min_pixels:
            continue

        # 4. Compute orientation using PCA (principal axis)
        mean = np.mean(pts, axis=0)
        centered = pts - mean
        # Covariance matrix
        cov = np.cov(centered.T)
        eigenvalues, eigenvectors = np.linalg.eig(cov)
        # Eigenvector with largest eigenvalue = principal direction
        principal_axis = eigenvectors[:, np.argmax(eigenvalues)]
        angle_rad = np.arctan2(principal_axis[0], principal_axis[1])
        angle_deg = angle_rad * 180 / np.pi

        # Normalize angle to [0, 180) to avoid sign ambiguity
        angle_deg = angle_deg % 180

        # Classify orientation
        if angle_deg <= 20 or angle_deg >= 160:
            orientation = "horizontal"
        elif 70 <= angle_deg <= 110:
            orientation = "vertical"
        else:
            orientation = "inclined"

        crack_info.append(
            {
                "id": label_id,
                "pixel_count": len(pts),
                "orientation": orientation,
                "angle_deg": round(float(angle_deg), 1),  # Convert to float, then round
            }
        )

    return crack_info
