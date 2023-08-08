import random

import cv2
from matplotlib import pyplot as plt
import numpy as np


def draw_boxes(image_path, model_output, scaling, padding, class_labels):
    image = cv2.imread(image_path)  # Read image
    colors = {
        name: [
            random.randint(0, 255) for _ in range(3)
        ] for i, name in enumerate(class_labels)
    }
    for i, (x0, y0, x1, y1, score, cls_id) in enumerate(model_output):
        box = np.array([x0, y0, x1, y1])
        box -= np.array(padding*2)
        box /= scaling
        box = box.round().astype(np.int32).tolist()
        cls_id = int(cls_id)
        score = round(float(score), 3)
        name = class_labels[cls_id]
        color = colors[name]
        name += ' '+str(score)
        cv2.rectangle(image, box[:2], box[2:], color,2)
        cv2.putText(
            image,
            name,
            (box[0], box[1] - 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            [0, 255, 0],
            thickness=2
        )
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    fig = plt.gcf()
    fig.set_size_inches(24, 12)
    plt.axis('off')
    plt.imshow(img)
