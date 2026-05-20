from pathlib import Path
import logging
import numpy as np
from skimage import color, draw, io, img_as_ubyte
import cv2

from services.cv_service import DetectionEngine

logger = logging.getLogger(__name__)

def apply_mask(image, mask, color, alpha=0.5):
    """Apply a colored mask to an image without importing matplotlib."""
    for c in range(3):
        image[:, :, c] = np.where(
            mask == 1,
            image[:, :, c] * (1 - alpha) + alpha * color[c] * 255,
            image[:, :, c]
        )
    return image


class PDAController:
    def __init__(self, view):
        self.view = view  # PDAPage UI
        self.cv_engine = DetectionEngine()  # Computer vision engine for PDA

    def upload_image(self, file_path):
        """Display uploaded image in the viewer"""
        self.view.display_image(file_path)

    def run_pda(self, file_path):
        if not file_path:
            self.view.display_results(
                {"error": "No image selected. Please upload an image first."}
            )
            return

        logger.info(f"Starting PDA analysis on: {file_path}")
        results = self.cv_engine.detect(file_path)
        self.view.last_results = results
        self.view.display_results(results)

        if "error" in results:
            logger.error(f"PDA analysis failed: {results['error']}")
            return

        logger.info("PDA analysis completed successfully")
        self.update_image_display(file_path, results, show_cracks=True)

    def update_image_display(self, file_path, results, show_cracks=False, score_threshold=0.5):
        """Show either original image or overlaid detection image."""
        if show_cracks and results is not None and "rois" in results and results["rois"].size > 0:
            overlay_path = self._create_detection_overlay(file_path, results, score_threshold)
            self.view.display_image(overlay_path)
        else:
            self.view.display_image(file_path)

    def _create_detection_overlay(self, file_path, results, score_threshold=0.5):
        image = io.imread(file_path)
        if image.ndim != 3:
            image = color.gray2rgb(image)
        if image.shape[-1] == 4:
            image = image[..., :3]
        image = img_as_ubyte(image)

        boxes = results["rois"].astype(np.int32).copy()
        masks = results["masks"].copy()
        scores = results.get("scores", np.ones(boxes.shape[0], dtype=np.float32))

        boxes, masks = self._crop_padded_detections(image.shape[:2], boxes, masks)

        overlay = image.copy()
        num_instances = boxes.shape[0]
        for i in range(num_instances):
            if scores[i] < score_threshold:
                continue

            mask = masks[:, :, i]
            if mask.sum() == 0:
                continue

            color_rgb = np.random.rand(3)
            overlay = apply_mask(overlay, mask, color_rgb, alpha=0.4)

            y1, x1, y2, x2 = boxes[i]
            y1, x1 = max(0, y1), max(0, x1)
            y2, x2 = min(overlay.shape[0] - 1, y2), min(overlay.shape[1] - 1, x2)

            rr, cc = draw.rectangle_perimeter(start=(y1, x1), end=(y2, x2), shape=overlay.shape)
            overlay[rr, cc] = (color_rgb * 255).astype(np.uint8)

            # Draw class ID with name (if available)
            if "class_ids" in results and i < len(results["class_ids"]):
                class_id = results["class_ids"][i]
                # Mapping dictionary
                class_names = {
                    1: "Column",
                    2: "Spalling",
                    3: "Horizontal",
                    4: "Vertical"
                }
                name = class_names.get(class_id, str(class_id))
                label = f"{class_id}-{name}"
                
                # Position above the box (or inside if too close to top)
                text_x, text_y = x1, y1 - 5
                if text_y < 10:
                    text_y = y1 + 20  # fallback inside the box
                cv2.putText(overlay, label, (text_x, text_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7,  # increased from 0.5 to 0.7
                            (color_rgb * 255).astype(int).tolist(), 2)  # thickness 2 for better readability


        overlay_path = Path(file_path).with_suffix(".overlay.png")
        io.imsave(str(overlay_path), overlay)
        return str(overlay_path)

    def _crop_padded_detections(self, original_shape, boxes, masks):
        orig_h, orig_w = original_shape

        top_pad, bottom_pad, left_pad, right_pad = self._get_padding_values(orig_h, orig_w)
        if top_pad == 0 and left_pad == 0:
            return boxes, masks

        boxes = boxes.astype(np.int32)
        boxes[:, [0, 2]] -= top_pad
        boxes[:, [1, 3]] -= left_pad
        boxes[:, [0, 2]] = np.clip(boxes[:, [0, 2]], 0, orig_h - 1)
        boxes[:, [1, 3]] = np.clip(boxes[:, [1, 3]], 0, orig_w - 1)

        masks = masks[top_pad:top_pad + orig_h, left_pad:left_pad + orig_w, :]
        return boxes, masks

    def _get_padding_values(self, height, width):
        if height % 64 > 0:
            max_h = height - (height % 64) + 64
            top_pad = (max_h - height) // 2
            bottom_pad = max_h - height - top_pad
        else:
            top_pad = bottom_pad = 0

        if width % 64 > 0:
            max_w = width - (width % 64) + 64
            left_pad = (max_w - width) // 2
            right_pad = max_w - width - left_pad
        else:
            left_pad = right_pad = 0

        return top_pad, bottom_pad, left_pad, right_pad