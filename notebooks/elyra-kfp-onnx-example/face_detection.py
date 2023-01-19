import numpy as np
from requests import post


def detect_faces(image, prediction_url, token):
    payload = _serialize(image)
    model_response = _get_model_response(payload, prediction_url, token)
    confidences, boxes = _extract_faces(model_response)
    return confidences, boxes


def _serialize(image):
    payload = {
        'inputs': [
            {
                'name': 'input',
                'shape': [1, 3, 480, 640],
                'datatype': 'FP32',
                'data': image.tolist(),
            }
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
    return model_output


def _extract_faces(model_response):
    model_outputs = model_response
    for output in model_outputs:
        if output['name'] == 'scores':
            scores = np.array(output['data'])
        elif output['name'] == 'boxes':
            boxes = np.array(output['data'])

    scores = scores.reshape(1, int(len(scores)/2), 2)
    boxes = boxes.reshape(1, int(len(boxes)/4), 4)
    return scores, boxes
