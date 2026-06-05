# controllers/pda_controller.py
import logging
from copy import deepcopy
import cv2
import numpy as np
import random
from pathlib import Path
from skimage import color, io, img_as_ubyte
from services.cv_service import DetectionEngine, class_names, get_bbox_area

logger = logging.getLogger(__name__)

def iou(boxA, boxB):
    xA = max(boxA[1], boxB[1]); yA = max(boxA[0], boxB[0])
    xB = min(boxA[3], boxB[3]); yB = min(boxA[2], boxB[2])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[3] - boxA[1]) * (boxA[2] - boxA[0])
    return interArea / float(boxAArea) if boxAArea > 0 else 0

class PDAController:
    def __init__(self):
        self.analysis_view = None
        self.correction_view = None
        self.summary_view = None
        self.cv_engine = DetectionEngine()
        self.original_results = None
        self.current_file_path = None
        self.damage_rules = {
            "level_5": {"min_h_bars": 3, "min_v_bars": 2},
            "level_4": {"min_h_bars": 1, "min_v_bars": 1, "min_spall_ratio": 50},
            "level_3": {"min_spall_ratio": 10},
            "level_2": {"min_v_cracks": 3},
            "level_1": {"min_h_cracks": 1, "max_v_cracks": 0}
        }

    def set_view(self, analysis_view, correction_view, summary_view):
        self.analysis_view = analysis_view
        self.correction_view = correction_view
        self.summary_view = summary_view

    def upload_image(self, file_path):
        self.current_file_path = file_path
        self.original_results = None
        if self.analysis_view: self.analysis_view.display_image(file_path)
        if self.correction_view: self.correction_view.display_image(file_path)
        if self.summary_view: self.summary_view.update_summary(None)

    def run_pda(self, file_path):
        if not self.analysis_view: return
        self.current_file_path = file_path
        results = self.cv_engine.detect(file_path)
        results["damage_level"] = self._recalculate_damage_level(results)
        self.original_results = deepcopy(results)
        self._update_all_views(file_path, results)

    def recalculate_results_with_new_mask(self, new_column_mask):
        if not self.original_results or not self.current_file_path:
            logger.warning("Cannot recalculate without initial analysis results.")
            return
        
        filtered_results = self._filter_defects_by_roi(self.original_results, new_column_mask)
        filtered_results["damage_level"] = self._recalculate_damage_level(filtered_results)
        
        self._update_all_views(self.current_file_path, filtered_results)
        logger.info(f"Results recalculated for new mask. New Damage Level: {filtered_results['damage_level']}")

    def restore_original_results(self):
        if not self.original_results or not self.current_file_path:
            logger.warning("No original results available to restore.")
            return
        self._update_all_views(self.current_file_path, self.original_results)
        logger.info("Original analysis results have been restored.")

    def update_damage_assessment(self, updated_data):
        if not self.analysis_view or not self.current_file_path: return
        updated_data["damage_level"] = self._recalculate_damage_level(updated_data)
        self._update_all_views(self.current_file_path, updated_data)
        logger.info(f"Damage assessment updated. New level: {updated_data['damage_level']}")

    def _update_all_views(self, file_path, results):
        results_copy = deepcopy(results)

        if self.analysis_view:
            self.analysis_view.last_results = results_copy
            self.analysis_view.display_results(results_copy)
            show_defects = self.analysis_view.show_defects_checkbox.isChecked()
            self.update_image_display(file_path, results_copy, show_cracks=show_defects)
        
        if self.correction_view:
            if self.correction_view.current_file_path != file_path:
                self.correction_view.display_image(file_path)
            self.correction_view.display_updated_results(results_copy)

        if self.summary_view:
            overlay_path = self._create_detection_overlay(file_path, results_copy)
            results_copy['overlay_path'] = overlay_path
            self.summary_view.update_summary(results_copy)

    def _filter_defects_by_roi(self, original_results, new_column_mask):
        recounted_results = deepcopy(original_results)
        filtered_rois, filtered_class_ids, filtered_scores = [], [], []
        spalling_area_in_mask = 0
        for i, roi in enumerate(original_results["rois"]):
            class_id = original_results["class_ids"][i]
            if 0 <= class_id < len(class_names) and class_names[class_id] == 'column': continue
            if iou(roi, new_column_mask) > 0.9:
                filtered_rois.append(roi)
                filtered_class_ids.append(class_id)
                filtered_scores.append(original_results["scores"][i])
                if 0 <= class_id < len(class_names) and class_names[class_id] == 'spalling':
                    spalling_area_in_mask += get_bbox_area(roi)

        new_column_area = get_bbox_area(new_column_mask)
        recounted_results.update({
            "rois": np.array(filtered_rois), "class_ids": filtered_class_ids, "scores": filtered_scores,
            "num_exposed_horizontal_bars": sum(1 for cid in filtered_class_ids if 0 <= cid < len(class_names) and class_names[cid] == 'horizontal'),
            "num_exposed_vertical_bars": sum(1 for cid in filtered_class_ids if 0 <= cid < len(class_names) and class_names[cid] == 'vertical'),
            "spalled_ratio": (spalling_area_in_mask / new_column_area) * 100 if new_column_area > 0 else 0,
        })
        return recounted_results

    def _recalculate_damage_level(self, data):
        rules = self.damage_rules
        h_bars = data.get("num_exposed_horizontal_bars", 0)
        v_bars = data.get("num_exposed_vertical_bars", 0)
        spall = data.get("spalled_ratio", 0)
        h_cracks = data.get("num_horizontal_cracks", 0)
        v_cracks = data.get("num_vertical_cracks", 0)

        if v_bars >= rules["level_5"]["min_v_bars"] or h_bars >= rules["level_5"]["min_h_bars"]:
            return "Level 5"
        if v_bars >= rules["level_4"]["min_v_bars"] or h_bars >= rules["level_4"]["min_h_bars"] or spall >= rules["level_4"]["min_spall_ratio"]:
            return "Level 4"
        if spall >= rules["level_3"]["min_spall_ratio"]:
            return "Level 3"
        if v_cracks >= rules["level_2"]["min_v_cracks"]:
            return "Level 2"
        if h_cracks >= rules["level_1"]["min_h_cracks"] and v_cracks <= rules["level_1"]["max_v_cracks"]:
            return "Level 1"
        return "Level 0"

    def update_image_display(self, file_path, results, show_cracks=False, score_threshold=0.5):
        """Show either original image or overlaid detection image."""
        if show_cracks and results and "rois" in results and np.array(results["rois"]).any():
            overlay_path = self._create_detection_overlay(file_path, results, score_threshold)
            self.analysis_view.display_image(overlay_path)
        else:
            self.analysis_view.display_image(file_path)

    def _create_detection_overlay(self, file_path, results, score_threshold=0.5):
        image = io.imread(file_path)
        if image.ndim != 3: image = color.gray2rgb(image)
        if image.shape[-1] == 4: image = image[..., :3]
        overlay = img_as_ubyte(image)

        if "crack_image" in results and results["crack_image"] is not None:
            crack_overlay = results["crack_image"]
            if crack_overlay.ndim == 2: crack_overlay = color.gray2rgb(crack_overlay)
            h, w, _ = overlay.shape
            crack_overlay_resized = cv2.resize(img_as_ubyte(crack_overlay), (w, h))
            overlay = cv2.addWeighted(overlay, 1, crack_overlay_resized, 0.6, 0)

        boxes = np.array(results["rois"]).astype(np.int32)
        masks = results.get("masks")
        scores = results.get("scores", np.ones(boxes.shape[0]))
        class_ids = results["class_ids"]
        
        padded_shape = masks.shape[:2] if masks is not None else image.shape[:2]

        cropped_boxes, cropped_masks = self._crop_padded_rois(
            image.shape[:2], padded_shape, boxes, masks
        )

        colors = { 1: (1,0,0), 2: (0,1,0), 3: (0,0,1), 4: (0.5,0,1) }

        for i in range(cropped_boxes.shape[0]):
            if scores[i] < score_threshold: continue
            
            class_id = class_ids[i]
            color_rgb = colors.get(class_id, (random.random(), random.random(), random.random()))
            cv_color = tuple(c * 255 for c in color_rgb)

            y1, x1, y2, x2 = cropped_boxes[i]
            cv2.rectangle(overlay, (int(x1), int(y1)), (int(x2), int(y2)), cv_color, 2)
            
            label = f"{class_names[class_id]}"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            text_y = y1 - 10 if y1 - 10 > h else y1 + h + 10
            cv2.putText(overlay, label, (int(x1), int(text_y)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cv_color, 2)

            if cropped_masks is not None and i < cropped_masks.shape[2]:
                mask = cropped_masks[:, :, i]
                if mask.sum() > 0:
                    mask_uint8 = (mask * 255).astype(np.uint8)
                    contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    cv2.drawContours(overlay, contours, -1, cv_color, 2)

        boxes_crack = results.get("boxes_crack", [])
        if boxes_crack and np.array(boxes_crack).any():
            cropped_crack_boxes, _ = self._crop_padded_rois(
                image.shape[:2], padded_shape, np.array(boxes_crack), None
            )
            for box in cropped_crack_boxes:
                y1, x1, y2, x2 = box
                cv2.rectangle(overlay, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 255), 2)  # Cyan for cracks

        cv2.putText(overlay, results["damage_level"], (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        overlay_path = Path(file_path).with_suffix(".overlay.png")
        io.imsave(str(overlay_path), overlay)
        return str(overlay_path)

    def _crop_padded_rois(self, original_shape, padded_shape, boxes, masks):
        orig_h, orig_w = original_shape
        padded_h, padded_w = padded_shape
        top_pad, left_pad = (padded_h - orig_h) // 2, (padded_w - orig_w) // 2

        if top_pad == 0 and left_pad == 0 and padded_h == orig_h and padded_w == orig_w:
            return boxes, masks

        boxes = boxes.astype(np.int32).copy()
        boxes[:, [0, 2]] = np.clip(boxes[:, [0, 2]] - top_pad, 0, orig_h - 1)
        boxes[:, [1, 3]] = np.clip(boxes[:, [1, 3]] - left_pad, 0, orig_w - 1)
        
        cropped_masks = None
        if masks is not None:
            cropped_masks = masks[top_pad : top_pad + orig_h, left_pad : left_pad + orig_w, :]
        return boxes, cropped_masks

    def _crop_padded_points(self, original_shape, padded_shape, points):
        orig_h, orig_w = original_shape
        padded_h, padded_w = padded_shape
        top_pad, left_pad = (padded_h - orig_h) // 2, (padded_w - orig_w) // 2

        points = np.array(points).astype(np.int32)
        points[:, 0] = np.clip(points[:, 0] - top_pad, 0, orig_h - 1)
        points[:, 1] = np.clip(points[:, 1] - left_pad, 0, orig_w - 1)
        return points
