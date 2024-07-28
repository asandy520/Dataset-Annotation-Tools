import os
import logging
from PIL import Image

# Configure logging to display PIL error messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_image_corrupt(image_path):
    """Check if an image is corrupt"""
    try:
        with Image.open(image_path) as img:
            img.load()
        return False
    except (IOError, SyntaxError, Image.DecompressionBombError) as e:
        handle_image_error(e, image_path)
        return True

def handle_image_error(error, image_path):
    """Handle image loading errors"""
    error_message = str(error)
    if "Corrupt JPEG data" in error_message or "Extraneous bytes before marker" in error_message:
        logging.info(f"Corrupt JPEG data detected: {image_path} - {error_message}")
    else:
        logging.info(f"Other image error detected: {image_path} - {error_message}")

def delete_corrupt_image(file_path):
    """Delete a corrupt image file"""
    try:
        os.remove(file_path)
        logging.info(f"Deleted corrupt image: {file_path}")
    except OSError as e:
        logging.error(f"Error deleting file {file_path}: {e}")

def process_images_in_directory(directory, target_folder="front_RGB"):
    """Process all image files in the target folder"""
    for root, _, files in os.walk(directory):
        if os.path.basename(root) == target_folder:
            for file in files:
                if is_image_file(file):
                    file_path = os.path.join(root, file)
                    if is_image_corrupt(file_path):
                        delete_corrupt_image(file_path)

def is_image_file(file_name):
    """Check if a file is an image file"""
    return file_name.lower().endswith(('.jpg', '.jpeg'))

def main(root_directory):
    """Main function to process all target folders"""
    process_images_in_directory(root_directory)

if __name__ == '__main__':
    ROOT_DIRECTORY = "/docker_disk/dataset/occu_set"
    main(ROOT_DIRECTORY)