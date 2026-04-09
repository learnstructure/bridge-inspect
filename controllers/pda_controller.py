from services.cv_service import run_crack_detection


class PDAController:
    def __init__(self, view):
        self.view = view  # PDAPage UI

    def upload_image(self, file_path):
        self.view.display_image(file_path)

    def run_pda(self, file_path):
        results = run_crack_detection(file_path)
        self.view.display_results(results)
