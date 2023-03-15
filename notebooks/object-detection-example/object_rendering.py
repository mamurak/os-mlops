import numpy as np
from PIL import Image, ImageColor, ImageDraw, ImageFont


def draw_boxes(image, boxes, scores, classes):
    """Overlay labeled boxes on an image with formatted scores and label names."""
    colors = list(ImageColor.colormap.values())
    class_colors = {}
    font = ImageFont.load_default()
    image_pil = Image.open(image)

    for index, class_ in enumerate(classes):
        box = boxes[index]
        display_str = f'{class_}: {int(100 * scores[index])}%'
        if class_ not in class_colors:
            class_colors[class_] = colors[hash(class_) * 8 % len(colors)]
        color = class_colors.get(class_)
        _draw_bounding_box_on_image(
            image_pil, box[0], box[1], box[2], box[3], color, font,
            display_str_list=[display_str]
        )
    return image_pil
    image_pil.show()


def _draw_bounding_box_on_image(
        image, ymin, xmin, ymax, xmax, color, font,
        thickness=4, display_str_list=()):
    """Adds a bounding box to an image."""
    draw = ImageDraw.Draw(image)
    im_width, im_height = image.size
    width_scaling_factor = im_width / 416
    height_scaling_factor = im_height / 416
    (left, right, top, bottom) = (
        xmin * width_scaling_factor,
        xmax * width_scaling_factor,
        ymin * height_scaling_factor,
        ymax * height_scaling_factor,
    )
    draw.line([(left, top), (left, bottom), (right, bottom), (right, top),
               (left, top)], width=thickness, fill=color)

    display_str_heights = [font.getsize(ds)[1] for ds in display_str_list]
    total_display_str_height = (1 + 2 * 0.05) * sum(display_str_heights)
    if top > total_display_str_height:
        text_bottom = top
    else:
        text_bottom = top + total_display_str_height

    for display_str in display_str_list[::-1]:
        text_width, text_height = font.getsize(display_str)
        margin = np.ceil(0.05 * text_height)
        draw.rectangle([(left, text_bottom - text_height - 2 * margin),
                        (left + text_width, text_bottom)], fill=color)
        draw.text((left + margin, text_bottom - text_height - margin),
                  display_str, fill="black", font=font)
        text_bottom -= text_height - 2 * margin
