import random

from PIL import Image, ImageDraw, ImageFont
from matplotlib import pyplot as plt
import numpy as np


def draw_boxes(image_path, model_output, scaling, padding, class_labels):
    image = Image.open(image_path).convert("RGB")  # Read image and convert to RGB
    draw = ImageDraw.Draw(image)

    # Load a default font
    try:
        font = ImageFont.truetype("arial.ttf", size=16)
    except IOError:
        font = ImageFont.load_default()

    colors = {
        name: tuple(
            random.randint(0, 255) for _ in range(3)
        ) for i, name in enumerate(class_labels)
    }

    for i, (x0, y0, x1, y1, score, cls_id) in enumerate(model_output):
        box = np.array([x0, y0, x1, y1])
        box -= np.array(padding * 2)
        box /= scaling
        box = box.round().astype(np.int32).tolist()
        cls_id = int(cls_id)
        score = round(float(score), 3)
        name = class_labels[cls_id]
        color = colors[name]
        name += ' ' + str(score)

        draw.rectangle(box, outline=color, width=2)
        draw.text(
            (box[0], box[1] - 15),
            name,
            fill=(0, 255, 0),
            font=font
        )

    # Convert image to an array for display with Matplotlib
    img = np.array(image)

    fig = plt.gcf()
    fig.set_size_inches(24, 12)
    plt.axis('off')
    plt.imshow(img)
