from glob import glob
from math import floor
from os import makedirs, path
from shutil import copy

from numpy import random

from classes import training_classes


def preprocess_data(data_folder='./data'):
    print('preprocessing data')

    for folder in ['images', 'labels']:
        for split in ['train', 'val', 'test']:
            local_folder = f'{data_folder}/{folder}/{split}'
            if not path.exists(local_folder):
                makedirs(local_folder)

    download_folder = f'{data_folder}/download'

    folder_names = [class_name.lower() for class_name in training_classes]
    images = [
        _get_filenames(f'{download_folder}/{folder_name}/images')
        for folder_name in folder_names
    ]

    seen_images = set()
    deduplicated_images = []

    for image_list in images:
        deduplicated_image_list = []
        for image in image_list:
            if image not in seen_images:
                seen_images.add(image)
                deduplicated_image_list.append(image)
        deduplicated_images.append(deduplicated_image_list)

    random.seed(42)
    train_ratio = 0.75
    val_ratio = 0.125
    for i, image_list in enumerate(deduplicated_images):
        random.shuffle(image_list)
        train_size = floor(train_ratio * len(image_list))
        val_size = floor(val_ratio * len(image_list))
        _split_dataset(
            download_folder,
            data_folder,
            folder_names[i],
            image_list,
            train_size=train_size,
            val_size=val_size,
        )

    print('data processing done')


def _get_filenames(folder):
    filenames = set()

    for local_path in glob(path.join(folder, '*.jpg')):
        # Extract the filename
        filename = path.split(local_path)[-1]
        filenames.add(filename)

    return filenames


def _split_dataset(
        download_folder, data_folder, item, image_names, train_size, val_size):

    for i, image_name in enumerate(image_names):
        # Label filename
        label_name = image_name.replace('.jpg', '.txt')

        # Split into train, val, or test
        if i < train_size:
            split = 'train'
        elif i < train_size + val_size:
            split = 'val'
        else:
            split = 'test'

        # Source paths
        source_image_path = f'{download_folder}/{item}/images/{image_name}'
        source_label_path = f'{download_folder}/{item}/darknet/{label_name}'

        # Destination paths
        target_image_folder = f'{data_folder}/images/{split}'
        target_label_folder = f'{data_folder}/labels/{split}'

        # Copy files
        copy(source_image_path, target_image_folder)
        copy(source_label_path, target_label_folder)


if __name__ == '__main__':
    preprocess_data(data_folder='/data')
