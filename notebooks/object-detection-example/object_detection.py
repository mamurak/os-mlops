import numpy as np
from requests import post
import torch
import torchvision


def detect_objects(
        image,
        prediction_url,
        classes_count,
        token='',
        confidence_threshold=0.2,
        iou_threshold=0.6,
        ):

    payload = _serialize(image)
    model_response = _get_model_response(
        payload, prediction_url, token, classes_count
    )
    processed_output = postprocess(
        model_response, confidence_threshold, iou_threshold
    )
    return processed_output


def _serialize(image):
    payload = {
        'inputs': [
            {
                'name': 'images',
                'shape': [1, 3, 640, 640],
                'datatype': 'FP32',
                'data': image.flatten().tolist(),
            }
        ]
    }
    return payload


def _get_model_response(payload, prediction_url, token, classes_count):
    headers = {'Authorization': f'Bearer {token}'}
    raw_response = post(prediction_url, json=payload, headers=headers)
    try:
        response = raw_response.json()
    except:
        print(f'Failed to deserialize service response.\n'
              f'Status code: {raw_response.status_code}\n'
              f'Response body: {raw_response.text}')
    try:
        model_output = response['outputs']
    except:
        print(f'Failed to extract model output from service response.\n'
              f'Service response: {response}')
    unpacked_output = _unpack(model_output, classes_count)
    return unpacked_output


def _unpack(model_output, classes_count):
    arr = np.array(model_output[0]['data'])
    prediction_columns_number = 5 + classes_count
    output = arr.reshape(
        1,
        int(arr.shape[0] / prediction_columns_number),
        prediction_columns_number
    )  # Reshape the flat array prediction
    return output


def postprocess(
        prediction,
        conf_thres=0.5,
        iou_thres=0.6,
        classes=None,
        agnostic=False,
        multi_label=False,
        labels=(),
        max_det=300,
        nm=0,  # number of masks
):
    """Non-Maximum Suppression (NMS) on inference results to reject 
    overlapping detections

    Returns:
        list of detections, on (n,6) tensor per image [xyxy, conf, cls]
    """

    if isinstance(prediction, (list, tuple)):
        prediction = prediction[0]  # select only inference output

    bs = prediction.shape[0]  # batch size
    nc = prediction.shape[2] - nm - 5  # number of classes
    xc = prediction[..., 4] > conf_thres  # candidates

    max_wh = 7680  # (pixels) maximum box width and height
    max_nms = 30000  # maximum number of boxes into NMS
    multi_label &= nc > 1  # multiple labels per box (adds 0.5ms/img)
    merge = False  # use merge-NMS

    mi = 5 + nc  # mask start index
    output = [np.zeros((0, 6 + nm))] * bs
    for xi, x in enumerate(prediction):  # image index, image inference
        x = x[xc[xi]]  # confidence

        if labels and len(labels[xi]):
            lb = labels[xi]
            v = np.zeros((len(lb), nc + nm + 5))
            v[:, :4] = lb[:, 1:5]  # box
            v[:, 4] = 1.0  # conf
            v[np.arange(len(lb)), lb[:, 0].astype(int) + 5] = 1.0  # cls
            x = np.vstack((x, v))

        if not x.shape[0]:
            continue

        x[:, 5:] *= x[:, 4:5]  # conf = obj_conf * cls_conf

        box = _xywh2xyxy(x[:, :4])

        mask = x[:, mi:]  # zero columns if no masks

        if multi_label:
            i, j = np.where(x[:, 5:mi] > conf_thres)
            x = np.hstack((
                box[i], x[i, 5 + j][:, None], j[:, None].astype(float), mask[i]
            ))
        else:
            conf = np.max(x[:, 5:mi], axis=1, keepdims=True)
            j = np.argmax(x[:, 5:mi], axis=1, keepdims=True)
            x = np.hstack((box, conf, j.astype(float), mask))[conf.ravel() > conf_thres]

        if classes is not None:
            x = x[np.isin(x[:, 5], classes)]

        n = x.shape[0]
        if not n:
            continue
        elif n > max_nms:
            x = x[np.argsort(x[:, 4])[::-1][:max_nms]]
        else:
            x = x[np.argsort(x[:, 4])[::-1]]

        c = x[:, 5:6] * (0 if agnostic else max_wh)  # classes
        boxes, scores = x[:, :4] + c, x[:, 4]

        i = _nms(boxes, scores, iou_thres)  # NMS
        if len(i) > max_det:
            i = i[:max_det]

        if merge and (1 < n < 3E3):
            iou = _box_iou(boxes[i], boxes) > iou_thres  # iou matrix
            weights = iou * scores[None]  # box weights
            x[i, :4] = np.dot(weights, x[:, :4]) / weights.sum(1, keepdims=True)
            i = i[weights.sum(1) > 1]  # require redundancy

        output[xi] = x[i]

    return output[0]


def _xywh2xyxy(x):
    y = np.zeros_like(x)
    y[:, 0] = x[:, 0] - x[:, 2] / 2  # top left x
    y[:, 1] = x[:, 1] - x[:, 3] / 2  # top left y
    y[:, 2] = x[:, 0] + x[:, 2] / 2  # bottom right x
    y[:, 3] = x[:, 1] + x[:, 3] / 2  # bottom right y
    return y


def _box_iou(box1, box2, eps=1e-7):
    area1 = (box1[:, 2] - box1[:, 0]) * (box1[:, 3] - box1[:, 1])
    area2 = (box2[:, 2] - box2[:, 0]) * (box2[:, 3] - box2[:, 1])

    inter = (
        (np.minimum(box1[:, None, 2], box2[:, 2]) -
         np.maximum(box1[:, None, 0], box2[:, 0])).clip(0) *
        (np.minimum(box1[:, None, 3], box2[:, 3]) -
         np.maximum(box1[:, None, 1], box2[:, 1])).clip(0)
    )
    union = area1[:, None] + area2 - inter
    return inter / (union + eps)


def _nms(boxes, scores, iou_thres):
    """Non-Maximum Suppression (NMS) implementation using NumPy."""

    idxs = np.argsort(scores)[::-1]
    keep = []

    while len(idxs) > 0:
        i = idxs[0]
        keep.append(i)
        if len(idxs) == 1:
            break

        ious = _box_iou(boxes[i:i+1], boxes[idxs[1:]]).ravel()

        idxs = idxs[np.where(ious <= iou_thres)[0] + 1]

    return np.array(keep)
