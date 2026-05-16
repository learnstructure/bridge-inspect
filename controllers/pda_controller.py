from pathlib import Path
import logging
from services.cv_service import DetectionEngine


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

        # Check if there was an error in cv_service
        if "error" in results:
            logger.error(f"PDA analysis failed: {results['error']}")
            self.view.display_results(results)
            return

        logger.info("PDA analysis completed successfully")
        self.view.display_results(results)



        # try:
        #     logger.info(f"Starting PDA analysis on: {file_path}")
        #     results = self.cv_engine.detect(file_path)
        #     self.view.last_results = results
        #     self.view.display_results(results)

        #     # Check if there was an error in cv_service
        #     if "error" in results:
        #         logger.error(f"PDA analysis failed: {results['error']}")
        #         self.view.display_results(results)
        #         return

        #     logger.info("PDA analysis completed successfully")
        #     self.view.display_results(results)

        # except Exception as e:
        #     logger.error(f"Unexpected error during PDA: {e}")
        #     self.view.display_results({"error": f"Unexpected error: {str(e)}"})
        
