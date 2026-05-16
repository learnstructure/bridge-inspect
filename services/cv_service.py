import logging
logger = logging.getLogger(__name__)

import os
import tensorflow as tf
import mrcnn.model as modellib
from deficiency import DeficiencyConfig
import skimage
import numpy as np

class DetectionEngine:
    def __init__(self, model_dir="./models"):
        # Create inference config with batch size = 1
        class InferenceConfig(DeficiencyConfig):
            GPU_COUNT = 1
            IMAGES_PER_GPU = 1  # Set batch size to 1 for single image inference
        
        config = InferenceConfig()
        
        # MaskRCNN requires model_dir parameter
        logs_dir = os.path.join(model_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        self.mask_rcnn = modellib.MaskRCNN(
            mode="inference", 
            config=config,
            model_dir=logs_dir
        )
        
        # Load Mask R-CNN weights
        mask_rcnn_path = os.path.join(model_dir, "mask_rcnn_deficiency_0070.h5")
        self.mask_rcnn.load_weights(mask_rcnn_path, by_name=True)
        
        # Keras model for cracks
        crack_model_path = os.path.join(model_dir, "finetuned_rescale.h5")
        self.crack_model = tf.keras.models.load_model(crack_model_path)
    
    def detect(self, image_path):
        """Run Mask R-CNN detection on image from file path"""
        # Load image from file path
        image = skimage.io.imread(image_path)
        
        # If grayscale, convert to RGB
        if image.ndim != 3:
            # import skimage.color
            image = skimage.color.gray2rgb(image)
        
        # If has alpha channel, remove it
        if image.shape[-1] == 4:
            image = image[..., :3]
        
        # Pad image to multiples of 64
        oh, ow = image.shape[:2]
        
        if oh % 64 > 0:
            max_h = oh - (oh % 64) + 64
            top_pad = (max_h - oh) // 2
            bottom_pad = max_h - oh - top_pad
        else:
            top_pad = bottom_pad = 0
        
        if ow % 64 > 0:
            max_w = ow - (ow % 64) + 64
            left_pad = (max_w - ow) // 2
            right_pad = max_w - ow - left_pad
        else:
            left_pad = right_pad = 0
        
        padding = [(top_pad, bottom_pad), (left_pad, right_pad), (0, 0)]
        image = np.pad(image, padding, mode="constant", constant_values=0)
        
        # Run detection with batch size 1
        results = self.mask_rcnn.detect([image], verbose=0)
        # print(f"Mask R-CNN detection results: {results}")
        return results[0]