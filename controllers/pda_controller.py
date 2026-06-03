from pathlib import Path
import logging
import numpy as np
from skimage import color, io, img_as_ubyte
import cv2
import random

from services.cv_service import DetectionEngine, class_names

logger = logging.getLogger(__name__)

class PDAController:
    def __init__(self):
        self.analysis_view = None
        self.mask_view = None
        self.summary_view = None
        self.cv_engine = DetectionEngine()
        # Updated default rules to match the new UI labels and logic
        self.damage_rules = {
            "level_5": {"min_h_bars": 3, "min_v_bars": 2},
            "level_4": {"min_h_bars": 1, "min_v_bars": 1, "min_spall_ratio": 50},
            "level_3": {"min_spall_ratio": 10},
            "level_2": {"min_v_cracks": 3},
            "level_1": {"min_h_cracks": 1, "max_v_cracks": 0}
        }

    def set_view(self, analysis_view, mask_view, summary_view):
        self.analysis_view = analysis_view
        self.mask_view = mask_view
        self.summary_view = summary_view

    def upload_image(self, file_path):
        if self.analysis_view:
            self.analysis_view.display_image(file_path)

    def run_pda(self, file_path):
        if not self.analysis_view: return
        results = self.cv_engine.detect(file_path)
        results["damage_level"] = self._recalculate_damage_level(results)
        self._update_all_views(file_path, results)

    def update_damage_assessment(self, updated_data):
        if not self.analysis_view: return
        recalculated_level = self._recalculate_damage_level(updated_data)
        updated_data["damage_level"] = recalculated_level
        self._update_all_views(self.analysis_view.current_file_path, updated_data)
        logger.info(f"Damage assessment updated. New level: {recalculated_level}")

    def update_damage_rules(self, new_rules):
        """Updates the damage classification rules from user input."""
        try:
            for level, params in new_rules.items():
                for k, v in params.items():
                    # Ensure the key exists before trying to update it
                    if k in self.damage_rules[level]:
                        self.damage_rules[level][k] = int(v)
            logger.info(f"Damage state rules updated: {self.damage_rules}")
            if self.analysis_view and self.analysis_view.last_results:
                self.update_damage_assessment(self.analysis_view.last_results)
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Error updating rules: {e}. Please ensure all inputs are valid.")

    def _update_all_views(self, file_path, results):
        if self.analysis_view:
            self.analysis_view.last_results = results
            self.analysis_view.display_results(results)
            self.update_image_display(file_path, results, show_cracks=self.analysis_view.show_defects_checkbox.isChecked())
        if self.mask_view:
            self.mask_view.display_image(file_path)
            self.mask_view.display_column_bbox(results)
        if self.summary_view:
            self.summary_view.update_summary(results)

    def _recalculate_damage_level(self, data):
        rules = self.damage_rules
        num_h_bars = data.get("num_exposed_horizontal_bars", 0)
        # Updated to use the count of exposed vertical bars
        num_v_bars = data.get("num_exposed_vertical_bars", 0)
        spall_ratio = data.get("spalled_ratio", 0)
        num_h_cracks = data.get("num_horizontal_cracks", 0)
        num_v_cracks = data.get("num_vertical_cracks", 0)

        # Logic updated to use num_v_bars and the new rule key
        if num_v_bars >= rules["level_5"]["min_v_bars"] or num_h_bars >= rules["level_5"]["min_h_bars"]: return "Level 5"
        if num_v_bars >= rules["level_4"]["min_v_bars"] or num_h_bars >= rules["level_4"]["min_h_bars"] or spall_ratio >= rules["level_4"]["min_spall_ratio"]: return "Level 4"
        if spall_ratio >= rules["level_3"]["min_spall_ratio"]: return "Level 3"
        if num_v_cracks >= rules["level_2"]["min_v_cracks"]: return "Level 2"
        if num_h_cracks >= rules["level_1"]["min_h_cracks"] and num_v_cracks <= rules["level_1"]["max_v_cracks"]: return "Level 1"
        return "Level 0"

    def update_image_display(self, file_path, results, show_cracks=False, score_threshold=0.5):
        # ... (rest of the method is unchanged)
        pass

    def _create_detection_overlay(self, file_path, results, score_threshold=0.5):
        # ... (rest of the method is unchanged)
        pass
