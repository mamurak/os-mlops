from base64 import b64decode
from glob import glob
from io import BytesIO
from os import path
from pickle import dump

from PIL import Image, ImageOps
import numpy as np


def preprocess_image_file(image_path):
    image = Image.open(image_path)
    return _transform(image)


def preprocess_encoded_image(base64encoded_image):
    img_bytes = b64decode(base64encoded_image)
    image = Image.open(BytesIO(img_bytes))
    return _transform(image)


def preprocess_image_folder(data_folder='./data'):
    print('Commencing data preprocessing.')

    image_names, image_file_paths = _scan_images_folder(data_folder)

    image_data = [
        preprocess_image_file(image_path)[0] for image_path in image_file_paths
    ]
    with open(f'{data_folder}/images.pickle', 'wb') as outputfile:
        dump([image_names, image_data], outputfile)

    print('Data preprocessing done.')


def _scan_images_folder(images_folder):
    print(f'Scanning images folder {images_folder}.')

    image_file_paths = glob(path.join(images_folder, "*.jpg"))
    image_names = [
        file_path.split('/')[-1].rstrip('.jpg')
        for file_path in image_file_paths
    ]
    print(f'Found image files: {image_file_paths}.')
    print(f'Image names: {image_names}.')
    return image_names, image_file_paths


def _transform(image, image_size=640):
    image, ratio, dwdh = _letterbox_image(image, image_size, auto=False)
    image = np.array(image).transpose((2, 0, 1))  # HWC->CHW for PyTorch model
    image = np.expand_dims(image, 0)  # Model expects an array of images
    image = np.ascontiguousarray(image)
    # Speed up things by rewriting the array contiguously in memory

    im = image.astype(np.float32)  # Model expects float32 data type
    im /= 255  # Convert RGB values [0-255] to [0-1]
    return im, ratio, dwdh


def _letterbox_image(
        im, image_size, color=(114, 114, 114), auto=True, scaleup=True, stride=32):

    # Ensure the image is in RGB mode
    if im.mode != 'RGB':
        im = im.convert('RGB')

    # Resize and pad image while meeting stride-multiple constraints
    shape = im.size  # current shape [width, height]
    new_shape = image_size
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[1], new_shape[1] / shape[0])
    if not scaleup:  # only scale down, do not scale up (for better val mAP)
        r = min(r, 1.0)

    # Compute padding
    new_unpad = int(round(shape[0] * r)), int(round(shape[1] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding

    if auto:  # minimum rectangle
        dw, dh = np.mod(dw, stride), np.mod(dh, stride)  # wh padding

    dw_half, dh_half = dw / 2, dh / 2  # split padding into two sides

    if shape != new_unpad[::-1]:  # resize
        im = im.resize(new_unpad, Image.BILINEAR)

    # Adjust border calculation to ensure the final dimensions are exactly new_shape
    top, bottom = int(dh_half), int(dh_half + 0.5)
    left, right = int(dw_half), int(dw_half + 0.5)

    im = ImageOps.expand(im, border=(left, top, right, bottom), fill=color)

    return im, r, (dw, dh)


if __name__ == '__main__':
    preprocess_image_folder(data_folder='/data')
