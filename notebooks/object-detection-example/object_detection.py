import numpy as np
from requests import post

from classes import classes


def detect_objects(image, prediction_url, token):
    payload = _serialize(image)
    model_response = _get_model_response(payload, prediction_url, token)
    boxes, scores, class_indices = _postprocess(*model_response)
    return boxes, scores, class_indices


def _serialize(image):
    payload = {
        'inputs': [
            {
                'name': 'input_1',
                'shape': [1, 3, 416, 416],
                'datatype': 'FP32',
                'data': image.flatten().tolist(),
            },
            {
                'name': 'image_shape',
                'shape': [1, 2],
                'datatype': 'FP32',
                'data': [416, 416],
            },
        ]
    }
    return payload


def _get_model_response(payload, prediction_url, token):
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
    unpacked_output = [_unpack(item) for item in model_output]
    return unpacked_output


def _unpack(response_item):
    return np.array(response_item['data']).reshape(response_item['shape'])


def _postprocess(raw_boxes, raw_scores, raw_class_indices):
    boxes, scores, detected_classes = [], [], []
    for raw_indices in raw_class_indices[0]:
        detected_classes.append(classes[raw_indices[1]])
        scores.append(raw_scores[tuple(raw_indices)])
        indices = (raw_indices[0], raw_indices[2])
        boxes.append(raw_boxes[indices])

    return boxes, scores, detected_classes
