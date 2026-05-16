#This file is not used currently. 

# from services.cv_service import run_crack_detection
# from services.cv_service import overlay_cracks_on_image
# import cv2
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PDAController:
    def __init__(self, view):
        self.view = view  # PDAPage UI

    def upload_image(self, file_path):
        """Display uploaded image in the viewer"""
        self.view.display_image(file_path)

    # def run_pda(self, file_path):
    #     """
    #     Run crack detection on the uploaded image.

    #     Args:
    #         file_path (str): Path to the image file
    #     """
    #     if not file_path:
    #         self.view.display_results(
    #             {"error": "No image selected. Please upload an image first."}
    #         )
    #         return

    #     try:
    #         logger.info(f"Starting PDA analysis on: {file_path}")
    #         results = run_crack_detection(file_path)
    #         self.view.last_results = results
    #         self.view.display_results(results)
    #         self.update_image_display(file_path, results, show_cracks=True)

    #         # Check if there was an error in cv_service
    #         if "error" in results:
    #             logger.error(f"PDA analysis failed: {results['error']}")
    #             self.view.display_results(results)
    #             return

    #         logger.info("PDA analysis completed successfully")
    #         self.view.display_results(results)

    #     except Exception as e:
    #         logger.error(f"Unexpected error during PDA: {e}")
    #         self.view.display_results({"error": f"Unexpected error: {str(e)}"})


    # def update_image_display(self, file_path, results, show_cracks=False):
    #     """Display image with optional crack overlay."""
    #     if show_cracks and "pred_mask" in results:
    #         # Create overlaid image and save temporarily
    #         overlaid_img = overlay_cracks_on_image(file_path, results["pred_mask"])
    #         temp_path = Path(file_path).parent / ".temp_overlay.jpg"
    #         cv2.imwrite(str(temp_path), overlaid_img)
    #         self.view.display_image(str(temp_path))
    #     else:
    #         # Display original image
    #         self.view.display_image(file_path)