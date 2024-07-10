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

highlight_color = (0, 0, 255)  # Red color for highlighting the latest line

# Global variables
selected_keypoint = None
selected_person = None
keypoints = []
add_mode = False
current_image_index = 0
images_list = []

def select_folder():
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory()
    return folder_path

def draw_keypoints(image, all_keypoints):
    for keypoints in all_keypoints:
        for pair, color in zip(l_pair, line_color):
            pt1 = (int(keypoints[pair[0] * 3]), int(keypoints[pair[0] * 3 + 1]))
            pt2 = (int(keypoints[pair[1] * 3]), int(keypoints[pair[1] * 3 + 1]))
#            if keypoints[pair[0] * 3 + 2] > 0.5 and keypoints[pair[1] * 3 + 2] > 0.5:
            cv2.line(image, pt1, pt2, color, 2)
        
        for i in range(0, len(keypoints), 3):
            x, y, confidence = keypoints[i], keypoints[i + 1], keypoints[i + 2]
            if confidence < 0.5:  # only draw keypoints with a high confidence
                cv2.circle(image, (int(x), int(y)), 5, p_color[i // 3], -1)
    return image

def highlight_keypoint_line(image, keypoints, pair, color):
    pt1 = (int(keypoints[pair[0] * 3]), int(keypoints[pair[0] * 3 + 1]))
    pt2 = (int(keypoints[pair[1] * 3]), int(keypoints[pair[1] * 3 + 1]))
    if keypoints[pair[0] * 3 + 2] > 0.5 and keypoints[pair[1] * 3 + 2] > 0.5:
        cv2.line(image, pt1, pt2, color, 2)

def mouse_callback(event, x, y, flags, param):
    global selected_keypoint, selected_person, add_mode, keypoints
    if event == cv2.EVENT_LBUTTONDOWN:
        if add_mode:
            if len(keypoints[selected_person]) < 78:
                keypoints[selected_person].extend([x, y, 1])
            add_mode = False
        else:
            for person_idx, person_keypoints in enumerate(keypoints):
                for i in range(0, len(person_keypoints), 3):
                    kx, ky = person_keypoints[i], person_keypoints[i + 1]
                    if (kx - x) ** 2 + (ky - y) ** 2 < 100:
                        selected_keypoint = i
                        selected_person = person_idx
                        break
    elif event == cv2.EVENT_MOUSEMOVE:
        if selected_keypoint is not None:
            keypoints[selected_person][selected_keypoint] = x
            keypoints[selected_person][selected_keypoint + 1] = y
    elif event == cv2.EVENT_LBUTTONUP:
        selected_keypoint = None

def main():
    global keypoints, add_mode, current_image_index, images_list
    folder_path = select_folder()
    json_file_path = os.path.join(folder_path, 'alphapose-results.json')
    
    with open(json_file_path) as f:
        data = json.load(f)
    
    img_dict = {}
    for entry in data:
        img_id = entry['image_id']
        person_keypoints = entry['keypoints']
        
        # Ensure keypoints list is of length 78 (26 keypoints * 3 values each)
        if len(person_keypoints) < 78:
            person_keypoints.extend([0, 0, 0] * (26 - len(person_keypoints) // 3))
        
        if img_id not in img_dict:
            img_dict[img_id] = []
        img_dict[img_id].append(person_keypoints)
    
    images_list = list(img_dict.keys())
    
    while current_image_index < len(images_list):
        img_id = images_list[current_image_index]
        keypoints = img_dict[img_id]
        img_path = os.path.join(folder_path, img_id)
        if os.path.exists(img_path):
            image = cv2.imread(img_path)
            
            cv2.namedWindow('Keypoints')
            cv2.setMouseCallback('Keypoints', mouse_callback)
            
            while True:
                img_copy = image.copy()
                for i, person_keypoints in enumerate(keypoints):
                    if i == selected_person and selected_keypoint is not None:
                        temp_keypoints = person_keypoints.copy()
                        temp_keypoints[selected_keypoint] = -1
                        temp_keypoints[selected_keypoint + 1] = -1
                        img_copy = draw_keypoints(img_copy, [temp_keypoints])
                        pair_indices = [j for j, pair in enumerate(l_pair) if pair[0] == selected_keypoint // 3 or pair[1] == selected_keypoint // 3]
                        for index in pair_indices:
                            highlight_keypoint_line(img_copy, temp_keypoints, l_pair[index], highlight_color)
                    else:
                        img_copy = draw_keypoints(img_copy, [person_keypoints])
                
                cv2.imshow('Keypoints', img_copy)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    cv2.destroyAllWindows()
                    return
                elif key == ord('a'):
                    add_mode = True
                elif key == ord('n'):  # Move to the next image
                    current_image_index += 1
                    break
                elif key == ord('p'):  # Move to the previous image
                    if current_image_index > 0:
                        current_image_index -= 1
                        break
            cv2.destroyAllWindows()
        else:
            print(f"Image {img_id} not found in the folder")
    
    with open(json_file_path, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    main()
