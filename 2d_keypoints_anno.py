import os
import json
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog

# Constants for keypoint visualization
l_pair = [
    (0, 1), (0, 2), (1, 3), (2, 4),  # Head
    (5, 18), (6, 18), (5, 7), (7, 9), (6, 8), (8, 10),  # Body
    (17, 18), (18, 19), (19, 11), (19, 12),
    (11, 13), (12, 14), (13, 15), (14, 16),
    (20, 24), (21, 25), (23, 25), (22, 24), (15, 24), (16, 25),  # Foot
]
p_color = [(0, 255, 255), (0, 191, 255), (0, 255, 102), (0, 77, 255), (0, 255, 0),  # Nose, LEye, REye, LEar, REar
           (77, 255, 255), (77, 255, 204), (77, 204, 255), (191, 255, 77), (77, 191, 255), (191, 255, 77),  # LShoulder, RShoulder, LElbow, RElbow, LWrist, RWrist
           (204, 77, 255), (77, 255, 204), (191, 77, 255), (77, 255, 191), (127, 77, 255), (77, 255, 127),  # LHip, RHip, LKnee, Rknee, LAnkle, RAnkle, Neck
           (77, 255, 255), (0, 255, 255), (77, 204, 255),  # head, neck, shoulder
           (0, 255, 255), (0, 191, 255), (0, 255, 102), (0, 77, 255), (0, 255, 0), (77, 255, 255)]  # foot

line_color = [(0, 215, 255), (0, 255, 204), (0, 134, 255), (0, 255, 50),
              (0, 255, 102), (77, 255, 222), (77, 196, 255), (77, 135, 255), (191, 255, 77), (77, 255, 77),
              (77, 191, 255), (204, 77, 255), (77, 222, 255), (255, 156, 127),
              (0, 127, 255), (255, 127, 77), (0, 77, 255), (255, 77, 36),
              (0, 77, 255), (0, 77, 255), (0, 77, 255), (0, 77, 255), (255, 156, 127), (255, 156, 127)]

# Global variables
selected_keypoint = None
selected_person_index = None
keypoints = []
add_mode = False

def select_folder():
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory()
    return folder_path

def draw_keypoints(image, keypoints_list, selected_keypoint, selected_person_index):
    for person_index, keypoints in enumerate(keypoints_list):
        for pair, color in zip(l_pair, line_color):
            pt1 = (int(keypoints[pair[0] * 3]), int(keypoints[pair[0] * 3 + 1]))
            pt2 = (int(keypoints[pair[1] * 3]), int(keypoints[pair[1] * 3 + 1]))
            if keypoints[pair[0] * 3 + 2] > 0.5 and keypoints[pair[1] * 3 + 2] > 0.5:
                cv2.line(image, pt1, pt2, color, 2)
        
        for i in range(0, len(keypoints), 3):
            if not (person_index == selected_person_index and i == selected_keypoint):
                x, y, confidence = keypoints[i], keypoints[i + 1], keypoints[i + 2]
                if confidence < 0.5:  # only draw keypoints with a high confidence
                    cv2.circle(image, (int(x), int(y)), 5, p_color[i // 3], -1)
    return image

def mouse_callback(event, x, y, flags, param):
    global selected_keypoint, selected_person_index, add_mode, keypoints
    if event == cv2.EVENT_LBUTTONDOWN:
        if add_mode:
            if len(keypoints) < 78:
                keypoints.extend([x, y, 1])
            add_mode = False
        else:
            for person_index, keypoints in enumerate(param):
                for i in range(0, len(keypoints), 3):
                    kx, ky = keypoints[i], keypoints[i + 1]
                    if (kx - x) ** 2 + (ky - y) ** 2 < 100:
                        selected_keypoint = i
                        selected_person_index = person_index
                        break
    elif event == cv2.EVENT_MOUSEMOVE:
        if selected_keypoint is not None and selected_person_index is not None:
            param[selected_person_index][selected_keypoint] = x
            param[selected_person_index][selected_keypoint + 1] = y
    elif event == cv2.EVENT_LBUTTONUP:
        selected_keypoint = None
        selected_person_index = None

def main():
    global keypoints, add_mode
    folder_path = select_folder()
    json_file_path = os.path.join(folder_path, 'alphapose-results.json')
    
    with open(json_file_path) as f:
        data = json.load(f)
    
    img_dict = {}
    for entry in data:
        img_id = entry['image_id']
        keypoints = entry['keypoints']
        
        # Ensure keypoints list is of length 78 (26 keypoints * 3 values each)
        if len(keypoints) < 78:
            keypoints.extend([0, 0, 0] * (26 - len(keypoints) // 3))
        
        if img_id not in img_dict:
            img_dict[img_id] = []
        img_dict[img_id].append(keypoints)
    
    for img_id, all_keypoints in img_dict.items():
        img_path = os.path.join(folder_path, img_id)
        if os.path.exists(img_path):
            image = cv2.imread(img_path)
            
            cv2.namedWindow('Keypoints')
            cv2.setMouseCallback('Keypoints', mouse_callback, param=all_keypoints)
            
            while True:
                img_copy = image.copy()
                img_copy = draw_keypoints(img_copy, all_keypoints, selected_keypoint, selected_person_index)
                cv2.imshow('Keypoints', img_copy)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('a'):
                    add_mode = True
            
            cv2.destroyAllWindows()
        else:
            print(f"Image {img_id} not found in the folder")
    
    with open(json_file_path, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    main()
