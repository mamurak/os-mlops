from glob import glob
from math import floor
from os import makedirs, path
from shutil import copy

from numpy import array, random


def preprocess_data(data_folder='./data'):
    print('preprocessing data')

    for folder in ['images', 'labels']:
        for split in ['train', 'val', 'test']:
            local_folder = f'{data_folder}/{folder}/{split}'
            if not path.exists(local_folder):
                makedirs(local_folder)

    download_folder = f'{data_folder}/download'
    bicycle_images = _get_filenames(f'{download_folder}/bicycle/images')
    car_images = _get_filenames(f'{download_folder}/car/images')
    traffic_sign_images = _get_filenames(
        f'{download_folder}/traffic sign/images'
    )

    duplicates1 = bicycle_images & car_images
    duplicates2 = car_images & traffic_sign_images
    duplicates3 = traffic_sign_images & bicycle_images
    duplicate_sum = len(duplicates1) + len(duplicates2) + len(duplicates3)
    print(f'Found {duplicate_sum} duplicates')

    bicycle_images -= duplicates1
    car_images -= duplicates2
    traffic_sign_images -= duplicates3
    print(
        f'Deduplicated data set contains '
        f'{len(bicycle_images)} bicycle images, '
        f'{len(car_images)} car images, and '
        f'{len(traffic_sign_images)} traffic sign images.'
    )

    bicycle_images = array(list(bicycle_images))
    car_images = array(list(car_images))
    traffic_sign_images = array(list(traffic_sign_images))

    # Use the same random seed for reproducability
    random.seed(42)
    random.shuffle(bicycle_images)
    random.shuffle(car_images)
    random.shuffle(traffic_sign_images)

    train_ratio = 0.75
    val_ratio = 0.125

    # Bicycle data
    bicycle_train_size = floor(train_ratio * len(bicycle_images))
    bicycle_val_size = floor(val_ratio * len(bicycle_images))
    _split_dataset(
        download_folder,
        data_folder,
        'bicycle',
        bicycle_images,
        train_size=bicycle_train_size,
        val_size=bicycle_val_size
    )

    # Car data
    car_train_size = floor(train_ratio * len(car_images))
    car_val_size = floor(val_ratio * len(car_images))
    _split_dataset(
        download_folder,
        data_folder,
        'car',
        car_images,
        train_size=car_train_size,
        val_size=car_val_size
    )

    # Traffic sign data
    traffic_sign_train_size = floor(train_ratio * len(traffic_sign_images))
    traffic_sign_val_size = floor(val_ratio * len(traffic_sign_images))
    _split_dataset(
        download_folder,
        data_folder,
        'traffic sign',
        traffic_sign_images,
        train_size=traffic_sign_train_size,
        val_size=traffic_sign_val_size
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
