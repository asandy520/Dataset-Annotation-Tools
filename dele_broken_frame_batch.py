import torch
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
from torchvision import transforms
from torchmetrics.image import StructuralSimilarityIndexMeasure
from PIL import Image

import os, glob

class MyDataset(Dataset):
    def __init__(self, data_paths):
        self.data_paths = data_paths
        self.totensor = transforms.ToTensor()
        
    def __len__(self):
        self.length = len(self.data_paths)
        return self.length
    
    def __getitem__(self, index):
        img1 = Image.open(self.data_paths[index])
        try:
            img2 = Image.open(self.data_paths[index+1])
        except:
            img2 = Image.open(self.data_paths[index])
        img1 = self.totensor(img1)
        img2 = self.totensor(img2)
        return img1, img2
    
def delete(folder):
    print(folder)
    img_paths = glob.glob(os.path.join(folder, '*.jpg'))
    img_ids = [int(os.path.basename(path).split('.')[0]) for path in img_paths]
    img_ids = sorted(img_ids)
    img_paths = [os.path.join(folder, str(img_id) + '.jpg') for img_id in img_ids]

    print(img_paths[0])
    dataset = MyDataset(img_paths)
    dataloader = DataLoader(dataset, batch_size=10, shuffle=False)
    for img1, img2 in dataloader:
        print(img1.shape, img2.shape)
        break
    
def main(env_path):
    folders = glob.glob(os.path.join(env_path, '*', '*', '*', 'front_RGB'))

    for folder in folders:
        delete(folder)
        break
if __name__ == '__main__':
    env_path = '/docker_disk/dataset/Env2'
    paths = main(env_path)