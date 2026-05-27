import logging
import math
import os
import random

import mrcnn.model as modellib
import numpy as np
import scipy.ndimage as ndimage
import skimage
import tensorflow as tf
from deficiency import DeficiencyConfig
from skimage import color
from sklearn.linear_model import LinearRegression, RANSACRegressor

logger = logging.getLogger(__name__)


class_names = ["BG", "column", "spalling", "horizontal", "vertical"]


class DetectionEngine:
    def __init__(self, model_dir="./models"):
        class InferenceConfig(DeficiencyConfig):
            GPU_COUNT = 1
            IMAGES_PER_GPU = 1

        config = InferenceConfig()
        logs_dir = os.path.join(model_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)

        self.mask_rcnn = modellib.MaskRCNN(mode="inference", config=config, model_dir=logs_dir)
        mask_rcnn_path = os.path.join(model_dir, "mask_rcnn_deficiency_0070.h5")
        self.mask_rcnn.load_weights(mask_rcnn_path, by_name=True)

        crack_model_path = os.path.join(model_dir, "finetuned_rescale.h5")
        self.crack_model = tf.keras.models.load_model(crack_model_path)

    def detect(self, image_path):
        image = skimage.io.imread(image_path)
        if image.ndim != 3:
            image = color.gray2rgb(image)
        if image.shape[-1] == 4:
            image = image[..., :3]

        oh, ow = image.shape[:2]
        max_h, max_w = oh, ow
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
        padded_image = np.pad(image, padding, mode="constant", constant_values=0)

        results = self.mask_rcnn.detect([padded_image], verbose=0)
        r = results[0]

        for i in range(len(r["rois"])):
            from_mask = np.where(r["masks"][:, :, i] == True)
            if from_mask[0].size > 0:
                r["rois"][i] = [
                    min(from_mask[0]),
                    min(from_mask[1]),
                    max(from_mask[0]),
                    max(from_mask[1]),
                ]

        self.image = image
        self.padded_image = padded_image
        self.class_ids = r["class_ids"]
        self.masks = r["masks"]
        self.rois = r["rois"]
        self.scores = r["scores"]
        self.max_h = max_h
        self.max_w = max_w

        (self.columnIndex,) = np.where(self.class_ids == 1)
        (self.spallingIndex,) = np.where(self.class_ids == 2)
        (self.horizontalIndex,) = np.where(self.class_ids == 3)
        (self.verticalIndex,) = np.where(self.class_ids == 4)
        self.title = ""
        self.max_dist = 0
        self.spalled_ratio = 0
        self.dist_coord = []
        self.cid = -1
        self.connection = []
        self.boxes_crack = []
        self.num_horizontal_cracks = 0
        self.num_vertical_cracks = 0

        self.column_detect()

        valid_indices = np.unique(np.concatenate([
            self.columnIndex,
            self.spallingIndex,
            self.horizontalIndex,
            self.verticalIndex
        ]).astype(int))

        new_cid = -1
        if self.cid != -1:
            match = np.where(valid_indices == self.cid)[0]
            if match.size > 0:
                new_cid = match[0]

        processed_results = {
            "rois": self.rois[valid_indices],
            "class_ids": self.class_ids[valid_indices],
            "scores": self.scores[valid_indices],
            "masks": self.masks[:, :, valid_indices],
            "damage_level": self.title,
            "column_present": self.columnIndex.size > 0,
            "image_shape": self.image.shape,
            "dist_coord": self.dist_coord,
            "max_dist": self.max_dist,
            "spalled_ratio": self.spalled_ratio,
            "cid": new_cid,
            "connection": self.connection,
            "boxes_crack": self.boxes_crack,
            "num_horizontal_cracks": self.num_horizontal_cracks,
            "num_vertical_cracks": self.num_vertical_cracks,
            "num_exposed_horizontal_bars": len(self.horizontalIndex),
            "num_exposed_vertical_bars": len(self.connection),
        }

        if hasattr(self, "newimg"):
            processed_results["crack_image"] = self.newimg
        
        return processed_results

    def column_detect(self):
        if self.columnIndex.size == 0:
            self.title = "Column Detection Failed"
            self.crack_detection(columnInstance=False)
        else:
            self.exposed_bar()

    def exposed_bar(self):
        validVerticalIndex = np.array([], dtype="int32")
        validHorizontalIndex = np.array([], dtype="int32")
        self.allowance = 1000

        if self.verticalIndex.size > 0:
            for i in range(self.columnIndex.size):
                columnRoi = self.rois[self.columnIndex[i]]
                for j in range(self.verticalIndex.size):
                    verticalRoi = self.rois[self.verticalIndex[j]]
                    if (
                        verticalRoi[0] >= columnRoi[0] - self.allowance
                        and verticalRoi[1] >= columnRoi[1] - self.allowance
                        and verticalRoi[2] <= columnRoi[2] + self.allowance
                        and verticalRoi[3] <= columnRoi[3] + self.allowance
                    ):
                        validVerticalIndex = np.append(validVerticalIndex, self.verticalIndex[j])
        self.verticalIndex = validVerticalIndex
        if len(self.verticalIndex) > 0:
            self.verticalLineConnection()

        if self.horizontalIndex.size > 0:
            for i in range(self.columnIndex.size):
                columnRoi = self.rois[self.columnIndex[i]]
                for j in range(self.horizontalIndex.size):
                    horizontalRoi = self.rois[self.horizontalIndex[j]]
                    if (
                        horizontalRoi[0] >= columnRoi[0] - self.allowance
                        and horizontalRoi[1] >= columnRoi[1] - self.allowance
                        and horizontalRoi[2] <= columnRoi[2] + self.allowance
                        and horizontalRoi[3] <= columnRoi[3] + self.allowance
                    ):
                        validHorizontalIndex = np.append(validHorizontalIndex, self.horizontalIndex[j])
        self.horizontalIndex = validHorizontalIndex
        self.spalling_detection()

    def verticalLineConnection(self):
        self.connection = []
        verticalRois = [self.rois[i] for i in self.verticalIndex]
        verticalRois = sorted(verticalRois, key=lambda x: (x[0], x[1]))

        for roi in verticalRois:
            midy, midx = (roi[2] + roi[0]) / 2, (roi[3] + roi[1]) / 2
            flag = False
            for connectedset in self.connection:
                last = connectedset[-1]
                last_y, last_x = (last[2] + last[0]) / 2, (last[3] + last[1]) / 2
                actual = np.linalg.norm(np.array([midy, midx]) - np.array([last_y, last_x]))
                threshold = math.sqrt(
                    (abs(((last[2] - last[0]) / 2)) + abs(((roi[2] - roi[0]) / 2))) ** 2
                    + (abs(((last[3] - last[1]) / 2)) + abs(((roi[3] - roi[1]) / 2))) ** 2
                )
                if actual <= (threshold + 100):
                    connectedset.append(roi)
                    flag = True
                    break
            if not self.connection:
                self.connection.append([roi])
                continue
            if not flag:
                self.connection.append([roi])

    def spalling_detection(self):
        validSpallingIndex = np.array([], dtype="int32")
        self.allowance = 100
        if self.spallingIndex.size > 0:
            for i in range(self.columnIndex.size):
                columnRoi = self.rois[self.columnIndex[i]]
                for j in range(self.spallingIndex.size):
                    spallingRoi = self.rois[self.spallingIndex[j]]
                    if (
                        ((
                            columnRoi[0] + self.allowance <= spallingRoi[0] <= columnRoi[2] - self.allowance and
                            columnRoi[1] + self.allowance <= spallingRoi[1] <= columnRoi[3] - self.allowance
                        ) or (
                            columnRoi[0] + self.allowance <= spallingRoi[2] <= columnRoi[2] - self.allowance and
                            columnRoi[1] + self.allowance <= spallingRoi[3] <= columnRoi[3] - self.allowance
                        ) or (
                            columnRoi[0] + self.allowance <= spallingRoi[0] <= columnRoi[2] - self.allowance and
                            columnRoi[1] + self.allowance <= spallingRoi[3] <= columnRoi[3] - self.allowance
                        ) or (
                            columnRoi[0] + self.allowance <= spallingRoi[2] <= columnRoi[2] - self.allowance and
                            columnRoi[1] + self.allowance <= spallingRoi[1] <= columnRoi[3] - self.allowance
                        ))
                    ):
                        validSpallingIndex = np.append(validSpallingIndex, self.spallingIndex[j])
        self.spallingIndex = validSpallingIndex
        validSpallingSizeIndex = np.array([], dtype="int32")
        for i in range(self.columnIndex.size):
            columnRoi = self.rois[self.columnIndex[i]]
            columnSize = abs(columnRoi[2] - columnRoi[0]) * abs(columnRoi[3] - columnRoi[1])
            for j in range(self.spallingIndex.size):
                spallingRoi = self.rois[self.spallingIndex[j]]
                spalledSize = abs(spallingRoi[2] - spallingRoi[0]) * abs(spallingRoi[3] - spallingRoi[1])
                if spalledSize > columnSize * 0.005:
                    validSpallingSizeIndex = np.append(validSpallingSizeIndex, self.spallingIndex[j])
        self.spallingIndex = validSpallingSizeIndex
        self.maximumArea()

    def maximumArea(self, columnInstance=True):
        for i in range(self.spallingIndex.size):
            row, col = np.where(self.masks[:, :, self.spallingIndex[i]] == True)
            new_row = np.unique(row)
            reduced_coord = []
            for j in range(len(new_row)):
                row_tmp = new_row[j]
                col1, col2 = np.min(np.where(row == row_tmp)), np.max(np.where(row == row_tmp))
                reduced_coord.append([row_tmp, col[col1]])
                reduced_coord.append([row_tmp, col[col2]])
            res_tmp = [[0, 0], [0, 0]]
            max_dist_tmp = 0
            for j in range(len(reduced_coord) - 1):
                for k in range(j, len(reduced_coord)):
                    new_dist = np.linalg.norm(np.array(reduced_coord[j]) - np.array(reduced_coord[k]))
                    if max_dist_tmp < new_dist:
                        max_dist_tmp = new_dist
                        res_tmp[0] = reduced_coord[j]
                        res_tmp[1] = reduced_coord[k]
                if max_dist_tmp > self.max_dist:
                    self.cid = self.spallingIndex[i]
                    self.max_dist = max_dist_tmp
                    self.dist_coord = res_tmp
        if self.cid != -1 and columnInstance:
            self.calcDeficiency()
        elif self.cid == -1 and len(self.columnIndex) > 0 and columnInstance:
            self.crack_detection()

    def crack_detection(self, columnInstance=True):
        oh, ow = self.image.shape[:2]
        colcoor = [0, 0, oh, ow]
        if columnInstance:
            colcoor = self.rois[self.columnIndex[0]]
        
        new_map = np.full((oh * ow), 0).reshape(oh, ow)
        m, n = round((self.max_h - 64) / 32) + 1, round((self.max_w - 64) / 32) + 1
        patch_size = 32

        for j in range(n - 1):
            for i in range(m - 1):
                new_h1, new_h2 = (patch_size * i), (patch_size * i + 64)
                new_w1, new_w2 = (patch_size * j), (patch_size * j + 64)

                if (
                    (colcoor[0] <= new_h1 <= colcoor[2]) and (colcoor[1] <= new_w1 <= colcoor[3]) and
                    (colcoor[0] <= new_h2 <= colcoor[2]) and (colcoor[1] <= new_w2 <= colcoor[3])
                ):
                    patch = self.image[new_h1:new_h2, new_w1:new_w2]
                    if patch.shape[0] != 64 or patch.shape[1] != 64:
                        continue
                    
                    x = np.expand_dims(patch, axis=0) / 255.0
                    classes = self.crack_model.predict_classes(x)
                    if classes[0] == 1:
                        new_map[new_h1:new_h2, new_w1:new_w2] = 1
        
        self.newimg = self.image.copy()
        self.newimg[:, :, 0] = np.where(
            new_map[:, :] == 1,
            self.image[:, :, 0] * 0.5 + 0.5 * 255 * 255,
            self.image[:, :, 0]
        )

        save_new_map = new_map
        total_crack = []
        diff = 32 * (2**0.5)
        for j in range(n - 1):
            for i in range(m - 1):
                new_h1, new_h2 = (patch_size * i), (patch_size * i + 64)
                new_w1, new_w2 = (patch_size * j), (patch_size * j + 64)
                
                if new_h2 > oh or new_w2 > ow:
                    continue

                if save_new_map[new_h1:new_h2, new_w1:new_w2].all() == 1:
                    center_point = [((new_h2 - 1) + new_h1) / 2, ((new_w2 - 1) + new_w1) / 2]
                    flag = False
                    for k in range(len(total_crack)):
                        for l in range(len(total_crack[k])):
                            dist = math.sqrt(((total_crack[k][l][0] - center_point[0]) ** 2) + ((total_crack[k][l][1] - center_point[1]) ** 2))
                            if dist <= diff:
                                total_crack[k].append(center_point)
                                flag = True
                                break
                        if flag:
                            break
                    if not flag:
                        total_crack.append([center_point])

        self.boxes_crack = []
        for k in range(len(total_crack)):
            y_coords = [p[0] for p in total_crack[k]]
            x_coords = [p[1] for p in total_crack[k]]
            y1, y2 = min(y_coords) - 32, max(y_coords) + 32
            x1, x2 = min(x_coords) - 32, max(x_coords) + 32
            self.boxes_crack.append(np.array([y1, x1, y2, x2]))

        level1 = 0
        level2 = 0
        for box in self.boxes_crack:
            y1, x1, y2, x2 = [round(c) for c in box]
            if ((y2 - y1) * (x2 - x1)) > (64 * 64):
                crack_patch = self.image[y1:y2, x1:x2]
                if crack_patch.size == 0:
                    continue
                
                filtered_crack = ndimage.gaussian_filter(crack_patch, sigma=(1, 1, 0), order=0)
                gray_crack = color.rgb2gray(filtered_crack)

                hog_features = self.compute_hog_features(
                    gray_crack, n_orientations=9, pixels_per_cell=(8, 8), cells_per_block=(1, 1)
                )
                if hog_features > 80:
                    level1 += 1
                elif hog_features < 70:
                    level2 += 1
        
        self.num_horizontal_cracks = level1
        self.num_vertical_cracks = level2

        if not level2 and level1:
            self.title = "Level 1"
        if level2 and level2 >= 3:
            self.title = "Level 2"
        if not columnInstance:
            self.title = "Column Detection failed " + self.title

    def compute_gradient(self, image):
        gx = np.zeros_like(image, dtype=np.float64)
        gy = np.zeros_like(image, dtype=np.float64)
        gx[:, 1:-1] = (image[:, 2:] - image[:, :-2]) / 2.0
        gy[1:-1, :] = (image[2:, :] - image[:-2, :]) / 2.0
        gx[:, 0] = image[:, 1] - image[:, 0]
        gy[0, :] = image[1, :] - image[0, :]
        gx[:, -1] = image[:, -1] - image[:, -2]
        gy[-1, :] = image[-1, :] - image[-2, :]
        return gx, gy

    def compute_hog_cell(self, n_orientations, magnitudes, orientations):
        bin_width = 180 / n_orientations
        hog_modified2 = np.zeros(n_orientations * 2)
        bin_width3 = 90 / (n_orientations * 2)

        for i in range(orientations.shape[0]):
            for j in range(orientations.shape[1]):
                orientation = orientations[i, j]
                magnitude = magnitudes[i,j]

                if orientation > 90:
                    orientation = 180 - orientation
                if orientation == 90:
                    orientation = 0
                
                lower_bin_idx3 = int(orientation / bin_width3)
                if 0 < lower_bin_idx3 < 17:
                    hog_modified2[lower_bin_idx3] += magnitude * 0.5
                    hog_modified2[lower_bin_idx3 - 1] += magnitude * 0.25
                    hog_modified2[lower_bin_idx3 + 1] += magnitude * 0.25
                elif lower_bin_idx3 == 0:
                    hog_modified2[lower_bin_idx3] += magnitude * 0.25
                    hog_modified2[lower_bin_idx3 + 1] += magnitude * 0.25
                else: # 17
                    hog_modified2[lower_bin_idx3] += magnitude * 0.5
                    hog_modified2[lower_bin_idx3 - 1] += magnitude * 0.5
        return hog_modified2

    def compute_hog_features(self, image, n_orientations, pixels_per_cell, cells_per_block):
        gx, gy = self.compute_gradient(image)
        sy, sx = gx.shape
        cx, cy = pixels_per_cell

        magnitudes = np.hypot(gx, gy)
        orientations = np.rad2deg(np.arctan2(gy, gx)) % 180

        n_cellsx = int(sx / cx)
        n_cellsy = int(sy / cy)
        modified_hog2 = []

        for it_y in range(n_cellsy):
            for it_x in range(n_cellsx):
                magnitudes_patch = magnitudes[it_y * cy : (it_y + 1) * cy, it_x * cx : (it_x + 1) * cx]
                orientations_patch = orientations[it_y * cy : (it_y + 1) * cy, it_x * cx : (it_x + 1) * cx]
                temp_modified2 = self.compute_hog_cell(n_orientations, magnitudes_patch, orientations_patch)
                modified_hog2.append(temp_modified2.tolist())
        
        modified_hog2 = np.array(modified_hog2)
        column_sums3 = modified_hog2.sum(axis=0)
        maxindex = np.argmax(column_sums3)
        maxangle = maxindex * (90 / (n_orientations * 2))
        return maxangle

    def calcDeficiency(self):

        if self.columnIndex.size > 0:
            m, c, m2, c2 = self.calcColumnWidth()
            if m is None: return

            if self.cid != -1:
                cur = self.rois[self.cid][0] - 300
                f1 = m * cur + c
                f2 = m2 * cur + c2
                if abs(f1-f2) > 0:
                    ratio = (self.max_dist / abs(f1 - f2)) * 100
                    self.spalled_ratio = ratio
                    print("Spalled Ratio:", ratio )


        if len(self.connection) >= 2 or len(self.horizontalIndex) >= 3:
            self.title = "Level 5"
            return
        if len(self.connection) >= 1 or len(self.horizontalIndex) >= 1:
            self.title = "Level 4"
            return

        if self.columnIndex.size > 0:
            m, c, m2, c2 = self.calcColumnWidth()
            if m is None: return

            if self.cid != -1:
                cur = self.rois[self.cid][0] - 300
                f1 = m * cur + c
                f2 = m2 * cur + c2
                if abs(f1-f2) > 0:
                    ratio = (self.max_dist / abs(f1 - f2)) * 100
                    self.spalled_ratio = ratio
                    if ratio >= 50:
                        self.title = "Level 4"
                    elif 10 <= ratio <= 30:
                        self.title = "Level 3"

    def calcColumnWidth(self):
        if self.columnIndex.size == 0:
            return None, None, None, None
        columnMaskSample = self.masks[:, :, self.columnIndex[0]]
        topY, bottomY = self.rois[self.columnIndex[0]][0] + 50, self.rois[self.columnIndex[0]][2] - 50
        leftmostx, leftmosty = [], []
        rightmostx, rightmosty = [], []

        for y in range(topY, bottomY + 1):
            if y >= self.masks.shape[0]: continue
            xsample = self.masks[y, :, self.columnIndex[0]]
            (x,) = np.where(xsample == 1)
            if x.size > 0:
                leftmosty.append(y)
                rightmosty.append(y)
                leftmostx.append(x[0])
                rightmostx.append(x[-1])
        if not rightmostx or not leftmostx:
            return None, None, None, None

        X = np.array(rightmostx).reshape(-1, 1)
        y = np.array(rightmosty).reshape(-1, 1)
        ransac = RANSACRegressor(min_samples=2, max_trials=3000, random_state=42, residual_threshold=15)
        ransac.fit(y, X)
        if not hasattr(ransac, 'estimator_'): return None,None,None,None
        m, c = float(ransac.estimator_.coef_), float(ransac.estimator_.intercept_)

        X2 = np.array(leftmostx).reshape(-1, 1)
        y2 = np.array(leftmosty).reshape(-1, 1)
        ransac2 = RANSACRegressor(min_samples=2, max_trials=3000, random_state=42, residual_threshold=15)
        ransac2.fit(y2, X2)
        if not hasattr(ransac2, 'estimator_'): return None,None,None,None
        m2, c2 = float(ransac2.estimator_.coef_), float(ransac2.estimator_.intercept_)
        return m, c, m2, c2
