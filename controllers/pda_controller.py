# controllers/pda_controller.py
import logging
from copy import deepcopy
import cv2
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
        self.correction_view = None  # Updated name
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
        self.correction_view = correction_view  # Updated name
        self.summary_view = summary_view

    def upload_image(self, file_path):
        self.current_file_path = file_path
        self.original_results = None
        if self.analysis_view: self.analysis_view.display_image(file_path)
        if self.correction_view: self.correction_view.display_image(file_path)  # Updated name
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
        
        overlay = self._generate_final_overlay(self.current_file_path, filtered_results)
        filtered_results["overlay_image"] = overlay

        if self.correction_view: self.correction_view.display_updated_results(filtered_results)  # Updated name
        if self.summary_view: self.summary_view.update_summary(filtered_results)

        logger.info(f"Results recalculated for new mask. New Damage Level: {filtered_results['damage_level']}")

    def restore_original_results(self):
        if not self.original_results or not self.current_file_path:
            logger.warning("No original results available to restore.")
            return
        self._update_all_views(self.current_file_path, self.original_results)
        logger.info("Original analysis results have been restored.")

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
                if 0 <= class_id < len(class_names) and class_names[class_id] == 'spalling': spalling_area_in_mask += get_bbox_area(roi)

        new_column_area = get_bbox_area(new_column_mask)
        recounted_results.update({
            "rois": filtered_rois, "class_ids": filtered_class_ids, "scores": filtered_scores,
            "num_exposed_horizontal_bars": sum(1 for cid in filtered_class_ids if 0 <= cid < len(class_names) and class_names[cid] == 'horizontal'),
            "num_exposed_vertical_bars": sum(1 for cid in filtered_class_ids if 0 <= cid < len(class_names) and class_names[cid] == 'vertical'),
            "spalled_ratio": (spalling_area_in_mask / new_column_area) * 100 if new_column_area > 0 else 0,
        })
        return recounted_results

    def update_damage_assessment(self, updated_data):
        if not self.analysis_view or not self.current_file_path: return
        updated_data["damage_level"] = self._recalculate_damage_level(updated_data)
        self._update_all_views(self.current_file_path, updated_data)
        logger.info(f"Damage assessment updated. New level: {updated_data['damage_level']}")

    def _update_all_views(self, file_path, results):
        results_copy = deepcopy(results)
        overlay = self._generate_final_overlay(file_path, results_copy)
        results_copy["overlay_image"] = overlay

        if self.analysis_view:
            self.analysis_view.last_results = results_copy
            self.analysis_view.display_results(results_copy)
            show_defects = self.analysis_view.show_defects_checkbox.isChecked()
            self.update_image_display(file_path, results_copy, show_cracks=show_defects)
        if self.correction_view:  # Updated name
            if self.correction_view.current_file_path != file_path: self.correction_view.display_image(file_path)  # Updated name
            self.correction_view.display_updated_results(results_copy)
        if self.summary_view:
            self.summary_view.update_summary(results_copy)

    def _recalculate_damage_level(self, data):
        rules, h_bars, v_bars, spall, h_cracks, v_cracks = self.damage_rules, data.get("num_exposed_horizontal_bars", 0), data.get("num_exposed_vertical_bars", 0), data.get("spalled_ratio", 0), data.get("num_horizontal_cracks", 0), data.get("num_vertical_cracks", 0)
        if v_bars >= rules["level_5"]["min_v_bars"] or h_bars >= rules["level_5"]["min_h_bars"]: return "Level 5"
        if v_bars >= rules["level_4"]["min_v_bars"] or h_bars >= rules["level_4"]["min_h_bars"] or spall >= rules["level_4"]["min_spall_ratio"]: return "Level 4"
        if spall >= rules["level_3"]["min_spall_ratio"]: return "Level 3"
        if v_cracks >= rules["level_2"]["min_v_cracks"]: return "Level 2"
        if h_cracks >= rules["level_1"]["min_h_cracks"] and v_cracks <= rules["level_1"]["max_v_cracks"]: return "Level 1"
        return "Level 0"

    def _generate_final_overlay(self, file_path, results, score_threshold=0.5):
        base_overlay = self._create_detection_overlay(file_path, results, score_threshold)
        if "crack_image" in results and results["crack_image"] is not None:
            crack_overlay = results["crack_image"]
            if crack_overlay.ndim == 2: crack_overlay = cv2.cvtColor(crack_overlay, cv2.COLOR_GRAY2BGR)
            elif crack_overlay.shape[2] == 4: crack_overlay = cv2.cvtColor(crack_overlay, cv2.COLOR_RGBA2BGR)
            h, w, _ = base_overlay.shape
            crack_overlay_resized = cv2.resize(crack_overlay, (w, h))
            return cv2.addWeighted(base_overlay, 1, img_as_ubyte(crack_overlay_resized), 0.6, 0)
        return base_overlay

    def update_image_display(self, file_path, results, show_cracks=False):
        if not self.analysis_view: return
        if show_cracks and "overlay_image" in results:
            self.analysis_view.display_image(results["overlay_image"], is_np_array=True)
        else:
            self.analysis_view.display_image(file_path)

    def _create_detection_overlay(self, file_path, results, score_threshold=0.5):
        try:
            image = io.imread(file_path)
            if image.ndim != 3: image = color.gray2rgb(image)
            if image.shape[-1] == 4: image = image[..., :3]
            overlay = img_as_ubyte(image.copy())
            for i, roi in enumerate(results.get("rois", [])):
                if results["scores"][i] < score_threshold: continue
                class_id = results["class_ids"][i]
                if 0 <= class_id < len(class_names):
                    class_name = class_names[class_id]
                else:
                    class_name = 'unknown'
                y1, x1, y2, x2 = roi
                c = {"column": (0,0,255), "spalling": (0,255,0), "horizontal": (255,0,0), "vertical": (255,255,0)}.get(class_name, (255,0,255))
                cv2.rectangle(overlay, (x1, y1), (x2, y2), c, 2)
                label = f"{class_name}: {results['scores'][i]:.2f}"
                cv2.putText(overlay, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 2)
            return overlay
        except Exception as e:
            logger.error(f"Error creating detection overlay: {e}")
            return img_as_ubyte(io.imread(file_path))
