from csv import writer
from pickle import load

import numpy as np
from onnxruntime import InferenceSession

from classes import classes


def predict(data_folder='./data'):
    print('Commencing offline scoring.')

    with open(f'{data_folder}/images.pickle', 'rb') as inputfile:
        image_names, images = load(inputfile)

    session = InferenceSession('model.onnx')

    raw_results = [
        session.run(
            [], {'input_1': image_data, 'image_shape': [[416, 416]]}
        )
        for image_data in images
    ]
    results = [
        _postprocess(*raw_result) for raw_result in raw_results
    ]
    _to_csv(results, image_names, data_folder)

    print('Offline scoring complete.')


def _postprocess(raw_boxes, raw_scores, raw_class_indices):
    boxes, scores, detected_classes = [], [], []
    for raw_indices in raw_class_indices[0]:
        detected_classes.append(classes[raw_indices[1]])
        scores.append(raw_scores[tuple(raw_indices)])
        indices = (raw_indices[0], raw_indices[2])
        boxes.append(raw_boxes[indices])

    return boxes, scores, detected_classes


def _to_csv(results, image_names, data_folder):
    column_names = ['file id', 'object', 'score', 'bounding box']

    with open(f'{data_folder}/results.csv', 'w', newline='') as outputfile:
        csv_writer = writer(outputfile, delimiter='|')
        csv_writer.writerow(column_names)
        for result_index, result in enumerate(results):
            image_name = image_names[result_index]
            bounding_boxes, scores, object_names = result
            for object_index, object_name in enumerate(object_names):
                box_string = np.array2string(
                    bounding_boxes[object_index], precision=1, separator=', '
                )
                csv_writer.writerow(
                    [image_name, object_name, scores[object_index], box_string]
                )


if __name__ == '__main__':
    predict(data_folder='/data')
