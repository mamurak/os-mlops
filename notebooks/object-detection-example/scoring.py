from csv import writer
from os import environ
from pickle import load
from pprint import pformat

import numpy as np
from onnxruntime import InferenceSession
import torch
import torchvision

from classes import classes


def predict(class_labels=None, data_folder='./data'):
    print('Commencing offline scoring.')

    class_labels_type = environ.get('class_labels_type', 'coco')
    class_labels = classes[class_labels_type]
    print(f'Class labels are: {pformat(class_labels)}')

    confidence_threshold = float(environ.get('confidence_threshold', '0.2'))
    iou_threshold = float(environ.get('iou_threshold', '0.6'))

    with open(f'{data_folder}/images.pickle', 'rb') as inputfile:
        image_names, images = load(inputfile)

    session = InferenceSession(
        'model.onnx', providers=['CPUExecutionProvider']
    )

    raw_results = np.array([
        session.run([], {'images': image_data})[0]
        for image_data in images
    ])

    results = _postprocess(
        raw_results, confidence_threshold, iou_threshold, class_labels
    )
    _to_csv(results, image_names, data_folder)

    print('Offline scoring complete.')


def _postprocess(
        prediction,
        conf_thres,
        iou_thres,
        class_labels,
        max_det=300,
        nm=0,  # number of masks
):
    """Non-Maximum Suppression (NMS) on inference results to reject 
    overlapping detections

    Returns:
        list of detections, on (n,6) tensor per image [xyxy, conf, cls]
    """

    prediction = torch.Tensor(prediction)
    bs = prediction.shape[0]  # batch size
    nc = prediction.shape[2] - nm - 5  # number of classes
    xc = prediction[..., 4] > conf_thres  # candidates

    # Settings
    max_wh = 7680  # (pixels) maximum box width and height
    max_nms = 30000  # maximum number of boxes into torchvision.ops.nms()

    mi = 5 + nc  # mask start index
    output = [torch.zeros((0, 6 + nm), device=prediction.device)] * bs

    results = []

    for xi, x in enumerate(prediction):  # image index, image inference
        # Apply constraints
        # x[((x[..., 2:4] < min_wh) | (x[..., 2:4] > max_wh)).any(1), 4] = 0
        # width-height
        x = x[xc[xi]]  # confidence

        # If none remain process next image
        if not x.shape[0]:
            continue

        # Compute conf
        x[:, 5:] *= x[:, 4:5]  # conf = obj_conf * cls_conf

        # Box/Mask
        box = _xywh2xyxy(x[:, :4])
        # center_x, center_y, width, height) to (x1, y1, x2, y2)

        mask = x[:, mi:]  # zero columns if no masks

        # Detections matrix nx6 (xyxy, conf, cls)
        conf, j = x[:, 5:mi].max(1, keepdim=True)
        x = torch.cat((box, conf, j.float(), mask), 1)[
            conf.view(-1) > conf_thres
        ]

        # Check shape
        n = x.shape[0]  # number of boxes
        if not n:  # no boxes
            continue
        elif n > max_nms:  # excess boxes
            x = x[x[:, 4].argsort(descending=True)[:max_nms]]  # sort by confidence
        else:
            x = x[x[:, 4].argsort(descending=True)]  # sort by confidence

        # Batched NMS
        c = x[:, 5:6] * max_wh  # classes
        boxes = x[:, :4] + c
        scores = x[:, 4]
        # boxes (offset by class), scores

        i = torchvision.ops.nms(boxes, scores, iou_thres)  # NMS
        if i.shape[0] > max_det:  # limit detections
            i = i[:max_det]

        output[xi] = x[i]

        final_boxes = np.array(output[xi][..., :4])
        final_boxes = final_boxes.round().astype(np.int32).tolist()
        cls_id = np.array(output[xi][..., 5], dtype=int)
        scores = np.array(output[xi][..., 4])
        names = [class_labels[id_] for id_ in cls_id]

        results.append([final_boxes, scores, names])

    return results


def _xywh2xyxy(x):
    # Convert nx4 boxes from [x, y, w, h] to [x1, y1, x2, y2]
    # where xy1=top-left, xy2=bottom-right

    y = torch.zeros_like(x) if isinstance(x, torch.Tensor) else np.zeros_like(x)
    y[:, 0] = x[:, 0] - x[:, 2] / 2  # top left x
    y[:, 1] = x[:, 1] - x[:, 3] / 2  # top left y
    y[:, 2] = x[:, 0] + x[:, 2] / 2  # bottom right x
    y[:, 3] = x[:, 1] + x[:, 3] / 2  # bottom right y
    return y


def _box_iou(box1, box2, eps=1e-7):
    # https://github.com/pytorch/vision/blob/master/torchvision/ops/boxes.py
    """
    Return intersection-over-union (Jaccard index) of boxes.
    Both sets of boxes are expected to be in (x1, y1, x2, y2) format.
    Arguments:
        box1 (Tensor[N, 4])
        box2 (Tensor[M, 4])
    Returns:
        iou (Tensor[N, M]): the NxM matrix containing the pairwise
            IoU values for every element in boxes1 and boxes2
    """

    # inter(N,M) = (rb(N,M,2) - lt(N,M,2)).clamp(0).prod(2)
    (a1, a2), (b1, b2) = box1.unsqueeze(1).chunk(2, 2), box2.unsqueeze(0).chunk(
        2, 2
    )
    inter = (torch.min(a2, b2) - torch.max(a1, b1)).clamp(0).prod(2)

    # IoU = inter / (area1 + area2 - inter)
    return inter / ((a2 - a1).prod(2) + (b2 - b1).prod(2) - inter + eps)


def _to_csv(results, image_names, data_folder):
    column_names = ['file id', 'object', 'score', 'bounding box']

    with open(f'{data_folder}/results.csv', 'w', newline='') as outputfile:
        csv_writer = writer(outputfile, delimiter='\t')
        csv_writer.writerow(column_names)
        for result_index, result in enumerate(results):
            image_name = image_names[result_index]
            bounding_boxes, scores, object_names = result
            for object_index, object_name in enumerate(object_names):
                box_string = str(bounding_boxes[object_index])
                csv_writer.writerow(
                    [image_name, object_name, scores[object_index], box_string]
                )


if __name__ == '__main__':
    predict(data_folder='/data')
