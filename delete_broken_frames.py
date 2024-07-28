import os
import glob
import logging
from PIL import Image
import numpy as np
from tqdm import trange, tqdm
from skimage.metrics import structural_similarity as ssim

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_ssim(img1, img2):
    return ssim(img1, img2, multichannel=True)

def move_file_to_trash(folder, img_path):
    trash_folder = os.path.join(folder, 'trash')
    os.makedirs(trash_folder, exist_ok=True)
    try:
        os.rename(img_path, os.path.join(trash_folder, os.path.basename(img_path)))
        logging.info(f"Moved file to trash: {img_path}")
    except Exception as e:
        logging.error(f"Error moving file {img_path} to trash: {e}")

def is_image_corrupt(image_path):
    try:
        with Image.open(image_path) as img:
            img.load()
        return False
    except (IOError, SyntaxError, Image.DecompressionBombError) as e:
        logging.info(f"Corrupt image detected: {image_path} - {e}")
        return True

def delete_corrupt_images(folder):
    image_paths = get_sorted_image_paths(folder)
    
    if not image_paths:
        logging.warning(f"No images found in folder: {folder}")
        return
    
    process_images(image_paths)

def get_sorted_image_paths(folder):
    img_paths = glob.glob(os.path.join(folder, '*.jpg'))
    img_paths.sort(key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
    return img_paths

def open_image(image_path):
    with Image.open(image_path) as img:
        return np.array(img)

def delete_image(image_path):
    try:
        os.remove(image_path)
        logging.info(f"Deleted corrupt image: {image_path}")
    except Exception as e:
        logging.error(f"Error deleting image {image_path}: {e}")
    
def process_images(image_paths):
    if is_image_corrupt(image_paths[0]):
        delete_image(image_paths[0])
        return

    img1 = open_image(image_paths[0])

    for i in trange(1, len(image_paths)):
        if is_image_corrupt(image_paths[i]):
            delete_image(image_paths[i])
            continue

        img2 = open_image(image_paths[i])
        compare_and_process_images(img1, img2, image_paths, i)
        img1 = img2

def compare_and_process_images(img1, img2, image_paths, index):
    ssim_value = calculate_ssim(img1, img2)
    logging.info(f"SSIM between {image_paths[index - 1]} and {image_paths[index]}: {ssim_value}")

    if ssim_value < 0.9:
        move_file_to_trash(os.path.dirname(image_paths[index]), image_paths[index])
        logging.info(f"Low SSIM detected. Moved to trash: {image_paths[index]}")

def main(env_path):
    folders = glob.glob(os.path.join(env_path, '*', '*', '*', 'front_RGB'))
    for folder in folders:
        delete_corrupt_images(folder)

def check_done(folder):
    folders = glob.glob(os.path.join(env_path, '*', '*', '*', 'front_RGB'))
    not_done = []
    for folder in tqdm(folders):
        trash_folder = os.path.join(folder, 'trash')
        if os.path.exists(trash_folder):
            continue
        not_done.append(folder)
    return not_done

def main(env_path):
    folders = glob.glob(os.path.join(env_path, '*', '*', '*', 'front_RGB'))
    for folder in folders:
        delete_corrupt_images(folder)

def one_folder(folder):
    delete_corrupt_images(folder)

if __name__ == '__main__':
    env_path = '/docker_disk/dataset/Env0'
    # main(env_path)
    not_done = check_done(env_path)
    for n in not_done:
        one_folder(n)