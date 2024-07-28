import os
import cv2
import json
from tqdm import tqdm

def load_annotations(json_path):
    with open(json_path, 'r') as file:
        annotations = json.load(file)
    return annotations

def save_annotations(json_path, annotations):
    with open(json_path, 'w') as file:
        json.dump(annotations, file, indent=4)

def remove_corrupt_images(json_path, image_dir):
    annotations = load_annotations(json_path)
    valid_annotations = []
    deleted_count = 0

    for annotation in tqdm(annotations, desc="Processing images", unit="image"):
        image_path = os.path.join(image_dir, annotation['image_id'])
        image = cv2.imread(image_path)
        
        if image is None:
            print(f"Image {annotation['image_id']} is corrupt or missing. Removing from annotations.")
            deleted_count += 1
        else:
            valid_annotations.append(annotation)

    save_annotations(json_path, valid_annotations)
    print(f"Deleted {deleted_count} annotations with corrupt or missing images from {json_path}.")

def process_all_directories(base_dir):
    directories = [os.path.join(root, 'front_RGB') for root, dirs, files in os.walk(base_dir) if 'front_RGB' in dirs]

    for image_dir in tqdm(directories, desc="Processing directories", unit="directory"):
        json_path = os.path.join(os.path.dirname(image_dir), 'alphapose-results.json')

        if os.path.isfile(json_path):
            print(f"Processing JSON file: {json_path}")
            remove_corrupt_images(json_path, image_dir)

# Base directory containing all your folders
base_dir = '/docker_disk/dataset/Env0/F2M2F3/5_posi/240506_224934'

# Run the function
process_all_directories(base_dir)
