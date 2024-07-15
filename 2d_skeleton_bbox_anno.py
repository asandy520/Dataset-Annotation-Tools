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
selected_box = None
selected_box_corner = None
keypoints = []
boxes = []
current_image_index = 0
images_list = []
folder_path = ''
json_file_path = ''
LOW_CONFIDENCE_THRESHOLD = 0.5  # Adjust this value as needed

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

def draw_boxes(image, all_boxes):
    for box in all_boxes:
        x, y, w, h = map(int, box)
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Green color for the box
    return image

def highlight_keypoint_line(image, keypoints, pair, color):
    pt1 = (int(keypoints[pair[0] * 3]), int(keypoints[pair[0] * 3 + 1]))
    pt2 = (int(keypoints[pair[1] * 3]), int(keypoints[pair[1] * 3 + 1]))
    if keypoints[pair[0] * 3 + 2] > 0.5 and keypoints[pair[1] * 3 + 2] > 0.5:
        cv2.line(image, pt1, pt2, color, 2)
        
def jump_to_next_flagged():
    global current_image_index, images_list, flagged_images
    for i in range(current_image_index + 1, len(images_list)):
        if images_list[i] in flagged_images:
            current_image_index = i
            return True
    return False

def jump_to_prev_flagged():
    global current_image_index, images_list, flagged_images
    for i in range(current_image_index - 1, -1, -1):
        if images_list[i] in flagged_images:
            current_image_index = i
            return True
    return False

def mouse_callback(event, x, y, flags, param):
    global selected_keypoint, selected_person, selected_box, selected_box_corner, keypoints, boxes
    if event == cv2.EVENT_LBUTTONDOWN:
        # Check if a keypoint is selected
        selected_keypoint = None
        selected_person = None
        for person_idx, person_keypoints in enumerate(keypoints):
            for i in range(0, len(person_keypoints), 3):
                kx, ky = person_keypoints[i], person_keypoints[i + 1]
                if (kx - x) ** 2 + (ky - y) ** 2 < 100:
                    selected_keypoint = i
                    selected_person = person_idx
                    return
        
        # Check if a box is selected
        selected_box = None
        selected_box_corner = None
        for box_idx, box in enumerate(boxes):
            bx, by, bw, bh = box
            if bx < x < bx + bw and by < y < by + bh:
                selected_box = box_idx
                if x - bx < 10 and y - by < 10:
                    selected_box_corner = "tl"  # top-left corner
                elif x - bx < 10 and by + bh - y < 10:
                    selected_box_corner = "bl"  # bottom-left corner
                elif bx + bw - x < 10 and y - by < 10:
                    selected_box_corner = "tr"  # top-right corner
                elif bx + bw - x < 10 and by + bh - y < 10:
                    selected_box_corner = "br"  # bottom-right corner
                else:
                    selected_box_corner = None  # inside box, move it
                return

    elif event == cv2.EVENT_MOUSEMOVE:
        if selected_keypoint is not None and selected_person is not None:
            keypoints[selected_person][selected_keypoint] = x
            keypoints[selected_person][selected_keypoint + 1] = y
            save_annotations()
        elif selected_box is not None:
            bx, by, bw, bh = boxes[selected_box]
            if selected_box_corner == "tl":
                boxes[selected_box] = [x, y, bx + bw - x, by + bh - y]
            elif selected_box_corner == "bl":
                boxes[selected_box] = [x, by, bx + bw - x, y - by]
            elif selected_box_corner == "tr":
                boxes[selected_box] = [bx, y, x - bx, by + bh - y]
            elif selected_box_corner == "br":
                boxes[selected_box] = [bx, by, x - bx, y - by]
            else:
                boxes[selected_box] = [x - bw // 2, y - bh // 2, bw, bh]
            save_annotations()

    elif event == cv2.EVENT_LBUTTONUP:
        selected_keypoint = None
        selected_person = None
        selected_box = None
        selected_box_corner = None
        save_annotations()

def save_annotations():
    global keypoints, boxes, json_file_path, current_image_index, images_list
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        image_name = images_list[current_image_index]
        
        # Remove existing entries for this image
        data = [entry for entry in data if entry['image_id'] != image_name]
        
        # Add new entries for each person/object in the image
        for i in range(len(keypoints)):
            new_entry = {
                'image_id': image_name,
                'keypoints': keypoints[i],
                'box': boxes[i]
            }
            data.append(new_entry)

        with open(json_file_path, 'w') as file:
            json.dump(data, file, indent=4)
        print(f"Annotations saved for {image_name}")
    except Exception as e:
        print(f"Error saving annotations: {str(e)}")

def main():
    global folder_path, keypoints, boxes, json_file_path, current_image_index, images_list, flagged_images
    folder_path = select_folder()
    json_file_path = os.path.join(folder_path, 'alphapose-results.json')

    with open(json_file_path, 'r') as file:
        data = json.load(file)

    img_dict = {}
    flagged_images = set()
    for entry in data:
        image_name = entry['image_id']
        if image_name not in img_dict:
            img_dict[image_name] = {'keypoints': [], 'boxes': []}
        img_dict[image_name]['keypoints'].append(entry['keypoints'])
        img_dict[image_name]['boxes'].append(entry['box'])
        
        # Check for low confidence keypoints
        for keypoint in entry['keypoints'][2::3]:  # Check every third element (confidence scores)
            if keypoint < LOW_CONFIDENCE_THRESHOLD:
                flagged_images.add(image_name)
                break

    images_list = sorted(img_dict.keys())
    print(f"Found {len(flagged_images)} images with low confidence keypoints.")

    while current_image_index < len(images_list):
        image_name = images_list[current_image_index]
        img_path = os.path.join(folder_path, image_name)
        img = cv2.imread(img_path)

        keypoints = img_dict[image_name]['keypoints']
        boxes = img_dict[image_name]['boxes']

        cv2.namedWindow('Keypoints')
        cv2.setMouseCallback('Keypoints', mouse_callback)

        while True:
            img_copy = img.copy()
            img_copy = draw_keypoints(img_copy, keypoints)
            img_copy = draw_boxes(img_copy, boxes)

            if image_name in flagged_images:
                cv2.putText(img_copy, "LOW CONFIDENCE", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            if selected_person is not None and selected_keypoint is not None:
                for pair in l_pair:
                    if selected_keypoint // 3 in pair:
                        highlight_keypoint_line(img_copy, keypoints[selected_person], pair, highlight_color)
            else:
                img_copy = draw_keypoints(img_copy, keypoints)

            cv2.imshow('Keypoints', img_copy)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):  # 'q' to quit
                print("Quitting the program.")
                cv2.destroyAllWindows()
                return
            elif key == 27:  # ESC to exit
                print("Exiting the program.")
                cv2.destroyAllWindows()
                return
            elif key == ord('n'):  # 'n' for next image
                current_image_index += 1
                break
            elif key == ord('p'):  # 'p' for previous image
                current_image_index = max(0, current_image_index - 1)
                break
            elif key == ord('j'):  # 'j' to jump to next low confidence image
                if jump_to_next_flagged():
                    break
                else:
                    print("No more low confidence images ahead")
            elif key == ord('k'):  # 'k' to jump to previous low confidence image
                if jump_to_prev_flagged():
                    break
                else:
                    print("No more low confidence images before")

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
