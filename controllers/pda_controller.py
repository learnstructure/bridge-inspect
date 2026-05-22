from pathlib import Path
import logging
import numpy as np
from skimage import color, draw, io, img_as_ubyte
import cv2
import random

from services.cv_service import DetectionEngine, class_names

logger = logging.getLogger(__name__)

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

    def update_image_display(
        self, file_path, results, show_cracks=False, score_threshold=0.5
    ):
        """Show either original image or overlaid detection image."""
        if (
            show_cracks
            and results is not None
            and "rois" in results
            and results["rois"].any()
        ):
            overlay_path = self._create_detection_overlay(
                file_path, results, score_threshold
            )
            self.view.display_image(overlay_path)
        else:
            self.view.display_image(file_path)

    def _create_detection_overlay(
        self, file_path, results, score_threshold=0.5
    ):
        image = io.imread(file_path)
        if image.ndim != 3:
            image = color.gray2rgb(image)
        if image.shape[-1] == 4:
            image = image[..., :3]
        image = img_as_ubyte(image)

        if "crack_image" in results:
            overlay = results["crack_image"]
        else:
            overlay = image.copy()

        boxes = results["rois"].astype(np.int32).copy()
        masks = results["masks"].copy()
        scores = results.get("scores", np.ones(boxes.shape[0], dtype=np.float32))
        class_ids = results["class_ids"]
        damage_level = results["damage_level"]
        dist_coord = results.get("dist_coord")
        max_dist = results.get("max_dist")
        cid = results.get("cid")
        connection = results.get("connection")
        boxes_crack = results.get("boxes_crack", [])
        
        padded_shape = masks.shape[:2]

        cropped_boxes, cropped_masks = self._crop_padded_rois(
            image.shape[:2], padded_shape, boxes, masks
        )

        colors = {
            1: (1.0, 0.0, 0.0),  # Red for column
            2: (0.0, 1.0, 0.0),  # Green for spalling
            3: (0.0, 0.0, 1.0),  # Blue for horizontal
            4: (0.5, 0.0, 1.0),  # Purple for vertical
        }

        num_instances = cropped_boxes.shape[0]
        for i in range(num_instances):
            if scores[i] < score_threshold:
                continue

            mask = cropped_masks[:, :, i]
            if mask.sum() == 0:
                continue

            class_id = class_ids[i]
            color_rgb = colors.get(class_id, (random.random(), random.random(), random.random()))
            cv_color = (color_rgb[0] * 255, color_rgb[1] * 255, color_rgb[2] * 255)

            # Draw mask outline instead of filling
            mask_uint8 = (mask * 255).astype(np.uint8)
            contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(overlay, contours, -1, cv_color, 2)

            y1, x1, y2, x2 = cropped_boxes[i]

            # Draw bounding box
            cv2.rectangle(overlay, (int(x1), int(y1)), (int(x2), int(y2)), cv_color, 1)

            name = class_names[class_id]
            label = f"{name}"
            text_x, text_y = x1, y1 - 10
            if text_y < 10:
                text_y = y1 + 20
            cv2.putText(
                overlay,
                label,
                (int(text_x), int(text_y)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                cv_color,
                2,
            )

            if dist_coord and cid == i:
                dist_coord_cropped = self._crop_padded_points(
                    image.shape[:2], padded_shape, dist_coord
                )
                cv2.line(
                    overlay,
                    (int(dist_coord_cropped[0][1]), int(dist_coord_cropped[0][0])),
                    (int(dist_coord_cropped[1][1]), int(dist_coord_cropped[1][0])),
                    (255, 255, 255),
                    2,
                )
                caption2 = "dist {:.3f}".format(max_dist)
                cv2.putText(
                    overlay,
                    caption2,
                    (int(x1), int(y1) + 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                )

        if connection:
            for connectedset in connection:
                cropped_connected_rois, _ = self._crop_padded_rois(
                    image.shape[:2],
                    padded_shape,
                    np.array(connectedset),
                    np.zeros(padded_shape + (len(connectedset),), dtype=bool),
                )

                if len(cropped_connected_rois) > 1:
                    point1, point2 = (
                        cropped_connected_rois[0],
                        cropped_connected_rois[-1],
                    )
                    if point1[1] >= point2[3]:
                        cv2.rectangle(
                            overlay,
                            (int(point2[1]), int(point1[0])),
                            (int(point1[3]), int(point2[2])),
                            (255, 255, 255),
                            2,
                        )
                    else:
                        cv2.rectangle(
                            overlay,
                            (int(point1[1]), int(point1[0])),
                            (int(point2[3]), int(point2[2])),
                            (255, 255, 255),
                            2,
                        )

                elif len(cropped_connected_rois) == 1:
                    point = cropped_connected_rois[0]
                    cv2.rectangle(
                        overlay,
                        (int(point[1]), int(point[0])),
                        (int(point[3]), int(point[2])),
                        (255, 255, 255),
                        2,
                    )
        
        # Draw bounding boxes for cracks
        if boxes_crack:
            cropped_crack_boxes, _ = self._crop_padded_rois(
                image.shape[:2], 
                padded_shape, 
                np.array(boxes_crack),
                np.zeros(padded_shape + (len(boxes_crack),), dtype=bool)
            )
            for box in cropped_crack_boxes:
                y1, x1, y2, x2 = box
                # Ensure box coordinates are within the image dimensions
                y1, y2 = np.clip([y1, y2], 0, image.shape[0] - 1)
                x1, x2 = np.clip([x1, x2], 0, image.shape[1] - 1)
                cv2.rectangle(overlay, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 255), 2)  # Cyan for cracks


        cv2.putText(
            overlay,
            damage_level,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        overlay_path = Path(file_path).with_suffix(".overlay.png")
        io.imsave(str(overlay_path), overlay)
        return str(overlay_path)

    def _crop_padded_rois(self, original_shape, padded_shape, boxes, masks):
        orig_h, orig_w = original_shape
        padded_h, padded_w = padded_shape

        top_pad = (padded_h - orig_h) // 2
        left_pad = (padded_w - orig_w) // 2

        if top_pad == 0 and left_pad == 0 and padded_h == orig_h and padded_w == orig_w:
            return boxes, masks

        boxes = boxes.astype(np.int32).copy()
        boxes[:, [0, 2]] -= top_pad
        boxes[:, [1, 3]] -= left_pad
        boxes[:, [0, 2]] = np.clip(boxes[:, [0, 2]], 0, orig_h - 1)
        boxes[:, [1, 3]] = np.clip(boxes[:, [1, 3]], 0, orig_w - 1)

        cropped_masks = masks[
            top_pad : top_pad + orig_h, left_pad : left_pad + orig_w, :
        ]

        return boxes, cropped_masks

    def _crop_padded_points(self, original_shape, padded_shape, points):
        orig_h, orig_w = original_shape
        padded_h, padded_w = padded_shape

        top_pad = (padded_h - orig_h) // 2
        left_pad = (padded_w - orig_w) // 2

        points = np.array(points).astype(np.int32)
        points[:, 0] -= top_pad
        points[:, 1] -= left_pad

        points[:, 0] = np.clip(points[:, 0], 0, orig_h - 1)
        points[:, 1] = np.clip(points[:, 1], 0, orig_w - 1)

        return points
