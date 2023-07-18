import cv2
import numpy as np


def preprocess(image_path, image_size=640):
    image = cv2.imread(image_path)
    image, ratio, dwdh = _letterbox_image(image, image_size, auto=False)
    image = image.transpose((2, 0, 1))  # HWC->CHW for PyTorch model
    image = np.expand_dims(image, 0)  # Model expects an array of images
    image = np.ascontiguousarray(image)
    # Speed up things by rewriting the array contiguously in memory

    im = image.astype(np.float32)  # Model expects float32 data type
    im /= 255  # Convert RGB values [0-255] to [0-1]
    return im, ratio, dwdh


def _letterbox_image(
        im, image_size, color=(114, 114, 114), auto=True, scaleup=True, stride=32):

    # Resize and pad image while meeting stride-multiple constraints
    shape = im.shape[:2]  # current shape [height, width]
    new_shape = image_size
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup:  # only scale down, do not scale up (for better val mAP)
        r = min(r, 1.0)

    # Compute padding
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding

    if auto:  # minimum rectangle
        dw, dh = np.mod(dw, stride), np.mod(dh, stride)  # wh padding

    dw /= 2  # divide padding into 2 sides
    dh /= 2

    if shape[::-1] != new_unpad:  # resize
        im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(
        im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color
    )  # add border

    return im, r, (dw, dh)
